from app.notion_source import NotionPageMetadata, parse_notion_page_metadata


def test_parse_notion_page_metadata_extracts_required_fields() -> None:
    payload = {
        "id": "page-123",
        "parent": {"type": "page_id", "page_id": "parent-456"},
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
                "multi_select": [{"name": "/HR"}, {"name": "/PeopleOps"}],
            },
            "acl_allow_users": {
                "type": "rich_text",
                "rich_text": [{"plain_text": "manager@company.com, hrbp@company.com"}],
            },
        },
    }

    metadata = parse_notion_page_metadata(payload)

    assert metadata == NotionPageMetadata(
        page_id="page-123",
        parent_id="parent-456",
        title="Leave Policy",
        path="/HR/Policies/Leave",
        last_edited_time="2026-03-12T12:00:00.000Z",
        acl_restricted=True,
        acl_allow_ou=["/HR", "/PeopleOps"],
        acl_allow_users=["manager@company.com", "hrbp@company.com"],
    )


def test_parse_notion_page_metadata_defaults_acl_values_when_absent() -> None:
    payload = {
        "id": "page-789",
        "parent": {"type": "database_id", "database_id": "db-001"},
        "last_edited_time": "2026-03-12T13:00:00.000Z",
        "properties": {
            "Name": {
                "type": "title",
                "title": [{"plain_text": "Engineering Handbook"}],
            }
        },
    }

    metadata = parse_notion_page_metadata(payload)

    assert metadata.page_id == "page-789"
    assert metadata.parent_id == "db-001"
    assert metadata.title == "Engineering Handbook"
    assert metadata.path is None
    assert metadata.last_edited_time == "2026-03-12T13:00:00.000Z"
    assert metadata.acl_restricted is False
    assert metadata.acl_allow_ou == []
    assert metadata.acl_allow_users == []
