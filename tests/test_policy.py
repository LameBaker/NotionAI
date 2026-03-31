from app.models import RootAccessPolicy
from app.policy import evaluate_page_access


def _root_policy(*, allow_ou: list[str], allow_users: list[str]) -> RootAccessPolicy:
    return RootAccessPolicy(
        name="root",
        page_id="00000000-0000-0000-0000-000000000000",
        allow_ou=tuple(allow_ou),
        allow_users=tuple(allow_users),
    )


def test_root_allow_by_ou_prefix() -> None:
    root = _root_policy(allow_ou=["/Development"], allow_users=[])

    assert (
        evaluate_page_access(
            user_email="dev1@company.com",
            user_ou="/Development/Backend",
            root_policy=root,
        )
        is True
    )


def test_root_allow_by_user_email() -> None:
    root = _root_policy(allow_ou=["/Development"], allow_users=["alice@company.com"])

    assert (
        evaluate_page_access(
            user_email="alice@company.com",
            user_ou="/Sales",
            root_policy=root,
        )
        is True
    )


def test_deny_when_unmatched() -> None:
    root = _root_policy(allow_ou=["/Development"], allow_users=[])

    assert (
        evaluate_page_access(
            user_email="bob@company.com",
            user_ou="/Sales",
            root_policy=root,
        )
        is False
    )


def test_blank_allow_ou_values_do_not_grant_global_access() -> None:
    root = _root_policy(allow_ou=["   "], allow_users=[])

    assert (
        evaluate_page_access(
            user_email="user@company.com",
            user_ou="/Sales",
            root_policy=root,
        )
        is False
    )
