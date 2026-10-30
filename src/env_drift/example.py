"""Read the variable names a .env.example file documents."""

from __future__ import annotations

import re
from pathlib import Path

CANDIDATES = (".env.example", ".env.sample", ".env.template", ".env.dist", "example.env", ".env.defaults")
_LINE = re.compile(r"^\s*(?:export\s+)?([A-Za-z_][A-Za-z0-9_]*)\s*=")


def find(root: Path) -> Path | None:
    for name in CANDIDATES:
        if (root / name).is_file():
            return root / name
    return None


def parse(text: str) -> dict[str, int]:
    """Each documented name and the line it's on. Commented-out lines don't count."""
    names: dict[str, int] = {}
    for number, line in enumerate(text.splitlines(), start=1):
        match = _LINE.match(line)
        if match:
            names.setdefault(match.group(1), number)
    return names
