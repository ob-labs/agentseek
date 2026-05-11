from __future__ import annotations

from collections.abc import Iterable
from dataclasses import replace

from bub_tapestore_sqlalchemy.models import TapeEntryRecord
from bub_tapestore_sqlalchemy.store import SQLAlchemyTapeStore
from republic import RepublicError, TapeEntry, TapeQuery
from republic.core.errors import ErrorKind
from sqlalchemy import select
from sqlalchemy.orm import Session

from agentseek_tapestore_oceanbase.oceanbase import register_oceanbase_dialect
from agentseek_tapestore_oceanbase.vector_support import OceanBaseVectorEnhancer, normalize_vector_metric


class OceanBaseTapeStore(SQLAlchemyTapeStore):
    def __init__(
        self,
        url: str,
        *,
        echo: bool = False,
        embedding_model: str | None = None,
        vector_metric: str = "cosine",
    ) -> None:
        normalized_url = self._normalize_url(url)
        normalized_embedding_model = embedding_model.strip() if embedding_model is not None else None
        if "oceanbase" in normalized_url.drivername:
            register_oceanbase_dialect()

        super().__init__(str(normalized_url), echo=echo)

        self._vector_enhancer: OceanBaseVectorEnhancer | None = None
        if normalized_embedding_model and "oceanbase" in self._url.drivername:
            self._vector_enhancer = OceanBaseVectorEnhancer(
                store=self,
                embedding_model=normalized_embedding_model,
                vector_metric=normalize_vector_metric(vector_metric),
            )

    def fetch_all(self, query: TapeQuery) -> Iterable[TapeEntry]:
        normalized_query = replace(query, _kinds=self._normalized_kinds(query._kinds))
        if not normalized_query._query or self._vector_enhancer is None:
            return super().fetch_all(normalized_query)

        unrestricted_query = replace(normalized_query, _query=None, _limit=None)
        entries = list(super().fetch_all(unrestricted_query))
        if not entries:
            return []

        entry_by_id = {entry.id: entry for entry in entries}
        matched_entry_ids = self._vector_enhancer.matched_entry_ids(normalized_query)
        filtered = [entry_by_id[entry_id] for entry_id in matched_entry_ids if entry_id in entry_by_id]
        if normalized_query._limit is not None:
            return filtered[: normalized_query._limit]
        return filtered

    def resolve_query_bounds(
        self,
        session: Session,
        tape_id: int,
        query: TapeQuery,
    ) -> tuple[int | None, int | None]:
        if query._between_anchors is not None:
            start_name, end_name = query._between_anchors
            start_id = self._find_anchor_entry_id(session, tape_id, start_name, forward=False)
            if start_id is None:
                raise RepublicError(ErrorKind.NOT_FOUND, f"Anchor '{start_name}' was not found.")
            end_id = self._find_anchor_entry_id(
                session,
                tape_id,
                end_name,
                forward=True,
                after_entry_id=start_id,
            )
            if end_id is None:
                raise RepublicError(ErrorKind.NOT_FOUND, f"Anchor '{end_name}' was not found.")
            return start_id, end_id

        if query._after_last:
            anchor_id = self._find_anchor_entry_id(session, tape_id, None, forward=False)
            if anchor_id is None:
                raise RepublicError(ErrorKind.NOT_FOUND, "No anchors found in tape.")
            return anchor_id, None

        if query._after_anchor is not None:
            anchor_id = self._find_anchor_entry_id(session, tape_id, query._after_anchor, forward=False)
            if anchor_id is None:
                raise RepublicError(ErrorKind.NOT_FOUND, f"Anchor '{query._after_anchor}' was not found.")
            return anchor_id, None

        return None, None

    @staticmethod
    def _find_anchor_entry_id(
        session: Session,
        tape_id: int,
        name: str | None,
        *,
        forward: bool,
        after_entry_id: int = 0,
    ) -> int | None:
        statement = (
            select(TapeEntryRecord.entry_id)
            .where(TapeEntryRecord.tape_id == tape_id)
            .where(TapeEntryRecord.kind == "anchor")
        )
        if name is not None:
            statement = statement.where(TapeEntryRecord.anchor_name == name)
        if after_entry_id > 0:
            statement = statement.where(TapeEntryRecord.entry_id > after_entry_id)
        statement = statement.order_by(TapeEntryRecord.entry_id.asc() if forward else TapeEntryRecord.entry_id.desc())
        return session.scalar(statement.limit(1))
