from __future__ import annotations

from dataclasses import dataclass

from app.notion_source import NotionPageMetadata, parse_notion_page_metadata


@dataclass(frozen=True)
class IngestionFailure:
    index: int
    reason: str


@dataclass(frozen=True)
class IngestionResult:
    pages: list[NotionPageMetadata]
    failures: list[IngestionFailure]


def ingest_page_payloads(payloads: list[object]) -> IngestionResult:
    pages: list[NotionPageMetadata] = []
    failures: list[IngestionFailure] = []

    for index, payload in enumerate(payloads):
        if not isinstance(payload, dict):
            failures.append(IngestionFailure(index=index, reason="payload_not_mapping"))
            continue

        try:
            metadata = parse_notion_page_metadata(payload)
        except Exception:
            failures.append(IngestionFailure(index=index, reason="parse_error"))
            continue

        if not metadata.page_id:
            failures.append(IngestionFailure(index=index, reason="missing_page_id"))
            continue

        pages.append(metadata)

    return IngestionResult(pages=pages, failures=failures)
