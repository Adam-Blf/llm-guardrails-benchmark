"""LLM Guard (protectai/llm-guard) input pipeline.

Four input scanners chained the way the project documents a gateway setup:
PromptInjection (DeBERTa v3 v2), Toxicity (RoBERTa), Secrets (detect-secrets
plugins) and Anonymize (Presidio + a DeBERTa PII model). The input is blocked
as soon as one scanner marks it invalid.
"""

from __future__ import annotations

from guardbench.adapters.base import Decision, Guardrail
from guardbench.types import Task


class LLMGuard(Guardrail):
    name = "llm_guard"
    kind = "classifier"
    claimed = frozenset(
        {
            Task.DIRECT_INJECTION,
            Task.JAILBREAK,
            Task.INDIRECT_INJECTION,
            Task.TOXICITY,
            Task.PII,
        }
    )

    def __init__(self) -> None:
        self._scanners = None
        self._scan = None

    def load(self) -> None:
        from llm_guard import scan_prompt
        from llm_guard.input_scanners import Anonymize, PromptInjection, Secrets, Toxicity
        from llm_guard.vault import Vault

        self._scanners = [
            PromptInjection(threshold=0.5),
            Toxicity(threshold=0.5),
            Secrets(),
            Anonymize(Vault(), threshold=0.5),
        ]
        self._scan = scan_prompt

    def _decide(self, text: str) -> Decision:
        _, valid, scores = self._scan(self._scanners, text)
        failed = sorted(name for name, ok in valid.items() if not ok)
        risk = max(scores.values(), default=0.0)
        return Decision(bool(failed), max(risk, 0.0), ",".join(failed))
