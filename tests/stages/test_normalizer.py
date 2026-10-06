"""Stage 0 against a recorded fixture: no paid API calls."""

from ideagate.pipeline.context import RunContext
from ideagate.schemas.brief import IdeaBrief, IdeaInput
from ideagate.stages import normalizer


def _ctx(config, repo, run_id, idea_id):
    return RunContext(config=config, repo=repo, run_id=run_id, idea_id=idea_id, stage="normalizer")


def test_normalizer_produces_valid_brief_and_logs_cost(config, repo, fixture_backend):
    run = repo.create_run({"idea": "Vue 2 migration audit"})
    ctx = _ctx(config, repo, run.id, run.idea_id)
    brief = normalizer.run(IdeaInput(idea="Vue 2 migration audit"), ctx)

    assert isinstance(brief, IdeaBrief)
    assert 3 <= len(brief.riskiest_assumptions) <= 5
    call = fixture_backend.calls[0]
    assert call["model"] == config.models.strong  # model comes from config, never code
    assert call["tools"] == []  # agents get no tools in M1
    assert "<untrusted_idea>" in call["prompt"]
    assert repo.cost_by_stage(run.id) == {"normalizer": 0.0123}
    assert (config.reports_dir / str(run.id) / "run.log.jsonl").exists()


def test_duplicate_flagged(config, repo, fixture_backend):
    old = repo.create_run({"idea": "x"})
    repo.update_idea(
        old.idea_id,
        title="Old",
        one_liner=(
            "A fixed-fee audit that estimates the cost and risk of migrating a Vue 2 codebase to Vue 3."
        ),
    )
    new = repo.create_run({"idea": "Vue 2 migration audit"})
    brief = normalizer.run(IdeaInput(idea="Vue 2 migration audit"), _ctx(config, repo, new.id, new.idea_id))
    assert [d.idea_id for d in brief.possible_duplicates] == [old.idea_id]


def test_human_note_reaches_prompt(config, repo, fixture_backend):
    run = repo.create_run({"idea": "Vue 2 migration audit"})
    ctx = _ctx(config, repo, run.id, run.idea_id)
    ctx.note = "focus on agencies"
    normalizer.run(IdeaInput(idea="Vue 2 migration audit"), ctx)
    assert "focus on agencies" in fixture_backend.calls[0]["prompt"]
