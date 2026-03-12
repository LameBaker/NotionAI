import pytest

from app.google_adapter import GoogleAdapterError, GoogleAdminDirectoryAdapter
from app.local_flow import run_local_flow
from app.notion_adapter import NotionAdapterError, NotionApiAdapter


class FakeGoogleClient:
    def __init__(self, error: Exception | None = None):
        self._error = error

    def get_user(self, email: str):
        if self._error is not None:
            raise self._error
        return None


class FakeNotionClient:
    def __init__(self, error: Exception | None = None):
        self._error = error

    def fetch_pages(self, root_page_id: str):
        if self._error is not None:
            raise self._error
        return []


class FailingService:
    def __init__(self, error: Exception):
        self._error = error

    def answer_question(self, **kwargs):
        raise self._error


def test_google_adapter_maps_connection_failures_to_adapter_error() -> None:
    adapter = GoogleAdminDirectoryAdapter(client=FakeGoogleClient(error=ConnectionError("offline")))

    with pytest.raises(GoogleAdapterError, match="Transient Google directory client failure"):
        adapter.get_user_by_email("dev1@company.com")


def test_notion_adapter_maps_timeout_failures_to_adapter_error() -> None:
    adapter = NotionApiAdapter(client=FakeNotionClient(error=TimeoutError("timeout")))

    with pytest.raises(NotionAdapterError, match="Transient Notion client failure"):
        adapter.fetch_page_payloads("root-1")


def test_local_flow_returns_safe_empty_payload_for_malformed_slack_event() -> None:
    payload = run_local_flow(
        {
            "type": "message",
            "text": "SECRET do not leak",
            "user_email": "dev1@company.com",
        },
        service=FailingService(error=RuntimeError("should not be called")),
        root_policies_by_page_id={},
        source_metadata_by_page_id={},
    )

    assert payload == {"text": "", "sources": []}


def test_local_flow_returns_safe_empty_payload_for_adapter_failures_without_leakage() -> None:
    payload = run_local_flow(
        {
            "type": "app_mention",
            "text": "How do I deploy?",
            "user_email": "dev1@company.com",
            "channel": "C123",
        },
        service=FailingService(error=GoogleAdapterError("SECRET internal failure details")),
        root_policies_by_page_id={},
        source_metadata_by_page_id={},
    )

    assert payload == {"text": "", "sources": []}
