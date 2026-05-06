"""Entry point: python -m tars_vault."""
import argparse
import os
import re
import sys
from pathlib import Path

from .server import run_stdio


def _is_unexpanded_var(value: str) -> bool:
    return bool(re.search(r"\$\{[^}]+\}|\$[A-Za-z_][A-Za-z0-9_]*", value))


def main() -> int:
    parser = argparse.ArgumentParser(prog="tars_vault")
    parser.add_argument("--transport", default="stdio", choices=["stdio"])
    parser.add_argument(
        "--vault",
        default=os.environ.get("TARS_VAULT_PATH"),
        help="Absolute path to the TARS Markdown workspace (or set TARS_VAULT_PATH).",
    )
    args = parser.parse_args()
    vault = args.vault
    if vault and _is_unexpanded_var(vault):
        print(
            f"warning: TARS_VAULT_PATH was not expanded ({vault}); "
            f"defaulting to Claude working folder {Path.cwd()}",
            file=sys.stderr,
        )
        vault = str(Path.cwd())
    if not vault:
        print(
            f"warning: TARS_VAULT_PATH env or --vault not set; "
            f"defaulting to Claude working folder {Path.cwd()}",
            file=sys.stderr,
        )
        vault = str(Path.cwd())
    return run_stdio(vault_path=vault)


if __name__ == "__main__":
    raise SystemExit(main())
