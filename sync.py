#!/usr/bin/env python3
"""Notion sync — fetch pages, chunk, embed into ChromaDB."""
from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime, timezone
from pathlib import Path

from notion_client import Client as NotionClient

from app.config import load_access_policy_config
from app.env import load_env
from app.notion_crawler import chunk_text, crawl_root
from app.vector_store import ChromaVectorStore

SYNC_STATE_FILE = Path(".sync_state.json")


def _load_last_sync() -> str | None:
    if SYNC_STATE_FILE.exists():
        data = json.loads(SYNC_STATE_FILE.read_text())
        return data.get("last_sync_time")
    return None


def _save_last_sync(timestamp: str) -> None:
    SYNC_STATE_FILE.write_text(json.dumps({"last_sync_time": timestamp}))


def _find_updated_pages(
    client: NotionClient, root_page_id: str, since: str
) -> list[str]:
    """Use Notion search API to find pages edited after `since` under a root."""
    updated_ids: list[str] = []
    cursor = None
    while True:
        response = client.search(
            filter={"property": "object", "value": "page"},
            sort={"direction": "descending", "timestamp": "last_edited_time"},
            start_cursor=cursor,
            page_size=100,
        )
        results = response.get("results", [])
        if not results:
            break

        for page in results:
            edited = page.get("last_edited_time", "")
            if edited <= since:
                return updated_ids
            page_id = page.get("id", "")
            if page_id:
                updated_ids.append(page_id)

        if not response.get("has_more"):
            break
        cursor = response.get("next_cursor")

    return updated_ids


def main() -> int:
    parser = argparse.ArgumentParser(description="Sync Notion pages to ChromaDB")
    parser.add_argument("--full", action="store_true", help="Full resync (ignore last sync time)")
    args = parser.parse_args()

    env = load_env(dotenv_path=".env")
    config = load_access_policy_config("configs/access_policies.yaml")

    notion = NotionClient(auth=env.notion_token)
    store = ChromaVectorStore(persist_dir=".chroma_data")

    sync_start = datetime.now(timezone.utc).isoformat()
    last_sync = None if args.full else _load_last_sync()

    if last_sync:
        print(f"Incremental sync (changes since {last_sync})")
    else:
        print("Full sync")

    total_chunks = 0
    for root in config.roots:
        print(f"Crawling {root.name} ({root.page_id})...")
        pages = crawl_root(notion, root.page_id)
        print(f"  Found {len(pages)} pages")

        if last_sync:
            # Filter to only pages edited since last sync
            before = len(pages)
            pages = [p for p in pages if p.get("last_edited_time", "") > last_sync]
            print(f"  {len(pages)} updated since last sync (skipped {before - len(pages)})")

        chunks = []
        for page in pages:
            text_chunks = chunk_text(page["text"])
            for i, text in enumerate(text_chunks):
                chunks.append({
                    "chunk_id": f"{page['page_id']}_{i}",
                    "page_id": page["page_id"],
                    "root_id": root.page_id,
                    "title": page["title"],
                    "text": text,
                })

        if chunks:
            store.upsert_chunks(chunks)
        total_chunks += len(chunks)
        print(f"  Indexed {len(chunks)} chunks")

    _save_last_sync(sync_start)
    print(f"Done. Total: {total_chunks} chunks indexed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
