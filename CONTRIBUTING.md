# Contributing

Thanks for helping. This project reads values from NBE pellet burner controllers and publishes them to Home Assistant. It controls a heating appliance, so changes are made carefully.

## Ground rules

- **Read-only.** The bridge only reads from the controller. A change that writes to the controller (setpoints, on/off) needs a design discussion first, confirmation on every command, safe limits and an audit log. Open an issue before writing code for it.
- **No secrets or personal data** in code, tests, logs, issues or screenshots. Use placeholders such as `192.0.2.10` and `123456`.
- **Say what you tested.** Hardware behaviour differs between controller firmware versions. State your burner model, controller version and firmware.

## Workflow

1. Fork, then branch from `master`: `type/short-description` (for example `fix/timeseries-path`).
2. Write the test first. Make the smallest change that makes it pass.
3. Run the checks:
   ```
   python3 -m venv .venv
   .venv/bin/pip install -r requirements-dev.txt
   .venv/bin/ruff check src tests
   .venv/bin/pytest
   ```
   `requirements.in` and `requirements-dev.in` hold the direct dependencies and are the source. `requirements.txt` and `requirements-dev.txt` are generated from them and hash-pinned; CI and the Docker image install from them with `--require-hashes`. After changing a pin in a `.in` file, regenerate with `pip-compile --generate-hashes --strip-extras -o requirements.txt requirements.in` (and `-o requirements-dev.txt requirements-dev.in`). Dependabot bumps the hash-pinned `.txt` files; if it leaves the `.in` pin behind, update that pin to match.
4. Update `CHANGELOG.md`.
5. Open a pull request. Squash merge is used. Keep one logical change per pull request.

## Commits

Conventional Commits: `feat`, `fix`, `docs`, `refactor`, `test`, `chore`. Imperative, lowercase subject.

## Pre-commit (optional)

`pre-commit install` runs `gitleaks` and `ruff` before each commit.

## Releases

Maintainers tag `vX.Y.Z` (patch bumps by default). The release workflow checks that the tag matches `__version__`, runs CI, publishes a multi-arch image to GHCR and creates the GitHub release.

## License

By contributing you agree that your contribution is licensed under GPL-3.0-or-later, the license of this project.
