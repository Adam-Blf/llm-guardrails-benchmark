"""Benchmark suite assembly: one labelled slice per risk family."""

from __future__ import annotations

from collections.abc import Callable

from guardbench.data.agentic import agent_tool_abuse, indirect_injection
from guardbench.data.benign_fr import benign_fr
from guardbench.data.public import direct_injection, jailbreak, pii, toxicity
from guardbench.types import Sample, Task

LOADERS: dict[Task, Callable[[int, int], list[Sample]]] = {
    Task.DIRECT_INJECTION: direct_injection,
    Task.JAILBREAK: jailbreak,
    Task.INDIRECT_INJECTION: indirect_injection,
    Task.AGENT_TOOL_ABUSE: agent_tool_abuse,
    Task.TOXICITY: toxicity,
    Task.PII: pii,
    Task.BENIGN_FR: benign_fr,
}


def build_suite(n_per_class: int, seed: int, tasks: list[Task] | None = None) -> list[Sample]:
    """All samples of the requested tasks, deterministic for (n_per_class, seed)."""
    suite: list[Sample] = []
    for task in tasks or list(LOADERS):
        suite.extend(LOADERS[task](n_per_class, seed))
    uids = [s.uid for s in suite]
    if len(uids) != len(set(uids)):
        raise ValueError("duplicate sample uid in suite")
    return suite
