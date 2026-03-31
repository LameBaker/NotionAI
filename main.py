#!/usr/bin/env python3
"""NotionAI Slack bot entrypoint."""
import logging
import signal
import sys

from app.bot import create_bot
from app.env import load_env


def main():
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(name)s] %(message)s",
        datefmt="%H:%M:%S",
    )

    env = load_env(dotenv_path=".env")
    log = logging.getLogger("notionai")
    log.info("Starting NotionAI bot...")

    _, handler = create_bot(env)

    def shutdown(signum, frame):
        log.info("Shutting down (signal %d)...", signum)
        handler.close()
        sys.exit(0)

    signal.signal(signal.SIGINT, shutdown)
    signal.signal(signal.SIGTERM, shutdown)

    handler.start()


if __name__ == "__main__":
    main()
