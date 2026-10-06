# IdeaGate

Takes a one-line product idea and returns a sourced verdict (Kill, Amend or Pursue). Proof of spending first, pre-sell second, build only after commitments.

**Status: M1 (skeleton and normalizer).** `run`, `resume` and `show` work; the pipeline currently ends after Stage 0 (idea to brief).

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

## Understanding the output
`run`, `resume` and `show` print the same report:
- **Run header:** run id, status (`completed` once Stage 0 finishes; `failed` if a stage errored, in which case `resume` continues) and total cost in USD.
- **Stage table:** one row per stage with its status, model, prompt version, cost and duration.
- **Idea brief** (from Stage 0): title and one-liner, target customer (and buyer if different), job to be done, current workaround, and the 3 to 5 riskiest assumptions that later stages will test.
- **Possible duplicates:** shown in yellow when the idea resembles one you ran before, with the earlier idea's id and a similarity percentage.

## Layout
`src/ideagate/`: `cli.py`, `config.py`, `db/`, `pipeline/` (orchestrator, context), `stages/`, `schemas/`, `agents/runner.py` (Agent SDK wrapper), `prompts/` (versioned `.md` files), `tools/`, `exporters/`. Later milestones fill in the rest.
