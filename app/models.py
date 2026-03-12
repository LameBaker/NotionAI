from dataclasses import dataclass


@dataclass(frozen=True)
class RootAccessPolicy:
    name: str
    page_id: str
    allow_ou: list[str]
    allow_users: list[str]


@dataclass(frozen=True)
class AccessPolicyConfig:
    default: str
    roots: list[RootAccessPolicy]
