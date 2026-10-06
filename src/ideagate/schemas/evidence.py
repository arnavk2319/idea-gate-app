"""Shared schemas: every research output is a list of Finding, every Finding cites Evidence."""

from __future__ import annotations

from datetime import UTC, datetime
from typing import Literal

from pydantic import BaseModel, Field, field_validator

SourceType = Literal[
    "review", "forum", "pricing_page", "job_post", "gig_listing", "ad_library", "news", "funding", "other"
]
Verification = Literal["unverified", "verified", "contradicted", "unreachable"]
Confidence = Literal["low", "medium", "high"]


def _now() -> datetime:
    return datetime.now(UTC)


class Evidence(BaseModel):
    url: str
    title: str
    excerpt: str
    source_type: SourceType
    retrieved_at: datetime = Field(default_factory=_now)
    verification: Verification = "unverified"

    @field_validator("excerpt")
    @classmethod
    def _short_excerpt(cls, v: str) -> str:
        if len(v.split()) >= 40:
            raise ValueError("excerpt must be under 40 words")
        return v


class Finding(BaseModel):
    claim: str
    evidence: list[Evidence] = Field(min_length=1)
    confidence: Confidence
    stage: str
