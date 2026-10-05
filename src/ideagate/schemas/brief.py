from __future__ import annotations

from pydantic import BaseModel, Field


class IdeaInput(BaseModel):
    """What the user hands to `ideagate run`."""

    idea: str = Field(min_length=3)
    notes: str | None = None


class IdeaBriefCore(BaseModel):
    """The part of the brief the normalizer LLM writes (this is the output schema it must satisfy)."""

    title: str
    one_liner: str
    target_customer: str
    buyer: str | None = Field(default=None, description="Only if the buyer differs from the user.")
    job_to_be_done: str
    current_workaround: str
    riskiest_assumptions: list[str] = Field(min_length=3, max_length=5)
    search_keywords: list[str] = Field(min_length=1)
    adjacent_markets: list[str]
    geography: str


class DuplicateFlag(BaseModel):
    idea_id: int
    title: str
    one_liner: str
    similarity: float


class IdeaBrief(IdeaBriefCore):
    """Stage 0 output: the LLM brief plus duplicate flags added by code, not by the model."""

    possible_duplicates: list[DuplicateFlag] = []
