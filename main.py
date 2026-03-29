#!/usr/bin/env python3
"""NotionAI Slack bot entrypoint."""
from app.bot import create_bot
from app.env import load_env


def main():
    env = load_env(dotenv_path=".env")
    print("Starting NotionAI bot...")
    _, handler = create_bot(env)
    handler.start()


if __name__ == "__main__":
    main()
