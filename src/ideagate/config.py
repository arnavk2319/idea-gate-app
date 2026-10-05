"""Typed loader for ideagate.yaml. Secrets come from the environment (.env)."""
from __future__ import annotations

import os
from pathlib import Path
from typing import Literal

import yaml
from dotenv import load_dotenv
from pydantic import BaseModel, ConfigDict, field_validator, model_validator

RUBRIC_COLUMNS = (
    "moat",
    "competition",
    "proof_of_spending",
    "time_to_v1",
    "time_to_market",
    "projected_revenue",
    "amended_version",
)


class _Strict(BaseModel):
    model_config = ConfigDict(extra="forbid")


class ModelsConfig(_Strict):
    strong: str
    cheap: str

    @field_validator("strong", "cheap")
    @classmethod
    def _not_placeholder(cls, v: str) -> str:
        if not v.strip() or v.strip().startswith("<"):
            raise ValueError("set a real model id from the current Anthropic model list")
        return v


class BudgetsConfig(_Strict):
    run_usd_max: float
    stage_usd_max: float
    stage_timeout_s: int


class RubricConfig(_Strict):
    weights: dict[str, float]
    pursue_min_score: float
    kill_max_score: float
    min_spend_verdict_for_pursue: Literal["weak", "moderate", "strong"]

    @model_validator(mode="after")
    def _check(self) -> RubricConfig:
        missing = set(RUBRIC_COLUMNS) - set(self.weights)
        extra = set(self.weights) - set(RUBRIC_COLUMNS)
        if missing or extra:
            raise ValueError(f"rubric.weights keys mismatch (missing={sorted(missing)}, extra={sorted(extra)})")
        if self.kill_max_score >= self.pursue_min_score:
            raise ValueError("kill_max_score must be below pursue_min_score")
        return self


class CommitmentTargets(_Strict):
    high_paying: int
    medium_paying: int


class PlanningConfig(_Strict):
    weekly_hours: int
    sprint_weeks: int
    commitment_targets: CommitmentTargets


class SearchConfig(_Strict):
    provider: Literal["exa", "tavily"]
    cache_ttl_days: int


class SourcesConfig(_Strict):
    blocklist: list[str] = []
    per_domain_rps: float


class PathsConfig(_Strict):
    db: str
    reports_dir: str


class DuplicatesConfig(_Strict):
    similarity_threshold: float


class Config(_Strict):
    models: ModelsConfig
    budgets: BudgetsConfig
    rubric: RubricConfig
    planning: PlanningConfig
    search: SearchConfig
    sources: SourcesConfig
    paths: PathsConfig
    duplicates: DuplicatesConfig

    # Resolved at load time (not part of the YAML).
    base_dir: Path = Path(".")

    @property
    def db_path(self) -> Path:
        return (self.base_dir / self.paths.db).resolve()

    @property
    def reports_dir(self) -> Path:
        return (self.base_dir / self.paths.reports_dir).resolve()


class ConfigError(RuntimeError):
    pass


def find_config_path(explicit: str | os.PathLike | None = None) -> Path:
    candidate = explicit or os.environ.get("IDEAGATE_CONFIG") or "ideagate.yaml"
    path = Path(candidate)
    if not path.exists():
        raise ConfigError(f"Config not found at {path}. Copy ideagate.yaml.example to ideagate.yaml and edit it.")
    return path


def load_config(explicit: str | os.PathLike | None = None) -> Config:
    path = find_config_path(explicit)
    load_dotenv(path.parent / ".env", override=False)
    raw = yaml.safe_load(path.read_text()) or {}
    try:
        cfg = Config.model_validate(raw)
    except Exception as exc:  # pydantic.ValidationError -> friendlier message
        raise ConfigError(f"Invalid config {path}:\n{exc}") from exc
    return cfg.model_copy(update={"base_dir": path.resolve().parent})
