from __future__ import annotations

from app.models import RootAccessPolicy
from app.ou_utils import normalize_ou_path


def evaluate_page_access(
    *,
    user_email: str,
    user_ou: str,
    root_policy: RootAccessPolicy,
) -> bool:
    """Check if user has access to a root. Root-level ACL only.

    Page-level ACL (acl_restricted, acl_allow_ou, acl_allow_users) is not
    implemented — access is determined solely by root policy. See D-017.
    """
    normalized_email = user_email.strip().lower()

    return _matches_ou(user_ou, root_policy.allow_ou) or _matches_email(
        normalized_email, root_policy.allow_users
    )


def _matches_email(user_email: str, allowed_users: list[str]) -> bool:
    allowed = {email.strip().lower() for email in allowed_users}
    return user_email in allowed


def _matches_ou(user_ou: str, allowed_ou_prefixes: list[str]) -> bool:
    normalized_user_ou = normalize_ou_path(user_ou)

    for raw_prefix in allowed_ou_prefixes:
        if not raw_prefix.strip():
            continue
        prefix = normalize_ou_path(raw_prefix)
        if prefix == "/":
            return True
        if normalized_user_ou == prefix or normalized_user_ou.startswith(prefix + "/"):
            return True

    return False
