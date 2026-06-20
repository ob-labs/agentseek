"""OpenVINO model wrappers for LLM, embeddings, and reranking."""

from __future__ import annotations

import queue
from pathlib import Path
from threading import Thread
from typing import Any, Iterator, List, Optional, Sequence

import numpy as np
from langchain_core.callbacks import Callbacks
from langchain_core.callbacks.manager import CallbackManagerForLLMRun
from langchain_core.documents import Document
from langchain_core.documents.compressor import BaseDocumentCompressor
from langchain_core.embeddings import Embeddings
from langchain_core.language_models.llms import LLM
from langchain_core.outputs import GenerationChunk
from pydantic import ConfigDict


def _make_streamer_class():
    """Create streamer class inheriting from openvino_genai.StreamerBase."""
    import openvino_genai

    class _ChunkStreamer(openvino_genai.StreamerBase):
        """Token streamer implementing StreamerBase protocol."""

        def __init__(self, tokenizer: Any):
            super().__init__()
            self.tokenizer = tokenizer
            self.tokens_cache: list[int] = []
            self.text_queue: queue.Queue[str | None] = queue.Queue()
            self.print_len = 0

        def __iter__(self):
            return self

        def __next__(self) -> str:
            value = self.text_queue.get()
            if value is None:
                raise StopIteration
            return value

        def write(self, token_id: int) -> openvino_genai.StreamingStatus:
            self.tokens_cache.append(token_id)
            text = self.tokenizer.decode(self.tokens_cache)
            if len(text) > self.print_len and text[-1] != chr(65533):
                word = text[self.print_len :]
                self.print_len = len(text)
                self.text_queue.put(word)
            return openvino_genai.StreamingStatus.RUNNING

        def end(self):
            text = self.tokenizer.decode(self.tokens_cache)
            if len(text) > self.print_len:
                self.text_queue.put(text[self.print_len :])
            self.text_queue.put(None)

        def reset(self):
            self.tokens_cache = []
            self.text_queue = queue.Queue()
            self.print_len = 0

    return _ChunkStreamer


class OpenVINOLLM(LLM):
    """LangChain LLM backed by OpenVINO GenAI LLMPipeline."""

    ov_pipe: Any = None
    tokenizer: Any = None
    config: Any = None
    max_new_tokens: int = 512

    model_config = ConfigDict(extra="forbid", protected_namespaces=())

    @classmethod
    def from_model_path(
        cls, model_path: str, device: str = "CPU", **kwargs: Any
    ) -> "OpenVINOLLM":
        import openvino_genai

        ov_pipe = openvino_genai.LLMPipeline(model_path, device, **kwargs)
        config = ov_pipe.get_generation_config()
        tokenizer = ov_pipe.get_tokenizer()
        return cls(ov_pipe=ov_pipe, tokenizer=tokenizer, config=config)

    def _call(
        self,
        prompt: str,
        stop: Optional[List[str]] = None,
        run_manager: Optional[CallbackManagerForLLMRun] = None,
        **kwargs: Any,
    ) -> str:
        self.config.max_new_tokens = self.max_new_tokens
        if stop:
            self.config.stop_strings = set(stop)
        return self.ov_pipe.generate(prompt, self.config)

    def _stream(
        self,
        prompt: str,
        stop: Optional[List[str]] = None,
        run_manager: Optional[CallbackManagerForLLMRun] = None,
        **kwargs: Any,
    ) -> Iterator[GenerationChunk]:
        self.config.max_new_tokens = self.max_new_tokens
        if stop:
            self.config.stop_strings = set(stop)
        StreamerCls = _make_streamer_class()
        streamer = StreamerCls(self.tokenizer)

        def generate():
            streamer.reset()
            try:
                self.ov_pipe.generate(prompt, self.config, streamer)
            finally:
                streamer.end()

        t = Thread(target=generate)
        t.start()
        for chunk_text in streamer:
            chunk = GenerationChunk(text=chunk_text)
            if run_manager:
                run_manager.on_llm_new_token(chunk.text, chunk=chunk)
            yield chunk

    @property
    def _llm_type(self) -> str:
        return "openvino_pipeline"


class OpenVINOEmbeddings(Embeddings):
    """LangChain embeddings via OpenVINO GenAI TextEmbeddingPipeline."""

    def __init__(self, ov_pipe: Any):
        self._ov_pipe = ov_pipe

    @classmethod
    def from_model_path(
        cls, model_path: str, device: str = "CPU"
    ) -> "OpenVINOEmbeddings":
        import openvino_genai

        ov_pipe = openvino_genai.TextEmbeddingPipeline(model_path, device)
        return cls(ov_pipe=ov_pipe)

    def embed_documents(self, texts: List[str]) -> List[List[float]]:
        texts = [t.replace("\n", " ") for t in texts]
        return self._ov_pipe.embed_documents(texts)

    def embed_query(self, text: str) -> List[float]:
        return self._ov_pipe.embed_query(text)


class OpenVINOReranker(BaseDocumentCompressor):
    """Reranker using OpenVINO compiled cross-encoder model."""

    ov_model: Any = None
    tokenizer: Any = None
    top_n: int = 3

    model_config = ConfigDict(extra="forbid", protected_namespaces=())

    @classmethod
    def from_model_path(
        cls, model_path: str, device: str = "CPU", top_n: int = 3
    ) -> "OpenVINOReranker":
        import openvino as ov
        import openvino_genai

        core = ov.Core()
        compiled = core.compile_model(
            str(Path(model_path) / "openvino_model.xml"), device
        )
        tokenizer = openvino_genai.Tokenizer(model_path)
        return cls(ov_model=compiled, tokenizer=tokenizer, top_n=top_n)

    def compress_documents(
        self,
        documents: Sequence[Document],
        query: str,
        callbacks: Optional[Callbacks] = None,
    ) -> Sequence[Document]:
        if not documents:
            return []
        pairs = [query + "</s></s> " + doc.page_content for doc in documents]
        features = self.tokenizer.encode(pairs)
        outputs = self.ov_model(
            {"input_ids": features.input_ids, "attention_mask": features.attention_mask}
        )
        scores = outputs[0][:, 1] if outputs[0].shape[1] > 1 else outputs[0].flatten()
        scores = 1 / (1 + np.exp(-scores))
        ranked = sorted(
            zip(scores, range(len(documents))), key=lambda x: x[0], reverse=True
        )
        results = []
        for score, idx in ranked[: self.top_n]:
            doc = documents[idx]
            results.append(
                Document(
                    page_content=doc.page_content,
                    metadata={**doc.metadata, "relevance_score": float(score)},
                )
            )
        return results
