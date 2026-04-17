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
        help="Absolute path to the Obsidian vault (or set TARS_VAULT_PATH).",
    )
    args = parser.parse_args()
    if not args.vault:
        print("error: TARS_VAULT_PATH env or --vault required", file=sys.stderr)
        return 2
    return run_stdio(vault_path=args.vault)


if __name__ == "__main__":
    raise SystemExit(main())
