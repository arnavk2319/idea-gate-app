# IdeaGate

Takes a one-line product idea and returns a sourced verdict (Kill, Amend or Pursue). Proof of spending first, pre-sell second, build only after commitments. See `DECISIONS.md` for choices made along the way.

**Status: M1 (skeleton and normalizer), v0.1.0.** `run`, `resume` and `show` work; the pipeline currently ends after Stage 0 (idea to brief).

## Setup
```bash
python3.12 -m pip install --user uv        # once; or install uv another way
python3.12 -m uv sync
cp ideagate.yaml.example ideagate.yaml      # then edit
cp .env.example .env                         # then add ANTHROPIC_API_KEY
```

## Use
```bash
python3.12 -m uv run ideagate run "AI-assisted Vue 2 to Vue 3 migration audit"
python3.12 -m uv run ideagate show 1
python3.12 -m uv run ideagate resume 1       # continues from the last finished stage
```
State lives in `ideagate.db`; per-run structured logs in `reports/<run_id>/run.log.jsonl`.

## Tests (offline, no API calls)
```bash
python3.12 -m uv run pytest
```
Tests use a fake agent backend and fixtures; CI also runs them with the network blocked and API keys empty, so a test that tries to reach a paid API fails.

## Checks before a PR
CI runs these on every PR to `main`; run them locally first:
```bash
python3.12 -m uv lock --check          # lockfile matches pyproject.toml
python3.12 -m uv run ruff check .      # lint
python3.12 -m uv run ruff format --check .
python3.12 -m uv run pytest --disable-socket --allow-unix-socket
python3.12 scripts/check_pr.py origin/main   # version bumped, releases.md entry, no attribution trailers
```
Every PR must bump `version` in `pyproject.toml` and add a matching entry at the top of `releases.md`. `main` is protected: changes go through a PR with passing checks. Secrets are scanned with gitleaks.

## Layout
`src/ideagate/`: `cli.py`, `config.py`, `db/`, `pipeline/` (orchestrator, context), `stages/`, `schemas/`, `agents/runner.py` (Agent SDK wrapper), `prompts/` (versioned `.md` files), `tools/`, `exporters/`. Later milestones fill in the rest.
