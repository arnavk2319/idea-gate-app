"""Stage 0: raw idea -> IdeaBrief, plus near-duplicate flags against past ideas."""
from __future__ import annotations

from difflib import SequenceMatcher

from ideagate.agents.runner import run_structured
from ideagate.pipeline.context import RunContext
from ideagate.prompts import load_prompt
from ideagate.schemas.brief import DuplicateFlag, IdeaBrief, IdeaBriefCore, IdeaInput

STAGE = "normalizer"


def _similarity(a: str, b: str) -> float:
    return SequenceMatcher(None, a.lower(), b.lower()).ratio()


def find_duplicates(ctx: RunContext, one_liner: str) -> list[DuplicateFlag]:
    """M1 uses plain text similarity; embedding-based detection arrives in M5."""
    threshold = ctx.config.duplicates.similarity_threshold
    flags = []
    for past in ctx.repo.past_ideas(exclude_idea_id=ctx.idea_id):
        score = _similarity(one_liner, past.one_liner)
        if score >= threshold:
            flags.append(DuplicateFlag(idea_id=past.id, title=past.title, one_liner=past.one_liner, similarity=round(score, 3)))
    return sorted(flags, key=lambda f: -f.similarity)


def run(input: IdeaInput, ctx: RunContext) -> IdeaBrief:
    prompt = load_prompt(STAGE)
    ctx.prompt_version = prompt.version
    notes_block = f"Notes from the user:\n{input.notes}" if input.notes else ""
    core, _ = run_structured(
        ctx,
        agent=STAGE,
        prompt=prompt,
        values={"idea": input.idea, "notes_block": notes_block},
        output_model=IdeaBriefCore,
        tier="strong",
    )
    return IdeaBrief(**core.model_dump(), possible_duplicates=find_duplicates(ctx, core.one_liner))
