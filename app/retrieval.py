from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class RetrievalChunk:
    page_id: str
    chunk_id: str
    text: str
    root_id: str = ""


def filter_authorized_chunks(
    raw_results: list[RetrievalChunk], *, allowed_page_ids: set[str]
) -> list[RetrievalChunk]:
    if not allowed_page_ids:
        return []

    return [chunk for chunk in raw_results if chunk.page_id in allowed_page_ids]


def build_authorized_context(
    raw_results: list[RetrievalChunk], *, allowed_page_ids: set[str]
) -> str:
    # ACL filtering is applied before assembling prompt context.
    authorized_chunks = filter_authorized_chunks(raw_results, allowed_page_ids=allowed_page_ids)
    return _assemble_context(authorized_chunks)


def _assemble_context(chunks: list[RetrievalChunk]) -> str:
    return "\n\n".join(chunk.text for chunk in chunks)
