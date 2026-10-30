"""Find the environment variables that code reads."""

from __future__ import annotations

import os
import re
import subprocess
from dataclasses import dataclass
from pathlib import Path

NAME = r"([A-Za-z_][A-Za-z0-9_]*)"
Q = r"['\"`]"


def _compile(*patterns: str) -> list[re.Pattern[str]]:
    return [re.compile(p) for p in patterns]


# Literal reads only. Something like process.env[key] can't be resolved without running the code.
JS = _compile(
    rf"process\.env\.{NAME}",
    rf"process\.env\[\s*{Q}{NAME}{Q}\s*\]",
    rf"import\.meta\.env\.{NAME}",
    rf"Deno\.env\.get\(\s*{Q}{NAME}{Q}",
    rf"Bun\.env\.{NAME}",
)
LANGUAGES = {
    "js": JS,
    "py": _compile(rf"\b(?:environ(?:\.get)?|getenv)\s*[\[(]\s*{Q}{NAME}{Q}"),
    "rb": _compile(rf"\bENV(?:\.fetch\(\s*|\[\s*){Q}{NAME}{Q}"),
    "go": _compile(rf"\bos\.(?:Getenv|LookupEnv)\(\s*\"{NAME}\""),
    "rs": _compile(rf"\b(?:env::var(?:_os)?\(|env!\(|option_env!\()\s*\"{NAME}\""),
    "php": _compile(rf"\b(?:getenv|env)\(\s*{Q}{NAME}{Q}", rf"\$_ENV\[\s*{Q}{NAME}{Q}"),
    "jvm": _compile(rf"\bSystem\.getenv\(\s*\"{NAME}\""),
    "cs": _compile(rf"\bEnvironment\.GetEnvironmentVariable\(\s*\"{NAME}\""),
}
SUFFIXES = {
    **dict.fromkeys(
        (".js", ".jsx", ".mjs", ".cjs", ".ts", ".tsx", ".mts", ".cts", ".vue", ".svelte", ".astro"), "js"
    ),
    ".py": "py",
    **dict.fromkeys((".rb", ".rake", ".erb"), "rb"),
    ".go": "go",
    ".rs": "rs",
    ".php": "php",
    **dict.fromkeys((".java", ".kt", ".kts", ".scala"), "jvm"),
    ".cs": "cs",
}

# const { API_URL, TOKEN: token, DEBUG = "0" } = process.env
_DESTRUCTURE = re.compile(r"\{([^{}]*)\}\s*=\s*(?:process\.env|import\.meta\.env|Bun\.env)\b")

SKIP_DIRS = {
    ".git",
    "node_modules",
    ".venv",
    "venv",
    "__pycache__",
    "dist",
    "build",
    ".next",
    ".nuxt",
    ".svelte-kit",
    "vendor",
    "target",
    "coverage",
    ".turbo",
    ".cache",
}
MAX_BYTES = 1_000_000


@dataclass(frozen=True)
class Use:
    name: str
    file: str
    line: int


def _destructured(line: str) -> list[str]:
    names = []
    for match in _DESTRUCTURE.finditer(line):
        for part in match.group(1).split(","):
            key = part.split(":")[0].split("=")[0].strip()
            if re.fullmatch(NAME, key):
                names.append(key)
    return names


def scan_text(text: str, file: str) -> list[Use]:
    language = SUFFIXES.get(Path(file).suffix.lower())
    if not language:
        return []
    patterns = LANGUAGES[language]
    found = []
    for number, line in enumerate(text.splitlines(), start=1):
        names = [m.group(1) for p in patterns for m in p.finditer(line)]
        if language == "js":
            names += _destructured(line)
        found += [Use(name, file, number) for name in dict.fromkeys(names)]
    return found


def source_files(root: Path) -> list[Path]:
    """Files git knows about (tracked or new, minus ignored), or a plain walk outside a repo."""
    try:
        out = subprocess.run(
            ["git", "-C", str(root), "ls-files", "-z", "--cached", "--others", "--exclude-standard"],
            capture_output=True,
            check=True,
        ).stdout
        paths = [root / p for p in out.decode("utf-8", "replace").split("\0") if p]
    except (OSError, subprocess.CalledProcessError):
        paths = []
        for folder, dirs, files in os.walk(root):
            dirs[:] = [d for d in dirs if d not in SKIP_DIRS]
            paths += [Path(folder) / f for f in files]
    return sorted(
        p
        for p in paths
        if p.suffix.lower() in SUFFIXES
        and not SKIP_DIRS.intersection(p.relative_to(root).parts)
        and p.is_file()
        and p.stat().st_size <= MAX_BYTES
    )


def scan(root: Path) -> list[Use]:
    uses = []
    for path in source_files(root):
        text = path.read_text(encoding="utf-8", errors="replace")
        uses += scan_text(text, path.relative_to(root).as_posix())
    return uses
