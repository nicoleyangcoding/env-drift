# Changelog

All notable changes are listed here. The format follows [Keep a Changelog](https://keepachangelog.com/en/1.1.0/), and versions follow [Semantic Versioning](https://semver.org/).

## [0.2.0] - 2026-11-13

### Added
- Mark an example entry with `# env-drift: optional` so it's never reported as unused

## [0.1.0] - 2026-10-30

### Added
- Find environment variable reads in JavaScript, TypeScript, Python, Ruby, Go, Rust, PHP, Java, Kotlin, Scala and C#
- Compare them with `.env.example` (or `.env.sample`, `.env.template` and similar) and report missing and unused names
- `--ignore` names or globs, `--strict` to fail on unused entries
- Output as text, JSON, or GitHub annotations
- GitHub Action that marks missing variables on the pull request and writes a job summary
