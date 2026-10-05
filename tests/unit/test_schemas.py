import pytest
from pydantic import ValidationError

from ideagate.schemas.brief import IdeaBriefCore
from ideagate.schemas.evidence import Evidence, Finding


def _ev(**kw):
    return dict(url="https://x.com", title="t", excerpt="short", source_type="review", **kw)


def test_finding_requires_evidence():
    with pytest.raises(ValidationError):
        Finding(claim="Market is $5B", evidence=[], confidence="high", stage="market")


def test_excerpt_limit():
    with pytest.raises(ValidationError):
        Evidence(**{**_ev(), "excerpt": " ".join(["w"] * 40)})


def test_assumptions_bounds():
    base = dict(title="t", one_liner="o", target_customer="c", job_to_be_done="j", current_workaround="w",
                search_keywords=["k"], adjacent_markets=[], geography="global")
    with pytest.raises(ValidationError):
        IdeaBriefCore(**base, riskiest_assumptions=["a", "b"])
    with pytest.raises(ValidationError):
        IdeaBriefCore(**base, riskiest_assumptions=list("abcdef"))
    assert IdeaBriefCore(**base, riskiest_assumptions=["a", "b", "c"])
