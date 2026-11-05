"""Adapter registry. Heavy imports stay inside factories so `--help` and CI stay light."""

from __future__ import annotations

from collections.abc import Callable

from guardbench.adapters.base import Decision, Guardrail


def _regex() -> Guardrail:
    from guardbench.adapters.regex_baseline import RegexBaseline

    return RegexBaseline()


def _protectai() -> Guardrail:
    from guardbench.adapters.hf_classifier import protectai_deberta

    return protectai_deberta()


def _prompt_guard() -> Guardrail:
    from guardbench.adapters.hf_classifier import prompt_guard

    return prompt_guard()


def _gliguard() -> Guardrail:
    from guardbench.adapters.gliner2_guard import GliGuard

    return GliGuard()


def _gliner2_pii() -> Guardrail:
    from guardbench.adapters.gliner2_guard import Gliner2PII

    return Gliner2PII()


def _presidio() -> Guardrail:
    from guardbench.adapters.presidio_pii import PresidioPII

    return PresidioPII()


def _llm_guard() -> Guardrail:
    from guardbench.adapters.llm_guard_adapter import LLMGuard

    return LLMGuard()


def _llama_guard() -> Guardrail:
    from guardbench.adapters.llama_guard import LlamaGuardOllama

    return LlamaGuardOllama()


def _llama_guard_hf_1b() -> Guardrail:
    from guardbench.adapters.llama_guard import LlamaGuardHF

    return LlamaGuardHF("meta-llama/Llama-Guard-3-1B")


def _llama_guard_hf_8b() -> Guardrail:
    from guardbench.adapters.llama_guard import LlamaGuardHF

    return LlamaGuardHF("meta-llama/Llama-Guard-3-8B")


def _nemo() -> Guardrail:
    from guardbench.adapters.nemo import NemoSelfCheck

    return NemoSelfCheck()


def _rebuff() -> Guardrail:
    from guardbench.adapters.rebuff_heuristic import RebuffHeuristic

    return RebuffHeuristic()


def _lakera() -> Guardrail:
    from guardbench.adapters.lakera import LakeraGuard

    return LakeraGuard()


REGISTRY: dict[str, Callable[[], Guardrail]] = {
    "regex_baseline": _regex,
    "rebuff_heuristic": _rebuff,
    "protectai_deberta_v2": _protectai,
    "prompt_guard_86m": _prompt_guard,
    "gliner2_gliguard": _gliguard,
    "gliner2_pii": _gliner2_pii,
    "presidio": _presidio,
    "llm_guard": _llm_guard,
    "llama_guard3_1b": _llama_guard,
    "nemo_guardrails": _nemo,
    "lakera_guard": _lakera,
    "llama_guard3_1b_hf": _llama_guard_hf_1b,
    "llama_guard3_8b_hf": _llama_guard_hf_8b,
}

# Tools run by default on a CPU laptop. The *_hf Llama Guard variants are meant
# for the GPU notebook, where Ollama is not available.
CPU_DEFAULT = [n for n in REGISTRY if not n.endswith("_hf")]


def make(name: str) -> Guardrail:
    try:
        return REGISTRY[name]()
    except KeyError as exc:
        raise ValueError(f"unknown tool {name!r}; known: {', '.join(REGISTRY)}") from exc


__all__ = ["CPU_DEFAULT", "REGISTRY", "Decision", "Guardrail", "make"]
