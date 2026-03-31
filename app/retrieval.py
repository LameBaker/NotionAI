from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class RetrievalChunk:
    page_id: str
    chunk_id: str
    text: str          # small child chunk (used for search)
    root_id: str = ""
    title: str = ""
    page_url: str = ""
    parent_text: str = ""  # large parent chunk (used for LLM context)
