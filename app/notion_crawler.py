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
    last_edited = page.get("last_edited_time", "")
    blocks = _get_all_blocks(client, page_id)

    # Extract text from all blocks (including nested toggles, callouts, etc.)
    parts: list[str] = []
    child_page_ids: list[str] = []

    for block in blocks:
        block_type = block.get("type", "")

        if block_type == "child_page":
            child_id = block.get("id", "")
            if child_id:
                child_page_ids.append(child_id)
            continue

        if block_type == "child_database":
            continue

        _collect_block_text(client, block, parts)

    text = "\n\n".join(parts)
    if text.strip():
        pages.append({"page_id": page_id, "title": title, "text": text, "last_edited_time": last_edited})

    for child_id in child_page_ids:
        _crawl_recursive(client, child_id, pages)


def _collect_block_text(client: NotionClient, block: dict, parts: list[str]) -> None:
    """Extract text from a block and recursively from its children."""
    text = _extract_rich_text(block)
    if text:
        parts.append(text)

    # If block has children (toggles, callouts, columns, etc.), fetch them
    if block.get("has_children"):
        block_id = block.get("id", "")
        if not block_id:
            return
        children = _get_all_blocks(client, block_id)
        for child in children:
            child_type = child.get("type", "")
            if child_type in ("child_page", "child_database"):
                continue
            _collect_block_text(client, child, parts)


def _extract_rich_text(block: dict) -> str:
    """Extract plain text from a block's rich_text field."""
    block_type = block.get("type", "")
    data = block.get(block_type, {})

    # Most blocks use rich_text
    rich_texts = data.get("rich_text", [])

    # Some blocks use different field names
    if not rich_texts:
        rich_texts = data.get("text", [])

    # Table cells, etc.
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
        response = client.blocks.children.list(block_id, start_cursor=cursor, page_size=100)
        blocks.extend(response.get("results", []))
        if not response.get("has_more"):
            break
        cursor = response.get("next_cursor")
    return blocks


def _extract_page_title(page: dict) -> str:
    props = page.get("properties", {})
    for val in props.values():
        if isinstance(val, dict) and val.get("type") == "title":
            entries = val.get("title", [])
            parts = [e.get("plain_text", "") for e in entries if isinstance(e, dict)]
            return " ".join(parts).strip()
    return ""
