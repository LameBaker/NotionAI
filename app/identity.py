from __future__ import annotations

from typing import Protocol


class InvalidCorporateEmailError(ValueError):
    """Raised when identity resolution is requested for a non-corporate email."""


class DirectoryClient(Protocol):
    def get_user_by_email(self, email: str) -> dict[str, str] | None:
        """Return a Google user payload by corporate email, or None when not found."""


class GoogleDirectoryIdentityResolver:
    def __init__(self, *, client: DirectoryClient, corporate_domain: str) -> None:
        self._client = client
        self._corporate_domain = corporate_domain.strip().lower()

    def resolve_org_unit_by_email(self, email: str) -> str | None:
        normalized_email = email.strip().lower()
        if not self._is_corporate_email(normalized_email):
            raise InvalidCorporateEmailError("Identity resolution requires a corporate email")

        user = self._client.get_user_by_email(normalized_email)
        if user is None:
            return None

        return _normalize_ou_path(user.get("orgUnitPath", ""))

    def _is_corporate_email(self, email: str) -> bool:
        return email.endswith(f"@{self._corporate_domain}")


def _normalize_ou_path(path: str) -> str:
    value = path.strip()
    if not value:
        return "/"

    if not value.startswith("/"):
        value = "/" + value

    if value != "/":
        value = value.rstrip("/")

    return value
