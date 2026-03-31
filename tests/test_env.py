import os
from unittest.mock import patch

import pytest

from app.env import load_env


def test_load_env_reads_required_values():
    env = {
        "SLACK_BOT_TOKEN": "xoxb-test",
        "SLACK_APP_TOKEN": "xapp-test",
        "ANTHROPIC_API_KEY": "sk-ant-test",
        "NOTION_TOKEN": "ntn_test",
        "GOOGLE_APPLICATION_CREDENTIALS": "creds.json",
        "GOOGLE_ADMIN_SUBJECT": "admin@test.com",
    }
    with patch.dict(os.environ, env, clear=False):
        config = load_env()

    assert config.slack_bot_token == "xoxb-test"
    assert config.slack_app_token == "xapp-test"
    assert config.anthropic_api_key == "sk-ant-test"
    assert config.notion_token == "ntn_test"
    assert config.google_credentials_path == "creds.json"
    assert config.google_admin_subject == "admin@test.com"
    assert config.corporate_domain == "overgear.com"  # default
    assert config.config_path == "configs/access_policies.yaml"  # default


def test_load_env_raises_for_missing_required():
    # Unset only the required keys (keep PATH, HOME, etc. intact)
    unset = {k: "" for k in [
        "SLACK_BOT_TOKEN", "SLACK_APP_TOKEN", "ANTHROPIC_API_KEY",
        "NOTION_TOKEN", "GOOGLE_APPLICATION_CREDENTIALS", "GOOGLE_ADMIN_SUBJECT",
    ]}
    with patch.dict(os.environ, unset, clear=False):
        with pytest.raises(ValueError, match="SLACK_BOT_TOKEN"):
            load_env()
