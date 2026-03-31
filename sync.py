#!/usr/bin/env python3
"""Notion sync — fetch pages, chunk, embed into ChromaDB."""
from __future__ import annotations

import argparse
import json
import logging
from datetime import datetime, timezone
from pathlib import Path

from notion_client import Client as NotionClient

from app.config import load_access_policy_config
from app.env import load_env
from app.notion_crawler import chunk_text, crawl_database, crawl_root
from app.vector_store import ChromaVectorStore

log = logging.getLogger("notionai.sync")

# Resolve relative to project root, not cwd
_PROJECT_ROOT = Path(__file__).parent
SYNC_STATE_FILE = _PROJECT_ROOT / ".sync_state.json"


def _load_last_sync() -> str | None:
    if SYNC_STATE_FILE.exists():
        data = json.loads(SYNC_STATE_FILE.read_text())
        return data.get("last_sync_time")
    return None


def _save_last_sync(timestamp: str) -> None:
    SYNC_STATE_FILE.write_text(json.dumps({"last_sync_time": timestamp}))


def main() -> int:
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(name)s] %(message)s",
        datefmt="%H:%M:%S",
    )

    parser = argparse.ArgumentParser(description="Sync Notion pages to ChromaDB")
    parser.add_argument("--full", action="store_true", help="Full resync (ignore last sync time)")
    args = parser.parse_args()

    env = load_env(dotenv_path=".env")
    config = load_access_policy_config(env.config_path)

    notion = NotionClient(auth=env.notion_token, timeout_ms=60_000)
    store = ChromaVectorStore(persist_dir=".chroma_data")

    # Use consistent Z-suffix format (matches Notion's format for correct comparison)
    sync_start = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%S.000Z")
    last_sync = None if args.full else _load_last_sync()

    if last_sync:
        log.info("Incremental sync (changes since %s)", last_sync)
    else:
        log.info("Full sync")

    total_chunks = 0
    for root in config.roots:
        log.info("Crawling %s (%s) [%s]...", root.name, root.page_id, root.root_type)

        # NOTE: crawl_root/crawl_database still fetches ALL pages even on incremental sync.
        # The filtering by last_edited_time happens after the full crawl, so API call count
        # is the same. This saves embedding/upsert cost but not API rate budget.
        # TODO: Use Notion search API with last_edited_time filter to skip unchanged pages.
        if root.root_type == "database":
            pages = crawl_database(notion, root.page_id, token=env.notion_token)
        else:
            pages = crawl_root(notion, root.page_id)

        log.info("  Found %d pages", len(pages))

        if last_sync:
            before = len(pages)
            pages = [p for p in pages if p.get("last_edited_time", "") > last_sync]
            log.info("  %d updated since last sync (skipped %d)", len(pages), before - len(pages))

        # Delete stale chunks for updated pages before upserting new ones
        for page in pages:
            store.delete_by_page_id(page["page_id"])

        chunks = []
        for page in pages:
            title = page["title"]
            prefixed_text = f"{title}\n\n{page['text']}" if title else page["text"]

            text_chunks = chunk_text(prefixed_text)
            for i, text in enumerate(text_chunks):
                chunks.append({
                    "chunk_id": f"{page['page_id']}_{i}",
                    "page_id": page["page_id"],
                    "root_id": root.page_id,
                    "title": title,
                    "text": text,
                })

        if chunks:
            store.upsert_chunks(chunks)
        total_chunks += len(chunks)
        log.info("  Indexed %d chunks", len(chunks))

    _save_last_sync(sync_start)
    log.info("Done. Total: %d chunks indexed.", total_chunks)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
