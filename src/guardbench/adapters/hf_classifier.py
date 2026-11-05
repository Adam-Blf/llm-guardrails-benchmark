"""Hugging Face sequence classifiers used as prompt-injection guardrails."""

from __future__ import annotations

import os

from guardbench.adapters.base import Decision, Guardrail
from guardbench.types import Task

_ATTACKS = frozenset(
    {Task.DIRECT_INJECTION, Task.JAILBREAK, Task.INDIRECT_INJECTION, Task.AGENT_TOOL_ABUSE}
)


def pick_device() -> int:
    """GPU 0 when CUDA is present (Colab run), else CPU (-1)."""
    try:
        import torch

        return 0 if torch.cuda.is_available() else -1
    except ImportError:
        return -1


class HFClassifier(Guardrail):
    """Generic wrapper: score = sum of probabilities of the 'attack' labels."""

    kind = "classifier"
    claimed = _ATTACKS

    def __init__(
        self,
        name: str,
        model_id: str,
        positive_labels: tuple[str, ...],
        threshold: float = 0.5,
        gated: bool = False,
    ) -> None:
        self.name = name
        self.model_id = model_id
        self.positive = {lbl.upper() for lbl in positive_labels}
        self.threshold = threshold
        self.gated = gated
        self._pipe = None

    def available(self) -> tuple[bool, str]:
        if self.gated and not os.getenv("HF_TOKEN"):
            return False, (
                f"{self.model_id} is gated on the Hugging Face Hub (licence acceptance); "
                "set HF_TOKEN with an account that accepted it"
            )
        return True, ""

    def load(self) -> None:
        from transformers import pipeline

        self._pipe = pipeline(
            "text-classification",
            model=self.model_id,
            token=os.getenv("HF_TOKEN") or None,
            device=pick_device(),
            truncation=True,
            max_length=512,
            top_k=None,
        )

    def _decide(self, text: str) -> Decision:
        out = self._pipe(text)
        rows = out[0] if out and isinstance(out[0], list) else out
        score = sum(r["score"] for r in rows if r["label"].upper() in self.positive)
        return Decision(score >= self.threshold, score)


def protectai_deberta() -> HFClassifier:
    return HFClassifier(
        "protectai_deberta_v2", "protectai/deberta-v3-base-prompt-injection-v2", ("INJECTION",)
    )


def prompt_guard() -> HFClassifier:
    # Prompt-Guard-86M labels: BENIGN, INJECTION, JAILBREAK. Any non-benign mass counts.
    return HFClassifier(
        "prompt_guard_86m",
        "meta-llama/Prompt-Guard-86M",
        ("INJECTION", "JAILBREAK"),
        gated=True,
    )
