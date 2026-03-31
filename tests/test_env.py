import os
from unittest.mock import patch

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
    with patch.dict(os.environ, {}, clear=True):
        try:
            load_env()
            assert False, "Should have raised"
        except ValueError as e:
            assert "SLACK_BOT_TOKEN" in str(e)
