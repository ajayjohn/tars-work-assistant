"""Thin wrapper around the obsidian-cli binary. Skeleton for Phase 1a."""
import os, subprocess


def binary() -> str:
    return os.environ.get("TARS_OBSIDIAN_CLI", "obsidian")


def run(args: list[str], *, timeout: float = 30.0) -> subprocess.CompletedProcess:
    """Invoke obsidian-cli with ``args`` and return the completed process."""
    return subprocess.run([binary(), *args], capture_output=True, text=True, timeout=timeout)
