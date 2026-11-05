"""Loaders for the public labelled datasets (direct attacks, toxicity, PII, benign)."""

from __future__ import annotations

import json

import pandas as pd

from guardbench.data import sources
from guardbench.data.sampling import clip, stratified, take
from guardbench.types import Sample, Task


def _samples(df: pd.DataFrame, task: Task, source: str, lang: str = "en") -> list[Sample]:
    return [
        Sample(
            uid=f"{task}:{source}:{i}",
            text=clip(row.text),
            label=int(row.label),
            task=task,
            source=source,
            lang=getattr(row, "lang", lang),
        )
        for i, row in enumerate(df.itertuples(index=False))
    ]


def direct_injection(n_per_class: int, seed: int) -> list[Sample]:
    """deepset test split (all rows) completed with safe-guard test rows."""
    deepset = pd.read_parquet(sources.fetch(sources.DEEPSET_TEST))[["text", "label"]]
    deepset = stratified(deepset, "label", n_per_class, seed)
    out = _samples(deepset, Task.DIRECT_INJECTION, "deepset")
    counts = deepset["label"].value_counts().to_dict()
    safeguard = pd.read_parquet(sources.fetch(sources.SAFEGUARD_TEST))[["text", "label"]]
    for label in (0, 1):
        missing = n_per_class - counts.get(label, 0)
        if missing > 0:
            extra = take(safeguard[safeguard["label"] == label], missing, seed)
            out += [
                Sample(f"{s.uid}:{label}", s.text, s.label, s.task, s.source, s.lang)
                for s in _samples(extra, Task.DIRECT_INJECTION, "safeguard")
            ]
    return out


def jailbreak(n_per_class: int, seed: int) -> list[Sample]:
    df = pd.read_csv(sources.fetch(sources.JAILBREAK_TEST))
    df = pd.DataFrame({"text": df["prompt"], "label": (df["type"] == "jailbreak").astype(int)})
    return _samples(stratified(df, "label", n_per_class, seed), Task.JAILBREAK, "jackhhao")


def toxicity(n_per_class: int, seed: int) -> list[Sample]:
    df = pd.read_csv(sources.fetch(sources.TOXICCHAT_TEST))
    df = pd.DataFrame({"text": df["user_input"], "label": df["toxicity"].astype(int)})
    return _samples(stratified(df, "label", n_per_class, seed), Task.TOXICITY, "toxicchat")


def _alpaca_en() -> pd.DataFrame:
    df = pd.read_parquet(sources.fetch(sources.ALPACA_EN))
    text = (df["instruction"].str.strip() + " " + df["input"].fillna("").str.strip()).str.strip()
    return pd.DataFrame({"text": text, "label": 0, "lang": "en"})


def alpaca_fr_pool(seed: int) -> pd.DataFrame:
    """Shuffled French instructions; callers slice disjoint ranges from it."""
    with open(sources.fetch(sources.ALPACA_FR), encoding="utf-8") as fh:
        rows = json.load(fh)
    df = pd.DataFrame(rows)
    text = (df["instruction"].str.strip() + " " + df["input"].fillna("").str.strip()).str.strip()
    out = pd.DataFrame({"text": text, "label": 0, "lang": "fr"})
    out = out[out["text"].str.len().between(20, 1500)]
    return out.sample(frac=1.0, random_state=seed).reset_index(drop=True)


def _pii_positives(file: sources.HubFile, n: int, seed: int, lang: str) -> pd.DataFrame:
    df = pd.read_json(sources.fetch(file), lines=True)
    df = df[df["privacy_mask"].map(len) > 0]
    picked = take(df, n, seed)
    return pd.DataFrame({"text": picked["source_text"], "label": 1, "lang": lang})


def pii(n_per_class: int, seed: int) -> list[Sample]:
    """ai4privacy texts (EN 60 %, FR 40 %) vs Alpaca instructions without PII labels."""
    n_fr = int(n_per_class * 0.4)
    n_en = n_per_class - n_fr
    pos = pd.concat(
        [
            _pii_positives(sources.PII_EN, n_en, seed, "en"),
            _pii_positives(sources.PII_FR, n_fr, seed, "fr"),
        ]
    )
    neg_en = take(_alpaca_en(), n_en, seed)
    neg_fr = alpaca_fr_pool(seed).iloc[:n_fr]
    out = []
    for frame, src in ((pos, "ai4privacy"), (neg_en, "alpaca_en"), (neg_fr, "alpaca_fr")):
        out += _samples(frame.reset_index(drop=True), Task.PII, src)
    return out


def alpaca_en_texts(n: int, seed: int) -> list[str]:
    """Short benign English sentences, used as filler for clean agent tool outputs."""
    df = pd.read_parquet(sources.fetch(sources.ALPACA_EN))
    out = df["output"].astype(str).str.split(r"(?<=[.!?])\s", regex=True).str[0]
    out = out[out.str.len().between(40, 220)]
    return take(out.to_frame("text"), n, seed)["text"].tolist()
