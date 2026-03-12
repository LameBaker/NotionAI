from app.ingestion import IngestionFailure, ingest_page_payloads
from app.notion_source import NotionPageMetadata


def test_ingest_page_payloads_parses_valid_metadata() -> None:
    payloads = [
        {
            "id": "page-123",
            "parent": {"type": "page_id", "page_id": "parent-1"},
            "last_edited_time": "2026-03-12T12:00:00.000Z",
            "path": "/HR/Policies/Leave",
            "properties": {
                "title": {
                    "type": "title",
                    "title": [{"plain_text": "Leave Policy"}],
                },
                "acl_restricted": {"type": "checkbox", "checkbox": True},
                "acl_allow_ou": {
                    "type": "multi_select",
                    "multi_select": [{"name": "/HR"}],
                },
            },
        }
    ]

    result = ingest_page_payloads(payloads)

    assert result.failures == []
    assert result.pages == [
        NotionPageMetadata(
            page_id="page-123",
            parent_id="parent-1",
            title="Leave Policy",
            path="/HR/Policies/Leave",
            last_edited_time="2026-03-12T12:00:00.000Z",
            acl_restricted=True,
            acl_allow_ou=["/HR"],
            acl_allow_users=[],
        )
    ]


def test_ingest_page_payloads_skips_malformed_payloads_and_records_failures() -> None:
    payloads = [
        "not-a-mapping",
        {"id": "   ", "properties": {}},
        {
            "id": "page-ok",
            "parent": {"type": "page_id", "page_id": "parent-ok"},
            "last_edited_time": "2026-03-12T13:00:00.000Z",
            "properties": {
                "title": {
                    "type": "title",
                    "title": [{"plain_text": "OK Page"}],
                }
            },
        },
    ]

    result = ingest_page_payloads(payloads)

    assert [page.page_id for page in result.pages] == ["page-ok"]
    assert result.failures == [
        IngestionFailure(index=0, reason="payload_not_mapping"),
        IngestionFailure(index=1, reason="missing_page_id"),
    ]
