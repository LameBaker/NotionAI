import pytest

from app.identity import GoogleDirectoryIdentityResolver, InvalidCorporateEmailError


class FakeDirectoryClient:
    def __init__(self, users_by_email: dict[str, dict[str, str]]):
        self._users_by_email = users_by_email
        self.calls: list[str] = []

    def get_user_by_email(self, email: str) -> dict[str, str] | None:
        self.calls.append(email)
        return self._users_by_email.get(email)


def test_resolve_org_unit_by_corporate_email_normalizes_org_unit_path() -> None:
    client = FakeDirectoryClient(
        {
            "dev1@company.com": {
                "primaryEmail": "dev1@company.com",
                "orgUnitPath": "Development/Backend/",
            }
        }
    )
    resolver = GoogleDirectoryIdentityResolver(client=client, corporate_domain="company.com")

    org_unit = resolver.resolve_org_unit_by_email("dev1@company.com")

    assert org_unit == "/Development/Backend"
    assert client.calls == ["dev1@company.com"]


def test_resolve_org_unit_by_email_returns_none_when_user_not_found() -> None:
    client = FakeDirectoryClient({})
    resolver = GoogleDirectoryIdentityResolver(client=client, corporate_domain="company.com")

    assert resolver.resolve_org_unit_by_email("missing@company.com") is None


def test_resolve_org_unit_by_email_rejects_non_corporate_email() -> None:
    client = FakeDirectoryClient({"user@gmail.com": {"orgUnitPath": "/External"}})
    resolver = GoogleDirectoryIdentityResolver(client=client, corporate_domain="company.com")

    with pytest.raises(InvalidCorporateEmailError, match="corporate email"):
        resolver.resolve_org_unit_by_email("user@gmail.com")

    assert client.calls == []
