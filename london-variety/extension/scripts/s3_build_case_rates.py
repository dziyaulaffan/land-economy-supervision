"""S3: weekly COVID-19 cases and case rates per 100,000 by 2023 LAD, England and Wales, 2020-2021.

Inputs
  England: UKHSA data dashboard API, COVID-19_cases_casesByDay (cases by specimen date), LTLA,
           saved by s3_download_cases.py under RAW/covid_cases/ukhsa/.
  Wales:   archived coronavirus dashboard (UKHSA), Cases/ltla_newCasesBySpecimenDate.csv, whose Welsh
           LTLA series are the Public Health Wales figures. October 2020 is missing for every Welsh LTLA
           in the archive. The October total is rebuilt as cumulative cases on the first day after the gap
           minus all non-October daily cases up to that day (cumulative count where the archive has it,
           11 LAs; otherwise cumulative rate x implied population), then spread over days with the Wales
           national daily profile (nation_newCasesBySpecimenDate).
  Populations: ONS mid-2020 population estimates on April 2023 LADs (Nomis NM_2002_1, current release,
           i.e. the series rebased to Census 2021), saved by s3_download_cases.py population.
  Geography: b4_ltla20_to_lad23.csv maps 2020 LTLA reporting codes to 2023 LADs.

Outputs (extension/data/clean/)
  s3_case_rates_la2023_weekly.csv: la_code, la_name, week_ending, cases, population, rate_per_100k,
      source, imputed_days.
  s3_case_rates_la2023_year_to_june2021.csv: mean weekly rate 1 Jul 2020 to 30 Jun 2021 and
      2020Q3..2021Q2 quarterly means.
  s3_validation.csv: national totals against the UKHSA and archive national series.
"""
import glob
import json
import sys
import zipfile
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent))
from ext_config import CLEAN, RAW  # noqa: E402

UKHSA = RAW / "covid_cases" / "ukhsa"
ARCH = RAW / "covid_cases" / "archive" / "cases.zip"
START, END = pd.Timestamp("2020-01-01"), pd.Timestamp("2021-12-31")

# Combined areas reported by UKHSA (code used by UKHSA -> member 2023 LADs)
COMBINED = {"E09000001": ["E09000001", "E09000012"],   # Hackney and City of London
            "E06000052": ["E06000052", "E06000053"]}   # Cornwall and Isles of Scilly


def england():
    rows = []
    for f in glob.glob(str(UKHSA / "COVID-19_cases_casesByDay_*.json")):
        for r in json.load(open(f)):
            rows.append((r["geography"], r["geography_code"], r["date"], r["metric_value"]))
    d = pd.DataFrame(rows, columns=["geo_name", "geo_code", "date", "cases"])
    d["date"] = pd.to_datetime(d["date"])
    # several API geography names can resolve to the same code; keep one series per code and date
    dup = d.groupby(["geo_code", "date"]).cases.nunique()
    assert (dup <= 1).all(), "conflicting series for one code"
    d = d.drop_duplicates(["geo_code", "date"])
    d = d[(d.date >= START) & (d.date <= END)]
    return d[["geo_code", "geo_name", "date", "cases"]].assign(source="UKHSA dashboard API COVID-19_cases_casesByDay", imputed=0)


def wales():
    z = zipfile.ZipFile(ARCH)
    new = pd.read_csv(z.open("Cases/ltla_newCasesBySpecimenDate.csv"))
    new["date"] = pd.to_datetime(new.date, format="%d/%m/%Y")
    new = new[new.area_code.str.startswith("W")]
    # The cumulative count file holds only 11 of the 22 Welsh LAs, so the cumulative RATE file (all 22,
    # rate per 100,000 to one decimal place) is used; the population behind it is recovered from
    # September 2020, when daily counts and cumulative rates both exist.
    cr = pd.read_csv(z.open("Cases/ltla_cumCasesBySpecimenDateRate.csv"))
    cr["date"] = pd.to_datetime(cr.date, format="ISO8601")
    cr = cr[cr.area_code.str.startswith("W")]
    cc = pd.read_csv(z.open("Cases/ltla_cumCasesBySpecimenDate.csv"))
    cc["date"] = pd.to_datetime(cc.date, format="%d/%m/%Y")
    cc = cc[cc.area_code.str.startswith("W")]
    nat = pd.read_csv(z.open("Cases/nation_newCasesBySpecimenDate.csv"))
    nat["date"] = pd.to_datetime(nat.date, format="ISO8601")
    nat = nat[nat.area_code == "W92000004"].set_index("date").value
    gap = pd.date_range("2020-10-01", "2020-10-31")
    prof = nat.reindex(gap).fillna(0)
    prof = prof / prof.sum()
    out, gaplog = [], []
    for code, g in new.groupby("area_code"):
        s = g.set_index("date").value.sort_index()
        r = cr[cr.area_code == code].set_index("date").value.sort_index()
        sep = pd.date_range("2020-09-01", "2020-09-30")
        cumnew = s.cumsum().reindex(sep).ffill()
        popimp = float((1e5 * cumnew / r.reindex(sep)).median())
        d2 = r[r.index > gap.max()].index.min()
        cum_after = r.loc[d2] * popimp / 1e5
        total_oct = cum_after - s[(s.index <= d2) & ~s.index.isin(gap)].sum()
        c = cc[cc.area_code == code].set_index("date").value
        cum_after_count = c.get(d2, np.nan)
        total_oct_count = cum_after_count - s[(s.index <= d2) & ~s.index.isin(gap)].sum()
        gaplog.append((code, g.area_name.iloc[0], d2.date(), round(popimp), round(total_oct, 1),
                       total_oct_count))
        total_oct = total_oct_count if not np.isnan(total_oct_count) else round(total_oct)
        imp = (prof * total_oct)
        full = pd.concat([s, imp]).sort_index()
        df = full.rename("cases").reset_index().rename(columns={"index": "date"})
        df["imputed"] = df.date.isin(gap).astype(int)
        df["geo_code"], df["geo_name"] = code, g.area_name.iloc[0].replace("-", " ")
        out.append(df)
    w = pd.concat(out)
    w = w[(w.date >= START) & (w.date <= END)]
    w["source"] = np.where(w.imputed == 1,
                           "Public Health Wales via archived coronavirus dashboard; Oct 2020 rebuilt from cumulative series",
                           "Public Health Wales via archived coronavirus dashboard (ltla_newCasesBySpecimenDate)")
    gaplog = pd.DataFrame(gaplog, columns=["la_code", "la_name", "cum_date_after_gap", "population_implied_by_rate",
                                           "oct2020_cases_from_cum_rate", "oct2020_cases_from_cum_count"])
    return w[["geo_code", "geo_name", "date", "cases", "source", "imputed"]], gaplog, nat


def main():
    lk = pd.read_csv(CLEAN / "b4_ltla20_to_lad23.csv")
    e = england()
    w, gaplog, wal_nat = wales()
    daily = pd.concat([e, w], ignore_index=True)

    # Map reporting codes to 2023 LADs. Reporting codes are 2020 LTLAs, 2021 unitaries (Northamptonshire)
    # or 2023 LADs; combined areas are split by population and flagged.
    lad23 = lk.groupby(["lad23_code", "lad23_name"]).size().reset_index()[["lad23_code", "lad23_name"]]
    mye = pd.read_csv(RAW / "nomis" / "mye_population_mid2020_la2023.csv")
    pop23 = mye.set_index("GEOGRAPHY_CODE").OBS_VALUE.reindex(lad23.lad23_code).astype(float)
    assert pop23.notna().all(), "missing mid-2020 population"
    code_to_lad = dict(zip(lk.ltla20_code, lk.lad23_code))
    code_to_lad.update({c: c for c in lad23.lad23_code})
    rows = []
    for code, g in daily.groupby("geo_code"):
        if code in COMBINED:
            members = COMBINED[code]
            tot = pop23[members].sum()
            for m in members:
                rows.append(g.assign(lad23_code=m, share=pop23[m] / tot, combined_with="+".join(members)))
        else:
            if code not in code_to_lad:
                print("unmapped reporting code", code, g.geo_name.iloc[0])
                continue
            rows.append(g.assign(lad23_code=code_to_lad[code], share=1.0, combined_with=""))
    d = pd.concat(rows, ignore_index=True)
    d["cases_w"] = d.cases * d.share
    # avoid double counting when both predecessor and successor codes are reported
    reps = d.groupby("lad23_code").geo_code.unique()
    for lad, codes in reps.items():
        if len(codes) > 1:
            print("several reporting codes for", lad, list(codes))
    dl = d.groupby(["lad23_code", "date"]).agg(cases=("cases_w", "sum"), imputed=("imputed", "max"),
                                                 source=("source", "first"),
                                                 combined_with=("combined_with", "first")).reset_index()
    # full daily grid, zero-filled before first reported case
    grid = pd.MultiIndex.from_product([pop23.index, pd.date_range(START, END)], names=["lad23_code", "date"])
    dl = dl.set_index(["lad23_code", "date"]).reindex(grid).reset_index()
    first = dl.groupby("lad23_code").source.transform(lambda s: s.dropna().iloc[0] if s.notna().any() else np.nan)
    dl["source"] = dl.source.fillna(first)
    dl["combined_with"] = dl.groupby("lad23_code").combined_with.transform(lambda s: s.dropna().iloc[0] if s.notna().any() else "")
    dl["cases"] = dl.cases.fillna(0.0)
    dl["imputed"] = dl.imputed.fillna(0).astype(int)
    missing = dl.groupby("lad23_code").source.apply(lambda s: s.isna().all())
    print("LADs without any series:", list(missing[missing].index))

    # weekly, Monday to Sunday, labelled by the Sunday; only complete weeks inside 2020-2021
    dl["week_ending"] = dl.date + pd.to_timedelta((6 - dl.date.dt.dayofweek) % 7, unit="D")
    wk = dl.groupby(["lad23_code", "week_ending"]).agg(cases=("cases", "sum"), ndays=("cases", "size"),
                                                       imputed_days=("imputed", "sum"),
                                                       source=("source", "first"),
                                                       combined_with=("combined_with", "first")).reset_index()
    wk = wk[wk.ndays == 7].drop(columns="ndays")
    wk["population"] = wk.lad23_code.map(pop23)
    wk["rate_per_100k"] = 1e5 * wk.cases / wk.population
    wk["la_name"] = wk.lad23_code.map(lad23.set_index("lad23_code").lad23_name)
    wk = wk.rename(columns={"lad23_code": "la_code"})
    wk["cases"] = wk.cases.round(2)
    wk = wk[["la_code", "la_name", "week_ending", "cases", "population", "rate_per_100k", "source",
             "imputed_days", "combined_with"]]
    wk.to_csv(CLEAN / "s3_case_rates_la2023_weekly.csv", index=False, date_format="%Y-%m-%d")
    print("weekly rows", len(wk), wk.la_code.nunique(), wk.week_ending.min(), wk.week_ending.max())

    # period means from daily data: mean weekly rate = 7 * cases / days / pop * 1e5
    def period(a, b, lab):
        s = dl[(dl.date >= a) & (dl.date <= b)]
        ndays = (pd.Timestamp(b) - pd.Timestamp(a)).days + 1
        g = s.groupby("lad23_code").agg(cases=("cases", "sum"), imp=("imputed", "sum"))
        g[lab] = 7e5 * g.cases / ndays / pop23.reindex(g.index)
        return g, ndays

    y, nd = period("2020-07-01", "2021-06-30", "mean_weekly_rate_jul2020_jun2021")
    res = y.rename(columns={"cases": "cases_jul2020_jun2021", "imp": "imputed_days"})
    for lab, a, b in [("2020Q3", "2020-07-01", "2020-09-30"), ("2020Q4", "2020-10-01", "2020-12-31"),
                      ("2021Q1", "2021-01-01", "2021-03-31"), ("2021Q2", "2021-04-01", "2021-06-30")]:
        q, _ = period(a, b, f"mean_weekly_rate_{lab}")
        res[f"mean_weekly_rate_{lab}"] = q[f"mean_weekly_rate_{lab}"]
    res["population"] = pop23
    res["la_name"] = lad23.set_index("lad23_code").lad23_name
    res["country"] = np.where(res.index.str.startswith("W"), "Wales", "England")
    res["source"] = dl.groupby("lad23_code").source.first().str.split(";").str[0]
    res["combined_with"] = dl.groupby("lad23_code").combined_with.first()
    res = res.reset_index().rename(columns={"lad23_code": "la_code"})
    cols = ["la_code", "la_name", "country", "population", "cases_jul2020_jun2021",
            "mean_weekly_rate_jul2020_jun2021", "mean_weekly_rate_2020Q3", "mean_weekly_rate_2020Q4",
            "mean_weekly_rate_2021Q1", "mean_weekly_rate_2021Q2", "imputed_days", "source", "combined_with"]
    res[cols].to_csv(CLEAN / "s3_case_rates_la2023_year_to_june2021.csv", index=False)

    # validation
    val = []
    z = zipfile.ZipFile(ARCH)
    nat = pd.read_csv(z.open("Cases/nation_newCasesBySpecimenDate.csv"))
    nat["date"] = pd.to_datetime(nat.date, format="ISO8601")
    for ctry, code, pref in [("England", "E92000001", "E"), ("Wales", "W92000004", "W")]:
        for a, b in [("2020-01-01", "2020-12-31"), ("2021-01-01", "2021-12-31"), ("2020-07-01", "2021-06-30"),
                     ("2020-10-01", "2020-10-31")]:
            la = dl[dl.lad23_code.str.startswith(pref) & dl.date.between(a, b)].cases.sum()
            n = nat[(nat.area_code == code) & nat.date.between(a, b)].value.sum()
            val.append((ctry, f"{a} to {b}", "sum of LAs (this file)", round(la)))
            val.append((ctry, f"{a} to {b}", "nation series, archived coronavirus dashboard", round(n)))
    nat_api = UKHSA.parent / "ukhsa_nation_england.json"
    if nat_api.exists():
        ne = pd.DataFrame(json.load(open(nat_api)))
        ne["date"] = pd.to_datetime(ne.date)
        for a, b in [("2020-01-01", "2020-12-31"), ("2021-01-01", "2021-12-31"), ("2020-07-01", "2021-06-30"),
                     ("2020-10-01", "2020-10-31")]:
            val.append(("England", f"{a} to {b}", "nation series, UKHSA dashboard API",
                        round(ne[ne.date.between(a, b)].metric_value.sum())))
    v = pd.DataFrame(val, columns=["country", "period", "series", "cases"])
    v.to_csv(CLEAN / "s3_validation.csv", index=False)
    print(v.to_string())
    gaplog.to_csv(CLEAN / "s3_wales_oct2020_rebuild.csv", index=False)
    print(gaplog.to_string())


if __name__ == "__main__":
    main()
