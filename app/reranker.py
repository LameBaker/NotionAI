"""Reranker: re-score search results with a cross-encoder + OU-based boost."""
from __future__ import annotations

import logging
from pathlib import Path

import yaml
from sentence_transformers import CrossEncoder

from app.retrieval import RetrievalChunk

log = logging.getLogger("notionai.reranker")

# BGE Reranker — proven combo with BGE-M3 on Russian benchmarks
_DEFAULT_MODEL = "BAAI/bge-reranker-v2-m3"

# Boost multiplier for chunks from user's "home" root
_HOME_ROOT_BOOST = 0.15


def _load_ou_home_roots(path: str = "configs/ou_home_roots.yaml") -> dict[str, list[str]]:
    config_path = Path(path)
    if not config_path.exists():
        return {}
    try:
        data = yaml.safe_load(config_path.read_text())
        return data.get("ou_home_roots", {})
    except Exception:
        log.debug("Failed to load ou_home_roots", exc_info=True)
        return {}


class BGEReranker:
    def __init__(self, model_name: str = _DEFAULT_MODEL) -> None:
        log.info("Loading reranker model %s...", model_name)
        self._model = CrossEncoder(model_name)
        self._ou_home_roots = _load_ou_home_roots()

    def rerank(
        self,
        query: str,
        chunks: list[RetrievalChunk],
        top_k: int = 5,
        *,
        user_ou: str = "",
        root_names: dict[str, str] | None = None,
    ) -> list[RetrievalChunk]:
        if not chunks:
            return []
        if len(chunks) <= top_k:
            return chunks

        # Use parent_text for reranking — more context = better scoring
        pairs = [(query, chunk.parent_text if chunk.parent_text else chunk.text) for chunk in chunks]
        scores = self._model.predict(pairs)

        # Apply OU-based boost
        home_root_names = set()
        if user_ou and self._ou_home_roots:
            # Try exact match, then parent OUs
            ou = user_ou
            while ou:
                if ou in self._ou_home_roots:
                    home_root_names = set(self._ou_home_roots[ou])
                    break
                ou = ou.rsplit("/", 1)[0] if "/" in ou else ""

        boosted_scores = []
        for i, (score, chunk) in enumerate(zip(scores, chunks)):
            chunk_root_name = (root_names or {}).get(chunk.root_id, "")
            if chunk_root_name in home_root_names:
                score = score + _HOME_ROOT_BOOST
            boosted_scores.append((score, chunk))

        if home_root_names:
            log.info("OU boost applied for %s → home roots: %s", user_ou, home_root_names)

        scored = sorted(boosted_scores, key=lambda x: x[0], reverse=True)

        # Deduplicate: keep best chunk per page_id
        seen_pages: set[str] = set()
        reranked: list[RetrievalChunk] = []
        for _, chunk in scored:
            if chunk.page_id not in seen_pages:
                seen_pages.add(chunk.page_id)
                reranked.append(chunk)
                if len(reranked) >= top_k:
                    break

        log.info("Reranked %d → %d chunks (top score: %.3f, bottom: %.3f)",
                 len(chunks), len(reranked), scored[0][0], scored[min(top_k - 1, len(scored) - 1)][0])

        return reranked
