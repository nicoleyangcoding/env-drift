"""Compare what code reads with what the example file documents."""

from __future__ import annotations

import fnmatch
import json
from dataclasses import dataclass

from .scan import Use

# Set by the OS, the shell, CI or the hosting platform, so nobody puts them in .env.example.
BUILT_IN = {
    "NODE_ENV",
    "PATH",
    "HOME",
    "USER",
    "USERNAME",
    "PWD",
    "SHELL",
    "TERM",
    "LANG",
    "TZ",
    "CI",
    "HOSTNAME",
    "TMPDIR",
    "TEMP",
    "TMP",
    "APPDATA",
    "LOCALAPPDATA",
    "USERPROFILE",
    "NEXT_RUNTIME",
    # Vite fills these in on import.meta.env
    "BASE_URL",
    "MODE",
    "DEV",
    "PROD",
    "SSR",
}
BUILT_IN_PREFIXES = ("GITHUB_", "RUNNER_", "VERCEL_", "NETLIFY_", "RENDER_", "RAILWAY_", "npm_")


@dataclass
class Result:
    example: str
    missing: dict[str, list[Use]]
    unused: dict[str, int]
    documented_and_used: int


def compare(
    uses: list[Use],
    documented: dict[str, int],
    example: str,
    ignore: list[str],
    optional: set[str] | frozenset[str] = frozenset(),
) -> Result:
    def skipped(name: str) -> bool:
        return (
            name in BUILT_IN
            or name.startswith(BUILT_IN_PREFIXES)
            or any(fnmatch.fnmatchcase(name, pattern) for pattern in ignore)
        )

    read: dict[str, list[Use]] = {}
    for use in uses:
        if not skipped(use.name):
            read.setdefault(use.name, []).append(use)
    every_name = {use.name for use in uses}
    missing = {name: found for name, found in sorted(read.items()) if name not in documented}
    unused = {
        name: line
        for name, line in sorted(documented.items())
        if name not in every_name and name not in optional and not skipped(name)
    }
    return Result(example, missing, unused, sum(1 for name in read if name in documented))


def _where(uses: list[Use], limit: int = 3) -> str:
    places = list(dict.fromkeys(f"{u.file}:{u.line}" for u in uses))
    shown = ", ".join(places[:limit])
    return shown + (f" (+{len(places) - limit} more)" if len(places) > limit else "")


def text(result: Result) -> str:
    out = []
    if result.missing:
        width = max(map(len, result.missing))
        out.append(f"Missing from {result.example} (your code reads these):")
        out += [f"  {name:<{width}}  {_where(uses)}" for name, uses in result.missing.items()]
        out.append("")
    if result.unused:
        width = max(map(len, result.unused))
        out.append(f"Unused in {result.example} (nothing reads these):")
        out += [f"  {name:<{width}}  {result.example}:{line}" for name, line in result.unused.items()]
        out.append("")
    if not result.missing and not result.unused:
        out.append(
            f"All good: every variable your code reads is in {result.example}, and every entry is used."
        )
    else:
        out.append(
            f"{len(result.missing)} missing, {len(result.unused)} unused, "
            f"{result.documented_and_used} documented and used."
        )
    return "\n".join(out)


def github(result: Result) -> str:
    """Workflow commands, so each problem shows up on the right line of the pull request."""
    out = []
    for name, uses in result.missing.items():
        for use in uses:
            out.append(
                f"::error file={use.file},line={use.line},title=env-drift::"
                f"{name} is read here but missing from {result.example}"
            )
    for name, line in result.unused.items():
        out.append(
            f"::warning file={result.example},line={line},title=env-drift::"
            f"{name} is documented but never read"
        )
    return "\n".join(out + [text(result)])


def as_json(result: Result) -> str:
    return json.dumps(
        {
            "example": result.example,
            "missing": [
                {"name": name, "used_at": [f"{u.file}:{u.line}" for u in uses]}
                for name, uses in result.missing.items()
            ],
            "unused": [{"name": name, "line": line} for name, line in result.unused.items()],
            "documented_and_used": result.documented_and_used,
        },
        indent=2,
    )
