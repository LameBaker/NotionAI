from __future__ import annotations

import logging
import re
import time

import httpx
from notion_client import Client as NotionClient
from notion_client.errors import APIResponseError

MAX_CRAWL_DEPTH = 50

log = logging.getLogger("notionai.crawler")


def chunk_text(text: str, max_chunk_size: int = 1000, overlap: int = 100) -> list[str]:
    """Split text into chunks with optional overlap between consecutive chunks."""
    if not text.strip():
        return []
    paragraphs = text.split("\n\n")
    raw_chunks: list[str] = []
    current = ""
    for para in paragraphs:
        para = para.strip()
        if not para:
            continue
        # Split oversized paragraphs by sentences
        if len(para) > max_chunk_size:
            if current:
                raw_chunks.append(current)
                current = ""
            for sub in _split_long_paragraph(para, max_chunk_size):
                raw_chunks.append(sub)
            continue
        if current and len(current) + len(para) + 2 > max_chunk_size:
            raw_chunks.append(current)
            current = para
        else:
            current = f"{current}\n\n{para}" if current else para
    if current:
        raw_chunks.append(current)

    # Apply overlap: prepend tail of previous chunk to next chunk
    if overlap <= 0 or len(raw_chunks) <= 1:
        return raw_chunks
    chunks = [raw_chunks[0]]
    for i in range(1, len(raw_chunks)):
        prev_tail = raw_chunks[i - 1][-overlap:]
        chunks.append(f"...{prev_tail}\n\n{raw_chunks[i]}")
    return chunks


def _split_long_paragraph(text: str, max_size: int) -> list[str]:
    """Split a long paragraph by sentence boundaries, then by hard limit."""
    sentences = re.split(r"(?<=[.!?。])\s+", text)
    chunks: list[str] = []
    current = ""
    for sent in sentences:
        if current and len(current) + len(sent) + 1 > max_size:
            chunks.append(current)
            current = sent
        else:
            current = f"{current} {sent}" if current else sent
    if current:
        chunks.append(current)
    # Final fallback: hard-split anything still over limit
    result = []
    for chunk in chunks:
        while len(chunk) > max_size:
            result.append(chunk[:max_size])
            chunk = chunk[max_size:]
        if chunk:
            result.append(chunk)
    return result


def crawl_root(client: NotionClient, root_page_id: str) -> list[dict]:
    """Recursively fetch all pages under a root. Returns list of {page_id, title, text}."""
    pages: list[dict] = []
    visited: set[str] = set()
    _crawl_recursive(client, root_page_id, pages, visited, depth=0)
    return pages


def crawl_database(client: NotionClient, database_id: str, *, token: str) -> list[dict]:
    """Fetch all pages from a Notion database. Returns list of {page_id, title, text}."""
    pages: list[dict] = []
    visited: set[str] = set()
    cursor = None

    while True:
        body: dict = {"page_size": 100}
        if cursor:
            body["start_cursor"] = cursor
        response = _retry_api_call(
            lambda b=body: _query_database_http(database_id, b, token)
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
            if text.strip():
                pages.append({
                    "page_id": page_id,
                    "title": title,
                    "text": text,
                    "last_edited_time": last_edited,
                })

        if not response.get("has_more"):
            break
        cursor = response.get("next_cursor")

    return pages


def _crawl_recursive(
    client: NotionClient, page_id: str, pages: list[dict], visited: set[str], *, depth: int = 0
) -> None:
    if page_id in visited:
        return
    if depth > MAX_CRAWL_DEPTH:
        log.warning("Max crawl depth %d reached at page %s, stopping", MAX_CRAWL_DEPTH, page_id)
        return
    visited.add(page_id)
    page = _retry_api_call(lambda: client.pages.retrieve(page_id))
    if page is None:
        log.warning("Skipping page %s (failed to retrieve)", page_id)
        return

    title = _extract_page_title(page)
    last_edited = page.get("last_edited_time", "")
    blocks = _get_all_blocks(client, page_id)

    # Extract text and discover child pages (including inside columns/callouts)
    parts: list[str] = []
    child_page_ids: list[str] = []
    heading_trail: list[str] = []

    _process_blocks(client, blocks, parts, child_page_ids, heading_trail)

    text = "\n\n".join(parts)
    if text.strip():
        pages.append({
            "page_id": page_id,
            "title": title,
            "text": text,
            "last_edited_time": last_edited,
        })

    for child_id in child_page_ids:
        _crawl_recursive(client, child_id, pages, visited, depth=depth + 1)


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
            lambda c=cursor: client.blocks.children.list(block_id, start_cursor=c, page_size=100)
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


_TRANSIENT_ERRORS = (TimeoutError, ConnectionError, httpx.TimeoutException, httpx.ConnectError)
_TRANSIENT_STATUS_CODES = {429, 500, 502, 503, 504}


def _retry_api_call(fn, retries: int = 3, delay: float = 2.0):
    for attempt in range(retries):
        try:
            return fn()
        except _TRANSIENT_ERRORS as exc:
            if attempt == retries - 1:
                log.warning("API call failed after %d retries: %s", retries, exc)
                return None
            log.debug("Transient error (attempt %d/%d): %s", attempt + 1, retries, exc)
            time.sleep(delay * (attempt + 1))
        except APIResponseError as exc:
            if exc.status in _TRANSIENT_STATUS_CODES:
                if attempt == retries - 1:
                    log.warning("API %d error after %d retries: %s", exc.status, retries, exc)
                    return None
                log.debug("Transient API %d (attempt %d/%d)", exc.status, attempt + 1, retries)
                time.sleep(delay * (attempt + 1))
            else:
                log.error("Permanent API error (status %d): %s", exc.status, exc)
                return None
        except httpx.HTTPStatusError as exc:
            status = exc.response.status_code
            if status in _TRANSIENT_STATUS_CODES:
                if attempt == retries - 1:
                    log.warning("HTTP %d after %d retries", status, retries)
                    return None
                log.debug("Transient HTTP %d (attempt %d/%d)", status, attempt + 1, retries)
                time.sleep(delay * (attempt + 1))
            else:
                log.error("Permanent HTTP error %d: %s", status, exc)
                return None
        except Exception as exc:
            log.error("Unexpected error: %s", exc)
            return None


def _extract_page_title(page: dict) -> str:
    props = page.get("properties", {})
    for val in props.values():
        if isinstance(val, dict) and val.get("type") == "title":
            entries = val.get("title", [])
            parts = [e.get("plain_text", "") for e in entries if isinstance(e, dict)]
            return " ".join(parts).strip()
    return ""
