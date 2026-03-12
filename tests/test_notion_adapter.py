import pytest

from app.notion_adapter import NotionAdapterError, NotionApiAdapter


class FakeNotionClient:
    def __init__(self, payloads=None, error: Exception | None = None):
        self._payloads = payloads
        self._error = error
        self.calls: list[str] = []

    def fetch_pages(self, root_page_id: str):
        self.calls.append(root_page_id)
        if self._error is not None:
            raise self._error
        return self._payloads


def test_notion_adapter_fetches_raw_page_payloads_from_client() -> None:
    payloads = [{"id": "page-1"}, {"id": "page-2"}]
    client = FakeNotionClient(payloads=payloads)
    adapter = NotionApiAdapter(client=client)

    result = adapter.fetch_page_payloads("root-1")

    assert result == payloads
    assert client.calls == ["root-1"]


def test_notion_adapter_returns_empty_list_when_client_returns_none() -> None:
    client = FakeNotionClient(payloads=None)
    adapter = NotionApiAdapter(client=client)

    assert adapter.fetch_page_payloads("root-1") == []


def test_notion_adapter_maps_transient_client_failure_to_adapter_error() -> None:
    client = FakeNotionClient(error=TimeoutError("notion timeout"))
    adapter = NotionApiAdapter(client=client)

    with pytest.raises(NotionAdapterError, match="Transient Notion client failure"):
        adapter.fetch_page_payloads("root-1")
