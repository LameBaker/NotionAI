import pytest

from app.google_adapter import GoogleAdapterError, GoogleAdminDirectoryAdapter


class FakeGoogleClient:
    def __init__(self, payload_by_email: dict[str, dict] | None = None, error: Exception | None = None):
        self._payload_by_email = payload_by_email or {}
        self._error = error
        self.calls: list[str] = []

    def get_user(self, email: str) -> dict | None:
        self.calls.append(email)
        if self._error is not None:
            raise self._error
        return self._payload_by_email.get(email)


def test_google_adapter_maps_sdk_payload_to_identity_contract() -> None:
    client = FakeGoogleClient(
        {
            "dev1@company.com": {
                "primaryEmail": "dev1@company.com",
                "orgUnitPath": "Development/Backend/",
                "suspended": False,
            }
        }
    )
    adapter = GoogleAdminDirectoryAdapter(client=client)

    user = adapter.get_user_by_email("dev1@company.com")

    assert user == {
        "primaryEmail": "dev1@company.com",
        "orgUnitPath": "Development/Backend/",
    }
    assert client.calls == ["dev1@company.com"]


def test_google_adapter_returns_none_when_user_not_found() -> None:
    client = FakeGoogleClient(payload_by_email={})
    adapter = GoogleAdminDirectoryAdapter(client=client)

    assert adapter.get_user_by_email("missing@company.com") is None


def test_google_adapter_maps_transient_client_failure_to_adapter_error() -> None:
    client = FakeGoogleClient(error=TimeoutError("directory timeout"))
    adapter = GoogleAdminDirectoryAdapter(client=client)

    with pytest.raises(GoogleAdapterError, match="Transient Google directory client failure"):
        adapter.get_user_by_email("dev1@company.com")
