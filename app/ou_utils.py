from __future__ import annotations


def normalize_ou_path(path: str) -> str:
    """Normalize a Google OU path: ensure leading /, strip trailing /, lowercase not applied."""
    value = path.strip()
    if not value:
        return "/"
    if not value.startswith("/"):
        value = "/" + value
    if value != "/":
        value = value.rstrip("/")
    return value
