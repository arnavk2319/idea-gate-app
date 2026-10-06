"""Seven tables. Stage outputs are stored as validated JSON so schemas can evolve without migrations."""

from __future__ import annotations

from datetime import UTC, datetime

from sqlalchemy import JSON, Column
from sqlmodel import Field, SQLModel


def utcnow() -> datetime:
    return datetime.now(UTC)


class Idea(SQLModel, table=True):
    id: int | None = Field(default=None, primary_key=True)
    title: str
    one_liner: str
    embedding: list[float] | None = Field(default=None, sa_column=Column(JSON))  # filled in M5
    created_at: datetime = Field(default_factory=utcnow)
    parent_idea_id: int | None = Field(default=None, foreign_key="idea.id")


class Run(SQLModel, table=True):
    id: int | None = Field(default=None, primary_key=True)
    idea_id: int | None = Field(default=None, foreign_key="idea.id")
    # running, at_gate, killed, pursued, failed, budget_stopped
    status: str = "running"
    current_stage: str | None = None
    total_usd: float = 0.0
    started_at: datetime = Field(default_factory=utcnow)
    finished_at: datetime | None = None
    # Not in the plan's field list: the raw user input, needed to resume/re-run from stored inputs.
    input_json: dict = Field(default_factory=dict, sa_column=Column(JSON))
    error: str | None = None


class StageResult(SQLModel, table=True):
    id: int | None = Field(default=None, primary_key=True)
    run_id: int = Field(foreign_key="run.id", index=True)
    stage: str = Field(index=True)
    status: str  # done, failed
    output_json: dict | None = Field(default=None, sa_column=Column(JSON))
    prompt_version: str | None = None
    model: str | None = None
    usd: float = 0.0
    duration_s: float = 0.0
    human_note: str | None = None
    # Not in the plan's field list: prompts, raw tool results and the stage input, so any stage can be re-run.
    input_json: dict | None = Field(default=None, sa_column=Column(JSON))
    trace_json: list | None = Field(default=None, sa_column=Column(JSON))
    created_at: datetime = Field(default_factory=utcnow)


class Evidence(SQLModel, table=True):
    id: int | None = Field(default=None, primary_key=True)
    url: str
    normalized_url: str = Field(index=True)
    title: str
    excerpt: str
    source_type: str
    retrieved_at: datetime = Field(default_factory=utcnow)
    verification: str = "unverified"


class FindingEvidence(SQLModel, table=True):
    id: int | None = Field(default=None, primary_key=True)
    finding_id: str = Field(index=True)
    evidence_id: int = Field(foreign_key="evidence.id")
    stage_result_id: int = Field(foreign_key="stageresult.id")


class CostEvent(SQLModel, table=True):
    id: int | None = Field(default=None, primary_key=True)
    run_id: int = Field(foreign_key="run.id", index=True)
    stage: str
    agent: str
    model: str
    input_tokens: int = 0
    output_tokens: int = 0
    usd: float = 0.0
    at: datetime = Field(default_factory=utcnow)


class Decision(SQLModel, table=True):
    id: int | None = Field(default=None, primary_key=True)
    run_id: int = Field(foreign_key="run.id", index=True)
    model_decision: str
    human_decision: str | None = None
    override_reason: str | None = None
    at: datetime = Field(default_factory=utcnow)
