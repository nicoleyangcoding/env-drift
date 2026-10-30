# Roadmap

Small, focused releases. Ideas and votes are welcome in [issues](https://github.com/nicoleyangcoding/env-drift/issues).

## 0.2
- [ ] `--fix`: append missing names to the example file, each with an empty value and a `# used in <file>` comment
- [ ] `--fix --remove-unused`: comment out unused entries instead of deleting them
- [ ] Read `# env-drift: optional` on an example line to mark a variable as allowed-unused
- [ ] An inline `env-drift: ignore` comment on a code line to skip that read
- [ ] Count reads in `docker-compose.yml` (`${NAME}` and `environment:` keys) as uses

## 0.3
- [ ] Python: `os.environ.setdefault("X", ...)` and pydantic `BaseSettings` field names
- [ ] JavaScript: `env.X` after `const env = process.env`, and `zod`/`envalid`/`t3-env` schemas
- [ ] Next.js: warn when a `NEXT_PUBLIC_` name is read in server-only files, and the reverse
- [ ] Vite: warn when client code reads a name without the `VITE_` prefix (it will be undefined)
- [ ] Shell scripts: `${NAME}` and `$NAME` in `*.sh` files, behind `--include-shell`

## 0.4
- [ ] Monorepos: `--each` checks every folder that has its own example file and reports per folder
- [ ] Config file (`.env-drift.toml`) for ignore lists and extra example files
- [ ] `--format markdown` for pasting into pull requests and wikis
- [ ] `--format sarif` so findings show up in GitHub code scanning
- [ ] Group the output by file with `--by-file`

## 0.5
- [ ] Also compare against `.env` (names only, never values) with `--local`, to show what your own setup is missing
- [ ] Check that every name in the example also appears in the deployment config (`vercel.json`, `fly.toml`, `render.yaml`, `app.json`)
- [ ] Detect duplicate names in the example file and names that differ only by case
- [ ] Warn about example values that look like real secrets (long random strings, `sk_live_`, `AKIA`)

## Later
- [ ] More languages: Elixir (`System.get_env`), Swift (`ProcessInfo.processInfo.environment`), Dart (`Platform.environment`), Deno `Deno.env.toObject` destructuring
- [ ] A pre-commit hook definition (`.pre-commit-hooks.yaml`)
- [ ] Publish to PyPI so `pipx install env-drift` works
- [ ] Homebrew formula
- [ ] Generate a table of variables (name, where it's used, comment from the example) for the README

## Not planned
- Reading or printing secret values. env-drift only ever looks at names.
- Running code to resolve dynamic names.
