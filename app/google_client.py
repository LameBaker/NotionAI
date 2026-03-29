from __future__ import annotations

from google.oauth2 import service_account
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError


class RealGoogleDirectoryClient:
    """Implements DirectoryClient protocol using real Google Admin SDK."""

    def __init__(self, *, credentials_path: str, admin_subject: str) -> None:
        creds = service_account.Credentials.from_service_account_file(
            credentials_path,
            scopes=["https://www.googleapis.com/auth/admin.directory.user.readonly"],
        ).with_subject(admin_subject)
        service = build("admin", "directory_v1", credentials=creds, cache_discovery=False)
        self._users = service.users()

    def get_user_by_email(self, email: str) -> dict[str, str] | None:
        try:
            payload = self._users.get(userKey=email, projection="basic").execute()
        except HttpError as exc:
            if getattr(getattr(exc, "resp", None), "status", None) == 404:
                return None
            raise
        return {
            "primaryEmail": str(payload.get("primaryEmail", "")).strip(),
            "orgUnitPath": str(payload.get("orgUnitPath", "")).strip(),
        }
