from __future__ import annotations

from typing import Protocol

from app.google_adapter import GoogleAdapterError
from app.models import RootAccessPolicy
from app.notion_adapter import NotionAdapterError
from app.slack_runtime import (
    SlackRuntimeError,
    build_safe_empty_payload,
    build_service_request_from_event,
    build_slack_payload_from_service_response,
)


class ServiceOrchestrator(Protocol):
    def answer_question(
        self,
        *,
        user_email: str,
        question: str,
        root_policies_by_page_id: dict[str, RootAccessPolicy],
        source_metadata_by_page_id: dict[str, dict],
    ) -> dict:
        ...


def run_local_flow(
    event: dict,
    *,
    service: ServiceOrchestrator,
    root_policies_by_page_id: dict[str, RootAccessPolicy],
    source_metadata_by_page_id: dict[str, dict],
) -> dict:
    try:
        request = build_service_request_from_event(event)

        service_response = service.answer_question(
            user_email=request["user_email"],
            question=request["question"],
            root_policies_by_page_id=root_policies_by_page_id,
            source_metadata_by_page_id=source_metadata_by_page_id,
        )
    except (SlackRuntimeError, GoogleAdapterError, NotionAdapterError):
        return build_safe_empty_payload()

    return build_slack_payload_from_service_response(service_response)
