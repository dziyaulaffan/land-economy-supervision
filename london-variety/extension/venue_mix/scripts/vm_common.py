"""Shared paths for the venue-mix extension (extension/venue_mix/)."""
import sys
from pathlib import Path

VM = Path(__file__).resolve().parents[1]                 # extension/venue_mix/
EXT_SCRIPTS = VM.parent / "scripts"
sys.path.insert(0, str(EXT_SCRIPTS))
from ext_config import CLEAN, RAW, UA  # noqa: E402

DATA = VM / "data"
VRAW = RAW / "venue_mix"
BIG = Path.home() / "research-data" / "london-variety-extension" / "clean"
LEG = RAW / "restrictions" / "legislation"
for p in (DATA, VRAW):
    p.mkdir(parents=True, exist_ok=True)

VENUES = ["pubs_bars", "restaurants_cafes", "takeaways", "cinemas", "theatres_concert", "gyms", "nightclubs"]
