"""Shared paths for the recovery extension (extension/recovery/)."""
import sys
from pathlib import Path

REC = Path(__file__).resolve().parents[1]                # extension/recovery/
EXT = REC.parent
sys.path.insert(0, str(EXT / "scripts"))
sys.path.insert(0, str(EXT / "venue_mix" / "scripts"))
from ext_config import CLEAN, PILOT_RAW, RAW, UA  # noqa: E402

DATA = REC / "data"
RRAW = RAW / "recovery"
VM_DATA = EXT / "venue_mix" / "data"
for p in (DATA, RRAW):
    p.mkdir(parents=True, exist_ok=True)

GROUPS = {"a2534": range(25, 35), "a2029": range(20, 30), "a50p": range(50, 91)}   # 90 = 90+
DROP_LA = {"E09000001", "E06000053"}          # City of London, Isles of Scilly (as in the national extension)
