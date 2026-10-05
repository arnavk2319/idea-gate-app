"""Checkpoint/resume: a crash after one stage must not redo that stage."""
import pytest
from pydantic import BaseModel

from ideagate.pipeline.orchestrator import Orchestrator, StageSpec


class Out(BaseModel):
    n: int


class In(BaseModel):
    idea: str
    notes: str | None = None


def _build(counter, fail_second_once):
    state = {"failed": False}

    def first(inp, ctx):
        counter["first"] += 1
        ctx.record_cost(agent="a", model="m", input_tokens=1, output_tokens=1, usd=0.5)
        return Out(n=1)

    def second(inp, ctx):
        counter["second"] += 1
        if fail_second_once and not state["failed"]:
            state["failed"] = True
            raise RuntimeError("network down")
        return Out(n=2)

    build = lambda run_input, outs: In(**run_input)
    return [StageSpec("first", first, build, Out), StageSpec("second", second, build, Out)]


def test_resume_skips_finished_stage(config, repo):
    counter = {"first": 0, "second": 0}
    orch = Orchestrator(config, repo, _build(counter, fail_second_once=True))
    run_id = repo.create_run({"idea": "an idea"}).id

    with pytest.raises(RuntimeError):
        orch.execute(run_id)
    assert repo.get_run(run_id).status == "failed"
    assert repo.get_stage_result(run_id, "first") is not None

    orch.resume(run_id)
    assert counter == {"first": 1, "second": 2}  # stage "first" was never redone
    run = repo.get_run(run_id)
    assert run.status == "completed"
    assert run.total_usd == pytest.approx(0.5)
    assert repo.cost_by_stage(run_id) == {"first": pytest.approx(0.5)}


def test_resume_of_finished_run_is_a_noop(config, repo):
    counter = {"first": 0, "second": 0}
    orch = Orchestrator(config, repo, _build(counter, fail_second_once=False))
    run_id = repo.create_run({"idea": "an idea"}).id
    orch.execute(run_id)
    orch.resume(run_id)
    assert counter == {"first": 1, "second": 1}
