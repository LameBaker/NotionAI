from __future__ import annotations

from typing import Protocol


class NotionAdapterError(RuntimeError):
    """Raised when Notion client access fails at the adapter boundary."""


class NotionClient(Protocol):
    def fetch_pages(self, root_page_id: str):
        """Fetch raw page-like payloads for a root page from a Notion-like client."""


class NotionApiAdapter:
    def __init__(self, *, client: NotionClient) -> None:
        self._client = client

    def fetch_page_payloads(self, root_page_id: str) -> list[object]:
        try:
            payloads = self._client.fetch_pages(root_page_id)
        except (TimeoutError, ConnectionError) as exc:
            raise NotionAdapterError("Transient Notion client failure") from exc

        if payloads is None:
            return []

        return list(payloads)
