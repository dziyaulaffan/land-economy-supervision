"""V3. Design diagnostics for the venue-mix treatment, run before any migration outcome is opened.

Regression of the main treatment (variety-days lost, FHRS access, lambda = 1.5 km, 23 Mar 2020 to 22 Mar 2021)
on the Step 3 controls with local authority fixed effects, across 2021 MSOAs in England:
  log total access, log population density (Census 2021 TS006), log job density (BRES 2019 employment at
  2011 MSOA, Nomis NM_189_1, moved to 2021 MSOAs with the S4 population shares, per km2 of land implied by
  TS006), teleworkability, garden access, share of households in flats, private renting share, share aged
  20 to 39, student share (S1 controls).
The same regression is repeated for the OSM version, for 1 and 3 km decay, and for England and Wales.

Stopping rule, fixed before this script was first run (recorded in VENUE_MIX_NOTES.md): the residual variation
is judged too small to support estimation if the residual SD is below 2 days or below 10% of the raw SD of the
treatment in England. In that case the extension stops after Step 4.

Outputs (extension/venue_mix/data/):
  v3_controls_msoa.csv, v3_diagnostics.csv, v3_correlations.csv, v3_residual_msoa.csv,
  figures/v3_residual_map_<city>.png
"""
import glob

import numpy as np
import pandas as pd
import requests

from vm_common import CLEAN, DATA, RAW, UA, VRAW
from vm_core import ols_fe

NOMIS = "https://www.nomisweb.co.uk/api/v01/dataset"
CONTROLS = ["log_total_access", "log_pop_density", "log_job_density", "telework_share", "garden_share",
            "flat_share", "private_rent_share", "age20_39_share", "student_share"]
CITIES = {"London": ("region", "London"),
          "Greater Manchester": ("lad", ["E08000001", "E08000002", "E08000003", "E08000004", "E08000005",
                                         "E08000006", "E08000007", "E08000008", "E08000009", "E08000010"]),
          "West Midlands (Birmingham)": ("lad", ["E08000025", "E08000026", "E08000027", "E08000028",
                                                 "E08000029", "E08000030", "E08000031"])}


def fetch(url, dest):
    if dest.exists() and dest.stat().st_size > 1000:
        return pd.read_csv(dest)
    r = requests.get(url, headers=UA, timeout=300)
    r.raise_for_status()
    dest.write_bytes(r.content)
    return pd.read_csv(dest)


def controls():
    s1 = pd.read_csv(CLEAN / "s1_controls_msoa21.csv")
    dens = fetch(f"{NOMIS}/NM_2026_1.data.csv?geography=TYPE152&measures=20100&select=geography_code,obs_value",
                 VRAW / "census2021_ts006_density_msoa21.csv").rename(
        columns={"GEOGRAPHY_CODE": "msoa21cd", "OBS_VALUE": "pop_density"})
    bres = fetch(f"{NOMIS}/NM_189_1.data.csv?geography=TYPE297&date=2019&industry=37748736&employment_status=4"
                 "&measure=1&measures=20100&select=geography_code,obs_value", VRAW / "bres2019_employment_msoa11.csv"
                 ).rename(columns={"GEOGRAPHY_CODE": "msoa11cd", "OBS_VALUE": "jobs"})
    lk = pd.read_csv(CLEAN / "s4_lookup_msoa11_msoa21.csv")
    j = bres.merge(lk, on="msoa11cd")
    j["jobs"] = j.jobs * j.share
    jobs = j.groupby("msoa21cd").jobs.sum().rename("jobs_2019").reset_index()
    tr = pd.read_csv(DATA / "v2_treatment_msoa.csv")
    m = pd.read_csv(CLEAN / "msoa21_ew_lookup_pwc.csv")[["msoa21cd", "pop_census2021"]]
    d = (tr.merge(s1.drop(columns=["lad23cd"]), on="msoa21cd", how="left").merge(dens, on="msoa21cd", how="left")
         .merge(jobs, on="msoa21cd", how="left").merge(m, on="msoa21cd", how="left"))
    d["area_km2"] = d.pop_census2021 / d.pop_density
    d["job_density"] = d.jobs_2019 / d.area_km2
    d["log_pop_density"] = np.log(d.pop_density)
    d["log_job_density"] = np.log(d.job_density + 1)
    for v in ["fhrs", "osm"]:
        for lk_ in ["l10", "l15", "l30"]:
            d[f"log_total_access_{v}_{lk_}"] = np.log(d[f"total_access_{v}_{lk_}"])
    d["log_total_access"] = d.log_total_access_fhrs_l15
    d["nation"] = d.lad23cd.str[0]
    d.to_csv(DATA / "v3_controls_msoa.csv", index=False)
    print(f"controls: {len(d)} MSOAs; missing by column:\n{d[CONTROLS].isna().sum().to_string()}")
    print(f"BRES 2019 jobs: {bres.jobs.sum():,.0f} at 2011 MSOAs, {jobs.jobs_2019.sum():,.0f} after mapping")
    return d


def diag(d, treat, label, sample, ctrl):
    x = d.dropna(subset=[treat] + ctrl).copy()
    t = ols_fe(x, treat, ctrl, boot=False)
    # residual from the full model; within-LA SD for reference
    X = np.column_stack([pd.get_dummies(x.lad23cd, dtype=float).values, x[ctrl].values])
    beta = np.linalg.lstsq(X, x[treat].values, rcond=None)[0]
    res = x[treat].values - X @ beta
    within = x[treat] - x.groupby("lad23cd")[treat].transform("mean")
    Xf = pd.get_dummies(x.lad23cd, dtype=float).values
    r2_fe = 1 - ((x[treat].values - Xf @ np.linalg.lstsq(Xf, x[treat].values, rcond=None)[0]) ** 2).sum() / (
        (x[treat] - x[treat].mean()) ** 2).sum()
    out = dict(treatment=label, sample=sample, n_msoa=len(x), n_la=x.lad23cd.nunique(), raw_sd=x[treat].std(),
               within_la_sd=within.std(), r2_la_fe_only=r2_fe, r2_full=t.r2.iloc[0], residual_sd=res.std(ddof=1),
               residual_sd_over_raw=res.std(ddof=1) / x[treat].std(),
               residual_var_share_of_within=res.var(ddof=1) / within.var())
    coefs = t[["name", "coef", "se", "p_cr1"]].assign(treatment=label, sample=sample)
    return out, coefs, pd.Series(res, index=x.msoa21cd)


def maps(d, res):
    import geopandas as gpd
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    pages = sorted(glob.glob(str(RAW / "ons_geography" / "msoa21_bfe_v8" / "page_*.geojson")))
    poly = pd.concat([gpd.read_file(p) for p in pages], ignore_index=True).rename(columns={"MSOA21CD": "msoa21cd"})
    poly = gpd.GeoDataFrame(poly, geometry="geometry", crs=27700)
    poly["geometry"] = poly.geometry.make_valid()
    poly = poly.merge(d[["msoa21cd", "lad23cd", "region"]], on="msoa21cd").merge(
        res.rename("resid").reset_index(), on="msoa21cd", how="left")
    fig_dir = DATA / "figures"
    fig_dir.mkdir(exist_ok=True)
    lim = np.nanpercentile(np.abs(res), 98)
    for city, (kind, val) in CITIES.items():
        g = poly[poly.region == val] if kind == "region" else poly[poly.lad23cd.isin(val)]
        fig, ax = plt.subplots(figsize=(8, 7))
        g.plot(column="resid", cmap="RdBu_r", vmin=-lim, vmax=lim, legend=True, ax=ax, linewidth=0.1,
               edgecolor="white", legend_kwds={"label": "Residual variety-days lost (days)", "shrink": 0.6},
               missing_kwds={"color": "lightgrey"})
        g.dissolve("lad23cd").boundary.plot(ax=ax, color="black", linewidth=0.5)
        ax.set_axis_off()
        ax.set_title(f"{city}: variety-days lost net of controls and LA effects\n(FHRS access, 1.5 km decay)",
                     fontsize=10)
        fig.tight_layout()
        fname = fig_dir / f"v3_residual_map_{city.split(' ')[0].lower()}.png"
        fig.savefig(fname, dpi=150)
        plt.close(fig)
        print(f"map: {fname.name}, {len(g)} MSOAs, residual SD {g.resid.std():.2f}")


def main():
    d = controls()
    rows, coefs, res_main = [], [], None
    specs = [("vdl_main_fhrs_l15", "FHRS 1.5 km (main)", "England", "E"),
             ("vdl_main_fhrs_l15", "FHRS 1.5 km (main)", "England and Wales", None),
             ("vdl_main_osm_l15", "OSM 1.5 km", "England", "E"),
             ("vdl_main_fhrs_l10", "FHRS 1 km", "England", "E"),
             ("vdl_main_fhrs_l30", "FHRS 3 km", "England", "E")]
    for treat, lab, smp, nat in specs:
        x = d if nat is None else d[d.nation == nat]
        ctrl = [c if c != "log_total_access" else f"log_total_access_{treat.split('_', 3)[2]}_{treat[-3:]}"
                for c in CONTROLS]
        x = x.assign(**{c: x[c] for c in ctrl})
        o, c, r = diag(x, treat, lab, smp, ctrl)
        rows.append(o); coefs.append(c)
        if res_main is None:
            res_main = r
    out = pd.DataFrame(rows)
    out.to_csv(DATA / "v3_diagnostics.csv", index=False)
    pd.concat(coefs).to_csv(DATA / "v3_diagnostic_coefs.csv", index=False)
    e = d[d.nation == "E"]
    corr = e[["vdl_main_fhrs_l15", "vdl_main_osm_l15"] + CONTROLS].corr()
    corr.to_csv(DATA / "v3_correlations.csv")
    # within-LA correlations (each variable demeaned by LA)
    w = e[["lad23cd", "vdl_main_fhrs_l15"] + CONTROLS].dropna()
    wd = w[["vdl_main_fhrs_l15"] + CONTROLS] - w.groupby("lad23cd")[["vdl_main_fhrs_l15"] + CONTROLS].transform("mean")
    wcorr = wd.corr()
    wcorr.to_csv(DATA / "v3_correlations_within_la.csv")
    res_main.rename("resid_vdl_main_fhrs_l15").to_csv(DATA / "v3_residual_msoa.csv")
    pd.set_option("display.width", 220)
    print(out.round(3).to_string(index=False))
    print("\ncoefficients, main (England)\n", coefs[0][["name", "coef", "se", "p_cr1"]].round(3).to_string(index=False))
    print("\ncorrelation with VDL (England, raw and within LA)\n",
          pd.DataFrame({"raw": corr.vdl_main_fhrs_l15, "within_la": wcorr.vdl_main_fhrs_l15}).round(3).to_string())
    m = out.iloc[0]
    too_small = (m.residual_sd < 2) or (m.residual_sd_over_raw < 0.10)
    print(f"\nstopping rule: residual SD {m.residual_sd:.2f} days, {100 * m.residual_sd_over_raw:.1f}% of raw SD "
          f"-> {'TOO SMALL, stop after Step 4' if too_small else 'sufficient to proceed'}")
    maps(d, res_main)


if __name__ == "__main__":
    main()
