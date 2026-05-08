"""Entry point: python -m tars_vault."""
import argparse
import os
import sys

from .server import run_stdio


def main() -> int:
    parser = argparse.ArgumentParser(prog="tars_vault")
    parser.add_argument("--transport", default="stdio", choices=["stdio"])
    parser.add_argument(
        "--vault",
        default=os.environ.get("TARS_VAULT_PATH"),
        help="Absolute path to the TARS Markdown workspace (or set TARS_VAULT_PATH).",
    )
    args = parser.parse_args()
    return run_stdio(vault_path=args.vault)


if __name__ == "__main__":
    raise SystemExit(main())
