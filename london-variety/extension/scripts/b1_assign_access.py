"""B1c. Assign FHRS and OSM points to 2021 MSOAs and local authorities; build counts and access indices.

Geography
  MSOA: 2021 MSOA boundaries, BFE V8 (full extent of the realm, so coastal and riverside points fall inside),
        point-in-polygon in British National Grid. Points outside every polygon are snapped to the nearest
        MSOA if within 500 m; points further away are outside England and Wales (Scotland, sea) and dropped.
  LA:   MSOA -> LAD from NSPL Aug 2026 (every 2021 MSOA nests in one LAD). Reported on April 2023 LAD codes
        (Nomis TYPE424, as in the pilot): identical to 2026 codes except Barnsley E08000038 -> E08000016 and
        Sheffield E08000039 -> E08000019 (2024 code change after a small boundary change).
Access
  A_m(lambda) = sum_j units_j exp(-d_mj / lambda), lambda = 1, 1.5, 3 km, d in km from the 2021 MSOA
  population-weighted centroid (V2) of MSOA m.
  access_pt_*  : to the points themselves (exact coordinates), sum truncated at 30 km (weight < e^-10 at 3 km).
  access_pwc_* : pilot-style, each MSOA's units placed at its own population-weighted centroid (own units d=0).
"""
import glob
import json

import geopandas as gpd
import numpy as np
import pandas as pd
from pyproj import Transformer
from scipy.spatial import cKDTree

from ext_config import CLEAN, RAW

BIG = __import__("pathlib").Path.home() / "research-data" / "london-variety-extension" / "clean"
LAMBDAS = {"l10": 1.0, "l15": 1.5, "l30": 3.0}
CUTOFF_M = 30000
SNAP_M = 500
LAD26_TO_23 = {"E08000038": "E08000016", "E08000039": "E08000019"}
OSM_TYPES = ["restaurant", "cafe", "fast_food", "pub", "bar", "nightclub", "cinema", "theatre", "arts_centre",
             "fitness_centre"]
OSM_GROUPS = {"restaurant_cafe": ["restaurant", "cafe"], "pub_bar_club": ["pub", "bar", "nightclub"],
              "arts_venue": ["theatre", "arts_centre"]}
ACCESS_OSM = ["restaurant_cafe", "fast_food", "pub_bar_club", "cinema", "arts_venue", "fitness_centre"]
FHRS_CATS = ["restaurant_cafe", "pub_bar_club", "takeaway"]
TO_BNG = Transformer.from_crs(4326, 27700, always_xy=True)


def msoa_frames():
    pages = sorted(glob.glob(str(RAW / "ons_geography" / "msoa21_bfe_v8" / "page_*.geojson")))
    poly = pd.concat([gpd.read_file(p) for p in pages], ignore_index=True)
    poly = gpd.GeoDataFrame(poly, geometry="geometry", crs=27700)
    poly["geometry"] = poly.geometry.make_valid()
    poly = poly.rename(columns={"MSOA21CD": "msoa21cd", "MSOA21NM": "msoa21nm"})[["msoa21cd", "msoa21nm", "geometry"]]
    assert len(poly) == 7264 and poly.msoa21cd.is_unique
    pages = sorted(glob.glob(str(RAW / "ons_geography" / "msoa21_pwc_v2" / "page_*.geojson")))
    pwc = pd.concat([gpd.read_file(p) for p in pages], ignore_index=True)
    pwc = pd.DataFrame({"msoa21cd": pwc.MSOA21CD, "pwc_e": pwc.geometry.x, "pwc_n": pwc.geometry.y})
    assert len(pwc) == 7264 and set(pwc.msoa21cd) == set(poly.msoa21cd)
    n = pd.read_parquet(BIG / "nspl_ew.parquet", columns=["msoa21cd", "lad26cd"]).drop_duplicates()
    assert n.msoa21cd.is_unique
    n["lad23cd"] = n.lad26cd.replace(LAD26_TO_23)
    m = pwc.merge(n, on="msoa21cd", how="left").merge(poly[["msoa21cd", "msoa21nm"]], on="msoa21cd")
    assert m.lad23cd.notna().all()
    pop = pd.concat([pd.read_csv(f) for f in glob.glob(str(RAW / "nomis" / "census2021_ts001_msoa21_*.csv"))])
    m = m.merge(pop.rename(columns={"GEOGRAPHY_CODE": "msoa21cd", "OBS_VALUE": "pop_census2021"})[
        ["msoa21cd", "pop_census2021"]], on="msoa21cd", how="left")
    assert m.pop_census2021.notna().all()
    return poly, m


def assign(pts, poly):
    """pts: DataFrame with lat/long. Adds easting, northing, msoa21cd, assign_method."""
    pts = pts.reset_index(drop=True)
    e, n = TO_BNG.transform(pts["long"].values, pts["lat"].values)
    g = gpd.GeoDataFrame(pts.copy(), geometry=gpd.points_from_xy(e, n), crs=27700)
    g["easting"], g["northing"] = e, n
    j = gpd.sjoin(g, poly[["msoa21cd", "geometry"]], how="left", predicate="within")
    j = j[~j.index.duplicated()]  # a point on a shared edge: keep the first match
    j["assign_method"] = np.where(j.msoa21cd.notna(), "within", None)
    miss = j.msoa21cd.isna() & np.isfinite(j.easting)
    if miss.any():
        s = gpd.sjoin_nearest(j.loc[miss, ["geometry"]], poly[["msoa21cd", "geometry"]], how="left",
                              max_distance=SNAP_M, distance_col="snap_m")
        s = s[~s.index.duplicated()]
        ok = s.index[s.msoa21cd.notna()]
        j.loc[ok, "msoa21cd"] = s.loc[ok, "msoa21cd"]
        j.loc[ok, "assign_method"] = "nearest_within_500m"
    return pd.DataFrame(j.drop(columns=["geometry", "index_right"]))


def load_osm(snapshot):
    seen = {}
    for f in sorted(glob.glob(str(RAW / "ohsome" / snapshot / "tile_*.json"))):
        with open(f, encoding="utf-8") as fh:
            feats = json.load(fh)["features"]
        for ft in feats:
            p = ft["properties"]
            oid = p["@osmId"]
            if oid in seen:
                continue
            ring = ft["geometry"]["coordinates"][0]
            xs = [c[0] for c in ring]
            ys = [c[1] for c in ring]
            am, le = p.get("amenity"), p.get("leisure")
            typ = am if am in OSM_TYPES else ("fitness_centre" if le == "fitness_centre" else None)
            seen[oid] = dict(osm_id=oid, osm_type=p["@osmType"], osm_tag=typ, amenity=am, leisure=le,
                             name=p.get("name"), addr_postcode=p.get("addr:postcode"), fhrs_id=p.get("fhrs:id"),
                             long=(min(xs) + max(xs)) / 2, lat=(min(ys) + max(ys)) / 2,
                             bbox_w_deg=max(xs) - min(xs), bbox_h_deg=max(ys) - min(ys),
                             version=p.get("@version"), last_edit=p.get("@lastEdit"), snapshot=snapshot)
    d = pd.DataFrame(seen.values())
    assert d.osm_tag.notna().all(), d[d.osm_tag.isna()].head()
    return d


def access(m, pts_e, pts_n, W):
    """W: points x categories weights. Returns {lambda: MSOA x categories} via KD-tree, 30 km cutoff."""
    loc = np.column_stack([np.round(pts_e, 1), np.round(pts_n, 1)])
    key, inv = np.unique(loc, axis=0, return_inverse=True)
    Wl = np.zeros((len(key), W.shape[1]))
    np.add.at(Wl, inv.ravel(), W)
    tree_p = cKDTree(key)
    out = {lk: np.zeros((len(m), W.shape[1])) for lk in LAMBDAS}
    xy = m[["pwc_e", "pwc_n"]].values
    step = 250
    for s in range(0, len(m), step):
        tm = cKDTree(xy[s:s + step])
        D = tm.sparse_distance_matrix(tree_p, CUTOFF_M, output_type="coo_matrix")
        dkm = D.data / 1000
        for lk, lam in LAMBDAS.items():
            acc = np.zeros((tm.n, W.shape[1]))
            np.add.at(acc, D.row, np.exp(-dkm / lam)[:, None] * Wl[D.col])
            out[lk][s:s + step] = acc
        # sparse_distance_matrix drops exact zero distances: add co-located points with weight 1
        for i, js in enumerate(tm.query_ball_tree(tree_p, r=1e-6)):
            if js:
                for lk in LAMBDAS:
                    out[lk][s + i] += Wl[js].sum(axis=0)
    return out


def main():
    poly, m = msoa_frames()
    m.to_csv(CLEAN / "msoa21_ew_lookup_pwc.csv", index=False)
    la_of = m.set_index("msoa21cd").lad23cd

    # ---- points
    f = assign(pd.read_parquet(BIG / "fhrs_points_ew.parquet"), poly)
    f["lad23cd"] = f.msoa21cd.map(la_of)
    f.to_parquet(BIG / "fhrs_points_ew_assigned.parquet", index=False)
    osm = {}
    for snap in ["2019-12-31", "2022-12-31"]:
        o = assign(load_osm(snap), poly)
        o["lad23cd"] = o.msoa21cd.map(la_of)
        o.to_parquet(BIG / f"osm_points_{snap[:4]}_assigned.parquet", index=False)
        osm[snap[:4]] = o

    # ---- coverage summary
    rows = []
    for lab, d, cat in [("fhrs", f, "category")] + [(f"osm_{y}", o, "osm_tag") for y, o in osm.items()]:
        for c, g in list(d.groupby(cat)) + [("all", d)]:
            rows.append(dict(source=lab, category=c, points=len(g), with_coords=int(g.lat.notna().sum()),
                             in_msoa_within=int((g.assign_method == "within").sum()),
                             in_msoa_snapped=int((g.assign_method == "nearest_within_500m").sum()),
                             not_assigned=int(g.msoa21cd.isna().sum()),
                             msoas_with_any=int(g.msoa21cd.nunique()), las_with_any=int(g.lad23cd.nunique())))
    cov = pd.DataFrame(rows)
    cov["pct_assigned"] = (100 * (cov.in_msoa_within + cov.in_msoa_snapped) / cov.points).round(2)
    cov.to_csv(CLEAN / "b1_point_assignment_summary.csv", index=False)
    print(cov.to_string(index=False))

    # FHRS: inspecting authority (from the file) vs LA by location
    fa = f[f.msoa21cd.notna()].copy()
    auth = pd.read_csv(RAW / "fhrs" / "authorities_ew.csv", dtype=str)[["LocalAuthorityIdCode", "Name"]]
    fa["LocalAuthorityCode"] = fa.LocalAuthorityCode.astype(str)
    # modal located LA per inspecting authority; share of that authority's records located in its modal LA
    mode = fa.groupby("LocalAuthorityCode").lad23cd.agg(lambda s: s.value_counts().index[0])
    fa["modal_la"] = fa.LocalAuthorityCode.map(mode)
    agree = (fa.lad23cd == fa.modal_la).mean()
    print(f"FHRS: share of records located in their inspecting authority's modal LA: {agree:.4f}")

    # ---- MSOA x category counts
    cols = {}
    for c in FHRS_CATS:
        cols[f"fhrs_{c}"] = fa[fa.category == c].groupby("msoa21cd").size()
    for y, o in osm.items():
        oa = o[o.msoa21cd.notna()]
        for t in OSM_TYPES:
            cols[f"osm{y}_{t}"] = oa[oa.osm_tag == t].groupby("msoa21cd").size()
        for gname, members in OSM_GROUPS.items():
            cols[f"osm{y}_{gname}"] = oa[oa.osm_tag.isin(members)].groupby("msoa21cd").size()
    cnt = pd.DataFrame(cols).reindex(m.msoa21cd).fillna(0).astype(int)
    cnt.index.name = "msoa21cd"
    msoa = m[["msoa21cd", "msoa21nm", "lad23cd", "pop_census2021"]].merge(cnt.reset_index(), on="msoa21cd")
    msoa.to_csv(CLEAN / "msoa21_amenity_counts_ew.csv", index=False)
    la = msoa.drop(columns=["msoa21cd", "msoa21nm"]).groupby("lad23cd").sum()
    # alternative FHRS LA counts by inspecting authority (includes records with withheld addresses);
    # each FHRS authority is mapped to the LA where most of its located records fall
    fall = f.copy()
    fall["LocalAuthorityCode"] = fall.LocalAuthorityCode.astype(str)
    fall["auth_la"] = fall.LocalAuthorityCode.map(mode)
    for c in FHRS_CATS:
        la[f"fhrs_{c}_by_authority"] = fall[fall.category == c].groupby("auth_la").size().reindex(la.index).fillna(0)
    amap = auth.merge(mode.rename("lad23cd_modal").reset_index().rename(
        columns={"LocalAuthorityCode": "LocalAuthorityIdCode"}), on="LocalAuthorityIdCode", how="left")
    amap["share_located_in_modal_la"] = amap.LocalAuthorityIdCode.map(
        fa.assign(ok=fa.lad23cd == fa.modal_la).groupby("LocalAuthorityCode").ok.mean())
    amap.to_csv(CLEAN / "fhrs_authority_to_la2023.csv", index=False)
    la.reset_index().to_csv(CLEAN / "la2023_amenity_counts_ew.csv", index=False)
    print(f"MSOA counts: {len(msoa)} rows; LA counts: {len(la)} rows")

    # ---- access indices
    acc_cats, pts_e, pts_n, W, blocks = [], [], [], [], []
    spec = {f"fhrs_{c}": [c] for c in FHRS_CATS}
    acc_cats += list(spec)
    blocks.append((fa, "category", spec))
    for y, o in osm.items():
        spec = {f"osm{y}_{g}": OSM_GROUPS.get(g, [g]) for g in ACCESS_OSM}
        acc_cats += list(spec)
        blocks.append((o[o.msoa21cd.notna()], "osm_tag", spec))
    for d, col, spec in blocks:
        w = np.zeros((len(d), len(acc_cats)))
        for k, members in spec.items():
            w[:, acc_cats.index(k)] = d[col].isin(members).values
        pts_e.append(d.easting.values)
        pts_n.append(d.northing.values)
        W.append(w)
    A = access(m, np.concatenate(pts_e), np.concatenate(pts_n), np.vstack(W))
    out = m[["msoa21cd", "lad23cd", "pwc_e", "pwc_n"]].copy()
    newcols = {}
    for lk in LAMBDAS:
        for i, c in enumerate(acc_cats):
            newcols[f"access_pt_{lk}_{c}"] = A[lk][:, i]
    # pilot-style: MSOA counts at own PWC, all E&W MSOAs as sources (dense 7264 x 7264)
    xy = m[["pwc_e", "pwc_n"]].values
    Dm = (np.hypot(xy[:, 0][:, None] - xy[:, 0][None, :], xy[:, 1][:, None] - xy[:, 1][None, :]) / 1000
          ).astype(np.float32)
    U = cnt.loc[m.msoa21cd, acc_cats].values.astype(np.float32)
    for lk, lam in LAMBDAS.items():
        Am = np.exp(-Dm / lam) @ U
        for i, c in enumerate(acc_cats):
            newcols[f"access_pwc_{lk}_{c}"] = Am[:, i]
    out = pd.concat([out, pd.DataFrame(newcols)], axis=1)
    out.to_csv(CLEAN / "msoa21_amenity_access_ew.csv", index=False)
    print(f"access: {out.shape}")
    for c in acc_cats:
        a, b = out[f"access_pt_l15_{c}"], out[f"access_pwc_l15_{c}"]
        print(f"{c}: corr(log pt, log pwc) l15 = {np.log1p(a).corr(np.log1p(b)):.3f}; "
              f"total pt / total pwc = {a.sum() / b.sum():.3f}")


if __name__ == "__main__":
    main()
