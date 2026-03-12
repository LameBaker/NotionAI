from __future__ import annotations

from typing import Protocol


class GoogleAdapterError(RuntimeError):
    """Raised when Google directory access fails at the adapter boundary."""


class GoogleAdminClient(Protocol):
    def get_user(self, email: str) -> dict | None:
        """Fetch a user payload from a Google Admin SDK-like client."""


class GoogleAdminDirectoryAdapter:
    def __init__(self, *, client: GoogleAdminClient) -> None:
        self._client = client

    def get_user_by_email(self, email: str) -> dict[str, str] | None:
        try:
            payload = self._client.get_user(email)
        except (TimeoutError, ConnectionError) as exc:
            raise GoogleAdapterError("Transient Google directory client failure") from exc

        if payload is None:
            return None

        return {
            "primaryEmail": str(payload.get("primaryEmail", "")).strip(),
            "orgUnitPath": str(payload.get("orgUnitPath", "")).strip(),
        }
