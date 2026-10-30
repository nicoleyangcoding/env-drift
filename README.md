# env-drift

Find the environment variables your code reads that `.env.example` doesn't mention, and the entries in `.env.example` that nothing reads anymore.

New teammates clone the repo, copy `.env.example`, and the app crashes on a variable nobody wrote down. Or the example file keeps listing keys that were removed a year ago. `env-drift` checks the two against each other in under a second.

```
$ env-drift
Missing from .env.example (your code reads these):
  STRIPE_WEBHOOK_SECRET  api/webhooks.ts:14
  SENTRY_DSN             src/sentry.ts:3, worker/main.py:8

Unused in .env.example (nothing reads these):
  LEGACY_API_URL         .env.example:12

2 missing, 1 unused, 9 documented and used.
```

## Quick start

Requires Python 3.9 or newer. No dependencies.

```bash
pipx install git+https://github.com/nicoleyangcoding/env-drift
cd your-project
env-drift
```

It exits with status 1 when something is missing, so it works as a check in CI or a pre-commit hook.

## What it understands

| Language | Reads it finds |
| --- | --- |
| JavaScript, TypeScript, Vue, Svelte, Astro | `process.env.X`, `process.env["X"]`, `const { X } = process.env`, `import.meta.env.X`, `Deno.env.get("X")`, `Bun.env.X` |
| Python | `os.environ["X"]`, `os.environ.get("X")`, `os.getenv("X")` |
| Ruby | `ENV["X"]`, `ENV.fetch("X")` |
| Go | `os.Getenv("X")`, `os.LookupEnv("X")` |
| Rust | `env::var("X")`, `env!("X")`, `option_env!("X")` |
| PHP | `getenv("X")`, `env("X")`, `$_ENV["X"]` |
| Java, Kotlin, Scala, C# | `System.getenv("X")`, `Environment.GetEnvironmentVariable("X")` |

The example file is the first of `.env.example`, `.env.sample`, `.env.template`, `.env.dist`, `example.env` or `.env.defaults` it finds, or whatever you pass with `--example`.

It skips files git ignores, plus `node_modules`, virtual environments and build folders. Variables set by the system, CI or your host (`PATH`, `NODE_ENV`, `CI`, `GITHUB_*`, `VERCEL_*` and similar) are never reported.

## Options

```bash
env-drift services/api                       # check one folder of a monorepo
env-drift --example config/.env.sample       # use a different example file
env-drift --ignore 'DEBUG_*' --ignore LOCAL  # skip names or globs
env-drift --strict                           # also fail on unused entries
env-drift --format json                      # for scripts
```

## GitHub Action

```yaml
name: env
on: pull_request

jobs:
  env-drift:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v7
      - uses: nicoleyangcoding/env-drift@v0
```

Missing variables are marked on the exact line of the pull request, and the summary lands on the job page. Inputs: `path`, `example`, `ignore` (space-separated), `strict` (`true`/`false`).

## Limits

`env-drift` reads code; it doesn't run it. A name built at runtime, like `process.env[name]`, can't be seen. Those reads are skipped rather than guessed at.

## Privacy

It only reads variable *names* from your example file and source code. It never opens `.env` itself, never prints values, and makes no network requests.

## Contributing

Support for another language is usually a single regular expression. See [CONTRIBUTING.md](CONTRIBUTING.md). Planned work is in [ROADMAP.md](ROADMAP.md).

## License

[MIT](LICENSE)
