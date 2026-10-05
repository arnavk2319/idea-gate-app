"""Wrapper around the Claude Agent SDK: one structured-output call, no tools, with cost logging.

Agents get read-only tools only (and in M1, none at all). The SDK backend is injectable so
tests run offline against recorded fixtures.
"""
from __future__ import annotations

import asyncio
import time
from dataclasses import dataclass, field
from typing import Any, Awaitable, Callable, Protocol, TypeVar

from pydantic import BaseModel

from ideagate.prompts import Prompt

T = TypeVar("T", bound=BaseModel)


class AgentError(RuntimeError):
    pass


@dataclass
class RawResult:
    """What a backend returns, independent of the SDK's message classes."""

    structured_output: Any
    text: str | None
    usd: float
    input_tokens: int
    output_tokens: int
    model: str
    messages: list[dict] = field(default_factory=list)


class Backend(Protocol):
    def __call__(
        self,
        *,
        prompt: str,
        model: str,
        schema: dict,
        tools: list[str],
        max_budget_usd: float | None,
        timeout_s: float,
    ) -> Awaitable[RawResult]: ...


@dataclass
class AgentResult:
    output: Any
    usd: float
    input_tokens: int
    output_tokens: int
    model: str
    duration_s: float
    prompt_version: str


async def sdk_backend(
    *,
    prompt: str,
    model: str,
    schema: dict,
    tools: list[str],
    max_budget_usd: float | None,
    timeout_s: float,
) -> RawResult:
    # Imported lazily so offline tests never need the SDK or an API key.
    from claude_agent_sdk import AssistantMessage, ClaudeAgentOptions, ResultMessage, TextBlock, query

    options = ClaudeAgentOptions(
        model=model,
        tools=tools,  # [] removes every built-in tool
        setting_sources=[],  # ignore user/project Claude Code settings, skills and CLAUDE.md
        output_format={"type": "json_schema", "schema": schema},
        max_budget_usd=max_budget_usd,
        permission_mode="dontAsk",
    )
    messages: list[dict] = []
    result: ResultMessage | None = None

    async def _drive() -> None:
        nonlocal result
        async for message in query(prompt=prompt, options=options):
            if isinstance(message, AssistantMessage):
                text = "".join(b.text for b in message.content if isinstance(b, TextBlock))
                messages.append({"role": "assistant", "model": message.model, "text": text})
            elif isinstance(message, ResultMessage):
                result = message

    await asyncio.wait_for(_drive(), timeout=timeout_s)
    if result is None:
        raise AgentError("agent finished without a result message")
    if result.is_error:
        raise AgentError(f"agent error ({result.subtype}): {'; '.join(result.errors or []) or result.result}")
    usage = result.usage or {}
    input_tokens = (
        usage.get("input_tokens", 0)
        + usage.get("cache_creation_input_tokens", 0)
        + usage.get("cache_read_input_tokens", 0)
    )
    return RawResult(
        structured_output=result.structured_output,
        text=result.result,
        usd=float(result.total_cost_usd or 0.0),
        input_tokens=input_tokens,
        output_tokens=usage.get("output_tokens", 0),
        model=next(iter(result.model_usage or {}), model),
        messages=messages,
    )


_backend: Backend = sdk_backend


def set_backend(backend: Backend) -> None:
    """Swap the SDK backend (tests, replay from recorded fixtures)."""
    global _backend
    _backend = backend


def get_backend() -> Backend:
    return _backend


def run_structured(
    ctx: "RunContext",  # noqa: F821  (defined in pipeline.context; avoids a circular import)
    *,
    agent: str,
    prompt: Prompt,
    values: dict[str, str],
    output_model: type[T],
    schema_model: type[BaseModel] | None = None,
    tier: str = "strong",
    tools: list[str] | None = None,
) -> tuple[T, AgentResult]:
    """Render a prompt, call the model once, validate the structured output, log cost and trace."""
    schema_cls = schema_model or output_model
    model = getattr(ctx.config.models, tier)
    rendered = prompt.render(**values)
    if ctx.note:
        rendered += f"\n\nHuman note for this run (from the reviewer; take it into account):\n{ctx.note}"

    start = time.monotonic()
    ctx.log("agent_start", agent=agent, model=model, prompt_version=prompt.version)
    raw = asyncio.run(
        get_backend()(
            prompt=rendered,
            model=model,
            schema=schema_cls.model_json_schema(),
            tools=tools or [],
            max_budget_usd=ctx.config.budgets.stage_usd_max,
            timeout_s=ctx.config.budgets.stage_timeout_s,
        )
    )
    duration = time.monotonic() - start

    ctx.record_cost(agent=agent, model=raw.model, input_tokens=raw.input_tokens, output_tokens=raw.output_tokens, usd=raw.usd)
    ctx.trace.append({"agent": agent, "prompt": rendered, "messages": raw.messages, "structured_output": raw.structured_output})
    ctx.log("agent_end", agent=agent, model=raw.model, usd=raw.usd, duration_s=round(duration, 2))

    if raw.structured_output is None:
        raise AgentError(f"{agent}: model returned no structured output")
    parsed = output_model.model_validate(raw.structured_output)
    return parsed, AgentResult(
        output=parsed,
        usd=raw.usd,
        input_tokens=raw.input_tokens,
        output_tokens=raw.output_tokens,
        model=raw.model,
        duration_s=duration,
        prompt_version=prompt.version,
    )
