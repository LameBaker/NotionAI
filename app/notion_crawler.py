from __future__ import annotations

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


def fetch_page_text(client: NotionClient, page_id: str) -> str:
    blocks = _get_all_blocks(client, page_id)
    parts: list[str] = []
    for block in blocks:
        text = _extract_block_text(block)
        if text:
            parts.append(text)
    return "\n\n".join(parts)


def crawl_root(client: NotionClient, root_page_id: str) -> list[dict]:
    """Recursively fetch all pages under a root. Returns list of {page_id, title, text}."""
    pages: list[dict] = []
    _crawl_recursive(client, root_page_id, pages)
    return pages


def _crawl_recursive(client: NotionClient, page_id: str, pages: list[dict]) -> None:
    try:
        page = client.pages.retrieve(page_id)
    except Exception:
        return

    title = _extract_page_title(page)
    text = fetch_page_text(client, page_id)

    if text.strip():
        pages.append({"page_id": page_id, "title": title, "text": text})

    blocks = _get_all_blocks(client, page_id)
    for block in blocks:
        if block.get("type") == "child_page":
            child_id = block.get("id", "")
            if child_id:
                _crawl_recursive(client, child_id, pages)


def _get_all_blocks(client: NotionClient, block_id: str) -> list[dict]:
    blocks: list[dict] = []
    cursor = None
    while True:
        response = client.blocks.children.list(block_id, start_cursor=cursor, page_size=100)
        blocks.extend(response.get("results", []))
        if not response.get("has_more"):
            break
        cursor = response.get("next_cursor")
    return blocks


def _extract_block_text(block: dict) -> str:
    block_type = block.get("type", "")
    data = block.get(block_type, {})
    rich_texts = data.get("rich_text", [])
    if not rich_texts:
        rich_texts = data.get("text", [])
    parts = []
    for rt in rich_texts:
        if isinstance(rt, dict):
            parts.append(rt.get("plain_text", ""))
    return "".join(parts).strip()


def _extract_page_title(page: dict) -> str:
    props = page.get("properties", {})
    for val in props.values():
        if isinstance(val, dict) and val.get("type") == "title":
            entries = val.get("title", [])
            parts = [e.get("plain_text", "") for e in entries if isinstance(e, dict)]
            return " ".join(parts).strip()
    return ""
