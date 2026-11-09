"""V2. Venue-mix treatment: variety-days lost, by 2021 MSOA (England and Wales) and by 2023 LAD.

Access to venue type v from MSOA m (B1 method, extension/scripts/b1_assign_access.py):
    A_mv(lambda) = sum_j 1[j is type v] exp(-d_mj / lambda),  d in km from the 2021 MSOA population-weighted
    centroid to each point, lambda = 1, 1.5 (main) and 3 km, sum truncated at 30 km.
Variety-days lost:
    VDL_m = 365 * sum_v A_mv s_l(m),v / sum_v A_mv
where s_l,v is the share of days venue type v was closed in local authority l over the window (V1 calendar).
VDL is a weighted mean of closure shares with weights equal to each type's share of total access, so it
depends on the mix of venues and not on their number (doubling every type leaves it unchanged).

Two access versions:
  fhrs (main): pubs and bars, restaurants and cafes, takeaways from the food hygiene register (FHRS);
               cinemas, theatres and arts centres, gyms, nightclubs from OpenStreetMap 2019 (FHRS has no such types).
               FHRS "Pub/bar/nightclub" includes nightclubs, so OSM nightclub access is subtracted from it
               (floored at zero) to avoid counting nightclubs twice.
  osm (check): every type from the OpenStreetMap snapshot of 31 Dec 2019.

Outputs (extension/venue_mix/data/):
  v2_access_msoa.csv       access by type, version and lambda
  v2_treatment_msoa.csv    VDL (main window, year to June 2021, reopening window) by version and lambda
  v2_treatment_lad.csv     LAD versions (Census-2021-population-weighted means of the MSOA measures)
  v2_validation_ukbc.csv   OSM 2019 nightclub and theatre counts against UK Business Counts 2019 by LAD
"""
import numpy as np
import pandas as pd

from vm_common import BIG, CLEAN, DATA, RAW, VENUES
from b1_assign_access import LAMBDAS, access

WINDOWS = ["main", "yr_jun2021", "reopen"]
CATS = ["fhrs_pub_bar_club", "fhrs_restaurant_cafe", "fhrs_takeaway", "osm_pub_bar", "osm_restaurant_cafe",
        "osm_fast_food", "osm_cinema", "osm_theatre_arts", "osm_fitness_centre", "osm_nightclub"]
OSM_MEMBERS = {"osm_pub_bar": ["pub", "bar"], "osm_restaurant_cafe": ["restaurant", "cafe"],
               "osm_fast_food": ["fast_food"], "osm_cinema": ["cinema"], "osm_theatre_arts": ["theatre", "arts_centre"],
               "osm_fitness_centre": ["fitness_centre"], "osm_nightclub": ["nightclub"]}


def build_access(m):
    f = pd.read_parquet(BIG / "fhrs_points_ew_assigned.parquet", columns=["category", "easting", "northing", "msoa21cd"])
    f = f[f.msoa21cd.notna()]
    o = pd.read_parquet(BIG / "osm_points_2019_assigned.parquet", columns=["osm_tag", "easting", "northing", "msoa21cd"])
    o = o[o.msoa21cd.notna()]
    wf = np.zeros((len(f), len(CATS)))
    for c in ["pub_bar_club", "restaurant_cafe", "takeaway"]:
        wf[:, CATS.index(f"fhrs_{c}")] = (f.category == c).values
    wo = np.zeros((len(o), len(CATS)))
    for k, mem in OSM_MEMBERS.items():
        wo[:, CATS.index(k)] = o.osm_tag.isin(mem).values
    A = access(m, np.concatenate([f.easting.values, o.easting.values]),
               np.concatenate([f.northing.values, o.northing.values]), np.vstack([wf, wo]))
    out = m[["msoa21cd", "lad23cd"]].copy()
    for lk in LAMBDAS:
        a = pd.DataFrame(A[lk], columns=CATS)
        ver = {
            "fhrs": {"pubs_bars": np.maximum(a.fhrs_pub_bar_club - a.osm_nightclub, 0),
                     "restaurants_cafes": a.fhrs_restaurant_cafe, "takeaways": a.fhrs_takeaway},
            "osm": {"pubs_bars": a.osm_pub_bar, "restaurants_cafes": a.osm_restaurant_cafe, "takeaways": a.osm_fast_food},
        }
        for v, d in ver.items():
            d.update({"cinemas": a.osm_cinema, "theatres_concert": a.osm_theatre_arts, "gyms": a.osm_fitness_centre,
                      "nightclubs": a.osm_nightclub})
            for t in VENUES:
                out[f"A_{v}_{lk}_{t}"] = d[t].values
    return out


def build_treatment(acc, sh):
    t = acc[["msoa21cd", "lad23cd"]].merge(sh, left_on="lad23cd", right_on="lad23_code", how="left")
    assert t[f"closed_main_{VENUES[0]}"].notna().all(), "LAD missing from closure shares"
    out = acc[["msoa21cd", "lad23cd"]].copy()
    for v in ["fhrs", "osm"]:
        for lk in LAMBDAS:
            Am = acc[[f"A_{v}_{lk}_{x}" for x in VENUES]].values
            tot = Am.sum(axis=1)
            out[f"total_access_{v}_{lk}"] = tot
            for w in WINDOWS:
                S = t[[f"closed_{w}_{x}" for x in VENUES]].values
                out[f"vdl_{w}_{v}_{lk}"] = np.where(tot > 0, 365 * (Am * S).sum(axis=1) / np.where(tot > 0, tot, 1), np.nan)
            sh_mix = Am / np.where(tot > 0, tot, 1)[:, None]
            for i, x in enumerate(VENUES):
                out[f"mix_{v}_{lk}_{x}"] = sh_mix[:, i]
    return out


def lad_versions(tr, m):
    x = tr.merge(m[["msoa21cd", "pop_census2021"]], on="msoa21cd")
    cols = [c for c in tr.columns if c.startswith(("vdl_", "total_access_", "mix_"))]
    rows = {}
    for la, g in x.groupby("lad23cd"):
        w = g.pop_census2021.values
        rows[la] = {c: np.nansum(g[c].values * w) / w[~np.isnan(g[c].values)].sum() for c in cols}
    out = pd.DataFrame.from_dict(rows, orient="index")
    out.index.name = "lad23cd"
    return out.reset_index()


def validate_ukbc():
    la = pd.read_csv(CLEAN / "la2023_amenity_counts_ew.csv")
    u = pd.read_csv(RAW / "nomis" / "ukbc_local_units_2019_subclasses_la2023.csv", dtype={"GEOGRAPHY_CODE": str})
    u["sic"] = u.INDUSTRY_NAME.str[:5]
    U = u.pivot_table(index="GEOGRAPHY_CODE", columns="sic", values="OBS_VALUE", aggfunc="sum")
    la = la.set_index("lad23cd").join(U, how="left")
    pairs = [("osm2019_nightclub", ["56301"], "nightclubs vs 56301 Licensed clubs"),
             ("osm2019_theatre", ["90040"], "theatres vs 90040 Operation of arts facilities"),
             ("osm2019_theatre", ["90010", "90040"], "theatres vs 90010+90040 Performing arts + arts facilities"),
             ("osm2019_arts_venue", ["90040"], "theatres+arts centres vs 90040"),
             ("osm2019_cinema", ["59140"], "cinemas vs 59140 Motion picture projection"),
             ("osm2019_fitness_centre", ["93130"], "fitness centres vs 93130 Fitness facilities")]
    rows = []
    for col, sics, lab in pairs:
        a = la[col].astype(float)
        b = la[sics].sum(axis=1).astype(float)
        pk = la.pop_census2021 / 1000
        ok = b.notna()
        a, b, pk = a[ok], b[ok], pk[ok]
        rows.append(dict(comparison=lab, n_la=int(ok.sum()), osm_total=int(a.sum()), ukbc_total=int(b.sum()),
                         ratio=round(a.sum() / b.sum(), 3), r_levels=round(a.corr(b), 3),
                         r_log1p=round(np.log1p(a).corr(np.log1p(b)), 3),
                         rho_spearman=round(a.corr(b, method="spearman"), 3),
                         r_per1k=round((a / pk).corr(b / pk), 3),
                         r_per1k_excl_city=round((a / pk).drop("E09000001", errors="ignore").corr(
                             (b / pk).drop("E09000001", errors="ignore")), 3),
                         share_la_zero_osm=round((a == 0).mean(), 3), share_la_zero_ukbc=round((b == 0).mean(), 3)))
    v = pd.DataFrame(rows)
    v.to_csv(DATA / "v2_validation_ukbc.csv", index=False)
    print(v.to_string(index=False))


def main():
    m = pd.read_csv(CLEAN / "msoa21_ew_lookup_pwc.csv")
    sh = pd.read_csv(DATA / "v1_closure_shares_lad23.csv")
    acc = build_access(m)
    acc.to_csv(DATA / "v2_access_msoa.csv", index=False)
    tr = build_treatment(acc, sh)
    tr.to_csv(DATA / "v2_treatment_msoa.csv", index=False)
    lad = lad_versions(tr, m)
    lad.to_csv(DATA / "v2_treatment_lad.csv", index=False)
    pd.set_option("display.width", 220)
    c = [f"vdl_main_{v}_{lk}" for v in ["fhrs", "osm"] for lk in LAMBDAS]
    print("MSOA VDL (days), main window\n", tr[c].describe().round(2).to_string())
    print("\ncorrelations of MSOA VDL versions\n", tr[c].corr().round(3).to_string())
    print("\nmean venue mix, fhrs l15\n", tr[[f"mix_fhrs_l15_{x}" for x in VENUES]].mean().round(4).to_string())
    print("\nLAD VDL, year to June 2021 and reopening (fhrs l15)\n",
          lad[["vdl_yr_jun2021_fhrs_l15", "vdl_reopen_fhrs_l15"]].describe().round(2).to_string())
    validate_ukbc()


if __name__ == "__main__":
    main()
