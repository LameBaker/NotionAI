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
from app.notion_crawler import chunk_text, crawl_database, crawl_root
from app.vector_store import ChromaVectorStore

SYNC_STATE_FILE = Path(".sync_state.json")


def _load_last_sync() -> str | None:
    if SYNC_STATE_FILE.exists():
        data = json.loads(SYNC_STATE_FILE.read_text())
        return data.get("last_sync_time")
    return None


def _save_last_sync(timestamp: str) -> None:
    SYNC_STATE_FILE.write_text(json.dumps({"last_sync_time": timestamp}))


def main() -> int:
    parser = argparse.ArgumentParser(description="Sync Notion pages to ChromaDB")
    parser.add_argument("--full", action="store_true", help="Full resync (ignore last sync time)")
    args = parser.parse_args()

    env = load_env(dotenv_path=".env")
    config = load_access_policy_config(env.config_path)

    notion = NotionClient(auth=env.notion_token, timeout_ms=60_000)
    store = ChromaVectorStore(persist_dir=".chroma_data")

    sync_start = datetime.now(timezone.utc).isoformat()
    last_sync = None if args.full else _load_last_sync()

    if last_sync:
        print(f"Incremental sync (changes since {last_sync})", flush=True)
    else:
        print("Full sync", flush=True)

    total_chunks = 0
    for root in config.roots:
        print(f"Crawling {root.name} ({root.page_id}) [{root.root_type}]...", flush=True)

        if root.root_type == "database":
            pages = crawl_database(notion, root.page_id, token=env.notion_token)
        else:
            pages = crawl_root(notion, root.page_id)

        print(f"  Found {len(pages)} pages", flush=True)

        if last_sync:
            before = len(pages)
            pages = [p for p in pages if p.get("last_edited_time", "") > last_sync]
            print(f"  {len(pages)} updated since last sync (skipped {before - len(pages)})", flush=True)

        chunks = []
        for page in pages:
            title = page["title"]
            section_path = page.get("section_path", "")
            # Prepend title (and section path) for better embedding context
            prefix = title
            if section_path:
                prefix = f"{title} ({section_path})"
            prefixed_text = f"{prefix}\n\n{page['text']}" if prefix else page["text"]

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
        print(f"  Indexed {len(chunks)} chunks", flush=True)

    _save_last_sync(sync_start)
    print(f"Done. Total: {total_chunks} chunks indexed.", flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
