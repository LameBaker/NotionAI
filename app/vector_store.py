from __future__ import annotations

import chromadb
from chromadb.utils.embedding_functions import SentenceTransformerEmbeddingFunction

from app.retrieval import RetrievalChunk

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
            metadata={"hnsw:space": "cosine"},
            embedding_function=self._ef,
        )

    def upsert_chunks(self, chunks: list[dict]) -> None:
        if not chunks:
            return
        for i in range(0, len(chunks), _UPSERT_BATCH_SIZE):
            batch = chunks[i : i + _UPSERT_BATCH_SIZE]
            self._collection.upsert(
                ids=[c["chunk_id"] for c in batch],
                documents=[f"{_PASSAGE_PREFIX}{c['text']}" for c in batch],
                metadatas=[
                    {
                        "page_id": c["page_id"],
                        "root_id": c["root_id"],
                        "title": c.get("title", ""),
                        "text": c["text"],  # store original text without prefix
                    }
                    for c in batch
                ],
            )

    def delete_by_page_id(self, page_id: str) -> None:
        """Delete all chunks for a given page (for stale chunk cleanup)."""
        self._collection.delete(where={"page_id": page_id})

    def search(self, query: str, n_results: int = 5) -> list[RetrievalChunk]:
        if self._collection.count() == 0:
            return []
        results = self._collection.query(
            query_texts=[f"{_QUERY_PREFIX}{query}"],
            n_results=n_results,
        )
        chunks = []
        for i, doc_id in enumerate(results["ids"][0]):
            meta = results["metadatas"][0][i]
            chunks.append(
                RetrievalChunk(
                    page_id=meta["page_id"],
                    chunk_id=doc_id,
                    text=meta.get("text", results["documents"][0][i]),  # prefer original text
                    root_id=meta.get("root_id", ""),
                )
            )
        return chunks

    def clear(self) -> None:
        self._client.delete_collection("notion_chunks_e5")
        self._collection = self._client.get_or_create_collection(
            name="notion_chunks_e5",
            metadata={"hnsw:space": "cosine"},
            embedding_function=self._ef,
        )
