from __future__ import annotations

from typing import Protocol

from app.ou_utils import normalize_ou_path


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

        raw_path = user.get("orgUnitPath")
        if not isinstance(raw_path, str) or not raw_path.strip():
            return None
        return normalize_ou_path(raw_path)

    def _is_corporate_email(self, email: str) -> bool:
        return email.endswith(f"@{self._corporate_domain}")
