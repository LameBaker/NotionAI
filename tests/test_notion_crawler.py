from app.notion_crawler import chunk_text


def test_chunk_text_splits_by_size():
    text = "Абзац один.\n\nАбзац два.\n\nАбзац три."
    chunks = chunk_text(text, max_chunk_size=30)
    assert len(chunks) >= 2
    # Multi-paragraph chunks must respect size limit
    for chunk in chunks:
        if "\n\n" in chunk:
            assert len(chunk) <= 30


def test_chunk_text_preserves_all_content():
    text = "Hello world.\n\nFoo bar.\n\nBaz."
    chunks = chunk_text(text, max_chunk_size=1000)
    joined = "\n\n".join(chunks)
    assert "Hello world." in joined
    assert "Foo bar." in joined
    assert "Baz." in joined


def test_chunk_text_empty_input():
    assert chunk_text("", max_chunk_size=100) == []


def test_chunk_text_splits_long_paragraph():
    """A single paragraph longer than max_chunk_size gets split by sentences."""
    text = "Первое предложение. Второе предложение. Третье предложение. Четвертое предложение."
    chunks = chunk_text(text, max_chunk_size=50)
    assert len(chunks) >= 2
    joined = " ".join(chunks)
    assert "Первое" in joined
    assert "Четвертое" in joined
