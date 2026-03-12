from __future__ import annotations


class SlackRuntimeError(ValueError):
    """Raised when an incoming Slack-like event cannot be processed safely."""


def build_service_request_from_event(event: dict) -> dict:
    event_type = str(event.get("type", "")).strip()
    if event_type != "app_mention":
        raise SlackRuntimeError("Unsupported event type")

    question = str(event.get("text", "")).strip()
    user_email = str(event.get("user_email", "")).strip().lower()
    channel = str(event.get("channel", "")).strip()

    if not question or not user_email:
        raise SlackRuntimeError("Malformed Slack event")

    return {
        "user_email": user_email,
        "question": question,
        "channel": channel,
    }


def build_slack_payload_from_service_response(service_response: dict) -> dict:
    return {
        "text": str(service_response.get("answer_text", "")),
        "sources": service_response.get("sources", []),
    }
