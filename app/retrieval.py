from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class RetrievalChunk:
    page_id: str
    chunk_id: str
    text: str
    root_id: str = ""
