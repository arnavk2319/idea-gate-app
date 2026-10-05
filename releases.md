# Releases

Newest first. Every change set gets a version here (patch for fixes and docs, minor for a milestone or feature,
major for breaking changes), mirrored in `pyproject.toml` and as a git tag `vX.Y.Z`.

## v0.0.1 - 2026-10-05 - Project scaffolding (main)
- Packaging: `pyproject.toml` (Python 3.12, uv, Typer, Pydantic v2, SQLModel, Agent SDK) and `uv.lock`.
- Config templates: `ideagate.yaml.example`, `.env.example` (real `ideagate.yaml` and `.env` stay local).
- Docs: `README.md`, `DECISIONS.md` (open decisions resolved: Exa, Python, $3/run, no chat bot).
- `.gitignore` covering secrets, runtime data, tooling and assistant/project-management meta.
- Milestone code lives on feature branches; M1 is on `feature/module-1`.
