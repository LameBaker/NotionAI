from dataclasses import dataclass


@dataclass(frozen=True)
class RootAccessPolicy:
    name: str
    page_id: str
    allow_ou: tuple[str, ...]
    allow_users: tuple[str, ...]
    root_type: str = "page"  # "page" or "database"


@dataclass(frozen=True)
class AccessPolicyConfig:
    default: str
    roots: tuple[RootAccessPolicy, ...]
