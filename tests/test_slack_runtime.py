import pytest

from app.slack_runtime import (
    SlackRuntimeError,
    build_service_request_from_event,
    build_slack_payload_from_service_response,
)


def test_build_service_request_from_event_converts_supported_event() -> None:
    event = {
        "type": "app_mention",
        "text": "How do I deploy?",
        "user_email": "dev1@company.com",
        "channel": "C123",
    }

    request = build_service_request_from_event(event)

    assert request == {
        "user_email": "dev1@company.com",
        "question": "How do I deploy?",
        "channel": "C123",
    }


def test_build_slack_payload_from_service_response_converts_response_shape() -> None:
    service_response = {
        "answer_text": "Use the deploy tool.",
        "sources": [
            {
                "title": "Deploy Guide",
                "path": "/Development/Deploy",
                "last_edited_time": "2026-03-10T11:00:00.000Z",
                "page_id": "page-dev",
            }
        ],
    }

    payload = build_slack_payload_from_service_response(service_response)

    assert payload == {
        "text": "Use the deploy tool.",
        "sources": [
            {
                "title": "Deploy Guide",
                "path": "/Development/Deploy",
                "last_edited_time": "2026-03-10T11:00:00.000Z",
                "page_id": "page-dev",
            }
        ],
    }


def test_build_service_request_from_event_rejects_malformed_or_unsupported_events() -> None:
    with pytest.raises(SlackRuntimeError, match="Unsupported event type"):
        build_service_request_from_event({"type": "message"})

    with pytest.raises(SlackRuntimeError, match="Malformed Slack event"):
        build_service_request_from_event(
            {
                "type": "app_mention",
                "text": "",
                "user_email": "",
            }
        )
