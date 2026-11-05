"""Microsoft Presidio analyzer as a PII leakage guardrail (EN + FR)."""

from __future__ import annotations

import re

from guardbench.adapters.base import Decision, Guardrail
from guardbench.types import Task

ENTITIES = [
    "PERSON",
    "EMAIL_ADDRESS",
    "PHONE_NUMBER",
    "CREDIT_CARD",
    "IBAN_CODE",
    "IP_ADDRESS",
    "US_SSN",
    "LOCATION",
]
_FR_WORDS = re.compile(
    r"\b(le|la|les|des|une|est|pour|avec|dans|vous|nous|sur|pas|que|qui)\b", re.IGNORECASE
)


def guess_lang(text: str) -> str:
    """Cheap EN/FR switch: Presidio needs a language, a gateway rarely knows it."""
    words = max(1, len(text.split()))
    return "fr" if len(_FR_WORDS.findall(text)) / words > 0.08 else "en"


class PresidioPII(Guardrail):
    name = "presidio"
    kind = "ner"
    claimed = frozenset({Task.PII})

    def __init__(self, threshold: float = 0.5) -> None:
        self.threshold = threshold
        self._engine = None

    def load(self) -> None:
        from presidio_analyzer import AnalyzerEngine, RecognizerRegistry
        from presidio_analyzer.nlp_engine import NlpEngineProvider
        from presidio_analyzer.predefined_recognizers import (
            CreditCardRecognizer,
            EmailRecognizer,
            IbanRecognizer,
            IpRecognizer,
            PhoneRecognizer,
        )

        provider = NlpEngineProvider(
            nlp_configuration={
                "nlp_engine_name": "spacy",
                "models": [
                    {"lang_code": "en", "model_name": "en_core_web_sm"},
                    {"lang_code": "fr", "model_name": "fr_core_news_sm"},
                ],
            }
        )
        registry = RecognizerRegistry(supported_languages=["en", "fr"])
        registry.load_predefined_recognizers(languages=["en"])
        # Pattern recognizers ship for English only; register French copies.
        for cls in (EmailRecognizer, PhoneRecognizer, CreditCardRecognizer, IbanRecognizer,
                    IpRecognizer):
            registry.add_recognizer(cls(supported_language="fr"))
        self._engine = AnalyzerEngine(
            nlp_engine=provider.create_engine(),
            registry=registry,
            supported_languages=["en", "fr"],
        )

    def _decide(self, text: str) -> Decision:
        lang = guess_lang(text)
        results = self._engine.analyze(text=text, language=lang, entities=ENTITIES)
        best = max((r.score for r in results), default=0.0)
        kinds = sorted({r.entity_type for r in results if r.score >= self.threshold})
        return Decision(best >= self.threshold, best, f"{lang}:{','.join(kinds)}")
