"""Indirect injection (BIPIA) and agent tool-abuse (InjecAgent) slices.

Both are built as paired designs: the positive and the negative come from the
same carrier (same e-mail, same tool-response template), so a detector cannot
win by recognising the carrier style; it has to notice the injected instruction.
"""

from __future__ import annotations

import json
import random

from guardbench.data import sources
from guardbench.data.public import alpaca_en_texts
from guardbench.data.sampling import clip
from guardbench.types import Sample, Task

_POSITIONS = ("start", "middle", "end")


def _insert(context: str, attack: str, position: str) -> str:
    if position == "start":
        return f"{attack}\n{context}"
    if position == "end":
        return f"{context}\n{attack}"
    lines = context.split("\n")
    cut = len(lines) // 2
    return "\n".join([*lines[:cut], attack, *lines[cut:]])


def indirect_injection(n_per_class: int, seed: int) -> list[Sample]:
    """BIPIA e-mail contexts, clean vs carrying one BIPIA text attack.

    The guardrail sees what a RAG or e-mail assistant would retrieve: the
    external content only, not the user question. Capped by the 50 test e-mails.
    """
    rng = random.Random(seed)
    with open(sources.fetch(sources.BIPIA_EMAIL), encoding="utf-8") as fh:
        emails = [json.loads(line)["context"] for line in fh if line.strip()]
    with open(sources.fetch(sources.BIPIA_ATTACKS), encoding="utf-8") as fh:
        attacks = [(cat, a) for cat, items in json.load(fh).items() for a in items]
    rng.shuffle(emails)
    emails = emails[:n_per_class]
    out = []
    for i, ctx in enumerate(emails):
        category, attack = rng.choice(attacks)
        position = rng.choice(_POSITIONS)
        out.append(
            Sample(f"indirect:bipia:clean:{i}", clip(ctx), 0, Task.INDIRECT_INJECTION,
                   "bipia_email", meta={"category": "clean"})
        )
        out.append(
            Sample(
                f"indirect:bipia:attack:{i}",
                clip(_insert(ctx, attack, position), 2400),
                1,
                Task.INDIRECT_INJECTION,
                "bipia_email",
                meta={"category": category, "position": position},
            )
        )
    return out


def agent_tool_abuse(n_per_class: int, seed: int) -> list[Sample]:
    """InjecAgent tool responses with an attacker instruction vs benign filler.

    Positives are split evenly over the four InjecAgent variants (direct harm or
    data stealing, base or enhanced attack). Negatives fill the same 17 tool
    response templates with benign third-party sentences from Alpaca outputs.
    """
    rng = random.Random(seed)
    per_variant = max(1, n_per_class // len(sources.INJECAGENT_CASES))
    out: list[Sample] = []
    for variant, src in sources.INJECAGENT_CASES.items():
        with open(sources.fetch(src), encoding="utf-8") as fh:
            cases = json.load(fh)
        for j, case in enumerate(rng.sample(cases, per_variant)):
            out.append(
                Sample(
                    f"agent:injecagent:{variant}:{j}",
                    # InjecAgent stores the response JSON-quoted; strip the outer quotes
                    # so positives and negatives share exactly the same surface format.
                    clip(case["Tool Response"].strip().strip('"')),
                    1,
                    Task.AGENT_TOOL_ABUSE,
                    f"injecagent_{variant}",
                    meta={"attack_type": case["Attack Type"], "tool": case["User Tool"]},
                )
            )
    with open(sources.fetch(sources.INJECAGENT_USER), encoding="utf-8") as fh:
        templates = [json.loads(line) for line in fh if line.strip()]
    fillers = alpaca_en_texts(len(out), seed)
    for k, filler in enumerate(fillers):
        tpl = templates[k % len(templates)]
        safe = filler.replace("'", " ")
        text = tpl["Tool Response Template"].replace("<Attacker Instruction>", safe)
        out.append(
            Sample(f"agent:injecagent:clean:{k}", clip(text), 0, Task.AGENT_TOOL_ABUSE,
                   "injecagent_clean", meta={"tool": tpl["User Tool"]})
        )
    return out
