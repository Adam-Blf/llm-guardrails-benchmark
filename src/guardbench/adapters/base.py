"""Common interface every guardrail adapter implements."""

from __future__ import annotations

import time
from abc import ABC, abstractmethod
from dataclasses import dataclass

from guardbench.types import Task, Verdict


@dataclass(frozen=True)
class Decision:
    """Raw adapter answer before timing is attached."""

    flagged: bool
    score: float | None = None
    detail: str = ""


class Guardrail(ABC):
    """A guardrail scans one input text and decides whether to block it.

    Subclasses declare the risk families the vendor claims to cover (used for
    the coverage matrix), the deployment kind, and implement `load` and
    `_decide`. `available` must be cheap and never download anything: it lets
    the runner skip a tool with a documented reason (missing key, gated model,
    unreachable service) instead of crashing mid-run.
    """

    name: str = "abstract"
    kind: str = "classifier"  # classifier | llm | heuristic | api | ner
    claimed: frozenset[Task] = frozenset()
    # Pure-Python, single-threaded tools can be spread over worker processes:
    # per-call latency is still measured inside each worker on one core.
    parallel_ok: bool = False
    # Tools too slow for the full suite on a CPU run a seeded, stratified subset
    # of this many rows per (task, label) cell. None means the whole suite.
    max_per_class: int | None = None

    def available(self) -> tuple[bool, str]:
        return True, ""

    def load(self) -> None:  # noqa: B027 - optional hook, default is a no-op
        """Load models or clients. Called once before the first prediction."""

    def throttle(self) -> None:  # noqa: B027 - optional hook, default is a no-op
        """Rate limiting for remote APIs. Runs before the timer starts."""

    @abstractmethod
    def _decide(self, text: str) -> Decision:
        """Return the guardrail decision for one text."""

    def predict(self, text: str) -> Verdict:
        self.throttle()
        start = time.perf_counter()
        try:
            d = self._decide(text)
        except Exception as exc:  # one bad input must not stop a 1 000-row run
            elapsed = (time.perf_counter() - start) * 1000
            return Verdict(False, None, elapsed, error=f"{type(exc).__name__}: {exc}"[:300])
        elapsed = (time.perf_counter() - start) * 1000
        score = None if d.score is None else float(min(max(d.score, 0.0), 1.0))
        return Verdict(bool(d.flagged), score, elapsed, detail=d.detail[:200])
