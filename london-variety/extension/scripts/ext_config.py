"""Shared paths and helpers for the national extension (data assembly only, no regressions)."""
import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]                     # extension/
PROJECT = ROOT.parent                                          # london-variety/
# Raw downloads live outside OneDrive. Override with LONDON_VARIETY_EXT_RAW.
RAW = Path(os.environ.get("LONDON_VARIETY_EXT_RAW", Path.home() / "research-data" / "london-variety-extension" / "raw"))
# Raw files already downloaded by the London pilot (internal migration, PIPR, Google mobility, NSPL, Nomis).
PILOT_RAW = Path(os.environ.get("LONDON_VARIETY_RAW", Path.home() / "research-data" / "london-variety" / "raw"))
CLEAN = ROOT / "data" / "clean"
NOTES = ROOT / "notes"
for p in (RAW, CLEAN, NOTES):
    p.mkdir(parents=True, exist_ok=True)

sys.path.insert(0, str(PROJECT / "scripts"))
from config import UA, download  # noqa: E402  (reuse the pilot's download helper)
