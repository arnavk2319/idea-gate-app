from __future__ import annotations

import json
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from ideagate.config import Config
from ideagate.db.repo import Repo


@dataclass
class RunContext:
    """Everything a stage may touch. Stages never call other stages."""

    config: Config
    repo: Repo
    run_id: int
    idea_id: int | None = None
    stage: str = ""
    note: str | None = None  # human note from rerun-stage / the gate
    trace: list[dict] = field(default_factory=list)  # persisted with the stage result
    usd: float = 0.0
    prompt_version: str | None = None
    model: str | None = None

    @property
    def run_dir(self) -> Path:
        d = self.config.reports_dir / str(self.run_id)
        d.mkdir(parents=True, exist_ok=True)
        return d

    def log(self, event: str, **fields: Any) -> None:
        """Append one JSON line to reports/<run_id>/run.log.jsonl."""
        entry = {"ts": datetime.now(timezone.utc).isoformat(), "run_id": self.run_id, "stage": self.stage, "event": event, **fields}
        with (self.run_dir / "run.log.jsonl").open("a") as f:
            f.write(json.dumps(entry, default=str) + "\n")

    def record_cost(self, *, agent: str, model: str, input_tokens: int, output_tokens: int, usd: float) -> None:
        self.repo.add_cost_event(
            run_id=self.run_id, stage=self.stage, agent=agent, model=model,
            input_tokens=input_tokens, output_tokens=output_tokens, usd=usd,
        )
        self.usd += usd
        self.model = model
