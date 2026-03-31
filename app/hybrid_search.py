"""Hybrid search: combine vector (semantic) + BM25 (keyword) with Reciprocal Rank Fusion."""
from __future__ import annotations

import logging
import re

from rank_bm25 import BM25Okapi

from app.retrieval import RetrievalChunk

log = logging.getLogger("notionai.search")


def _tokenize(text: str) -> list[str]:
    """Simple whitespace + punctuation tokenizer for BM25."""
    return re.findall(r"\w+", text.lower())


class HybridSearcher:
    """Combines vector search results with BM25 keyword search via RRF."""

    def __init__(self, *, vector_store, rrf_k: int = 60) -> None:
        self._vector_store = vector_store
        self._rrf_k = rrf_k
        self._bm25: BM25Okapi | None = None
        self._bm25_chunks: list[RetrievalChunk] = []

    def build_bm25_index(self, chunks: list[RetrievalChunk]) -> None:
        """Build BM25 index from all chunks (call after vector store is populated)."""
        if not chunks:
            return
        self._bm25_chunks = chunks
        corpus = [_tokenize(c.text) for c in chunks]
        self._bm25 = BM25Okapi(corpus)
        log.info("BM25 index built with %d chunks", len(chunks))

    def search(self, query: str, n_results: int = 20) -> list[RetrievalChunk]:
        """Hybrid search: vector + BM25 merged with Reciprocal Rank Fusion."""
        # Vector search
        vector_results = self._vector_store.search(query, n_results=n_results)

        # BM25 search
        bm25_results: list[RetrievalChunk] = []
        if self._bm25 and self._bm25_chunks:
            query_tokens = _tokenize(query)
            scores = self._bm25.get_scores(query_tokens)
            top_indices = sorted(range(len(scores)), key=lambda i: scores[i], reverse=True)[:n_results]
            bm25_results = [self._bm25_chunks[i] for i in top_indices if scores[i] > 0]

        if not bm25_results:
            return vector_results

        # Reciprocal Rank Fusion
        rrf_scores: dict[str, float] = {}
        chunk_map: dict[str, RetrievalChunk] = {}

        for rank, chunk in enumerate(vector_results):
            rrf_scores[chunk.chunk_id] = rrf_scores.get(chunk.chunk_id, 0) + 1.0 / (self._rrf_k + rank + 1)
            chunk_map[chunk.chunk_id] = chunk

        for rank, chunk in enumerate(bm25_results):
            rrf_scores[chunk.chunk_id] = rrf_scores.get(chunk.chunk_id, 0) + 1.0 / (self._rrf_k + rank + 1)
            chunk_map[chunk.chunk_id] = chunk

        sorted_ids = sorted(rrf_scores, key=lambda cid: rrf_scores[cid], reverse=True)
        merged = [chunk_map[cid] for cid in sorted_ids[:n_results]]

        log.info("Hybrid search: %d vector + %d bm25 → %d merged (RRF)",
                 len(vector_results), len(bm25_results), len(merged))

        return merged
