# Decisions

Where the plan was ambiguous or the user chose, newest milestone last.

## Open decisions, resolved (2026-10-05)
- Search provider: **Exa** (behind a `SearchProvider` interface, built in M2).
- Agent SDK language: **Python 3.12**.
- Starting run budget: **$3.00 per run**, $0.75 per stage (placeholders; revisit after the first five runs).
- Chat bot: **dropped.** The M6 chat-bot trigger will not be built. M6 is calibration evals and scheduled refresh only.
- Golden set: seeded from the user's IdeaStack list (`evals/ideastack_source.md`). Tier 1 maps to an expected Pursue band, Tier 2 to Amend, Tier 3 and "ruled out" to Kill. Final 10 to 15 picked at M6.

## M1
- **uv installed via `pip install --user uv`** (no Homebrew on this machine); run it as `python3.12 -m uv ...` unless `~/.local/bin` is on PATH.
- **Model ids live only in `ideagate.yaml`.** The example file ships `claude-opus-5-5` (strong) and `claude-haiku-4-5` (cheap); config validation rejects `<placeholder>` values.
- **No temperature control in the Agent SDK.** `ClaudeAgentOptions` has no temperature field, so the plan's "scorer at low temperature" cannot be done through it. Revisit at M3: either accept the SDK default and lean on the rubric and hard rules, or call the Messages API directly for tool-free stages.
- **Stage 0 runs with `tools=[]`, `setting_sources=[]`.** No built-in tools and no inherited Claude Code settings, skills or CLAUDE.md. Research stages (M2) will get only read-only custom tools.
- **Structured output** via the SDK's `output_format` JSON schema, validated again with Pydantic. The schema is `IdeaBriefCore`; `possible_duplicates` is added by code, not by the model.
- **Run/StageResult gained a few columns not in the plan's table:** `Run.input_json`, `Run.error`, `StageResult.input_json`, `StageResult.trace_json`. They are what make resume and "re-run from stored inputs" possible.
- **Run status `completed`** is used when the pipeline ends after Stage 0 (the plan's statuses assume a gate). M3/M4 replace it with `at_gate`, `killed`, `pursued`.
- **Duplicate detection in M1** is plain text similarity (`difflib`, threshold in config). Embeddings arrive in M5; note Anthropic offers no embeddings API, so M5 needs Voyage AI or a local model.
- **Stages are synchronous**; the runner wraps the SDK's async `query()` with `asyncio.run`. M2 will run the four research agents concurrently with `asyncio.gather` over an async variant.
- **`stage_usd_max` and `stage_timeout_s` are already passed to the SDK** (`max_budget_usd`, a timeout). Full budget-stop handling with partial output remains M3.
- **Resume is by stage checkpoint.** A killed process loses at most the stage that was in flight.
