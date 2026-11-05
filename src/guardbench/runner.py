"""Benchmark execution: every tool on every sample, predictions written as they come.

Predictions are appended to results/<run>/predictions/<tool>.csv in small
batches, so an interrupted run loses at most one batch and resumes where it
stopped (rows already present are skipped).
"""

from __future__ import annotations

import csv
import json
import logging
import os
import platform
import time
from pathlib import Path

from guardbench import __version__
from guardbench.adapters import Guardrail, make
from guardbench.data import build_suite, sources
from guardbench.types import Sample

log = logging.getLogger("guardbench")

PRED_FIELDS = ["uid", "task", "source", "lang", "label", "flagged", "score", "latency_ms",
               "error", "detail"]
_FLUSH_EVERY = 25
_WARMUP = 3


def environment(threads: int) -> dict:
    env = {
        "guardbench": __version__,
        "python": platform.python_version(),
        "platform": platform.platform(),
        "processor": platform.processor() or platform.machine(),
        "cpu_count": os.cpu_count(),
        "torch_threads": threads,
        "device": "cpu",
    }
    try:
        import torch

        env["torch"] = torch.__version__
        if torch.cuda.is_available():
            env["device"] = "cuda"
            env["gpu"] = torch.cuda.get_device_name(0)
    except ImportError:
        env["torch"] = None
    return env


def _done_uids(path: Path) -> set[str]:
    if not path.exists():
        return set()
    with path.open(encoding="utf-8", newline="") as fh:
        return {row["uid"] for row in csv.DictReader(fh)}


def _row(sample: Sample, verdict) -> dict:
    return {
        "uid": sample.uid,
        "task": sample.task.value,
        "source": sample.source,
        "lang": sample.lang,
        "label": sample.label,
        "flagged": int(verdict.flagged),
        "score": "" if verdict.score is None else f"{verdict.score:.6f}",
        "latency_ms": f"{verdict.latency_ms:.3f}",
        "error": verdict.error or "",
        "detail": verdict.detail,
    }


_WORKER_TOOL: Guardrail | None = None


def _init_worker(name: str) -> None:
    global _WORKER_TOOL
    _WORKER_TOOL = make(name)
    _WORKER_TOOL.load()


def _worker_predict(text: str):
    return _WORKER_TOOL.predict(text)


def _verdicts(tool: Guardrail, todo: list[Sample], workers: int):
    """Yield verdicts in suite order, in parallel processes when the tool allows it."""
    if workers > 1 and tool.parallel_ok:
        import multiprocessing as mp

        with mp.get_context("spawn").Pool(workers, _init_worker, (tool.name,)) as pool:
            yield from pool.imap(_worker_predict, [s.text for s in todo], chunksize=2)
    else:
        for sample in todo:
            yield tool.predict(sample.text)


def run_tool(tool: Guardrail, suite: list[Sample], pred_path: Path, workers: int = 1) -> dict:
    """Run one tool over the suite. Returns its status record."""
    ok, reason = tool.available()
    if not ok:
        log.warning("skip %s: %s", tool.name, reason)
        return {"status": "skipped", "reason": reason}
    t0 = time.perf_counter()
    try:
        tool.load()
    except Exception as exc:
        log.exception("load failed for %s", tool.name)
        return {"status": "failed", "reason": f"load: {type(exc).__name__}: {exc}"[:400]}
    load_s = time.perf_counter() - t0
    for sample in suite[:_WARMUP]:  # first calls pay lazy init; keep them out of latency
        tool.predict(sample.text)
    done = _done_uids(pred_path)
    todo = [s for s in suite if s.uid not in done]
    pred_path.parent.mkdir(parents=True, exist_ok=True)
    new_file = not pred_path.exists()
    errors = 0
    with pred_path.open("a", encoding="utf-8", newline="") as fh:
        writer = csv.DictWriter(fh, fieldnames=PRED_FIELDS)
        if new_file:
            writer.writeheader()
        for i, (sample, verdict) in enumerate(
            zip(todo, _verdicts(tool, todo, workers), strict=True), start=1
        ):
            errors += verdict.error is not None
            writer.writerow(_row(sample, verdict))
            if i % _FLUSH_EVERY == 0:
                fh.flush()
                log.info("%s %d/%d", tool.name, i, len(todo))
    return {
        "status": "ok",
        "kind": tool.kind,
        "claimed": sorted(t.value for t in tool.claimed),
        "load_s": round(load_s, 2),
        "n_new": len(todo),
        "n_total": len(done) + len(todo),
        "errors_new": errors,
        "workers": workers if tool.parallel_ok else 1,
    }


def run(
    tools: list[str],
    run_dir: Path,
    n_per_class: int = 100,
    seed: int = 42,
    threads: int | None = None,
    workers: int = 1,
) -> dict:
    threads = threads or os.cpu_count() or 1
    try:
        import torch

        torch.manual_seed(seed)
        torch.set_num_threads(threads)
    except ImportError:
        pass
    os.environ.setdefault("HF_HUB_DISABLE_SYMLINKS_WARNING", "1")
    suite = build_suite(n_per_class, seed)
    run_dir.mkdir(parents=True, exist_ok=True)
    status_path = run_dir / "tools_status.json"
    status = json.loads(status_path.read_text(encoding="utf-8")) if status_path.exists() else {}
    for name in tools:
        log.info("=== %s", name)
        status[name] = run_tool(
            make(name), suite, run_dir / "predictions" / f"{name}.csv", workers
        )
        status_path.write_text(json.dumps(status, indent=2), encoding="utf-8")
    meta = {"n_per_class": n_per_class, "seed": seed, "n_samples": len(suite),
            "environment": environment(threads), "data": sources.manifest()}
    (run_dir / "run_meta.json").write_text(json.dumps(meta, indent=2), encoding="utf-8")
    return status
