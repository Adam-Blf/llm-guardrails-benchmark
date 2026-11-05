"""Pinned public data sources and a polite, cached downloader.

Every source is pinned to an immutable revision (Hub commit sha or Git commit)
so a rerun reads exactly the same bytes. Files are cached under data/cache and
downloaded once; nothing is fetched again if the cache is warm.
"""

from __future__ import annotations

import time
from dataclasses import dataclass
from pathlib import Path

import requests

CACHE_DIR = Path("data/cache")
_POLITE_DELAY_S = 1.0


@dataclass(frozen=True)
class HubFile:
    repo_id: str
    filename: str
    revision: str
    licence: str


@dataclass(frozen=True)
class GitFile:
    repo: str
    path: str
    commit: str
    licence: str

    @property
    def url(self) -> str:
        return f"https://raw.githubusercontent.com/{self.repo}/{self.commit}/{self.path}"


DEEPSET_TEST = HubFile(
    "deepset/prompt-injections",
    "data/test-00000-of-00001-701d16158af87368.parquet",
    "4f61ecb038e9c3fb77e21034b22511b523772cdd",
    "Apache-2.0",
)
SAFEGUARD_TEST = HubFile(
    "xTRam1/safe-guard-prompt-injection",
    "data/test-00000-of-00001.parquet",
    "a3a877d608f37b7d20d9945671902df895ecdb46",
    "unspecified",
)
JAILBREAK_TEST = HubFile(
    "jackhhao/jailbreak-classification",
    "balanced/jailbreak_dataset_test_balanced.csv",
    "2f2ceeb39658696fd3f462403562b6eea5306287",
    "Apache-2.0",
)
TOXICCHAT_TEST = HubFile(
    "lmsys/toxic-chat",
    "data/0124/toxic-chat_annotation_test.csv",
    "29df8e4dba60e1f4af4b4075c0705c5b313548a8",
    "CC-BY-NC-4.0",
)
PII_EN = HubFile(
    "ai4privacy/pii-masking-300k",
    "data/validation/1english_openpii_8k.jsonl",
    "c8c77895a005822682b66ab547fc0422579bc1d3",
    "ai4privacy licence (academic use)",
)
PII_FR = HubFile(
    "ai4privacy/pii-masking-300k",
    "data/validation/french_openpii_8k.jsonl",
    "c8c77895a005822682b66ab547fc0422579bc1d3",
    "ai4privacy licence (academic use)",
)
ALPACA_EN = HubFile(
    "tatsu-lab/alpaca",
    "data/train-00000-of-00001-a09b74b3ef9c3b56.parquet",
    "dce01c9b08f87459cf36a430d809084718273017",
    "CC-BY-NC-4.0",
)
ALPACA_FR = HubFile(
    "jpacifico/French-Alpaca-dataset-Instruct-110K",
    "Acquiesce_data_110k_instructions.json",
    "e153ef14ea6837d3b07a802bc15113a14f8f71eb",
    "Apache-2.0",
)

_BIPIA = "a004b69ec0dd446e0afd461d98cb5e96e120a5d0"
_INJECAGENT = "f19c9f2c79a41046eb13c03c51a24c567a8ffa07"
BIPIA_EMAIL = GitFile("microsoft/BIPIA", "benchmark/email/test.jsonl", _BIPIA, "MIT")
BIPIA_ATTACKS = GitFile("microsoft/BIPIA", "benchmark/text_attack_test.json", _BIPIA, "MIT")
INJECAGENT_USER = GitFile("uiuc-kang-lab/InjecAgent", "data/user_cases.jsonl", _INJECAGENT, "MIT")
INJECAGENT_CASES = {
    variant: GitFile(
        "uiuc-kang-lab/InjecAgent", f"data/test_cases_{variant}.json", _INJECAGENT, "MIT"
    )
    for variant in ("dh_base", "dh_enhanced", "ds_base", "ds_enhanced")
}


def fetch(source: HubFile | GitFile, cache_dir: Path = CACHE_DIR) -> Path:
    """Return a local path for the source, downloading it once if needed."""
    if isinstance(source, HubFile):
        from huggingface_hub import hf_hub_download

        return Path(
            hf_hub_download(
                repo_id=source.repo_id,
                filename=source.filename,
                revision=source.revision,
                repo_type="dataset",
                cache_dir=str(cache_dir / "hub"),
            )
        )
    target = cache_dir / "git" / source.repo.replace("/", "__") / source.commit / source.path
    if not target.exists():
        target.parent.mkdir(parents=True, exist_ok=True)
        resp = requests.get(source.url, timeout=60)
        resp.raise_for_status()
        target.write_bytes(resp.content)
        time.sleep(_POLITE_DELAY_S)
    return target


def manifest() -> list[dict[str, str]]:
    """Provenance table written next to the results."""
    rows = []
    for src in [
        DEEPSET_TEST,
        SAFEGUARD_TEST,
        JAILBREAK_TEST,
        TOXICCHAT_TEST,
        PII_EN,
        PII_FR,
        ALPACA_EN,
        ALPACA_FR,
        BIPIA_EMAIL,
        BIPIA_ATTACKS,
        INJECAGENT_USER,
        *INJECAGENT_CASES.values(),
    ]:
        if isinstance(src, HubFile):
            rows.append(
                {"source": f"hf:{src.repo_id}/{src.filename}", "revision": src.revision,
                 "licence": src.licence}
            )
        else:
            rows.append(
                {"source": f"github:{src.repo}/{src.path}", "revision": src.commit,
                 "licence": src.licence}
            )
    return rows
