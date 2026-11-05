"""Propagate the version from pyproject.toml (single source of truth) to the README.

Usage:
    python scripts/sync_version.py          # rewrite the README badge
    python scripts/sync_version.py --check  # exit 1 if README or CHANGELOG lag behind
"""

from __future__ import annotations

import re
import sys
import tomllib
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
BADGE = re.compile(r"(img\.shields\.io/badge/version-)([0-9]+\.[0-9]+\.[0-9]+)(-)")


def version() -> str:
    with (ROOT / "pyproject.toml").open("rb") as fh:
        return tomllib.load(fh)["project"]["version"]


def main(check: bool) -> int:
    v = version()
    readme = ROOT / "README.md"
    text = readme.read_text(encoding="utf-8")
    found = BADGE.search(text)
    problems = []
    if not found:
        problems.append("README has no version badge")
    elif found.group(2) != v:
        if check:
            problems.append(f"README badge {found.group(2)} != pyproject {v}")
        else:
            readme.write_text(BADGE.sub(rf"\g<1>{v}\g<3>", text), encoding="utf-8")
    changelog = (ROOT / "CHANGELOG.md").read_text(encoding="utf-8")
    if f"## [{v}]" not in changelog:
        problems.append(f"CHANGELOG has no entry for {v}")
    for p in problems:
        print(f"version: {p}")
    return 1 if problems else 0


if __name__ == "__main__":
    sys.exit(main("--check" in sys.argv))
