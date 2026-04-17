"""Test fixtures for tars-vault. Fixture vault lives in tests/fixtures/fixture-vault/."""
import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

FIXTURE_VAULT = ROOT / "tests" / "fixtures" / "fixture-vault"
os.environ.setdefault("TARS_VAULT_PATH", str(FIXTURE_VAULT))
