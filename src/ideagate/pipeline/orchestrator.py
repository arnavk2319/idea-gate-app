"""Deterministic state machine. Runs stages in order, persists each output before moving on.

LLM agents only ever run inside a stage. Resuming a run skips every stage that already has a
'done' result and continues from the first one that does not.
"""

from __future__ import annotations

import time
from collections.abc import Callable
from dataclasses import dataclass

from pydantic import BaseModel

from ideagate.config import Config
from ideagate.db.repo import Repo
from ideagate.pipeline.context import RunContext
from ideagate.schemas.brief import IdeaBrief, IdeaInput
from ideagate.stages import normalizer


@dataclass(frozen=True)
class StageSpec:
    name: str
    run: Callable[[BaseModel, RunContext], BaseModel]
    # Builds this stage's input from the run input and the outputs of earlier stages.
    build_input: Callable[[dict, dict[str, dict]], BaseModel]
    output_model: type[BaseModel]


def _normalizer_input(run_input: dict, _outputs: dict[str, dict]) -> BaseModel:
    return IdeaInput(**run_input)


# M1 registers Stage 0 only. Later milestones append stages here in pipeline order.
STAGES: list[StageSpec] = [
    StageSpec("normalizer", normalizer.run, _normalizer_input, IdeaBrief),
]


class Orchestrator:
    def __init__(self, config: Config, repo: Repo, stages: list[StageSpec] | None = None):
        self.config = config
        self.repo = repo
        self.stages = stages if stages is not None else STAGES

    def start(self, idea: str, notes: str | None = None) -> int:
        run = self.repo.create_run(IdeaInput(idea=idea, notes=notes).model_dump())
        return self.execute(run.id)

    def resume(self, run_id: int) -> int:
        run = self.repo.get_run(run_id)
        if run is None:
            raise KeyError(f"run {run_id} not found")
        if run.status in {"killed", "pursued"}:
            return run_id
        return self.execute(run_id)

    def execute(self, run_id: int) -> int:
        run = self.repo.get_run(run_id)
        self.repo.update_run(run_id, status="running", error=None, finished_at=None)
        outputs: dict[str, dict] = {}

        for spec in self.stages:
            done = self.repo.get_stage_result(run_id, spec.name)
            if done is not None:  # checkpoint hit: never redo finished work
                outputs[spec.name] = done.output_json
                continue

            ctx = RunContext(
                config=self.config, repo=self.repo, run_id=run_id, idea_id=run.idea_id, stage=spec.name
            )
            self.repo.update_run(run_id, current_stage=spec.name)
            ctx.log("stage_start")
            stage_input = spec.build_input(run.input_json, outputs)
            start = time.monotonic()
            try:
                result = spec.output_model.model_validate(spec.run(stage_input, ctx))
            except Exception as exc:
                self.repo.save_stage_result(
                    run_id=run_id,
                    stage=spec.name,
                    status="failed",
                    usd=ctx.usd,
                    trace_json=ctx.trace,
                    input_json=stage_input.model_dump(mode="json"),
                    prompt_version=ctx.prompt_version,
                    model=ctx.model,
                    duration_s=time.monotonic() - start,
                    output_json={"error": str(exc)},
                )
                self.repo.finish_run(run_id, "failed", error=f"{spec.name}: {exc}")
                ctx.log("stage_failed", error=str(exc))
                raise

            duration = time.monotonic() - start
            self.repo.save_stage_result(
                run_id=run_id,
                stage=spec.name,
                status="done",
                output_json=result.model_dump(mode="json"),
                prompt_version=ctx.prompt_version,
                model=ctx.model,
                usd=ctx.usd,
                duration_s=duration,
                input_json=stage_input.model_dump(mode="json"),
                trace_json=ctx.trace,
            )
            outputs[spec.name] = result.model_dump(mode="json")
            self._after_stage(spec.name, result, run.idea_id)
            ctx.log("stage_done", usd=ctx.usd, duration_s=round(duration, 2))

        # M1 ends after Stage 0, so the run is simply "completed".
        # M3/M4 replace this with at_gate/killed/pursued.
        self.repo.update_run(run_id, current_stage=None)
        self.repo.finish_run(run_id, "completed")
        return run_id

    def _after_stage(self, name: str, result: BaseModel, idea_id: int | None) -> None:
        if name == "normalizer" and idea_id is not None:
            self.repo.update_idea(idea_id, title=result.title, one_liner=result.one_liner)
