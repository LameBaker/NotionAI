from app.retrieval import RetrievalChunk, build_authorized_context, filter_authorized_chunks


def test_filter_authorized_chunks_excludes_unauthorized_results() -> None:
    raw_results = [
        RetrievalChunk(page_id="page-1", chunk_id="c1", text="Public policy summary"),
        RetrievalChunk(page_id="page-2", chunk_id="c2", text="SECRET: payroll plan"),
    ]

    filtered = filter_authorized_chunks(raw_results, allowed_page_ids={"page-1"})

    assert filtered == [raw_results[0]]


def test_filter_authorized_chunks_denies_by_default_when_allowed_set_empty() -> None:
    raw_results = [
        RetrievalChunk(page_id="page-1", chunk_id="c1", text="Any content"),
    ]

    filtered = filter_authorized_chunks(raw_results, allowed_page_ids=set())

    assert filtered == []


def test_build_authorized_context_filters_before_assembly() -> None:
    raw_results = [
        RetrievalChunk(page_id="page-1", chunk_id="c1", text="Allowed snippet"),
        RetrievalChunk(page_id="page-2", chunk_id="c2", text="SECRET: do not leak"),
    ]

    context = build_authorized_context(raw_results, allowed_page_ids={"page-1"})

    assert "Allowed snippet" in context
    assert "SECRET" not in context
