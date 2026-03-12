from __future__ import annotations

from app.google_adapter import GoogleAdminDirectoryAdapter
from app.identity import GoogleDirectoryIdentityResolver
from app.notion_source import parse_notion_page_metadata


class _GoogleClientFixture:
    def __init__(self, payload: dict[str, str] | None) -> None:
        self._payload = payload

    def get_user(self, email: str) -> dict[str, str] | None:
        return self._payload


def test_google_payload_contract_baseline_placeholder() -> None:
    payload = {
        "primaryEmail": "engineer@example.com",
        "orgUnitPath": "/Development",
    }
    adapter = GoogleAdminDirectoryAdapter(client=_GoogleClientFixture(payload))
    resolver = GoogleDirectoryIdentityResolver(client=adapter, corporate_domain="example.com")

    assert resolver.resolve_org_unit_by_email("engineer@example.com") == "/Development"


def test_notion_payload_contract_baseline_placeholder() -> None:
    raw_page = {
        "id": "page-123",
        "parent": {"page_id": "root-hr"},
        "path": "/HR/Benefits",
        "last_edited_time": "2026-03-11T10:00:00.000Z",
        "properties": {
            "Title": {
                "type": "title",
                "title": [{"plain_text": "Benefits Handbook"}],
            },
            "acl_restricted": {"checkbox": True},
            "acl_allow_ou": {
                "type": "multi_select",
                "multi_select": [{"name": "/HR"}],
            },
            "acl_allow_users": {
                "type": "rich_text",
                "rich_text": [{"plain_text": "legal@example.com, hr@example.com"}],
            },
        },
    }

    parsed = parse_notion_page_metadata(raw_page)

    assert parsed.page_id == "page-123"
    assert parsed.parent_id == "root-hr"
    assert parsed.title == "Benefits Handbook"
    assert parsed.path == "/HR/Benefits"
    assert parsed.last_edited_time == "2026-03-11T10:00:00.000Z"
    assert parsed.acl_restricted is True
    assert parsed.acl_allow_ou == ["/HR"]
    assert parsed.acl_allow_users == ["legal@example.com", "hr@example.com"]
