from app.models import RootAccessPolicy
from app.policy import evaluate_page_access


def _root_policy(*, allow_ou: list[str], allow_users: list[str]) -> RootAccessPolicy:
    return RootAccessPolicy(
        name="root",
        page_id="root-page",
        allow_ou=allow_ou,
        allow_users=allow_users,
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


def test_acl_restricted_requires_explicit_allows() -> None:
    root = _root_policy(allow_ou=["/"], allow_users=[])

    assert (
        evaluate_page_access(
            user_email="anyone@company.com",
            user_ou="/Any",
            root_policy=root,
            acl_restricted=True,
            acl_allow_ou=[],
            acl_allow_users=[],
        )
        is False
    )

    assert (
        evaluate_page_access(
            user_email="specific@company.com",
            user_ou="/Any",
            root_policy=root,
            acl_restricted=True,
            acl_allow_users=["specific@company.com"],
        )
        is True
    )


def test_acl_allow_expands_access_when_not_restricted() -> None:
    root = _root_policy(allow_ou=["/Development"], allow_users=[])

    assert (
        evaluate_page_access(
            user_email="guest@company.com",
            user_ou="/Sales",
            root_policy=root,
            acl_allow_users=["guest@company.com"],
        )
        is True
    )
