from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class NotionPageMetadata:
    page_id: str
    parent_id: str | None
    title: str
    path: str | None
    last_edited_time: str
    acl_restricted: bool
    acl_allow_ou: list[str]
    acl_allow_users: list[str]


def parse_notion_page_metadata(payload: dict) -> NotionPageMetadata:
    properties = payload.get("properties") or {}

    return NotionPageMetadata(
        page_id=str(payload.get("id", "")).strip(),
        parent_id=_extract_parent_id(payload.get("parent")),
        title=_extract_title(properties),
        path=_extract_path(payload.get("path")),
        last_edited_time=str(payload.get("last_edited_time", "")).strip(),
        acl_restricted=_extract_acl_restricted(properties.get("acl_restricted")),
        acl_allow_ou=_extract_acl_list(properties.get("acl_allow_ou")),
        acl_allow_users=_extract_acl_list(properties.get("acl_allow_users")),
    )


def _extract_parent_id(parent: object) -> str | None:
    if not isinstance(parent, dict):
        return None

    for key in ("page_id", "database_id", "block_id", "workspace"):
        value = parent.get(key)
        if isinstance(value, str) and value.strip():
            return value.strip()

    return None


def _extract_title(properties: dict) -> str:
    for value in properties.values():
        if isinstance(value, dict) and value.get("type") == "title":
            entries = value.get("title") or []
            if isinstance(entries, list):
                parts = []
                for entry in entries:
                    if isinstance(entry, dict):
                        text = str(entry.get("plain_text", "")).strip()
                        if text:
                            parts.append(text)
                if parts:
                    return " ".join(parts)

    return ""


def _extract_path(path_value: object) -> str | None:
    if isinstance(path_value, str):
        text = path_value.strip()
        return text or None

    if isinstance(path_value, list):
        parts = [str(item).strip(" /") for item in path_value if str(item).strip()]
        if parts:
            return "/" + "/".join(parts)

    return None


def _extract_acl_restricted(raw_value: object) -> bool:
    if isinstance(raw_value, bool):
        return raw_value

    if isinstance(raw_value, dict):
        if "checkbox" in raw_value:
            return bool(raw_value.get("checkbox"))
        if "value" in raw_value:
            return bool(raw_value.get("value"))

    return False


def _extract_acl_list(raw_value: object) -> list[str]:
    if raw_value is None:
        return []

    values: list[str] = []

    if isinstance(raw_value, list):
        values.extend(_normalize_entries(raw_value))
    elif isinstance(raw_value, str):
        values.extend(_split_csv_like(raw_value))
    elif isinstance(raw_value, dict):
        value_type = raw_value.get("type")
        if value_type == "multi_select":
            items = raw_value.get("multi_select") or []
            if isinstance(items, list):
                values.extend(
                    _normalize_entries(item.get("name", "") for item in items if isinstance(item, dict))
                )
        elif value_type == "rich_text":
            items = raw_value.get("rich_text") or []
            if isinstance(items, list):
                for item in items:
                    if isinstance(item, dict):
                        values.extend(_split_csv_like(str(item.get("plain_text", ""))))
        elif "value" in raw_value:
            value = raw_value.get("value")
            if isinstance(value, list):
                values.extend(_normalize_entries(value))
            elif isinstance(value, str):
                values.extend(_split_csv_like(value))

    deduped: list[str] = []
    seen: set[str] = set()
    for value in values:
        if value not in seen:
            seen.add(value)
            deduped.append(value)

    return deduped


def _normalize_entries(entries) -> list[str]:
    normalized = []
    for entry in entries:
        text = str(entry).strip()
        if text:
            normalized.append(text)
    return normalized


def _split_csv_like(raw_text: str) -> list[str]:
    parts = []
    for segment in raw_text.replace("\n", ",").split(","):
        value = segment.strip()
        if value:
            parts.append(value)
    return parts
