"""Transparent keyword and pattern baseline (EN + FR).

This is the floor every learned guardrail must beat. It mirrors what teams
often ship first: a deny-list of attack phrases plus PII and secret patterns.
"""

from __future__ import annotations

import re

from guardbench.adapters.base import Decision, Guardrail
from guardbench.types import Task

ATTACK_PATTERNS = [
    r"ignore (all |any |the )?(previous|prior|above|earlier) (instructions|prompts|rules)",
    r"disregard (all |any |the )?(previous|prior|above) ",
    r"forget (everything|all|your) (previous |prior )?(instructions|rules)",
    r"you are now (dan|in developer mode|unrestricted|free)",
    r"\bdo anything now\b",
    r"\bjailbreak(en|ed)?\b",
    r"developer mode",
    r"(reveal|print|show|repeat) (your|the) (system )?prompt",
    r"pretend (you are|to be) .{0,40}(no|without) (rules|restrictions|filters)",
    r"ignore[sz]? (toutes |les )?(les )?instructions (précédentes|ci-dessus)",
    r"oublie[sz]? (toutes )?(tes|vos|les) (instructions|règles)",
    r"vergiss (alle|alles)",
    r"ignoriere (alle|die) ",
    r"\bnew instructions?\s*:",
    r"\bimportant!!!",
]

PII_PATTERNS = {
    "email": r"[\w.+-]+@[\w-]+\.[\w.-]+",
    "phone": (
        r"\+\d{1,3}[\s.-]?\d{1,4}(?:[\s.-]?\d{2,4}){2,4}"  # international
        r"|\b0[1-9](?:[\s.]?\d{2}){4}\b"  # French national format
        r"|\(\d{3}\)\s?\d{3}-\d{4}|\b\d{3}[-.]\d{3}[-.]\d{4}\b"  # North American
    ),
    "card": r"\b(?:\d[ -]?){13,19}\b",
    "iban": r"\b[A-Z]{2}\d{2}(?:\s?[A-Z0-9]{4}){3,7}",
    "ssn_us": r"\b\d{3}-\d{2}-\d{4}\b",
    "nir_fr": r"\b[12]\s?\d{2}\s?\d{2}\s?\d{2}\s?\d{3}\s?\d{3}\s?\d{2}\b",
    "ipv4": r"\b(?:\d{1,3}\.){3}\d{1,3}\b",
}

SECRET_PATTERNS = {
    "aws_key": r"\bAKIA[0-9A-Z]{16}\b",
    "github_token": r"\bgh[pousr]_[A-Za-z0-9]{36}\b",
    "private_key": r"-----BEGIN [A-Z ]*PRIVATE KEY-----",
    "password_field": r"(?i)\b(password|mot de passe|passwd|pwd)\s*[:=]\s*\S{4,}",
}

TOXIC_WORDS = [
    "kill yourself", "fuck", "shit", "bitch", "nigger", "faggot", "retard", "whore",
    "cunt", "rape", "suicide", "bomb", "salope", "connard", "pute", "nique",
]


def _luhn_ok(digits: str) -> bool:
    nums = [int(c) for c in digits if c.isdigit()]
    if not 13 <= len(nums) <= 19:
        return False
    total = 0
    for i, n in enumerate(reversed(nums)):
        if i % 2 == 1:
            n = n * 2 - 9 if n * 2 > 9 else n * 2
        total += n
    return total % 10 == 0


class RegexBaseline(Guardrail):
    name = "regex_baseline"
    kind = "heuristic"
    claimed = frozenset(
        {Task.DIRECT_INJECTION, Task.JAILBREAK, Task.INDIRECT_INJECTION, Task.TOXICITY, Task.PII}
    )

    def __init__(self) -> None:
        flags = re.IGNORECASE
        self._attack = [re.compile(p, flags) for p in ATTACK_PATTERNS]
        self._pii = {k: re.compile(p) for k, p in PII_PATTERNS.items()}
        self._secret = {k: re.compile(p) for k, p in SECRET_PATTERNS.items()}
        self._toxic = re.compile(r"\b(" + "|".join(map(re.escape, TOXIC_WORDS)) + r")", flags)

    def hits(self, text: str) -> list[str]:
        found = [f"attack:{p.pattern[:20]}" for p in self._attack if p.search(text)]
        for name, pat in self._pii.items():
            for m in pat.finditer(text):
                value = m.group(0)
                if name == "card" and not _luhn_ok(value):
                    continue
                if name == "phone" and sum(c.isdigit() for c in value) < 9:
                    continue
                found.append(f"pii:{name}")
                break
        found += [f"secret:{n}" for n, p in self._secret.items() if p.search(text)]
        if self._toxic.search(text):
            found.append("toxic:lexicon")
        return found

    def _decide(self, text: str) -> Decision:
        hits = self.hits(text)
        return Decision(bool(hits), None, ",".join(hits))
