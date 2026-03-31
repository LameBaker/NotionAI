#!/usr/bin/env python3
"""NotionAI Slack bot entrypoint."""
import logging

from app.bot import create_bot
from app.env import load_env


def main():
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(name)s] %(message)s",
        datefmt="%H:%M:%S",
    )

    env = load_env(dotenv_path=".env")
    logging.getLogger("notionai").info("Starting NotionAI bot...")
    _, handler = create_bot(env)
    handler.start()


if __name__ == "__main__":
    main()
