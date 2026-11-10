import re
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent


def test_ets2_asset_folders_are_git_ignored_except_markers():
    lines = {line.strip() for line in (ROOT / ".gitignore").read_text().splitlines()}
    for folder in ("drivers", "brands", "trucks"):
        assert f"assets/{folder}/*" in lines
        assert f"!assets/{folder}/.gitkeep" in lines
    assert ".env" in lines


def test_no_credentials_are_hardcoded_in_source():
    literal = re.compile(r"""password\s*=\s*["']""", re.I)
    for path in ROOT.rglob("*.py"):
        if "tests" in path.parts or ".venv" in path.parts:
            continue
        assert not literal.search(path.read_text(encoding="utf-8")), path
