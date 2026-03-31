"""Reranker: re-score search results with a cross-encoder for better relevance."""
from __future__ import annotations

import logging

from sentence_transformers import CrossEncoder

from app.retrieval import RetrievalChunk

log = logging.getLogger("notionai.reranker")

# BGE Reranker — proven combo with BGE-M3 on Russian benchmarks
_DEFAULT_MODEL = "BAAI/bge-reranker-v2-m3"


class BGEReranker:
    def __init__(self, model_name: str = _DEFAULT_MODEL) -> None:
        log.info("Loading reranker model %s...", model_name)
        self._model = CrossEncoder(model_name)

    def rerank(self, query: str, chunks: list[RetrievalChunk], top_k: int = 5) -> list[RetrievalChunk]:
        if not chunks:
            return []
        if len(chunks) <= top_k:
            return chunks

        pairs = [(query, chunk.text) for chunk in chunks]
        scores = self._model.predict(pairs)

        scored = sorted(zip(scores, chunks), key=lambda x: x[0], reverse=True)
        reranked = [chunk for _, chunk in scored[:top_k]]

        log.info("Reranked %d → %d chunks (top score: %.3f, bottom: %.3f)",
                 len(chunks), len(reranked), scored[0][0], scored[min(top_k - 1, len(scored) - 1)][0])

        return reranked
