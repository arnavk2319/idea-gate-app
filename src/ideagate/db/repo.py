"""Thin data-access layer. Everything the orchestrator and CLI need to persist or read."""
from __future__ import annotations

from pathlib import Path
from typing import Optional

from sqlalchemy import func
from sqlmodel import Session, SQLModel, create_engine, select

from ideagate.db.models import CostEvent, Idea, Run, StageResult, utcnow


class Repo:
    def __init__(self, db_path: str | Path):
        if str(db_path) != ":memory:":
            Path(db_path).parent.mkdir(parents=True, exist_ok=True)
        url = "sqlite://" if str(db_path) == ":memory:" else f"sqlite:///{db_path}"
        self.engine = create_engine(url, connect_args={"check_same_thread": False})
        SQLModel.metadata.create_all(self.engine)

    def session(self) -> Session:
        return Session(self.engine, expire_on_commit=False)

    # ---- ideas / runs ----
    def create_run(self, input_json: dict, parent_idea_id: int | None = None) -> Run:
        with self.session() as s:
            idea = Idea(title=input_json["idea"][:80], one_liner=input_json["idea"], parent_idea_id=parent_idea_id)
            s.add(idea)
            s.commit()
            run = Run(idea_id=idea.id, input_json=input_json)
            s.add(run)
            s.commit()
            return run

    def get_run(self, run_id: int) -> Optional[Run]:
        with self.session() as s:
            return s.get(Run, run_id)

    def list_runs(self) -> list[Run]:
        with self.session() as s:
            return list(s.exec(select(Run).order_by(Run.id.desc())))

    def update_run(self, run_id: int, **fields) -> Run:
        with self.session() as s:
            run = s.get(Run, run_id)
            for k, v in fields.items():
                setattr(run, k, v)
            s.add(run)
            s.commit()
            return run

    def finish_run(self, run_id: int, status: str, error: str | None = None) -> Run:
        return self.update_run(run_id, status=status, finished_at=utcnow(), error=error)

    def get_idea(self, idea_id: int) -> Optional[Idea]:
        with self.session() as s:
            return s.get(Idea, idea_id)

    def update_idea(self, idea_id: int, **fields) -> None:
        with self.session() as s:
            idea = s.get(Idea, idea_id)
            for k, v in fields.items():
                setattr(idea, k, v)
            s.add(idea)
            s.commit()

    def past_ideas(self, exclude_idea_id: int | None = None) -> list[Idea]:
        with self.session() as s:
            q = select(Idea)
            if exclude_idea_id is not None:
                q = q.where(Idea.id != exclude_idea_id)
            return list(s.exec(q))

    # ---- stage results ----
    def save_stage_result(self, **fields) -> StageResult:
        with self.session() as s:
            sr = StageResult(**fields)
            s.add(sr)
            s.commit()
            return sr

    def get_stage_result(self, run_id: int, stage: str, status: str = "done") -> Optional[StageResult]:
        with self.session() as s:
            q = (
                select(StageResult)
                .where(StageResult.run_id == run_id, StageResult.stage == stage, StageResult.status == status)
                .order_by(StageResult.id.desc())
            )
            return s.exec(q).first()

    def stage_results(self, run_id: int) -> list[StageResult]:
        with self.session() as s:
            return list(s.exec(select(StageResult).where(StageResult.run_id == run_id).order_by(StageResult.id)))

    # ---- costs ----
    def add_cost_event(self, **fields) -> CostEvent:
        with self.session() as s:
            ev = CostEvent(**fields)
            s.add(ev)
            run = s.get(Run, fields["run_id"])
            run.total_usd = (run.total_usd or 0.0) + fields.get("usd", 0.0)
            s.add(run)
            s.commit()
            return ev

    def cost_by_stage(self, run_id: int) -> dict[str, float]:
        with self.session() as s:
            rows = s.exec(
                select(CostEvent.stage, func.sum(CostEvent.usd)).where(CostEvent.run_id == run_id).group_by(CostEvent.stage)
            )
            return {stage: float(total or 0.0) for stage, total in rows}
