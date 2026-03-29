from __future__ import annotations

import os
from dataclasses import dataclass

from dotenv import load_dotenv


@dataclass(frozen=True)
class EnvConfig:
    slack_bot_token: str
    slack_app_token: str
    anthropic_api_key: str
    notion_token: str
    google_credentials_path: str
    google_admin_subject: str


_REQUIRED = [
    "SLACK_BOT_TOKEN",
    "SLACK_APP_TOKEN",
    "ANTHROPIC_API_KEY",
    "NOTION_TOKEN",
    "GOOGLE_APPLICATION_CREDENTIALS",
    "GOOGLE_ADMIN_SUBJECT",
]


def load_env(dotenv_path: str | None = None) -> EnvConfig:
    if dotenv_path is not None:
        load_dotenv(dotenv_path, override=False)

    missing = [key for key in _REQUIRED if not os.getenv(key, "").strip()]
    if missing:
        raise ValueError(f"Missing required env vars: {', '.join(missing)}")

    return EnvConfig(
        slack_bot_token=os.environ["SLACK_BOT_TOKEN"].strip(),
        slack_app_token=os.environ["SLACK_APP_TOKEN"].strip(),
        anthropic_api_key=os.environ["ANTHROPIC_API_KEY"].strip(),
        notion_token=os.environ["NOTION_TOKEN"].strip(),
        google_credentials_path=os.environ["GOOGLE_APPLICATION_CREDENTIALS"].strip(),
        google_admin_subject=os.environ["GOOGLE_ADMIN_SUBJECT"].strip(),
    )
