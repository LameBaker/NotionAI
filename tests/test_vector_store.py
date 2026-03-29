from app.vector_store import ChromaVectorStore


def test_upsert_and_search_returns_relevant_chunks(tmp_path):
    store = ChromaVectorStore(persist_dir=str(tmp_path / "chroma"))

    store.upsert_chunks([
        {"chunk_id": "c1", "page_id": "p1", "root_id": "r1", "title": "Отпуска", "text": "Отпуск оформляется через Zoho People."},
        {"chunk_id": "c2", "page_id": "p2", "root_id": "r1", "title": "Зарплата", "text": "Зарплата выплачивается 10 числа."},
    ])

    results = store.search("как взять отпуск", n_results=2)

    assert len(results) >= 1
    assert results[0].page_id == "p1"
    assert "Zoho" in results[0].text


def test_search_empty_store_returns_empty(tmp_path):
    store = ChromaVectorStore(persist_dir=str(tmp_path / "chroma"))
    results = store.search("anything", n_results=5)
    assert results == []
