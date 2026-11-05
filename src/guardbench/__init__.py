"""guardbench: benchmark of guardrails for LLM and LLM agent security."""

from importlib.metadata import PackageNotFoundError, version

try:
    __version__ = version("guardbench")
except PackageNotFoundError:  # running from a source checkout without install
    __version__ = "0.0.0"
