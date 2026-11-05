"""GLiNER2-based guardrails (fastino): GLiGuard classifier and the PII extractor.

Both run as small bidirectional encoders in a single forward pass, which is the
whole point of the family: guardrail decisions without a generative model.
"""

from __future__ import annotations

from guardbench.adapters.base import Decision, Guardrail
from guardbench.types import Task

GUARD_MODEL = "fastino/gliguard-LLMGuardrails-300M"
PII_MODEL = "fastino/gliner2-privacy-filter-PII-multi"

_SCHEMA = {
    "prompt_safety": ["safe", "unsafe"],
    "jailbreak_detection": {
        "labels": ["prompt_injection", "jailbreak_attempt", "benign"],
        "multi_label": True,
        "cls_threshold": 0.4,
    },
}
_ATTACK_LABELS = {"prompt_injection", "jailbreak_attempt"}

# Subset of the 42 supported labels that matches a leakage policy: identity,
# contact, government and banking identifiers, credentials.
PII_LABELS = [
    "person", "email", "phone_number", "street_address", "date_of_birth",
    "national_id_number", "passport_number", "drivers_license_number", "tax_id",
    "iban", "card_number", "bank_account", "username", "ip_address", "password",
    "api_key",
]


def _load(model_id: str):
    from gliner2 import AutoExtractor

    from guardbench.adapters.hf_classifier import pick_device

    device = "cuda" if pick_device() == 0 else "cpu"
    return AutoExtractor.from_pretrained(model_id, map_location=device)


def gliguard_score(result: dict) -> tuple[bool, float, str]:
    """Combine the safety head and the jailbreak head into one decision."""
    safety = result.get("prompt_safety") or {}
    conf = float(safety.get("confidence", 0.0))
    p_unsafe = conf if safety.get("label") == "unsafe" else 1.0 - conf
    jb = result.get("jailbreak_detection") or []
    jb_hits = [x for x in jb if x.get("label") in _ATTACK_LABELS]
    p_attack = max((float(x.get("confidence", 0.0)) for x in jb_hits), default=0.0)
    flagged = p_unsafe >= 0.5 or p_attack >= 0.5
    labels = ",".join(x["label"] for x in jb_hits)
    return flagged, max(p_unsafe, p_attack), f"{safety.get('label', '?')}:{labels}"


class GliGuard(Guardrail):
    name = "gliner2_gliguard"
    kind = "classifier"
    claimed = frozenset(
        {Task.DIRECT_INJECTION, Task.JAILBREAK, Task.INDIRECT_INJECTION, Task.TOXICITY}
    )

    def __init__(self) -> None:
        self._model = None

    def load(self) -> None:
        self._model = _load(GUARD_MODEL)

    def _decide(self, text: str) -> Decision:
        result = self._model.classify_text(text, _SCHEMA, include_confidence=True)
        flagged, score, detail = gliguard_score(result)
        return Decision(flagged, score, detail)


class Gliner2PII(Guardrail):
    name = "gliner2_pii"
    kind = "ner"
    claimed = frozenset({Task.PII})

    def __init__(self, threshold: float = 0.5) -> None:
        self.threshold = threshold
        self._model = None

    def load(self) -> None:
        self._model = _load(PII_MODEL)

    def _decide(self, text: str) -> Decision:
        result = self._model.extract_entities(
            text, PII_LABELS, threshold=0.3, include_confidence=True
        )
        best, kinds = 0.0, set()
        for label, spans in (result.get("entities") or {}).items():
            for span in spans:
                c = float(span.get("confidence", 0.0))
                best = max(best, c)
                if c >= self.threshold:
                    kinds.add(label)
        return Decision(best >= self.threshold, best, ",".join(sorted(kinds)))
