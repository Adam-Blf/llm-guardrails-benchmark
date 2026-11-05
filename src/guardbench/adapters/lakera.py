"""Lakera Guard (SaaS) adapter. Skipped cleanly when LAKERA_API_KEY is absent."""

from __future__ import annotations

import os
import time

import requests

from guardbench.adapters.base import Decision, Guardrail
from guardbench.types import Task

API_URL = "https://api.lakera.ai/v2/guard"
_MIN_INTERVAL_S = 0.5  # at most two calls per second, well under the published limits


class LakeraGuard(Guardrail):
    name = "lakera_guard"
    kind = "api"
    claimed = frozenset(
        {
            Task.DIRECT_INJECTION,
            Task.JAILBREAK,
            Task.INDIRECT_INJECTION,
            Task.AGENT_TOOL_ABUSE,
            Task.TOXICITY,
            Task.PII,
        }
    )

    def __init__(self) -> None:
        self._session: requests.Session | None = None
        self._last_call = 0.0

    def available(self) -> tuple[bool, str]:
        if not os.getenv("LAKERA_API_KEY"):
            return False, "LAKERA_API_KEY not set (commercial SaaS, no free key in this project)"
        return True, ""

    def load(self) -> None:
        self._session = requests.Session()
        self._session.headers["Authorization"] = f"Bearer {os.environ['LAKERA_API_KEY']}"

    def throttle(self) -> None:
        wait = _MIN_INTERVAL_S - (time.monotonic() - self._last_call)
        if wait > 0:
            time.sleep(wait)
        self._last_call = time.monotonic()

    def _decide(self, text: str) -> Decision:
        resp = self._session.post(
            API_URL,
            json={"messages": [{"role": "user", "content": text}], "breakdown": True},
            timeout=30,
        )
        resp.raise_for_status()
        body = resp.json()
        hits = [b.get("detector_type", "") for b in body.get("breakdown", []) if b.get("detected")]
        return Decision(bool(body.get("flagged")), None, ",".join(hits))
