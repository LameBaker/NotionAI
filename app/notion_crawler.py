from __future__ import annotations

import time

import httpx
from notion_client import Client as NotionClient


def chunk_text(text: str, max_chunk_size: int = 1000) -> list[str]:
    if not text.strip():
        return []
    paragraphs = text.split("\n\n")
    chunks: list[str] = []
    current = ""
    for para in paragraphs:
        para = para.strip()
        if not para:
            continue
        if current and len(current) + len(para) + 2 > max_chunk_size:
            chunks.append(current)
            current = para
        else:
            current = f"{current}\n\n{para}" if current else para
    if current:
        chunks.append(current)
    return chunks


def crawl_root(client: NotionClient, root_page_id: str) -> list[dict]:
    """Recursively fetch all pages under a root. Returns list of {page_id, title, text}."""
    pages: list[dict] = []
    visited: set[str] = set()
    _crawl_recursive(client, root_page_id, pages, visited)
    return pages


def crawl_database(client: NotionClient, database_id: str, *, token: str = "") -> list[dict]:
    """Fetch all pages from a Notion database. Returns list of {page_id, title, text}."""
    pages: list[dict] = []
    visited: set[str] = set()
    cursor = None

    while True:
        body: dict = {"page_size": 100}
        if cursor:
            body["start_cursor"] = cursor
        response = _retry_api_call(
            lambda: _query_database_http(database_id, body, token)
        )
        if response is None:
            break

        for entry in response.get("results", []):
            page_id = entry.get("id", "")
            if not page_id or page_id in visited:
                continue
            visited.add(page_id)

            title = _extract_page_title(entry)
            last_edited = entry.get("last_edited_time", "")

            # Fetch page content
            blocks = _get_all_blocks(client, page_id)
            parts: list[str] = []
            section_trail: list[str] = []
            child_page_ids: list[str] = []
            _process_blocks(client, blocks, parts, child_page_ids, section_trail)

            text = "\n\n".join(parts)
            section_path = ""  # DB entries don't have heading hierarchy from parent

            if text.strip():
                pages.append({
                    "page_id": page_id,
                    "title": title,
                    "text": text,
                    "last_edited_time": last_edited,
                    "section_path": section_path,
                })

        if not response.get("has_more"):
            break
        cursor = response.get("next_cursor")

    return pages


def _crawl_recursive(
    client: NotionClient, page_id: str, pages: list[dict], visited: set[str]
) -> None:
    if page_id in visited:
        return
    visited.add(page_id)
    page = _retry_api_call(lambda: client.pages.retrieve(page_id))
    if page is None:
        return

    title = _extract_page_title(page)
    last_edited = page.get("last_edited_time", "")
    blocks = _get_all_blocks(client, page_id)

    # Extract text and discover child pages (including inside columns/callouts)
    parts: list[str] = []
    child_page_ids: list[str] = []
    section_trail: list[str] = []

    _process_blocks(client, blocks, parts, child_page_ids, section_trail)

    text = "\n\n".join(parts)
    if text.strip():
        pages.append({
            "page_id": page_id,
            "title": title,
            "text": text,
            "last_edited_time": last_edited,
            "section_path": " > ".join(section_trail) if section_trail else "",
        })

    for child_id in child_page_ids:
        _crawl_recursive(client, child_id, pages, visited)


def _process_blocks(
    client: NotionClient,
    blocks: list[dict],
    parts: list[str],
    child_page_ids: list[str],
    section_trail: list[str],
) -> None:
    """Extract text and collect child page IDs from blocks, recursively.
    Tracks heading hierarchy for section_path."""
    for block in blocks:
        block_type = block.get("type", "")

        if block_type == "child_page":
            child_id = block.get("id", "")
            if child_id:
                child_page_ids.append(child_id)
            continue

        if block_type == "child_database":
            child_id = block.get("id", "")
            if child_id:
                child_page_ids.append(child_id)
            continue

        # Track heading hierarchy for section path
        if block_type in ("heading_1", "heading_2", "heading_3"):
            heading_text = _extract_rich_text(block)
            if heading_text:
                level = int(block_type[-1])
                # Trim trail to current level
                while len(section_trail) >= level:
                    section_trail.pop()
                section_trail.append(heading_text)

        text = _extract_rich_text(block)
        if text:
            parts.append(text)

        # Recurse into children (toggles, callouts, columns, etc.)
        if block.get("has_children"):
            block_id = block.get("id", "")
            if block_id:
                children = _get_all_blocks(client, block_id)
                _process_blocks(client, children, parts, child_page_ids, section_trail)


def _extract_rich_text(block: dict) -> str:
    """Extract plain text from a block's rich_text field."""
    block_type = block.get("type", "")
    data = block.get(block_type, {})

    # Most blocks use rich_text
    rich_texts = data.get("rich_text", [])

    # Some blocks use different field names
    if not rich_texts:
        rich_texts = data.get("text", [])

    # Table cells
    if not rich_texts and block_type == "table_row":
        cells = data.get("cells", [])
        cell_texts = []
        for cell in cells:
            for rt in cell:
                if isinstance(rt, dict):
                    cell_texts.append(rt.get("plain_text", ""))
        return " | ".join(filter(None, cell_texts))

    parts = []
    for rt in rich_texts:
        if isinstance(rt, dict):
            parts.append(rt.get("plain_text", ""))
    return "".join(parts).strip()


def _get_all_blocks(client: NotionClient, block_id: str) -> list[dict]:
    blocks: list[dict] = []
    cursor = None
    while True:
        response = _retry_api_call(
            lambda: client.blocks.children.list(block_id, start_cursor=cursor, page_size=100)
        )
        if response is None:
            break
        blocks.extend(response.get("results", []))
        if not response.get("has_more"):
            break
        cursor = response.get("next_cursor")
    return blocks


def _query_database_http(database_id: str, body: dict, token: str) -> dict:
    """Direct HTTP call to Notion database query (SDK v2.7 removed this method)."""
    resp = httpx.post(
        f"https://api.notion.com/v1/databases/{database_id}/query",
        headers={
            "Authorization": f"Bearer {token}",
            "Notion-Version": "2022-06-28",
            "Content-Type": "application/json",
        },
        json=body,
        timeout=60.0,
    )
    resp.raise_for_status()
    return resp.json()


def _retry_api_call(fn, retries: int = 3, delay: float = 2.0):
    for attempt in range(retries):
        try:
            return fn()
        except Exception:
            if attempt == retries - 1:
                return None
            time.sleep(delay * (attempt + 1))


def _extract_page_title(page: dict) -> str:
    props = page.get("properties", {})
    for val in props.values():
        if isinstance(val, dict) and val.get("type") == "title":
            entries = val.get("title", [])
            parts = [e.get("plain_text", "") for e in entries if isinstance(e, dict)]
            return " ".join(parts).strip()
    return ""
