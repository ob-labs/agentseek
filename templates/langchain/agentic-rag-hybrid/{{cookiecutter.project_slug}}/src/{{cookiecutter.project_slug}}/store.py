from __future__ import annotations

import hashlib
import re
from dataclasses import replace
from pathlib import Path
from typing import Any

import yaml

from .embeddings import EmbeddingEngine, caption_image
from .hybrid import clamp_top_k, normalize_query, weighted_fuse, weights_for_mode
from .media import scan_images
from .models import ImageRecord, SearchHit, SearchMode, SearchTrace
from .settings import Settings, get_settings


def _image_id(path: Path) -> str:
    digest = hashlib.sha1(str(path.resolve()).encode("utf-8")).hexdigest()[:16]
    return f"{path.stem}-{digest}"


def _query_terms(query: str) -> list[str]:
    return list(dict.fromkeys(re.findall(r"\w+", query.lower())))


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


class HybridImageStore:
    def __init__(
        self,
        settings: Settings | None = None,
        embedding_engine: EmbeddingEngine | None = None,
    ) -> None:
        import pyseekdb
        from pyseekdb import Configuration, HNSWConfiguration

        self.settings = settings or get_settings()
        self.embedding_engine = embedding_engine or EmbeddingEngine(self.settings)
        self.client = pyseekdb.Client(
            host=self.settings.seekdb_host,
            port=int(self.settings.seekdb_port),
            database=self.settings.seekdb_db_name,
            user=self.settings.seekdb_user,
            password=self.settings.seekdb_password,
        )
        self.collection = self.client.get_or_create_collection(
            name=self.settings.image_table_name,
            configuration=Configuration(
                hnsw=HNSWConfiguration(
                    dimension=self.settings.embedding_dimension,
                    distance="l2",
                )
            ),
            embedding_function=None,
        )

    def ingest_directory(self, directory: Path) -> list[ImageRecord]:
        manifest = _caption_manifest(directory)
        records: list[ImageRecord] = []
        ids: list[str] = []
        embeddings: list[list[float]] = []
        metadatas: list[dict[str, str]] = []
        documents: list[str] = []
        for image_path in scan_images(directory):
            manifest_item = manifest.get(image_path.name, {})
            caption = str(manifest_item.get("caption") or caption_image(image_path, self.settings))
            tags = ", ".join(manifest_item.get("tags", []))
            image_id = _image_id(image_path)
            record = ImageRecord(
                image_id=image_id,
                file_name=image_path.name,
                file_path=image_path,
                caption=caption,
                metadata={"source_dir": str(directory), "tags": tags},
            )
            ids.append(image_id)
            embeddings.append(self.embedding_engine.embed_image(image_path))
            metadatas.append(
                {
                    "file_name": record.file_name,
                    "file_path": str(record.file_path),
                    "source_dir": str(directory),
                    "tags": tags,
                }
            )
            documents.append(caption)
            records.append(record)
        if ids:
            self.collection.upsert(
                ids=ids,
                embeddings=embeddings,
                metadatas=metadatas,
                documents=documents,
            )
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
        return {
            mode: self.search_text(query, mode, top_k)
            for mode in ("balanced", "semantic", "keyword", "exact")
        }

    def _search_routes(
        self,
        query: str,
        query_embedding: list[float],
        mode: SearchMode,
        top_k: int,
    ) -> SearchTrace:
        recall = max(top_k * self.settings.hybrid_recall_multiplier, top_k)
        terms = _query_terms(query)
        vector_results = self.collection.query(
            query_embeddings=[query_embedding],
            n_results=recall,
            include=["metadatas", "documents"],
        )
        fulltext_results = self.collection.get(
            where_document={"$contains": query},
            limit=recall,
            include=["metadatas", "documents"],
        )
        sparse_hits = self._sparse_hits(terms, recall)
        metadata_results = self.collection.get(
            limit=recall * 2,
            include=["metadatas", "documents"],
        )
        return _format_trace(
            query=query,
            mode=mode,
            vector_hits=self._query_hits(vector_results),
            sparse_hits=sparse_hits,
            fulltext_hits=self._get_hits(fulltext_results),
            metadata_hits=self._metadata_hits(metadata_results, terms, recall),
            top_k=top_k,
        )

    def _sparse_hits(self, terms: list[str], recall: int) -> list[SearchHit]:
        hits_by_id: dict[str, SearchHit] = {}
        score_by_id: dict[str, float] = {}
        terms_by_id: dict[str, set[str]] = {}
        for term in terms:
            raw = self.collection.get(
                where_document={"$contains": term},
                limit=recall,
                include=["metadatas", "documents"],
            )
            for rank, hit in enumerate(self._get_hits(raw), start=1):
                hits_by_id.setdefault(hit.image_id, hit)
                score_by_id[hit.image_id] = score_by_id.get(hit.image_id, 0.0) + (1.0 / rank)
                terms_by_id.setdefault(hit.image_id, set()).add(term)
        ranked_ids = sorted(score_by_id, key=lambda image_id: (-score_by_id[image_id], hits_by_id[image_id].file_name))
        return [
            replace(hits_by_id[image_id], rank=index + 1, matched_terms=sorted(terms_by_id[image_id]))
            for index, image_id in enumerate(ranked_ids[:recall])
        ]

    def _metadata_hits(self, raw: dict[str, Any], terms: list[str], recall: int) -> list[SearchHit]:
        ranked: list[tuple[int, SearchHit]] = []
        for hit in self._get_hits(raw):
            metadata_text = " ".join([hit.file_name, *[str(value) for value in hit.metadata.values()]]).lower()
            matched = [term for term in terms if term in metadata_text]
            if matched:
                ranked.append((len(matched), replace(hit, matched_terms=matched)))
        ranked.sort(key=lambda item: (-item[0], item[1].file_name))
        return [replace(hit, rank=index + 1) for index, (_, hit) in enumerate(ranked[:recall])]

    def _query_hits(self, raw: dict[str, Any]) -> list[SearchHit]:
        ids = raw.get("ids", [[]])[0]
        metadatas = raw.get("metadatas", [[]])[0]
        documents = raw.get("documents", [[]])[0]
        distances = raw.get("distances", [[]])[0] if raw.get("distances") else []
        return [
            self._hit(
                image_id=image_id,
                metadata=metadatas[index] if index < len(metadatas) else {},
                caption=documents[index] if index < len(documents) else "",
                rank=index + 1,
                distance=distances[index] if index < len(distances) else None,
            )
            for index, image_id in enumerate(ids)
        ]

    def _get_hits(self, raw: dict[str, Any]) -> list[SearchHit]:
        ids = raw.get("ids", [])
        metadatas = raw.get("metadatas", [])
        documents = raw.get("documents", [])
        return [
            self._hit(
                image_id=image_id,
                metadata=metadatas[index] if index < len(metadatas) else {},
                caption=documents[index] if index < len(documents) else "",
                rank=index + 1,
                distance=None,
            )
            for index, image_id in enumerate(ids)
        ]

    def _hit(
        self,
        image_id: str,
        metadata: dict[str, str],
        caption: str,
        rank: int,
        distance: float | None,
    ) -> SearchHit:
        file_name = metadata.get("file_name", image_id)
        return SearchHit(
            image_id=image_id,
            file_name=file_name,
            image_url=f"/custom/media/images/{image_id}",
            caption=caption,
            rank=rank,
            distance=distance,
            metadata=metadata,
        )
