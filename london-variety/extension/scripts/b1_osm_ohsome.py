"""B1b. OpenStreetMap snapshots (31 Dec 2019 and 31 Dec 2022) of hospitality and leisure amenities, from
the ohsome API v1 full-history database (https://api.ohsome.org/v1).

Endpoint: /elements/bbox. The v1 /elements/centroid and /elements/geometry endpoints return HTTP 403 on
29 Oct 2026 (v1 is being wound down, shutdown 30 Nov 2026; v2 needs an API key from a sign-up), while
/elements/bbox is still served openly. For a node the bbox is the point itself; for a way or relation the
point used is the centre of its bounding box (an approximation to the centroid). clipGeometry=false so
features crossing tile edges keep their full extent and can be de-duplicated by OSM id.

Tiles: 0.5 x 0.5 degree grid over England and Wales; tiles containing no E&W postcode (NSPL) are skipped.
One request per tile and snapshot (the two snapshots may run as two processes), 3 s pause, retries with backoff; tile files already on disk are skipped.
"""
import sys
import time

import numpy as np
import pandas as pd
import requests

from ext_config import RAW, UA

OUT = RAW / "ohsome"
BIG = __import__("pathlib").Path.home() / "research-data" / "london-variety-extension" / "clean"
API = "https://api.ohsome.org/v1/elements/bbox"
TIMES = ["2019-12-31", "2022-12-31"]
FILTER = ("(amenity in (restaurant,cafe,bar,pub,nightclub,cinema,theatre,arts_centre,fast_food) "
          "or leisure=fitness_centre) and (geometry:point or geometry:polygon)")
STEP = 0.5


def tiles():
    n = pd.read_parquet(BIG / "nspl_ew.parquet", columns=["lat", "long"])
    ix = np.floor(n.long / STEP).astype(int)
    iy = np.floor(n.lat / STEP).astype(int)
    t = pd.DataFrame({"ix": ix, "iy": iy}).drop_duplicates().sort_values(["iy", "ix"])
    return [(i * STEP, j * STEP, (i + 1) * STEP, (j + 1) * STEP) for i, j in zip(t.ix, t.iy)]


def fetch(bb, t, tries=6):
    data = {"bboxes": ",".join(f"{v:.2f}" for v in bb), "time": t, "filter": FILTER,
            "properties": "tags,metadata", "clipGeometry": "false"}
    for k in range(tries):
        try:
            r = requests.post(API, data=data, headers=UA, timeout=900)
            if r.status_code == 200:
                j = r.json()  # validates a complete response
                return r.content, len(j["features"])
            print(f"  HTTP {r.status_code} {bb} {t}: {r.text[:200]}")
        except (requests.RequestException, ValueError) as e:
            print(f"  error {e!r} {bb} {t}")
        time.sleep(10 * 2 ** k)
    raise RuntimeError(f"failed {bb} {t}")


def main():
    tl = tiles()
    print(f"{len(tl)} tiles x {len(TIMES)} snapshots")
    log = []
    times = sys.argv[1:] or TIMES  # optional: one snapshot per process (at most two concurrent requests)
    for t in times:
        d = OUT / t
        d.mkdir(parents=True, exist_ok=True)
        for bb in tl:
            f = d / f"tile_{bb[0]:+07.2f}_{bb[1]:+06.2f}.json"
            if f.exists() and f.stat().st_size > 0:
                continue
            t0 = time.time()
            content, nf = fetch(bb, t)
            tmp = f.with_suffix(".part")
            tmp.write_bytes(content)
            tmp.replace(f)
            log.append(dict(time=t, bbox=bb, features=nf, seconds=round(time.time() - t0, 1)))
            print(t, bb, nf, f"{time.time() - t0:.0f}s", flush=True)
            time.sleep(3)
    if log:
        pd.DataFrame(log).to_csv(OUT / "download_log.csv", index=False, mode="a",
                                 header=not (OUT / "download_log.csv").exists())


if __name__ == "__main__":
    main()
