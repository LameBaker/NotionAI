"""Semantic cache: return cached answers for similar questions."""
from __future__ import annotations

import json
import logging
import time
import threading

log = logging.getLogger("notionai.cache")

# Cache TTL in seconds (1 hour)
_DEFAULT_TTL = 3600
# Similarity threshold (0-1, higher = stricter match)
_SIMILARITY_THRESHOLD = 0.92


class SemanticCache:
    """Simple in-memory semantic cache using ChromaDB collection."""

    def __init__(self, *, vector_store, ttl: float = _DEFAULT_TTL) -> None:
        self._client = vector_store._client
        self._ef = vector_store._ef
        self._ttl = ttl
        self._lock = threading.Lock()
        self._collection = self._client.get_or_create_collection(
            name="query_cache",
            metadata={"hnsw:space": "cosine"},
            embedding_function=self._ef,
        )
        log.info("Semantic cache initialized (TTL=%ds)", ttl)

    def get(self, query: str, user_ou: str = "") -> dict | None:
        """Check cache for a similar query from same OU. Returns {answer, sources} or None."""
        with self._lock:
            if self._collection.count() == 0:
                return None

            try:
                results = self._collection.query(query_texts=[query], n_results=1, include=["metadatas", "distances"])
            except Exception:
                return None

            if not results["ids"][0]:
                return None

            meta = results["metadatas"][0][0]
            distance = results["distances"][0][0] if results.get("distances") else 1.0

            similarity = 1 - distance
            if similarity < _SIMILARITY_THRESHOLD:
                return None

            cached_at = meta.get("cached_at", 0)
            if time.time() - float(cached_at) > self._ttl:
                self._collection.delete(ids=[results["ids"][0][0]])
                return None

            # Check OU matches
            cached_ou = meta.get("user_ou", "")
            if cached_ou != user_ou:
                return None

            answer = meta.get("answer", "")
            try:
                sources = json.loads(meta.get("sources_json", "[]"))
            except Exception:
                sources = []

            log.info("Cache HIT (similarity=%.3f, ou=%s): %s", similarity, user_ou, query[:50])
            return {"answer": answer, "sources": sources}

    def put(self, query: str, answer: str, sources: list[dict] | None = None, user_ou: str = "") -> None:
        """Cache an answer with sources for a query, scoped by OU."""
        with self._lock:
            cache_id = f"cache_{hash(query + user_ou) & 0xFFFFFFFF}"
            try:
                sources_json = json.dumps(sources or [], ensure_ascii=False)[:3000]
                self._collection.upsert(
                    ids=[cache_id],
                    documents=[query],
                    metadatas=[{
                        "answer": answer[:3000],
                        "sources_json": sources_json,
                        "user_ou": user_ou,
                        "cached_at": str(time.time()),
                    }],
                )
            except Exception:
                log.debug("Cache put failed", exc_info=True)
