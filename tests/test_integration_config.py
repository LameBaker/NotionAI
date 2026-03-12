import os

import pytest

from app.integration_config import IntegrationConfig, IntegrationConfigError, load_integration_config


REQUIRED_ENV_KEYS = [
    "SLACK_BOT_TOKEN",
    "SLACK_SIGNING_SECRET",
    "GOOGLE_WORKSPACE_CUSTOMER_ID",
    "GOOGLE_SERVICE_ACCOUNT_EMAIL",
    "NOTION_API_TOKEN",
]


def _clear_required_env() -> None:
    for key in REQUIRED_ENV_KEYS:
        os.environ.pop(key, None)


def test_load_integration_config_reads_required_env_values() -> None:
    _clear_required_env()
    os.environ["SLACK_BOT_TOKEN"] = "xoxb-test"
    os.environ["SLACK_SIGNING_SECRET"] = "signing-secret"
    os.environ["GOOGLE_WORKSPACE_CUSTOMER_ID"] = "C12345"
    os.environ["GOOGLE_SERVICE_ACCOUNT_EMAIL"] = "svc@company.com"
    os.environ["NOTION_API_TOKEN"] = "secret_notion"

    config = load_integration_config()

    assert config == IntegrationConfig(
        slack_bot_token="xoxb-test",
        slack_signing_secret="signing-secret",
        google_workspace_customer_id="C12345",
        google_service_account_email="svc@company.com",
        notion_api_token="secret_notion",
        local_mode=False,
    )


def test_load_integration_config_raises_for_missing_required_env_values() -> None:
    _clear_required_env()

    with pytest.raises(IntegrationConfigError, match="Missing required env"):
        load_integration_config()


def test_load_integration_config_supports_safe_local_mode_defaults() -> None:
    _clear_required_env()
    os.environ["NOTIONAI_LOCAL_MODE"] = "true"

    config = load_integration_config()

    assert config.local_mode is True
    assert config.slack_bot_token == ""
    assert config.slack_signing_secret == ""
    assert config.google_workspace_customer_id == ""
    assert config.google_service_account_email == ""
    assert config.notion_api_token == ""
