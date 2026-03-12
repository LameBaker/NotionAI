from pathlib import Path
import sys

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app.config import load_access_policy_config


CONFIG_PATH = Path("configs/access_policies.yaml")


def test_load_access_policy_config_from_repo_file() -> None:
    config = load_access_policy_config(CONFIG_PATH)

    assert config.default == "deny_all"
    assert len(config.roots) == 2
    assert config.roots[0].name == "HR"
    assert config.roots[1].allow_ou == ["/Development"]


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
