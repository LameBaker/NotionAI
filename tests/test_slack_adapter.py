from app.slack_adapter import format_answer_response


def test_format_answer_response_includes_answer_and_safe_source_metadata() -> None:
    payload = format_answer_response(
        answer_text="You can request PTO in Workday.",
        sources=[
            {
                "title": "PTO Policy",
                "path": "/HR/Policies/PTO",
                "last_edited_time": "2026-03-10T09:00:00.000Z",
                "page_id": "page-pto",
            }
        ],
    )

    assert payload["answer_text"] == "You can request PTO in Workday."
    assert payload["sources"] == [
        {
            "title": "PTO Policy",
            "path": "/HR/Policies/PTO",
            "last_edited_time": "2026-03-10T09:00:00.000Z",
            "page_id": "page-pto",
        }
    ]


def test_format_answer_response_drops_unsafe_source_fields() -> None:
    payload = format_answer_response(
        answer_text="See policy",
        sources=[
            {
                "title": "Comp Review",
                "path": "/HR/Confidential",
                "last_edited_time": "2026-03-11T10:00:00.000Z",
                "page_id": "page-conf",
                "text": "SECRET salary bands",
                "snippet": "Top secret",
                "raw_chunk": "Internal only",
            }
        ],
    )

    source = payload["sources"][0]
    assert set(source.keys()) == {"title", "path", "last_edited_time", "page_id"}
    assert "text" not in source
    assert "snippet" not in source
    assert "raw_chunk" not in source


def test_format_answer_response_handles_missing_source_fields_with_safe_defaults() -> None:
    payload = format_answer_response(
        answer_text="No sources",
        sources=[{}],
    )

    assert payload["sources"] == [
        {
            "title": "",
            "path": "",
            "last_edited_time": "",
            "page_id": "",
        }
    ]
