from __future__ import annotations

import hashlib
import json
import re
import shutil
from collections import defaultdict, deque
from dataclasses import replace
from pathlib import Path
from typing import Any

import yaml
from langchain_core.documents import Document
from langchain_core.embeddings import Embeddings

from .embeddings import EmbeddingEngine, caption_image
from .hybrid import clamp_top_k, normalize_query, weighted_fuse, weights_for_mode
from .media import scan_images
from .models import ImageRecord, SearchHit, SearchMode, SearchTrace
from .settings import Settings, get_settings


def _image_id(path: Path) -> str:
    digest = hashlib.sha1(str(path.resolve()).encode("utf-8")).hexdigest()[:16]
    readable_stem = re.sub(r"[^A-Za-z0-9._-]+", "-", path.stem).strip("._-")[:64].strip("._-")
    return f"{readable_stem or 'image'}-{digest}"


def _query_terms(query: str) -> list[str]:
    return list(dict.fromkeys(re.findall(r"\w+", query.lower())))


def _positive_tags(tags: Any) -> list[str]:
    if isinstance(tags, str):
        raw_tags = tags.split(",")
    elif isinstance(tags, list):
        raw_tags = [str(tag) for tag in tags]
    else:
        raw_tags = []

    return [
        tag.strip()
        for tag in raw_tags
        if tag.strip() and not tag.strip().lower().startswith(("not ", "no "))
    ]


def _metadata_search_text(metadata: dict[str, Any]) -> str:
    fields: list[str] = []
    for key, value in metadata.items():
        if key not in {"file_name", "tags", "manifest_id"}:
            continue
        if key == "tags":
            fields.extend(_positive_tags(value))
        else:
            fields.append(str(value))
    return " ".join(fields)


def _document_search_text(document: Document) -> str:
    metadata = dict(document.metadata)
    return " ".join(
        [
            document.page_content,
            str(metadata.get("caption", "")),
            " ".join(_positive_tags(metadata.get("tags", ""))),
            str(metadata.get("manifest_id", "")),
        ]
    ).lower()


def _term_score(text: str, terms: list[str], query: str) -> tuple[float, list[str]]:
    matched: list[str] = []
    score = 0.0
    for term in terms:
        occurrences = len(re.findall(rf"\b{re.escape(term)}\b", text))
        if occurrences:
            matched.append(term)
            score += min(occurrences, 3)
    if query.lower() in text:
        score += len(terms)
    if terms:
        score += len(matched) / len(terms)
    return score, matched


def _sparse_vector(text: str) -> dict[int, float]:
    vector: dict[int, float] = {}
    for term in _query_terms(text):
        digest = hashlib.sha1(term.encode("utf-8")).hexdigest()
        index = (int(digest[:8], 16) % 50_000) + 1
        vector[index] = vector.get(index, 0.0) + 1.0
    return vector


def _caption_manifest(directory: Path) -> dict[str, dict[str, Any]]:
    for manifest_path in (directory / "manifest.yml", directory.parent / "manifest.yml"):
        if not manifest_path.is_file():
            continue
        data = yaml.safe_load(manifest_path.read_text(encoding="utf-8")) or {}
        return {
            item["file_name"]: item
            for item in data.get("images", [])
            if isinstance(item, dict) and item.get("file_name")
        }
    return {}


def _format_trace(
    query: str,
    mode: SearchMode,
    vector_hits: list[SearchHit],
    sparse_hits: list[SearchHit],
    fulltext_hits: list[SearchHit],
    metadata_hits: list[SearchHit],
    top_k: int,
) -> SearchTrace:
    weights = weights_for_mode(mode)
    hits = weighted_fuse(vector_hits, sparse_hits, fulltext_hits, metadata_hits, weights, top_k)
    return SearchTrace(
        query=query,
        mode=mode,
        weights=weights,
        route_counts={
            "vector": len(vector_hits),
            "sparse": len(sparse_hits),
            "fulltext": len(fulltext_hits),
            "metadata": len(metadata_hits),
        },
        hits=hits,
        explanation=(
            f"{mode} mode uses vector={weights.vector:.0%}, "
            f"sparse={weights.sparse:.0%}, fulltext={weights.fulltext:.0%}, "
            f"metadata={weights.metadata:.0%}."
        ),
    )


class HybridImageEmbeddings(Embeddings):
    """LangChain embedding adapter that lets image ingest store captions as text."""

    def __init__(self, engine: EmbeddingEngine) -> None:
        self.engine = engine
        self._staged_image_paths: dict[str, deque[Path]] = defaultdict(deque)

    def stage_image_document(self, page_content: str, image_path: Path) -> None:
        self._staged_image_paths[page_content].append(image_path)

    def embed_documents(self, texts: list[str]) -> list[list[float]]:
        vectors: list[list[float]] = []
        for text in texts:
            staged = self._staged_image_paths.get(text)
            if staged:
                vectors.append(self.engine.embed_image(staged.popleft()))
            else:
                vectors.append(self.engine.embed_text(text))
        return vectors

    def embed_query(self, text: str) -> list[float]:
        return self.engine.embed_text(text)


class HybridImageStore:
    def __init__(
        self,
        settings: Settings | None = None,
        embedding_engine: EmbeddingEngine | None = None,
    ) -> None:
        from langchain_oceanbase.vectorstores import OceanbaseVectorStore

        self.settings = settings or get_settings()
        self.embedding_engine = embedding_engine or EmbeddingEngine(self.settings)
        self.embedding_adapter = HybridImageEmbeddings(self.embedding_engine)
        self.vector_store = OceanbaseVectorStore(
            embedding_function=self.embedding_adapter,
            table_name=self.settings.image_table_name,
            connection_args={"db_name": self.settings.seekdb_db_name},
            path=str(self.settings.seekdb_path),
            embedding_dim=self.settings.embedding_dimension,
            vidx_metric_type="l2",
            include_sparse=True,
            include_fulltext=True,
        )

    def _managed_image_path(self, image_path: Path, image_id: str) -> Path:
        return self.settings.media_data_dir / "images" / f"{image_id}{image_path.suffix.lower()}"

    def ingest_directory(self, directory: Path) -> list[ImageRecord]:
        manifest = _caption_manifest(directory)
        records: list[ImageRecord] = []
        ids: list[str] = []
        documents: list[Document] = []
        extras: list[dict[str, Any]] = []
        for image_path in scan_images(directory):
            source_path = image_path.resolve()
            image_id = _image_id(source_path)
            managed_path = self._managed_image_path(source_path, image_id)
            managed_path.parent.mkdir(parents=True, exist_ok=True)
            if source_path != managed_path.resolve():
                shutil.copy2(source_path, managed_path)

            manifest_item = manifest.get(source_path.name, {})
            caption = str(manifest_item.get("caption") or caption_image(managed_path, self.settings))
            manifest_tags = manifest_item.get("tags", [])
            tags = ", ".join(manifest_tags)
            positive_tags = " ".join(_positive_tags(manifest_tags))
            manifest_id = str(manifest_item.get("id") or source_path.stem)
            metadata = {
                "image_id": image_id,
                "file_name": source_path.name,
                "file_path": str(managed_path),
                "source_dir": str(directory),
                "tags": tags,
                "manifest_id": manifest_id,
                "caption": caption,
            }
            record = ImageRecord(
                image_id=image_id,
                file_name=source_path.name,
                file_path=managed_path,
                caption=caption,
                metadata=metadata,
            )
            ids.append(image_id)
            self.embedding_adapter.stage_image_document(caption, managed_path)
            documents.append(Document(id=image_id, page_content=caption, metadata=metadata))
            search_text = " ".join([caption, positive_tags, source_path.name, manifest_id])
            extras.append(
                {
                    "sparse_embedding": _sparse_vector(search_text),
                    "fulltext_content": search_text,
                }
            )
            records.append(record)
        if ids:
            self.vector_store.add_documents(
                documents,
                ids=ids,
                extras=extras,
            )
            self._save_index_ids(ids)
        return records

    def search_text(self, query: str, mode: SearchMode, top_k: int) -> SearchTrace:
        query = normalize_query(query)
        top_k = clamp_top_k(top_k, self.settings.hybrid_max_top_k)
        query_embedding = self.embedding_engine.embed_text(query)
        return self._search_routes(query, query_embedding, mode, top_k)

    def search_image(self, image_path: Path, mode: SearchMode, top_k: int) -> SearchTrace:
        query = caption_image(image_path, self.settings)
        top_k = clamp_top_k(top_k, self.settings.hybrid_max_top_k)
        query_embedding = self.embedding_engine.embed_image(image_path)
        return self._search_routes(query, query_embedding, mode, top_k)

    def compare_modes(self, query: str, top_k: int) -> dict[SearchMode, SearchTrace]:
        query = normalize_query(query)
        top_k = clamp_top_k(top_k, self.settings.hybrid_max_top_k)
        query_embedding = self.embedding_engine.embed_text(query)
        candidates = self._retrieve_candidates(query, query_embedding, top_k)
        return {
            mode: _format_trace(query, mode, *candidates, top_k)
            for mode in ("balanced", "semantic", "keyword", "exact")
        }

    def _search_routes(
        self,
        query: str,
        query_embedding: list[float],
        mode: SearchMode,
        top_k: int,
    ) -> SearchTrace:
        candidates = self._retrieve_candidates(query, query_embedding, top_k)
        return _format_trace(query, mode, *candidates, top_k)

    def _retrieve_candidates(
        self,
        query: str,
        query_embedding: list[float],
        top_k: int,
    ) -> tuple[list[SearchHit], list[SearchHit], list[SearchHit], list[SearchHit]]:
        recall = max(top_k * self.settings.hybrid_recall_multiplier, top_k)
        terms = _query_terms(query)
        vector_results = self.vector_store.similarity_search_with_score_by_vector(query_embedding, k=recall)
        fulltext_hits = self._fulltext_hits(query, recall)
        indexed_docs = self.vector_store.get_by_ids(self._auxiliary_index_ids())
        return (
            self._scored_document_hits(vector_results),
            self._sparse_hits(query, recall, indexed_docs),
            fulltext_hits,
            self._metadata_hits(indexed_docs, terms, recall),
        )

    def _fulltext_hits(self, query: str, recall: int) -> list[SearchHit]:
        docs = self.vector_store.advanced_hybrid_search(
            fulltext_query=query,
            k=recall,
            modality_weights={"vector": 0.0, "sparse": 0.0, "fulltext": 1.0},
        )
        return self._document_hits_with_terms(docs, query)

    def _sparse_hits(
        self,
        query: str,
        recall: int,
        indexed_docs: list[Document] | None = None,
    ) -> list[SearchHit]:
        sparse_query = _sparse_vector(query)
        if not sparse_query:
            return []
        docs = self.vector_store.similarity_search_with_sparse_vector(sparse_query, k=recall)
        if indexed_docs is None:
            indexed_docs = self.vector_store.get_by_ids(self._auxiliary_index_ids())
        doc_pool = self._dedupe_documents([*docs, *indexed_docs])
        ranked_hits = self._rank_term_document_hits(doc_pool, query, recall)
        if ranked_hits:
            return ranked_hits
        return self._document_hits_with_terms(docs, query)

    def _metadata_hits_from_index(self, terms: list[str], recall: int) -> list[SearchHit]:
        return self._metadata_hits(self.vector_store.get_by_ids(self._auxiliary_index_ids()), terms, recall)

    def _metadata_hits(self, docs: list[Document], terms: list[str], recall: int) -> list[SearchHit]:
        ranked: list[tuple[int, SearchHit]] = []
        for hit, document in zip(self._document_hits(docs), docs, strict=False):
            metadata_text = _metadata_search_text(dict(document.metadata)).lower()
            matched = [term for term in terms if re.search(rf"\b{re.escape(term)}\b", metadata_text)]
            if matched:
                ranked.append((len(matched), replace(hit, matched_terms=matched)))
        ranked.sort(key=lambda item: (-item[0], item[1].file_name))
        return [replace(hit, rank=index + 1) for index, (_, hit) in enumerate(ranked[:recall])]

    def _scored_document_hits(self, results: list[tuple[Document, float]]) -> list[SearchHit]:
        return [
            self._hit_from_document(
                document=document,
                rank=index + 1,
                distance=score,
            )
            for index, (document, score) in enumerate(results)
        ]

    def _document_hits(self, docs: list[Document]) -> list[SearchHit]:
        return [
            self._hit_from_document(document=document, rank=index + 1, distance=None)
            for index, document in enumerate(docs)
        ]

    def _document_hits_with_terms(self, docs: list[Document], query: str) -> list[SearchHit]:
        terms = _query_terms(query)
        hits: list[SearchHit] = []
        for hit, document in zip(self._document_hits(docs), docs, strict=False):
            _, matched = _term_score(_document_search_text(document), terms, query)
            hits.append(replace(hit, matched_terms=matched))
        return hits

    def _rank_term_document_hits(self, docs: list[Document], query: str, recall: int) -> list[SearchHit]:
        terms = _query_terms(query)
        ranked: list[tuple[float, SearchHit]] = []
        for hit, document in zip(self._document_hits(docs), docs, strict=False):
            score, matched = _term_score(_document_search_text(document), terms, query)
            if matched:
                ranked.append((score, replace(hit, matched_terms=matched, distance=1.0 / score if score else None)))
        ranked.sort(key=lambda item: (-item[0], item[1].file_name))
        return [replace(hit, rank=index + 1) for index, (_, hit) in enumerate(ranked[:recall])]

    def _dedupe_documents(self, docs: list[Document]) -> list[Document]:
        deduped: dict[str, Document] = {}
        for index, document in enumerate(docs):
            metadata = dict(document.metadata)
            key = str(metadata.get("image_id") or document.id or metadata.get("manifest_id") or metadata.get("file_name") or index)
            deduped.setdefault(key, document)
        return list(deduped.values())

    def _hit_from_document(
        self,
        document: Document,
        rank: int,
        distance: float | None,
    ) -> SearchHit:
        metadata = {str(key): str(value) for key, value in document.metadata.items()}
        image_id = str(metadata.get("image_id") or document.id or metadata.get("manifest_id") or rank)
        file_name = metadata.get("file_name", image_id)
        return SearchHit(
            image_id=image_id,
            file_name=file_name,
            image_url=f"/custom/media/images/{image_id}",
            caption=metadata.get("caption") or document.page_content,
            rank=rank,
            distance=distance,
            metadata=metadata,
        )

    def _index_ids_path(self) -> Path:
        return self.settings.media_data_dir / "indexes" / f"{self.settings.image_table_name}.json"

    def _save_index_ids(self, ids: list[str]) -> None:
        path = self._index_ids_path()
        path.parent.mkdir(parents=True, exist_ok=True)
        existing = self._load_index_ids()
        merged = list(dict.fromkeys([*existing, *ids]))
        path.write_text(json.dumps(merged, indent=2), encoding="utf-8")

    def _load_index_ids(self) -> list[str]:
        path = self._index_ids_path()
        if not path.is_file():
            return []
        data = json.loads(path.read_text(encoding="utf-8"))
        return [str(item) for item in data if item]

    def _auxiliary_index_ids(self) -> list[str]:
        limit = max(self.settings.hybrid_auxiliary_candidate_limit, 0)
        if limit == 0:
            return []
        return self._load_index_ids()[:limit]
