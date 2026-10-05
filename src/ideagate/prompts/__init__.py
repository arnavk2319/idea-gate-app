"""Prompt loader. Prompts live as .md files with a version header; they are never inlined in Python."""
from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

import yaml

PROMPTS_DIR = Path(__file__).parent


@dataclass(frozen=True)
class Prompt:
    stage: str
    version: str
    output_schema: str
    body: str

    def render(self, **values: str) -> str:
        text = self.body
        for key, value in values.items():
            text = text.replace("{{" + key + "}}", value)
        return text


def load_prompt(name: str) -> Prompt:
    raw = (PROMPTS_DIR / f"{name}.md").read_text()
    if not raw.startswith("---\n"):
        raise ValueError(f"prompt {name} is missing its version header")
    _, header, body = raw.split("---\n", 2)
    meta = yaml.safe_load(header)
    for key in ("stage", "version", "output_schema"):
        if key not in meta:
            raise ValueError(f"prompt {name} header is missing '{key}'")
    return Prompt(stage=meta["stage"], version=str(meta["version"]), output_schema=meta["output_schema"], body=body.strip())
