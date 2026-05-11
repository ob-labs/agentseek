from __future__ import annotations

from collections.abc import Iterable

from any_llm.api import embedding as anyllm_embedding
from bub_tapestore_sqlalchemy.models import TapeEntryRecord
from pyobvector import VECTOR, VectorIndex, cosine_distance, l2_distance
from pyobvector.client.index_param import IndexParam, VecIndexType
from sqlalchemy import Column, DateTime, ForeignKey, Integer, MetaData, String, Table, Text, func, inspect, select
from sqlalchemy.orm import Session

DEFAULT_VECTOR_RESULT_LIMIT = 10
VECTOR_DIMENSIONS_KEY = "vector_dimensions"
ALLOWED_VECTOR_METRICS = {"cosine", "l2"}


def normalize_vector_metric(value: str) -> str:
    normalized = value.strip().lower()
    if normalized not in ALLOWED_VECTOR_METRICS:
        raise ValueError(f"vector_metric must be one of {sorted(ALLOWED_VECTOR_METRICS)}")
    return normalized


class OceanBaseVectorEnhancer:
    def __init__(
        self,
        *,
        store,
        embedding_model: str,
        vector_metric: str,
    ) -> None:
        self._store = store
        self._embedding_model = embedding_model
        self._vector_metric = normalize_vector_metric(vector_metric)
        self._metadata = MetaData()
        self._vector_table_cache: dict[int, Table] = {}
        self._vector_dimensions = self._load_vector_dimensions()
        if self._vector_dimensions is not None:
            with self._store._session_factory.begin() as session:
                self._ensure_schema(session, self._vector_dimensions)

    def matched_entry_ids(self, query) -> list[int]:
        with self._store._write_lock, self._store._session_factory.begin() as session:
            tape_id = self._store._tape_id(session, query.tape)
            if tape_id is None:
                return []
            lower_bound, upper_bound = self._store.resolve_query_bounds(session, tape_id, query)
            self._embed_unindexed_messages(session, tape_id)
            if self._vector_dimensions is None:
                return []

            table = self._vector_table(self._vector_dimensions)
            query_embedding = self._compute_embeddings([str(query._query)])[0]
            distance_expr = self._distance_expression(table.c.embedding, query_embedding)

            statement = (
                select(table.c.entry_id)
                .join(
                    TapeEntryRecord,
                    (TapeEntryRecord.tape_id == table.c.tape_id) & (TapeEntryRecord.entry_id == table.c.entry_id),
                )
                .where(table.c.tape_id == tape_id)
            )
            if lower_bound is not None:
                statement = statement.where(TapeEntryRecord.entry_id > lower_bound)
            if upper_bound is not None:
                statement = statement.where(TapeEntryRecord.entry_id < upper_bound)
            if query._between_dates is not None:
                start_date, end_date = query._between_dates
                statement = statement.where(TapeEntryRecord.entry_date >= start_date)
                statement = statement.where(TapeEntryRecord.entry_date <= end_date)
            if query._kinds:
                statement = statement.where(TapeEntryRecord.kind.in_(query._kinds))
            statement = statement.order_by(distance_expr, TapeEntryRecord.entry_id)
            statement = statement.limit(query._limit or DEFAULT_VECTOR_RESULT_LIMIT)
            return list(session.scalars(statement).all())

    def _embed_unindexed_messages(self, session: Session, tape_id: int) -> int:
        statement = (
            select(
                TapeEntryRecord.entry_id,
                TapeEntryRecord.payload,
            )
            .where(TapeEntryRecord.tape_id == tape_id)
            .where(TapeEntryRecord.kind == "message")
            .order_by(TapeEntryRecord.entry_id)
        )
        if self._vector_dimensions is not None:
            table = self._vector_table(self._vector_dimensions)
            statement = statement.outerjoin(
                table,
                (table.c.tape_id == TapeEntryRecord.tape_id) & (table.c.entry_id == TapeEntryRecord.entry_id),
            ).where(table.c.entry_id.is_(None))

        rows = session.execute(statement).all()
        texts_by_entry_id: list[tuple[int, str]] = []
        for row in rows:
            text = self._text_of_payload(row.payload)
            if text:
                texts_by_entry_id.append((int(row.entry_id), text))
        if not texts_by_entry_id:
            return 0

        embeddings = self._compute_embeddings([text for _, text in texts_by_entry_id])
        table = self._ensure_schema(session, len(embeddings[0]))
        for (entry_id, _text), embedding in zip(texts_by_entry_id, embeddings, strict=True):
            session.execute(
                table.insert().values(
                    tape_id=tape_id,
                    entry_id=entry_id,
                    embedding=embedding,
                )
            )
        return len(texts_by_entry_id)

    def _ensure_schema(self, session: Session, dimensions: int) -> Table:
        if dimensions <= 0:
            raise ValueError("vector dimensions must be >= 1")
        if self._vector_dimensions is not None and self._vector_dimensions != dimensions:
            raise RuntimeError(f"Embedding dimensions {dimensions} do not match stored size {self._vector_dimensions}.")

        metadata_table = self._metadata_table()
        metadata_table.create(bind=session.connection(), checkfirst=True)

        table = self._vector_table(dimensions)
        table.create(bind=session.connection(), checkfirst=True)
        self._vector_index(table).create(bind=session.connection(), checkfirst=True)

        existing = session.execute(
            select(metadata_table.c.value).where(metadata_table.c.key == VECTOR_DIMENSIONS_KEY)
        ).scalar_one_or_none()
        if existing is None:
            session.execute(
                metadata_table.insert().values(
                    key=VECTOR_DIMENSIONS_KEY,
                    value=str(dimensions),
                )
            )
        elif str(existing) != str(dimensions):
            session.execute(
                metadata_table
                .update()
                .where(metadata_table.c.key == VECTOR_DIMENSIONS_KEY)
                .values(value=str(dimensions))
            )

        self._vector_dimensions = dimensions
        return table

    def _load_vector_dimensions(self) -> int | None:
        inspector = inspect(self._store._engine)
        if "tape_store_oceanbase_metadata" not in set(inspector.get_table_names()):
            return None
        metadata_table = self._metadata_table()
        with self._store._session_factory() as session:
            value = session.execute(
                select(metadata_table.c.value).where(metadata_table.c.key == VECTOR_DIMENSIONS_KEY)
            ).scalar_one_or_none()
        if value is None:
            return None
        return int(value)

    def _metadata_table(self) -> Table:
        return Table(
            "tape_store_oceanbase_metadata",
            self._metadata,
            Column("key", String(128), primary_key=True),
            Column("value", Text, nullable=False),
            Column(
                "created_at",
                DateTime(timezone=True),
                nullable=False,
                server_default=func.now(),
            ),
            extend_existing=True,
        )

    def _vector_table(self, dimensions: int) -> Table:
        table = self._vector_table_cache.get(dimensions)
        if table is not None:
            return table
        table = Table(
            "tape_entry_embeddings",
            self._metadata,
            Column(
                "tape_id",
                Integer,
                ForeignKey("tapes.id", ondelete="CASCADE"),
                primary_key=True,
            ),
            Column("entry_id", Integer, primary_key=True),
            Column("embedding", VECTOR(dimensions), nullable=False),
            Column(
                "created_at",
                DateTime(timezone=True),
                nullable=False,
                server_default=func.now(),
            ),
            extend_existing=True,
        )
        self._vector_table_cache[dimensions] = table
        return table

    def _vector_index(self, table: Table):
        index_param = IndexParam(
            index_name="idx_tape_entry_embeddings_vector",
            field_name="embedding",
            index_type=VecIndexType.HNSW,
            metric_type=self._vector_metric,
            params={
                "M": 16,
                "efConstruction": 200,
                "efSearch": 40,
            },
        )
        return VectorIndex(
            "idx_tape_entry_embeddings_vector",
            table.c.embedding,
            params=index_param.param_str(),
        )

    def _distance_expression(self, embedding_column, query_embedding: list[float]):
        if self._vector_metric == "l2":
            return l2_distance(embedding_column, query_embedding)
        return cosine_distance(embedding_column, query_embedding)

    def _compute_embeddings(self, texts: list[str]) -> list[list[float]]:
        response = anyllm_embedding(
            self._embedding_model,
            texts,
            allow_running_loop=True,
        )
        return self._embedding_response_to_vectors(response)

    @classmethod
    def _embedding_response_to_vectors(cls, response: object) -> list[list[float]]:
        data = getattr(response, "data", None)
        if not isinstance(data, list) or not data:
            raise RuntimeError("Embedding response did not include any vectors.")
        vectors: list[list[float]] = []
        for item in data:
            vectors.append(cls._normalize_embedding(getattr(item, "embedding", None), None))
        return vectors

    @staticmethod
    def _normalize_embedding(
        value: Iterable[float] | object,
        expected_dimensions: int | None,
    ) -> list[float]:
        if not isinstance(value, Iterable) or isinstance(value, (str, bytes, bytearray)):
            raise TypeError("embedding must be an iterable of numbers.")
        embedding: list[float] = []
        for item in value:
            if not isinstance(item, int | float):
                raise TypeError("embedding values must be numbers.")
            embedding.append(float(item))
        if not embedding:
            raise ValueError("embedding must not be empty.")
        if expected_dimensions is not None and len(embedding) != expected_dimensions:
            raise ValueError(f"embedding dimensions must match configured size {expected_dimensions}.")
        return embedding

    @staticmethod
    def _text_of_payload(payload: object) -> str | None:
        parts = list(OceanBaseVectorEnhancer._iter_text_fragments(payload))
        if not parts:
            return None
        return "\n".join(parts)

    @staticmethod
    def _iter_text_fragments(value: object) -> Iterable[str]:
        if isinstance(value, str):
            stripped = value.strip()
            if stripped:
                yield stripped
            return
        if isinstance(value, dict):
            for item in value.values():
                yield from OceanBaseVectorEnhancer._iter_text_fragments(item)
            return
        if isinstance(value, list | tuple):
            for item in value:
                yield from OceanBaseVectorEnhancer._iter_text_fragments(item)
