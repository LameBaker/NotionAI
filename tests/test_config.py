from pathlib import Path

import pytest

from app.config import load_access_policy_config


CONFIG_PATH = Path("configs/access_policies.yaml")


def test_load_access_policy_config_from_repo_file() -> None:
    config = load_access_policy_config(CONFIG_PATH)

    assert config.default == "deny_all"
    assert len(config.roots) == 13
    assert config.roots[0].name == "HR"
    assert "/Development" in config.roots[0].allow_ou  # resolved from group
    assert config.roots[1].name == "Development"
    assert config.roots[1].allow_ou == ["/Development", "/Product"]


def test_load_access_policy_config_requires_deny_all_default(tmp_path: Path) -> None:
    config_path = tmp_path / "access_policies.yaml"
    config_path.write_text(
        """
default: allow_all
roots:
  - name: HR
    page_id: "page-id"
    allow_ou:
      - "/"
    allow_users: []
""".strip()
    )

    with pytest.raises(ValueError, match="deny_all"):
        load_access_policy_config(config_path)


def test_load_access_policy_config_resolves_ou_groups(tmp_path: Path) -> None:
    config_path = tmp_path / "access_policies.yaml"
    config_path.write_text(
        """
default: deny_all

groups:
  all_internal:
    - "/Development"
    - "/Sales"

roots:
  - name: HR
    page_id: "hr-page"
    allow_ou_group: all_internal
    allow_users: []

  - name: Dev
    page_id: "dev-page"
    allow_ou:
      - "/Development"
    allow_users: []
""".strip()
    )

    config = load_access_policy_config(config_path)

    assert config.roots[0].name == "HR"
    assert config.roots[0].allow_ou == ["/Development", "/Sales"]
    assert config.roots[1].name == "Dev"
    assert config.roots[1].allow_ou == ["/Development"]
