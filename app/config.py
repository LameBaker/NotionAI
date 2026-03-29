from __future__ import annotations

from pathlib import Path
from typing import Any

import yaml

from app.models import AccessPolicyConfig, RootAccessPolicy


def load_access_policy_config(path: Path | str) -> AccessPolicyConfig:
    config_path = Path(path)
    payload = yaml.safe_load(config_path.read_text())

    if not isinstance(payload, dict):
        raise ValueError("Access policy config must be a mapping")

    default = payload.get("default")
    if default != "deny_all":
        raise ValueError("Access policy default must be 'deny_all'")

    groups = _parse_groups(payload.get("groups", {}))

    raw_roots = payload.get("roots", [])
    if not isinstance(raw_roots, list):
        raise ValueError("roots must be a list")

    roots = [_build_root_policy(item, groups) for item in raw_roots]
    return AccessPolicyConfig(default=default, roots=roots)


def _parse_groups(raw_groups: Any) -> dict[str, list[str]]:
    if not isinstance(raw_groups, dict):
        return {}
    groups: dict[str, list[str]] = {}
    for name, values in raw_groups.items():
        if isinstance(values, list):
            groups[str(name)] = [str(v) for v in values]
    return groups


def _build_root_policy(payload: Any, groups: dict[str, list[str]]) -> RootAccessPolicy:
    if not isinstance(payload, dict):
        raise ValueError("root entry must be a mapping")

    name = str(payload.get("name", "")).strip()
    page_id = str(payload.get("page_id", "")).strip()

    allow_ou_group = str(payload.get("allow_ou_group", "")).strip()
    if allow_ou_group and allow_ou_group in groups:
        allow_ou = list(groups[allow_ou_group])
    else:
        allow_ou = payload.get("allow_ou", [])

    allow_users = payload.get("allow_users", [])

    if not name or not page_id:
        raise ValueError("root entries require name and page_id")
    if not isinstance(allow_ou, list) or not isinstance(allow_users, list):
        raise ValueError("allow_ou and allow_users must be lists")

    return RootAccessPolicy(
        name=name,
        page_id=page_id,
        allow_ou=[str(item) for item in allow_ou],
        allow_users=[str(item) for item in allow_users],
    )
