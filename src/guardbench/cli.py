"""Command line interface: `python -m guardbench <command>`.

    run       execute the tools on the suite and write predictions
    analyse   compute metric tables from the predictions of a run
    figures   draw the charts of a run into reports/figures
    report    build the PDF report from the committed results
    list      show the registered tools and their availability
"""

from __future__ import annotations

import argparse
import logging
import sys
from pathlib import Path

from guardbench import __version__


def _cmd_run(args: argparse.Namespace) -> int:
    from guardbench.adapters import CPU_DEFAULT
    from guardbench.runner import run

    tools = args.tools or CPU_DEFAULT
    status = run(tools, Path(args.results) / args.run, args.n_per_class, args.seed,
                 args.threads, args.workers)
    for name, st in status.items():
        print(f"{name:24s} {st['status']:8s} {st.get('reason', '')}")
    return 0


def _cmd_analyse(args: argparse.Namespace) -> int:
    from guardbench.analysis import analyse

    tables = analyse(Path(args.results) / args.run, n_boot=args.n_boot, seed=args.seed)
    cols = ["tool", "attack_macro_youden", "attack_macro_f1", "fr_benign_fpr",
            "lat_p50_ms", "lat_p95_ms"]
    print(tables["overall"][cols].to_string(index=False, float_format=lambda v: f"{v:.3f}"))
    return 0


def _cmd_figures(args: argparse.Namespace) -> int:
    from guardbench.report.figures import draw_all

    for path in draw_all(Path(args.results) / args.run, Path(args.out)):
        print(path)
    return 0


def _cmd_report(args: argparse.Namespace) -> int:
    from guardbench.report.build import build_pdf

    print(build_pdf(Path(args.out)))
    return 0


def _cmd_list(_: argparse.Namespace) -> int:
    from guardbench.adapters import REGISTRY, make

    for name in REGISTRY:
        ok, reason = make(name).available()
        print(f"{name:24s} {'available' if ok else 'unavailable':12s} {reason}")
    return 0


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(prog="guardbench", description=__doc__,
                                formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("--version", action="version", version=f"guardbench {__version__}")
    p.add_argument("--results", default="results", help="results root directory")
    p.add_argument("--run", default="cpu-baseline", help="run name (sub-directory of results)")
    p.add_argument("--seed", type=int, default=42)
    sub = p.add_subparsers(dest="command", required=True)

    r = sub.add_parser("run", help="run the benchmark")
    r.add_argument("--tools", nargs="*", help="tool names (default: every CPU tool)")
    r.add_argument("--n-per-class", type=int, default=100)
    r.add_argument("--threads", type=int, default=None, help="torch CPU threads")
    r.add_argument("--workers", type=int, default=1,
                   help="processes for pure-Python tools flagged parallel_ok (Rebuff)")
    r.set_defaults(func=_cmd_run)

    a = sub.add_parser("analyse", help="compute metrics for a run")
    a.add_argument("--n-boot", type=int, default=1000)
    a.set_defaults(func=_cmd_analyse)

    f = sub.add_parser("figures", help="draw charts for a run")
    f.add_argument("--out", default="reports/figures")
    f.set_defaults(func=_cmd_figures)

    rep = sub.add_parser("report", help="build the PDF report")
    rep.add_argument("--out", default="reports")
    rep.set_defaults(func=_cmd_report)

    sub.add_parser("list", help="list tools").set_defaults(func=_cmd_list)
    return p


def main(argv: list[str] | None = None) -> int:
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
    args = build_parser().parse_args(argv)
    return args.func(args)


if __name__ == "__main__":
    sys.exit(main())
