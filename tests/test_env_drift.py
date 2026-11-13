from __future__ import annotations

import json
import subprocess
from pathlib import Path

import pytest

from env_drift import cli, example, report, scan


def names(text: str, file: str) -> list[str]:
    return [u.name for u in scan.scan_text(text, file)]


@pytest.mark.parametrize(
    ("file", "line", "expected"),
    [
        (
            "a.ts",
            "const url = process.env.API_URL ?? process.env['FALLBACK_URL']",
            ["API_URL", "FALLBACK_URL"],
        ),
        (
            "a.js",
            "const { STRIPE_KEY, TOKEN: token, DEBUG = '0' } = process.env",
            ["STRIPE_KEY", "TOKEN", "DEBUG"],
        ),
        ("a.tsx", "fetch(import.meta.env.VITE_API)", ["VITE_API"]),
        ("a.ts", "Deno.env.get('DENO_KEY'); Bun.env.BUN_KEY", ["DENO_KEY", "BUN_KEY"]),
        (
            "a.py",
            'os.environ["DB_URL"]; os.environ.get("DB_POOL"); os.getenv("DB_USER")',
            ["DB_URL", "DB_POOL", "DB_USER"],
        ),
        ("a.py", "from os import environ, getenv; environ['A']; getenv('B')", ["A", "B"]),
        ("a.rb", 'ENV["RAILS_KEY"]; ENV.fetch("REDIS_URL")', ["RAILS_KEY", "REDIS_URL"]),
        ("main.go", 'os.Getenv("PORT"); os.LookupEnv("GO_SECRET")', ["PORT", "GO_SECRET"]),
        ("main.rs", 'env::var("RUST_KEY"); env!("BUILD_ID")', ["RUST_KEY", "BUILD_ID"]),
        ("a.php", "env('APP_KEY'); getenv(\"MAIL_HOST\"); $_ENV['QUEUE']", ["APP_KEY", "MAIL_HOST", "QUEUE"]),
        ("A.java", 'System.getenv("JAVA_KEY")', ["JAVA_KEY"]),
        ("A.cs", 'Environment.GetEnvironmentVariable("CS_KEY")', ["CS_KEY"]),
        ("a.ts", "const key = process.env[name]", []),
        ("notes.md", "process.env.NOT_CODE", []),
    ],
)
def test_scan_text(file, line, expected):
    assert names(line, file) == expected


def test_line_numbers():
    uses = scan.scan_text("a\nb\nprocess.env.X\n", "a.js")
    assert uses == [scan.Use("X", "a.js", 3)]


def test_parse_example():
    text = "# comment\nexport A=1\nB=\n  C = 3\n# D=4\nB=again\nnot a line\n"
    assert example.parse(text) == {"A": 2, "B": 3, "C": 4}


def test_optional_marker():
    text = "A=  # env-drift: optional\nB=1 #env-drift:Optional\nC=  # optional\n# D=  # env-drift: optional\n"
    assert example.optional(text) == {"A", "B"}


def project(tmp_path: Path, files: dict[str, str]) -> Path:
    for name, body in files.items():
        path = tmp_path / name
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(body)
    return tmp_path


def test_compare_and_builtins():
    uses = [
        scan.Use("API_URL", "a.ts", 1),
        scan.Use("SECRET", "a.ts", 2),
        scan.Use("SECRET", "b.py", 9),
        scan.Use("NODE_ENV", "a.ts", 3),
        scan.Use("GITHUB_SHA", "a.ts", 4),
        scan.Use("DEBUG_SQL", "a.ts", 5),
    ]
    result = report.compare(uses, {"API_URL": 1, "OLD": 2, "NODE_ENV": 3}, ".env.example", ["DEBUG_*"])
    assert list(result.missing) == ["SECRET"]
    assert [u.file for u in result.missing["SECRET"]] == ["a.ts", "b.py"]
    assert result.unused == {"OLD": 2}
    assert result.documented_and_used == 1


def test_cli_end_to_end(tmp_path, capsys):
    root = project(
        tmp_path,
        {
            ".env.example": "API_URL=\nOLD_TOKEN=\n",
            "src/app.ts": "fetch(process.env.API_URL)\nconst k = process.env.STRIPE_KEY\n",
            "node_modules/x/index.js": "process.env.IGNORED_DEP",
        },
    )
    assert cli.main([str(root)]) == 1
    out = capsys.readouterr().out
    assert "STRIPE_KEY" in out and "src/app.ts:2" in out
    assert "OLD_TOKEN" in out and "IGNORED_DEP" not in out
    assert "1 missing, 1 unused, 1 documented and used." in out


def test_cli_exit_codes_and_formats(tmp_path, capsys):
    root = project(tmp_path, {".env.sample": "A=\nB=\n", "x.py": "os.getenv('A')"})
    assert cli.main([str(root)]) == 0
    assert cli.main([str(root), "--strict"]) == 1
    capsys.readouterr()
    cli.main([str(root), "--format", "json"])
    data = json.loads(capsys.readouterr().out)
    assert data["example"] == ".env.sample" and data["unused"] == [{"name": "B", "line": 2}]
    cli.main([str(root), "--format", "github"])
    assert "::warning file=.env.sample,line=2,title=env-drift::B is documented but never read" in (
        capsys.readouterr().out
    )


def test_all_good(tmp_path, capsys):
    root = project(tmp_path, {".env.example": "A=\n", "x.go": 'os.Getenv("A")'})
    assert cli.main([str(root)]) == 0
    assert "All good" in capsys.readouterr().out


def test_missing_example(tmp_path, capsys):
    assert cli.main([str(tmp_path)]) == 2
    assert "no example file found" in capsys.readouterr().err


def test_respects_gitignore(tmp_path, capsys):
    root = project(
        tmp_path,
        {
            ".gitignore": "generated/\n",
            ".env.example": "A=\n",
            "a.js": "process.env.A",
            "generated/b.js": "process.env.B",
        },
    )
    subprocess.run(["git", "init", "-q", str(root)], check=True)
    assert cli.main([str(root)]) == 0


def test_optional_entries_are_not_unused(tmp_path, capsys):
    root = project(
        tmp_path,
        {".env.example": "A=\nSENTRY_DSN=  # env-drift: optional\nOLD=\n", "x.py": "os.getenv('A')"},
    )
    assert cli.main([str(root), "--strict"]) == 1
    out = capsys.readouterr().out
    assert "OLD" in out and "SENTRY_DSN" not in out
    assert "0 missing, 1 unused, 1 documented and used." in out
