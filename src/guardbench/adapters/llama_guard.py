"""Llama Guard 3, served by Ollama (CPU baseline) or by transformers (GPU run).

Llama Guard answers "safe" or "unsafe\\nS<k>" following the MLCommons hazard
taxonomy (S1 violent crimes ... S14 code interpreter abuse). The risk score is
the probability mass of the first generated token being "unsafe", normalised
against "safe", which makes ROC-AUC computable.
"""

from __future__ import annotations

import math
import os

import requests

from guardbench.adapters.base import Decision, Guardrail
from guardbench.types import Task

_CLAIMED = frozenset({Task.JAILBREAK, Task.TOXICITY})


def _unsafe_prob(lp_unsafe: float | None, lp_safe: float | None) -> float | None:
    if lp_unsafe is None and lp_safe is None:
        return None
    pu = math.exp(lp_unsafe) if lp_unsafe is not None else 0.0
    ps = math.exp(lp_safe) if lp_safe is not None else 0.0
    return pu / (pu + ps) if pu + ps else None


class LlamaGuardOllama(Guardrail):
    kind = "llm"
    claimed = _CLAIMED

    def __init__(self, model: str = "llama-guard3:1b", host: str | None = None) -> None:
        self.model = model
        self.name = "llama_guard3_1b" if model.endswith(":1b") else f"llama_guard_{model}"
        self.host = (host or os.getenv("OLLAMA_HOST", "http://127.0.0.1:11434")).rstrip("/")

    def available(self) -> tuple[bool, str]:
        try:
            tags = requests.get(f"{self.host}/api/tags", timeout=5).json()
        except (requests.RequestException, ValueError) as exc:
            return False, f"Ollama unreachable at {self.host} ({type(exc).__name__})"
        names = {m.get("name") for m in tags.get("models", [])}
        if self.model not in names:
            return False, f"Ollama model {self.model} not pulled (ollama pull {self.model})"
        return True, ""

    def _decide(self, text: str) -> Decision:
        resp = requests.post(
            f"{self.host}/api/chat",
            json={
                "model": self.model,
                "messages": [{"role": "user", "content": text}],
                "stream": False,
                "logprobs": True,
                "top_logprobs": 5,
                "options": {"temperature": 0, "num_predict": 8, "seed": 42},
            },
            timeout=300,
        )
        resp.raise_for_status()
        body = resp.json()
        answer = body["message"]["content"].strip()
        first = (body.get("logprobs") or [{}])[0].get("top_logprobs", [])
        lps = {t["token"].strip().lower(): t["logprob"] for t in first}
        score = _unsafe_prob(lps.get("unsafe"), lps.get("safe"))
        return Decision(answer.lower().startswith("unsafe"), score, answer.replace("\n", " "))


class LlamaGuardHF(Guardrail):
    """transformers backend for GPU runs (Colab). Gated: needs HF_TOKEN."""

    kind = "llm"
    claimed = _CLAIMED

    def __init__(self, model_id: str = "meta-llama/Llama-Guard-3-8B", load_4bit: bool = False):
        self.model_id = model_id
        self.load_4bit = load_4bit
        self.name = "llama_guard3_" + model_id.rsplit("-", 1)[-1].lower() + "_hf"
        self._tok = self._model = None

    def available(self) -> tuple[bool, str]:
        if not os.getenv("HF_TOKEN"):
            return False, f"{self.model_id} is gated; set HF_TOKEN"
        return True, ""

    def load(self) -> None:
        import torch
        from transformers import AutoModelForCausalLM, AutoTokenizer

        token = os.getenv("HF_TOKEN")
        self._tok = AutoTokenizer.from_pretrained(self.model_id, token=token)
        # fp16 on GPU: the Colab T4 has no native bfloat16. The 8B model does not
        # fit a 16 GB T4 in fp16, so it is loaded in 4-bit NF4 (bitsandbytes).
        extra = {}
        if self.load_4bit:
            from transformers import BitsAndBytesConfig

            extra["quantization_config"] = BitsAndBytesConfig(
                load_in_4bit=True, bnb_4bit_quant_type="nf4",
                bnb_4bit_compute_dtype=torch.float16,
            )
        dtype = torch.float16 if torch.cuda.is_available() else torch.float32
        self._model = AutoModelForCausalLM.from_pretrained(
            self.model_id, token=token, torch_dtype=dtype, device_map="auto", **extra
        )
        self._ids = {
            w: self._tok.encode(w, add_special_tokens=False)[0] for w in ("safe", "unsafe")
        }

    def _decide(self, text: str) -> Decision:
        import torch

        chat = [{"role": "user", "content": [{"type": "text", "text": text}]}]
        ids = self._tok.apply_chat_template(chat, return_tensors="pt").to(self._model.device)
        with torch.no_grad():
            out = self._model.generate(
                ids, max_new_tokens=8, do_sample=False, output_scores=True,
                return_dict_in_generate=True, pad_token_id=self._tok.eos_token_id,
            )
        logp = torch.log_softmax(out.scores[0][0].float(), dim=-1)
        score = _unsafe_prob(float(logp[self._ids["unsafe"]]), float(logp[self._ids["safe"]]))
        answer = self._tok.decode(out.sequences[0][ids.shape[-1]:], skip_special_tokens=True)
        return Decision(answer.strip().lower().startswith("unsafe"), score, answer.strip())
