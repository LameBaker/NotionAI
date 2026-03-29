#!/usr/bin/env python3
"""Notion sync — fetch pages, chunk, embed into ChromaDB."""
from __future__ import annotations

import sys

from notion_client import Client as NotionClient

from app.config import load_access_policy_config
from app.env import load_env
from app.notion_crawler import chunk_text, crawl_root
from app.vector_store import ChromaVectorStore


def main() -> int:
    env = load_env(dotenv_path=".env")
    config = load_access_policy_config("configs/access_policies.yaml")

    notion = NotionClient(auth=env.notion_token)
    store = ChromaVectorStore(persist_dir=".chroma_data")

    total_chunks = 0
    for root in config.roots:
        print(f"Crawling {root.name} ({root.page_id})...")
        pages = crawl_root(notion, root.page_id)
        print(f"  Found {len(pages)} pages")

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

        store.upsert_chunks(chunks)
        total_chunks += len(chunks)
        print(f"  Indexed {len(chunks)} chunks")

    print(f"Done. Total: {total_chunks} chunks indexed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
