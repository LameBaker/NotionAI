from __future__ import annotations

import chromadb
from chromadb.utils.embedding_functions import SentenceTransformerEmbeddingFunction

from app.retrieval import RetrievalChunk

# Multilingual model — works well with Russian text
EMBEDDING_MODEL = "paraphrase-multilingual-MiniLM-L12-v2"


class ChromaVectorStore:
    """Implements Retriever protocol from app/service.py via search()."""

    def __init__(self, *, persist_dir: str = ".chroma_data") -> None:
        self._client = chromadb.PersistentClient(path=persist_dir)
        self._ef = SentenceTransformerEmbeddingFunction(model_name=EMBEDDING_MODEL)
        self._collection = self._client.get_or_create_collection(
            name="notion_chunks_ml",
            metadata={"hnsw:space": "cosine"},
            embedding_function=self._ef,
        )

    def upsert_chunks(self, chunks: list[dict]) -> None:
        if not chunks:
            return
        self._collection.upsert(
            ids=[c["chunk_id"] for c in chunks],
            documents=[c["text"] for c in chunks],
            metadatas=[
                {"page_id": c["page_id"], "root_id": c["root_id"], "title": c.get("title", "")}
                for c in chunks
            ],
        )

    def search(self, query: str, n_results: int = 5) -> list[RetrievalChunk]:
        if self._collection.count() == 0:
            return []
        results = self._collection.query(query_texts=[query], n_results=n_results)
        chunks = []
        for i, doc_id in enumerate(results["ids"][0]):
            meta = results["metadatas"][0][i]
            chunks.append(
                RetrievalChunk(
                    page_id=meta["page_id"],
                    chunk_id=doc_id,
                    text=results["documents"][0][i],
                    root_id=meta.get("root_id", ""),
                )
            )
        return chunks

    def clear(self) -> None:
        self._client.delete_collection("notion_chunks_ml")
        self._collection = self._client.get_or_create_collection(
            name="notion_chunks_ml",
            metadata={"hnsw:space": "cosine"},
            embedding_function=self._ef,
        )
