"""Core value objects shared by loaders, adapters, runner and metrics."""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import StrEnum


class Task(StrEnum):
    """Risk families evaluated by the benchmark (one dataset slice each)."""

    DIRECT_INJECTION = "direct_injection"
    JAILBREAK = "jailbreak"
    INDIRECT_INJECTION = "indirect_injection"
    AGENT_TOOL_ABUSE = "agent_tool_abuse"
    TOXICITY = "toxicity"
    PII = "pii"
    BENIGN_FR = "benign_fr"


@dataclass(frozen=True)
class Sample:
    """One labelled input. label=1 means the guardrail SHOULD flag it."""

    uid: str
    text: str
    label: int
    task: Task
    source: str
    lang: str = "en"
    meta: dict = field(default_factory=dict, hash=False, compare=False)


@dataclass
class Verdict:
    """Output of one guardrail call on one input.

    score is a risk score in [0, 1] when the tool exposes one, else None.
    error is set when the call failed; such rows are excluded from metrics
    and counted separately so failures never look like decisions.
    """

    flagged: bool
    score: float | None
    latency_ms: float
    error: str | None = None
    detail: str = ""
