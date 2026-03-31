#!/usr/bin/env python3
"""Find Notion pages/databases that the integration can't access.

Crawls all configured roots and reports pages where API returns 403/404.
Run: .venv/bin/python scripts/check_access_gaps.py
"""
from __future__ import annotations

import sys
import time

from notion_client import Client as NotionClient
from notion_client.errors import APIResponseError

from app.config import load_access_policy_config
from app.env import load_env


def main() -> int:
    env = load_env(dotenv_path=".env")
    config = load_access_policy_config("configs/access_policies.yaml")
    client = NotionClient(auth=env.notion_token, timeout_ms=60_000)

    accessible = 0
    denied: list[dict] = []
    errors: list[dict] = []
    visited: set[str] = set()

    for root in config.roots:
        print(f"\nChecking {root.name} ({root.page_id})...", flush=True)
        _check_recursive(client, root.page_id, root.name, visited, denied, errors)
        accessible = len(visited) - len(denied) - len(errors)

    print(f"\n{'='*60}", flush=True)
    print(f"Total checked: {len(visited)}", flush=True)
    print(f"Accessible: {len(visited) - len(denied) - len(errors)}", flush=True)
    print(f"Access denied: {len(denied)}", flush=True)
    print(f"Errors: {len(errors)}", flush=True)

    if denied:
        print(f"\n--- ACCESS DENIED ({len(denied)}) ---", flush=True)
        print("These pages/databases need to be shared with your integration:", flush=True)
        for item in denied:
            print(f"  [{item['type']}] {item['id']} (parent: {item['parent']}, root: {item['root']})", flush=True)

    if errors:
        print(f"\n--- ERRORS ({len(errors)}) ---", flush=True)
        for item in errors:
            print(f"  {item['id']}: {item['error']} (root: {item['root']})", flush=True)

    return 0


def _check_recursive(
    client: NotionClient,
    page_id: str,
    root_name: str,
    visited: set[str],
    denied: list[dict],
    errors: list[dict],
) -> None:
    if page_id in visited:
        return
    visited.add(page_id)

    # Try to access the page
    try:
        client.pages.retrieve(page_id)
    except APIResponseError as e:
        if e.status in (403, 404):
            denied.append({"id": page_id, "type": "page", "parent": "?", "root": root_name})
            return
        errors.append({"id": page_id, "error": str(e), "root": root_name})
        return
    except Exception as e:
        errors.append({"id": page_id, "error": str(e), "root": root_name})
        return

    # Get all blocks
    blocks = _get_blocks_safe(client, page_id)

    for block in blocks:
        block_type = block.get("type", "")
        block_id = block.get("id", "")

        if block_type == "child_page" and block_id:
            _check_recursive(client, block_id, root_name, visited, denied, errors)

        elif block_type == "child_database" and block_id:
            if block_id not in visited:
                visited.add(block_id)
                try:
                    client.databases.retrieve(block_id)
                except APIResponseError as e:
                    if e.status in (403, 404):
                        denied.append({"id": block_id, "type": "database", "parent": page_id, "root": root_name})
                except Exception as e:
                    errors.append({"id": block_id, "error": str(e), "root": root_name})

        # Check nested blocks (columns, callouts, toggles may contain child_page/child_database)
        elif block.get("has_children") and block_id:
            nested = _get_blocks_safe(client, block_id)
            for nb in nested:
                nb_type = nb.get("type", "")
                nb_id = nb.get("id", "")
                if nb_type == "child_page" and nb_id:
                    _check_recursive(client, nb_id, root_name, visited, denied, errors)
                elif nb_type == "child_database" and nb_id:
                    if nb_id not in visited:
                        visited.add(nb_id)
                        try:
                            client.databases.retrieve(nb_id)
                        except APIResponseError as e:
                            if e.status in (403, 404):
                                denied.append({"id": nb_id, "type": "database", "parent": page_id, "root": root_name})
                        except Exception as e:
                            errors.append({"id": nb_id, "error": str(e), "root": root_name})
                elif nb.get("has_children") and nb_id:
                    # One more level deep for deeply nested structures
                    deep = _get_blocks_safe(client, nb_id)
                    for db in deep:
                        db_type = db.get("type", "")
                        db_id = db.get("id", "")
                        if db_type == "child_page" and db_id:
                            _check_recursive(client, db_id, root_name, visited, denied, errors)
                        elif db_type == "child_database" and db_id:
                            if db_id not in visited:
                                visited.add(db_id)
                                try:
                                    client.databases.retrieve(db_id)
                                except APIResponseError as e:
                                    if e.status in (403, 404):
                                        denied.append({"id": db_id, "type": "database", "parent": page_id, "root": root_name})
                                except Exception:
                                    pass


def _get_blocks_safe(client: NotionClient, block_id: str) -> list[dict]:
    blocks: list[dict] = []
    cursor = None
    while True:
        try:
            resp = client.blocks.children.list(block_id, start_cursor=cursor, page_size=100)
        except Exception:
            break
        blocks.extend(resp.get("results", []))
        if not resp.get("has_more"):
            break
        cursor = resp.get("next_cursor")
    return blocks


if __name__ == "__main__":
    raise SystemExit(main())
