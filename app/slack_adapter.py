from __future__ import annotations


SAFE_SOURCE_FIELDS = ("title", "path", "last_edited_time", "page_id")


def format_answer_response(answer_text: str, sources: list[dict]) -> dict:
    return {
        "answer_text": str(answer_text),
        "sources": [_sanitize_source(source) for source in sources],
    }


def _sanitize_source(source: dict) -> dict:
    return {field: str(source.get(field, "")) for field in SAFE_SOURCE_FIELDS}
