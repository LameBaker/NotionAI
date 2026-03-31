from __future__ import annotations

import logging

import chromadb
from chromadb.utils.embedding_functions import SentenceTransformerEmbeddingFunction

from app.retrieval import RetrievalChunk

log = logging.getLogger("notionai.vector_store")

# Multilingual model — good quality for Russian text
# Requires "query: " prefix for queries and "passage: " prefix for documents
EMBEDDING_MODEL = "intfloat/multilingual-e5-base"
_PASSAGE_PREFIX = "passage: "
_QUERY_PREFIX = "query: "
_UPSERT_BATCH_SIZE = 500


class ChromaVectorStore:
    """ChromaDB vector store. Used by app/bot.py and sync.py."""

    def __init__(self, *, persist_dir: str = ".chroma_data") -> None:
        self._client = chromadb.PersistentClient(path=persist_dir)
        self._ef = SentenceTransformerEmbeddingFunction(model_name=EMBEDDING_MODEL)
        self._collection = self._client.get_or_create_collection(
            name="notion_chunks_e5",
            metadata={"hnsw:space": "cosine", "hnsw:search_ef": 50},
            embedding_function=self._ef,
        )

    def upsert_chunks(self, chunks: list[dict]) -> None:
        if not chunks:
            return
        for i in range(0, len(chunks), _UPSERT_BATCH_SIZE):
            batch = chunks[i : i + _UPSERT_BATCH_SIZE]
            try:
                self._collection.upsert(
                    ids=[c["chunk_id"] for c in batch],
                    documents=[f"{_PASSAGE_PREFIX}{c['text']}" for c in batch],
                    metadatas=[
                        {
                            "page_id": c.get("page_id", ""),
                            "root_id": c.get("root_id", ""),
                            "title": c.get("title", ""),
                        }
                        for c in batch
                    ],
                )
            except KeyError as exc:
                log.error("Invalid chunk data — missing key %s in batch starting at %d", exc, i)
                raise

    def delete_by_page_id(self, page_id: str) -> None:
        """Delete all chunks for a given page (for stale chunk cleanup)."""
        self._collection.delete(where={"page_id": page_id})

    def search(self, query: str, n_results: int = 5) -> list[RetrievalChunk]:
        try:
            results = self._collection.query(
                query_texts=[f"{_QUERY_PREFIX}{query}"],
                n_results=n_results,
            )
        except Exception:
            log.exception("ChromaDB search failed")
            return []

        chunks = []
        for i, doc_id in enumerate(results["ids"][0]):
            meta = results["metadatas"][0][i]
            # Strip passage prefix from stored document to get original text
            doc_text = results["documents"][0][i]
            if doc_text.startswith(_PASSAGE_PREFIX):
                doc_text = doc_text[len(_PASSAGE_PREFIX) :]
            chunks.append(
                RetrievalChunk(
                    page_id=meta.get("page_id", ""),
                    chunk_id=doc_id,
                    text=doc_text,
                    root_id=meta.get("root_id", ""),
                )
            )
        return chunks

    def clear(self) -> None:
        self._client.delete_collection("notion_chunks_e5")
        self._collection = self._client.get_or_create_collection(
            name="notion_chunks_e5",
            metadata={"hnsw:space": "cosine", "hnsw:search_ef": 50},
            embedding_function=self._ef,
        )
