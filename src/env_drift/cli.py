"""env-drift command line."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from . import __version__, example, report, scan


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="env-drift",
        description="Find environment variables your code reads that .env.example doesn't list, "
        "and listed ones nothing reads.",
        epilog="Examples:\n  env-drift\n  env-drift services/api --example services/api/.env.sample\n"
        "  env-drift --ignore 'DEBUG_*' --strict",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument("path", nargs="?", default=".", help="project folder (default: current folder)")
    parser.add_argument("--example", metavar="FILE", help="example file (default: .env.example or similar)")
    parser.add_argument(
        "--ignore", action="append", default=[], metavar="NAME", help="skip a name or glob (repeatable)"
    )
    parser.add_argument("--strict", action="store_true", help="also fail when the example has unused entries")
    parser.add_argument("--format", choices=("text", "json", "github"), default="text")
    parser.add_argument("--version", action="version", version=f"env-drift {__version__}")
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    root = Path(args.path).resolve()
    if not root.is_dir():
        print(f"env-drift: {args.path} is not a folder", file=sys.stderr)
        return 2

    path = Path(args.example) if args.example else example.find(root)
    if path is None or not path.is_file():
        names = ", ".join(example.CANDIDATES[:3])
        print(
            f"env-drift: no example file found in {args.path} (looked for {names}, ...). "
            "Pass --example FILE.",
            file=sys.stderr,
        )
        return 2

    try:
        shown = path.resolve().relative_to(root).as_posix()
    except ValueError:
        shown = str(path)
    result = report.compare(
        scan.scan(root), example.parse(path.read_text(encoding="utf-8")), shown, args.ignore
    )
    print({"text": report.text, "json": report.as_json, "github": report.github}[args.format](result))
    return 1 if result.missing or (args.strict and result.unused) else 0


if __name__ == "__main__":
    sys.exit(main())
