from __future__ import annotations

import os
from dataclasses import dataclass


class IntegrationConfigError(ValueError):
    """Raised when required integration configuration is missing or invalid."""


@dataclass(frozen=True)
class IntegrationConfig:
    slack_bot_token: str
    slack_signing_secret: str
    google_workspace_customer_id: str
    google_service_account_email: str
    notion_api_token: str
    local_mode: bool


_REQUIRED_ENV = (
    "SLACK_BOT_TOKEN",
    "SLACK_SIGNING_SECRET",
    "GOOGLE_WORKSPACE_CUSTOMER_ID",
    "GOOGLE_SERVICE_ACCOUNT_EMAIL",
    "NOTION_API_TOKEN",
)


def load_integration_config() -> IntegrationConfig:
    local_mode = _is_truthy(os.environ.get("NOTIONAI_LOCAL_MODE", ""))

    if local_mode:
        return IntegrationConfig(
            slack_bot_token="",
            slack_signing_secret="",
            google_workspace_customer_id="",
            google_service_account_email="",
            notion_api_token="",
            local_mode=True,
        )

    values = {key: os.environ.get(key, "").strip() for key in _REQUIRED_ENV}
    missing = [key for key, value in values.items() if not value]
    if missing:
        raise IntegrationConfigError(f"Missing required env: {', '.join(missing)}")

    return IntegrationConfig(
        slack_bot_token=values["SLACK_BOT_TOKEN"],
        slack_signing_secret=values["SLACK_SIGNING_SECRET"],
        google_workspace_customer_id=values["GOOGLE_WORKSPACE_CUSTOMER_ID"],
        google_service_account_email=values["GOOGLE_SERVICE_ACCOUNT_EMAIL"],
        notion_api_token=values["NOTION_API_TOKEN"],
        local_mode=False,
    )


def _is_truthy(value: str) -> bool:
    return value.strip().lower() in {"1", "true", "yes"}
