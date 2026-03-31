#!/usr/bin/env python3
"""Notion sync — fetch pages, chunk, embed into ChromaDB."""
from __future__ import annotations

import argparse
import fcntl
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
SYNC_LOCK_FILE = _PROJECT_ROOT / ".sync_lock"


def _load_last_sync() -> str | None:
    if SYNC_STATE_FILE.exists():
        data = json.loads(SYNC_STATE_FILE.read_text())
        return data.get("last_sync_time")
    return None


def _save_last_sync(timestamp: str) -> None:
    SYNC_STATE_FILE.write_text(json.dumps({"last_sync_time": timestamp}))


def _parse_notion_timestamp(ts: str) -> datetime:
    """Parse Notion ISO 8601 timestamp to datetime for robust comparison."""
    # Notion format: 2026-03-29T10:00:00.000Z
    ts = ts.replace("Z", "+00:00")
    return datetime.fromisoformat(ts)


def _is_updated_since(page: dict, since_dt: datetime) -> bool:
    """Check if page was edited after the given datetime."""
    raw = page.get("last_edited_time", "")
    if not raw:
        return True  # No timestamp = assume updated (safe default)
    try:
        return _parse_notion_timestamp(raw) > since_dt
    except (ValueError, TypeError):
        return True  # Can't parse = assume updated


def _find_parent_index(child_text: str, parent_chunks: list[str]) -> int | None:
    """Find which parent chunk contains the child text (by overlap)."""
    # Strip overlap prefix if present
    clean = child_text.lstrip(".").strip()
    for i, parent in enumerate(parent_chunks):
        if clean[:50] in parent:
            return i
    return 0 if parent_chunks else None


def main() -> int:
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(name)s] %(message)s",
        datefmt="%H:%M:%S",
    )

    # File lock — prevent concurrent sync processes from corrupting ChromaDB
    lock_fd = open(SYNC_LOCK_FILE, "w")
    try:
        fcntl.flock(lock_fd, fcntl.LOCK_EX | fcntl.LOCK_NB)
    except BlockingIOError:
        lock_fd.close()
        log.error("Another sync process is already running. Exiting.")
        return 1

    parser = argparse.ArgumentParser(description="Sync Notion pages to ChromaDB")
    parser.add_argument("--full", action="store_true", help="Full resync (ignore last sync time)")
    args = parser.parse_args()

    env = load_env(dotenv_path=".env")
    config = load_access_policy_config(env.config_path)

    notion = NotionClient(auth=env.notion_token, timeout_ms=60_000)
    chroma_path = str(_PROJECT_ROOT / ".chroma_data")
    store = ChromaVectorStore(persist_dir=chroma_path)

    sync_start = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%S.000Z")
    last_sync = None if args.full else _load_last_sync()
    last_sync_dt = _parse_notion_timestamp(last_sync) if last_sync else None

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

        if last_sync_dt:
            before = len(pages)
            pages = [p for p in pages if _is_updated_since(p, last_sync_dt)]
            log.info("  %d updated since last sync (skipped %d)", len(pages), before - len(pages))

        # Delete stale chunks for updated pages before upserting new ones
        for page in pages:
            store.delete_by_page_id(page["page_id"])

        chunks = []
        for page in pages:
            title = page["title"]
            prefixed_text = f"{title}\n\n{page['text']}" if title else page["text"]

            page_id = page["page_id"]
            page_url = f"https://www.notion.so/{page_id.replace('-', '')}"

            # Parent chunks (large, for LLM context)
            parent_chunks = chunk_text(prefixed_text, max_chunk_size=1500, overlap=0)
            # Child chunks (small, for precise search)
            child_chunks = chunk_text(prefixed_text, max_chunk_size=300, overlap=50)

            for i, text in enumerate(child_chunks):
                # Find which parent chunk contains this child
                parent_idx = _find_parent_index(text, parent_chunks)
                parent_text = parent_chunks[parent_idx] if parent_idx is not None else text

                chunks.append({
                    "chunk_id": f"{page_id}_{i}",
                    "page_id": page_id,
                    "root_id": root.page_id,
                    "title": title,
                    "text": text,              # small chunk for search embedding
                    "parent_text": parent_text, # large chunk for LLM context
                    "page_url": page_url,
                })

        if chunks:
            store.upsert_chunks(chunks)
        total_chunks += len(chunks)
        log.info("  Indexed %d chunks", len(chunks))

    _save_last_sync(sync_start)
    log.info("Done. Total: %d chunks indexed.", total_chunks)

    # Release lock
    fcntl.flock(lock_fd, fcntl.LOCK_UN)
    lock_fd.close()

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
