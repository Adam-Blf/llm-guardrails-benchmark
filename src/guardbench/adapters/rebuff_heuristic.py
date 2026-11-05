"""Rebuff, heuristic layer only.

Rebuff (protectai/rebuff, archived) chains a keyword heuristic, a vector store
of past attacks (Pinecone) and an LLM judge (OpenAI). The hosted service is
gone and the two last layers need paid third-party accounts, so only the local
heuristic is benchmarked. It is loaded straight from the installed module file
because `import rebuff` pulls an obsolete LangChain stack (the package pins
langchain 0.1 and numpy < 2), which is installed with --no-deps.
"""

from __future__ import annotations

import importlib.util
from pathlib import Path

from guardbench.adapters.base import Decision, Guardrail
from guardbench.types import Task

MAX_HEURISTIC_SCORE = 0.75  # Rebuff SDK default: flagged when score > 0.75


def _load_heuristic():
    spec = importlib.util.find_spec("rebuff")
    if spec is None or not spec.submodule_search_locations:
        raise ImportError("rebuff is not installed (pip install --no-deps rebuff==0.1.1)")
    path = Path(next(iter(spec.submodule_search_locations))) / "detect_pi_heuristics.py"
    mod_spec = importlib.util.spec_from_file_location("rebuff_heuristics", path)
    module = importlib.util.module_from_spec(mod_spec)
    mod_spec.loader.exec_module(module)
    return module.detect_prompt_injection_using_heuristic_on_input


class RebuffHeuristic(Guardrail):
    name = "rebuff_heuristic"
    kind = "heuristic"
    parallel_ok = True
    claimed = frozenset({Task.DIRECT_INJECTION, Task.INDIRECT_INJECTION})

    def __init__(self) -> None:
        self._fn = None

    def available(self) -> tuple[bool, str]:
        if importlib.util.find_spec("rebuff") is None:
            return False, "rebuff not installed (pip install --no-deps rebuff==0.1.1)"
        return True, ""

    def load(self) -> None:
        self._fn = _load_heuristic()

    def _decide(self, text: str) -> Decision:
        score = float(self._fn(text))
        return Decision(score > MAX_HEURISTIC_SCORE, score)
