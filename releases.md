# Releases

Newest first. Every change set gets a version here (patch for fixes and docs, minor for a milestone or feature,
major for breaking changes), mirrored in `pyproject.toml` and as a git tag `vX.Y.Z`.

## v0.1.0 - 2026-10-05 - M1: skeleton and normalizer (feature/module-1)
- Config: typed `ideagate.yaml` loader; rejects placeholder model ids and invalid rubric weights.
- DB: seven SQLModel tables plus `input_json`/`trace_json`/`error` columns for resume and re-run.
- Schemas: `Evidence`, `Finding`, `IdeaInput`, `IdeaBrief` (3 to 5 riskiest assumptions enforced).
- Agent runner: Claude Agent SDK wrapper with structured output, no tools, cost logging and traces; backend is injectable for offline tests.
- Stage 0 normalizer with a versioned prompt file; text-similarity duplicate flags.
- Orchestrator with per-stage checkpoints and `resume`; JSON-lines run logs.
- CLI: `run`, `resume`, `show`.
- 15 offline tests (config, schemas, prompts, orchestrator resume, normalizer fixture, CLI).
- Merged `main` (CI, ruff config) in; fixed ruff lint and format issues so the new PR checks pass.
- README: added an output guide; DECISIONS: lint, PR gate, network-blocked test decisions and the development workflow (kept out of the README).

## v0.0.3 - 2026-10-05 - PR checks (main)
- Added GitHub Actions CI for PRs to `main`: lockfile check, ruff lint and format, pytest with network blocked and API keys empty, package build, gitleaks secret scan.
- Added `scripts/check_pr.py`: version must be bumped, newest `releases.md` entry must match, no attribution trailers in commits.
- Added PR template checklist; added `ruff` and `pytest-socket` dev dependencies and ruff config.
- Branch protection rules still need to be enabled in GitHub settings.

## v0.0.2 - 2026-10-05 - Connect to GitHub (main)
- Merged the placeholder "Initial commit" from the new GitHub repo into local history (unrelated histories); kept our README.
- Added `origin` remote; `main`, `feature/module-1` and tags pushed.

## v0.0.1 - 2026-10-05 - Project scaffolding (main)
- Packaging: `pyproject.toml` (Python 3.12, uv, Typer, Pydantic v2, SQLModel, Agent SDK) and `uv.lock`.
- Config templates: `ideagate.yaml.example`, `.env.example` (real `ideagate.yaml` and `.env` stay local).
- Docs: `README.md`, `DECISIONS.md` (open decisions resolved: Exa, Python, $3/run, no chat bot).
- `.gitignore` covering secrets, runtime data, tooling and assistant/project-management meta.
- Milestone code lives on feature branches; M1 is on `feature/module-1`.
