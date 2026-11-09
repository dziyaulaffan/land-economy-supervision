# Estimation notes: borough and MSOA event studies

Run 28 October 2026. Rebuilt by `python scripts/run_all.py`. Sections 1-6 cover the borough event studies (`70_controls.py`, `80_event_study.py`, `85_contdid.R`, `90_event_study_plots.py`). Sections 7-11 cover the second round: rent trend break, HonestDiD, MSOA correlations and MSOA house prices (`82_rent_trend_break.py`, `83_honestdid.R`, `75_msoa_amenity.py`, `87_msoa_house_prices.py`). Section 12 covers the third round: the MSOA price model extended to 2026Q3 with distance, property-type and 2019-price controls (`76_msoa_distance.py`, `87_msoa_house_prices.py`). Section 13 covers the fourth round: the headline and mediator house-price specifications, the rent return measure, price-to-rent ratios and pound values (`82`, `87`, `88_price_to_rent.py`, `89_pound_values.py`). Section 14 covers the fifth round: the consumption access index and ring counts in place of own-MSOA density, plus the completion-lag window (`77_msoa_access.py`, `92_msoa_access_event_study.py`). Section 15 covers the sixth round: age-group migration event studies and the closure, reopening and later decomposition (`94_migration_age.py`, `95_reversal.py`). Section 16 covers the seventh round: the young-adult triple difference, student checks and the hospitality-worker control (`96_age_ddd.py`). Section 17 covers the pre-period check (`97_preperiod_check.py`). HonestDiD is cached, so `run_all.py` skips it when its inputs are unchanged. The full rebuild takes about 80 minutes, about 50 of them in `83_honestdid.R`.

All coefficients below are estimates from 32 boroughs. They carry real uncertainty, and the pre-trend evidence (section 4) means none of them should yet be read as causal.

## 1. Model

```
y_bt = a_b + l_t + Σ_{k≠base} β_k · 1[t=k] · D_b + Σ_c Σ_{k≠base} γ_ck · 1[t=k] · X_cb + e_bt
```

- **Units:** 32 London boroughs (City of London excluded). Borough fixed effects a_b and period fixed effects l_t.
- **Treatment D_b:**
  - **Continuous:** standardised log of 2019 I+R local units per 1,000 residents. Mean 0, SD 1 across the 32 boroughs. One SD equals 0.567 log points.
  - **Binned:** within-zone amenity terciles. T2 and T3 are dummies; T1 (bottom third within zone) is the reference.
- **Controls X_cb:** 2011 or 2020 levels, standardised across the 32 boroughs, each interacted with every period. They are entered one at a time, then all four together.
- **Inference:**
  - Standard errors are CR1, clustered by borough, with t(31) critical values.
  - The small-sample correction follows the fixest/reghdfe convention: borough fixed effects are nested in clusters and not counted in K.
  - Wild cluster restricted bootstrap p-values (null imposed, Rademacher weights, B = 9,999, seed 20261028) are reported for every event-time coefficient.

## 2. Specifications and sample sizes

| Outcome | Periods | Omitted | Treatment | Specs | N | Clusters | K (all params) |
|---|---|---|---|---|---|---|---|
| Net migration with rest of UK per 1,000 mid-2019 residents (`nonlondon_net`) | Years to June 2015-2025 (11) | Year to June 2019 | Continuous | baseline, +garden, +telework, +age2039, +privrent, +all | 352 | 32 | 52 / 62 / 92 |
| same | same | same | Binned (T2, T3) | same 6 | 352 | 32 | 62 / 72 / 102 |
| 100 × log quarterly mean PIPR index | 2015Q1-2026Q3 (47) | 2019Q4 | Continuous | same 6 | 1,504 | 32 | 124 / 170 / 308 |
| same | same | same | Binned (T2, T3) | same 6 | 1,504 | 32 | 170 / 216 / 354 |

There are 24 regressions in total. The K column reads baseline / one control / all controls. Per-specification details, including pre-trend tests, are in `outputs/event_study/spec_summary.csv`.

**Outputs**
- `outputs/event_study/regression_table.csv`: one row per outcome × treatment × spec × term × period, 1,008 rows. Columns are coef, se_cluster, t, p_cluster, p_wcb, 95% CI, pre-trend F and p, N, clusters and K.
- `outputs/event_study/es_{migration,rents}_{continuous,binned}.png`: six panels per figure, one per specification. The pre-period is shaded, and filled markers mean wild bootstrap p < 0.05.
- `outputs/event_study/contdid_rents_*.{txt,png}`: the continuous DiD robustness check (section 5).

## 3. Verification

- **Point estimates and standard errors** were checked against `pyfixest` 0.60 `feols(... | borough + period, vcov=CRV1)`. Coefficients agree exactly and SEs to within 1e-14.
- **Bootstrap p-values** were checked against `wildboottest` 0.3.2 via `pyfixest.wildboottest` on 7 coefficients. Differences are within Monte Carlo error: for example 0.0079 vs 0.0072, 0.0853 vs 0.0872, and 0.0062 vs 0.0043. The bootstrap here is a vectorised restricted bootstrap written in `80_event_study.py`. `wildboottest` is too slow to loop over the 1,008 coefficients.

## 4. What the estimates show (descriptive; not yet causal)

**Pre-trends fail for rents in every specification, and for migration in most.** This is the main result of this stage.

**Rents**
- In the baseline continuous model, a 1 SD higher amenity borough had rents about 3 log points higher in 2015Q1 relative to 2019Q4. That gap closes steadily over 2015-2019, then reverses after 2020: −3.5 in 2021Q4 (WCB p < 0.001) and −2.5 in 2022Q4 (p = 0.002).
- So high-amenity boroughs were already on a slower rent path before the pandemic. The post-2020 dip partly continues that trend and partly sits on top of it.
- The joint pre-trend Wald test rejects at p < 0.001 in all 6 continuous rent specifications, and for the top tercile in all 6 binned ones. For the middle tercile p runs from below 0.001 to 0.075. With 19 restrictions and 32 clusters this test over-rejects, but the point estimates alone show the trend.
- Teleworkability (correlation 0.82 with the treatment) moves the pre-period most. With it the 2015Q1 coefficient falls to 1.2 (p = 0.35), while the 2021Q4 coefficient stays at −3.8 (p = 0.001).
- With all four controls the post-2020 dip disappears: −0.9 in 2021Q4, p = 0.56.

**Migration**
- Baseline continuous model:
  - Year to June 2020: −2.8 per 1,000 per SD (WCB p = 0.002).
  - Year to June 2021: −1.7 (p = 0.24). This is the exodus year, but it is noisy.
  - Year to June 2022: +1.7 (p = 0.09), the return.
- The pre-period is not flat. 2016 is −1.8 (p = 0.008), and the pre-trend Wald p = 0.008.
- Controls change the picture a lot:
  - With teleworkability the 2020 effect shrinks to −1.1 (p = 0.20). The 2022 return grows to +4.1 (p < 0.001), and the pre-period is flatter (Wald p = 0.11).
  - With all four controls every post coefficient is insignificant, and 2015 becomes +3.5 (p = 0.006).
- **Binned:** the top tercile shows −3.3 in 2020 (p = 0.05) and −3.6 in 2021 (p = 0.23), against a pre-period 2016 coefficient of −4.7 (p < 0.001).

**Take-away for the method stage.** These controls are strongly collinear with amenity density, with correlations of 0.61 to 0.82 in absolute value. With 32 units, the specification with all four controls has little independent variation left in the treatment. The pre-trends suggest the method needs:
- borough-specific or group-specific linear trends,
- a synthetic-control or reweighting comparison, or
- a finer geography, such as MSOA house prices, with more units per zone.

## 5. Callaway, Goodman-Bacon and Sant'Anna continuous DiD (robustness, rents)

- **Package:** `contdid` 0.1.1 from CRAN (R 4.6.1), function `cont_did()`. This is the method authors' own implementation (Callaway, Goodman-Bacon and Sant'Anna), and `run_all.py` calls it.
- **Python ports:** `moderndid` 0.4.1 and `contdid` 0.1.0 exist on PyPI. Neither was used or tested.
- **Judgement call:** the estimator needs an untreated group (dose 0). Every borough has positive amenity density, and all were exposed in the same quarter.
  - The bottom within-zone tercile (10 boroughs) is coded as the never-treated comparison group.
  - The other 22 boroughs are treated from 2020Q1, with dose = log(I+R units per 1,000).
  - Effects are therefore relative to low-amenity boroughs, not to zero amenity.
- **Settings:** linear dose (degree 1, no knots), `control_group = "nevertreated"`, `base_period = "universal"`, multiplier bootstrap with 999 draws, clustered by borough.
- **Results**
  - Overall ACRT (slope) = −3.28 per log point of density (SE 0.76, 95% CI −4.76 to −1.79). That is about −1.9 per SD, which has the same sign as the TWFE baseline.
  - Overall ATT (level) = −1.02 (SE 0.87, CI −2.72 to 0.68).
  - The event-study aggregation shows the same pre-period pattern as the TWFE models: several pre-2020 event times exclude zero.
- **Caveats**
  - Event-time −1 is not normalised to zero in the package output, even with `base_period = "universal"`.
  - The package warns that the uniform-band critical value fell below the pointwise one and switched to pointwise intervals, so only pointwise intervals are reported.
  - The `level` / `eventstudy` combination needs a 0/1 dose, so a binary treatment variable is passed for that run only.
- `contdid` does not support covariates (`xformula` is "not currently supported"), so this check has no controls.

## 6. Judgement calls and things that failed

1. **Migration outcome.** Net migration with the rest of the UK (`nonlondon_net`: E&W LAs outside London plus Scotland/NI), per 1,000 mid-2019 residents. Within-London moves are excluded so that moves between treated boroughs do not net out. The year to June 2020 is coded as a post period, but it covers only about 3 months of pandemic (mid-March to June 2020).
2. **Rent outcome.** 100 × log of the quarterly mean of the monthly PIPR index (January 2023 = 100), using complete quarters only. PIPR is a smoothed stock measure covering all tenancies, so it moves slowly and is serially correlated. That inflates pre-period precision and favours smooth pre-trends.
3. **Terciles within zone.** These are rank-based. Inner London has 13 boroughs, split 4/4/5; Outer London has 19, split 6/6/7. The same tercile codes are pooled across zones, and no zone × period effects are included, as specified. A variant with zone × period effects would separate the two dimensions further, but it was not run.
4. **Teleworkability route.** This used the ONS 2020 occupation measure ("Which jobs can be done from home?", 21 July 2020), mapped to 2011 Census minor groups (QS606EW). Dingel-Neiman was not needed.
   - ONS gives a 0-5 score with no cut-off. "Can be done from home" is defined as a score below 1.5, which covers 44% of UK employment.
   - At 2.5, chefs (2.48) and cleaners (2.44) would count as teleworkable. One misclassification remains: nursery nurses (1.48) count as teleworkable at 1.5.
   - A 2.0 threshold version and an employment-weighted mean score are saved as alternatives in `controls_borough.csv`. Only the 1.5 version enters the regressions.
5. **Control timing.** Census controls are from 2011, nine years before the shock. Garden access is from April 2020.
6. **Pre-trend Wald test.** This is an addition to the specification. It is cluster-robust with F(q, 31) and is unreliable when q is large relative to 32 clusters, especially for rents (q = 19). Read the plotted coefficients rather than the p-value.
7. **Small-sample convention.** Borough fixed effects are not counted in K, matching fixest's default. Counting them, the Stata `regress i.borough` convention, would widen SEs by about 6% in the migration model with all controls and by about 1% for rents.
8. **Failures and workarounds.**
   - `wildboottest` failed with string cluster IDs (a numba typing error), so integer IDs are used for the check.
   - The first `contdid` install timed out on a dependency (BMisc) and was retried with a longer timeout.
   - Passing `clustervars = "id"` triggered a "two-way clustering not supported" warning, so the default clustering on `idname` is used instead.
9. **Not done at this stage.** MSOA house-price analysis is left for the next stage. MSOA controls are built (`controls_msoa2011.csv`) but not used here.

## 7. Rent trend break (`82_rent_trend_break.py`)

**Specification**

```
y_bt = a_b + l_t + δ · D_b · τ_t + Σ_{k ≥ 2020Q1} θ_k · 1[t=k] · D_b + e_bt
```

- τ_t counts quarters since 2019Q4.
- Each post-2020 quarter has its own D interaction, so δ is identified from 2015Q1-2019Q4 only. θ_k is the deviation from the pre-trend extrapolated forward.
- This is the baseline continuous treatment with no controls: N = 1,504, 32 clusters, K = 106.
- Inference: CR1 clustered by borough, plus WCR bootstrap (B = 9,999).

**Outputs:** `outputs/event_study/rent_trend_break.csv` and `rent_trend_break.png`. The plot shows the event study with the extrapolated line (left) and the deviations (right).

**Results**
- **Pre-2020 slope:** δ = −0.199 per quarter per SD of log amenity density (SE 0.042, WCB p = 0.004).
- **Deviations from the extrapolated trend:**

  | Quarters | Deviation (100 × log points) | WCB p |
  |---|---|---|
  | 2020Q1 | +1.73 | 0.003 |
  | 2020Q2 | +1.30 | 0.041 |
  | 2020Q3-2022Q4 | between −0.53 and +1.33 | all ≥ 0.199 |
  | 2023Q2-2026Q3 | +3.2 to +5.4 | 0.005-0.071; 12 of 14 below 0.05 |

- **Reading:** once a linear pre-trend is extrapolated, the 2021-22 dip in high-amenity rents disappears. What remains is a rise above trend from 2023.

**Judgement calls and caveats**
- **The pre-2020 path is U-shaped, not linear.** Coefficients fall from +3.1 (2015Q1) to about −1.0 (2018Q2-Q3), then rise to 0 at 2019Q4. The single linear trend misses 2018-19 and extrapolates a downward slope. The deviations depend on that extrapolation, and the trend's confidence band widens to about ±2 points by 2026.
- **Where the line sits.** Borough fixed effects absorb the trend's level, so the line is the least-squares fit to all pre-2020 coefficients. It does not pass through 0 at 2019Q4; it sits at −1.41 there. The plotted line is recovered exactly from the estimates, and the script checks this.
- **Possible follow-up, not run:** fit the trend on a later window, such as 2018Q1-2019Q4, or allow a quadratic. Section 8 gives a related bound.

## 8. HonestDiD sensitivity (`83_honestdid.R`)

**Setup**
- Package: `HonestDiD` 0.2.8 (R 4.6.1).
- Inputs: the baseline continuous event studies (section 2), using the coefficients and their CR1 borough-clustered covariance.
- The covariance is symmetrised. Its smallest eigenvalue is −3e-15, so HonestDiD warns that it is not PSD; this is numerical noise.
- The omitted period is the last pre-period, as the package requires.

**Targets (l_vec)**
- Migration: the year to June 2020 effect, and the average of 2020 and 2021.
- Rents: the 2021Q4 effect (the trough), and the average over 2020Q1-2022Q4.

**Restrictions**
- **Relative magnitudes (Δ^RM):** post-period violations are at most Mbar times the largest pre-period violation.
  - Grid: Mbar = 0, 0.25, 0.5, 0.75, 1, 1.5, 2 for the plots.
  - The breakdown is found by 4 bisection steps between the bracketing grid values, so it is precise to 0.016.
- **Smoothness (Δ^SD):** the slope of the violation path changes by at most M per period.
  - Grid: 41 values from 0 to 3 × the largest absolute second difference of the pre-period path.
  - Breakdown precision is one grid step: 0.25 for migration and 0.029 for rents.
  - M = 0 means a linear trend.
- **Breakdown value:** the smallest Mbar or M at which the robust 95% CI includes zero.

| Outcome | Target | Estimate | Original 95% CI | Breakdown Mbar (RM) | Breakdown M (SD) | SD robust CI at M = 0 |
|---|---|---|---|---|---|---|
| Migration | Year to June 2020 | -2.83 | [-4.05, -1.62] | 0.719 | 2.014 (grid step 0.252) | [-3.57, -2.00] |
| Migration | Average, years to June 2020 and 2021 | -2.25 | [-4.07, -0.43] | 0.156 | 0.504 (grid step 0.252) | [-4.52, -2.03] |
| Rents | 2021Q4 | -3.53 | [-5.00, -2.07] | 0.375 | 0.147 (grid step 0.029) | [-5.16, -4.04] |
| Rents | Average, 2020Q1-2022Q4 | -2.12 | [-3.31, -0.93] | 0.234 | 0.118 (grid step 0.029) | [-3.02, -2.25] |

**Reading**
- **Migration:**
  - The 2020 drop survives a post-period violation up to 0.72 times the largest pre-period one.
  - The 2020-21 average survives only up to 0.16 times. The largest pre-period violation, in 2016 (about 1.8 per 1,000), is large relative to the effect.
- **Rents, breakdown values:** the 2021Q4 dip breaks down at Mbar = 0.38 and M = 0.15. The 2020Q1-2022Q4 average breaks down at Mbar = 0.23 and M = 0.12. All four rent breakdown values are below 0.4, so moderate violations relative to the observed pre-trend would overturn the rent dip.
- **Rents, smoothness bound versus the trend break:**
  - The smoothness CI at M = 0 for 2021Q4 is [−5.2, −4.0]. This says the dip is larger once a linear trend is allowed, which is the opposite of section 7.
  - The two differ because the smoothness bound extrapolates the slope near the base period, where 2018-19 rises towards 0. Section 7 uses the average 2015-19 slope, which is downward.
  - Both are artefacts of the U-shaped pre-period. Neither restriction is clearly right for these data.

**Judgement calls**
- The targets were chosen at this stage, since none were set in advance.
- `gridPoints` was cut from 1,000 to 250, and the relative-magnitudes grid is coarse plus bisection. At default settings one Mbar value took 25 s for migration and about 4 minutes for rents (19 pre-periods), which made a fine grid impractical.
- The relative-magnitudes Mbar values run in parallel on 8 cores via `doParallel`.
- At large Mbar (1.5 and 2 for rents), the robust CI's lower end sits at HonestDiD's default test-inversion grid boundary (about −15). Those intervals are truncated and really wider. The breakdown values are all below 0.75, inside the range where the bounds are interior, so they are unaffected.
- HonestDiD's intervals are asymptotic, and here they rest on a 32-cluster covariance matrix.

**Outputs**
- `honestdid_breakdown.csv` (summary).
- `honestdid_<outcome>_<target>_{rm,sd}.csv` (full CI paths).
- `honestdid_<outcome>_<target>_{rm,sd}.png` (8 plots).

## 9. MSOA amenity density and correlations (`75_msoa_amenity.py`)

**Amenity density**
- I+R local units in 2019 (2011 MSOAs, from section 4 of the inventory) per 1,000 residents.
- Population: mid-2019 small-area estimates on 2011 MSOAs (Nomis NM_2010_1). This is the 2011-based series, not rebased to Census 2021. The borough measure uses rebased estimates.
- Nomis rounds unit counts to the nearest 5. The 3 MSOAs with 0 units are set to 1 unit before taking logs.
- The City's MSOA is excluded, leaving 982 MSOAs.
- `D_msoa` is log density standardised across the 982 MSOAs.

**Correlations of log amenity density with each control (N = 982)**

| Control | Overall | Within borough (borough means removed) |
|---|---|---|
| Teleworkability | 0.586 | 0.439 |
| Garden access | −0.429 | −0.320 |
| Share aged 20-39 | 0.459 | 0.378 |
| Private renting share | 0.494 | 0.420 |

**Flag check.** The within-borough correlation with teleworkability is **0.44, not above 0.6**, so no flag. Across boroughs it was 0.82. Removing borough means removes much of the confounding with teleworkability, though 0.44 remains material.

The table is in `outputs/event_study/msoa_correlations.csv`; the MSOA data are in `data/clean/msoa_amenity_controls.csv`.

## 10. MSOA house-price event study (`87_msoa_house_prices.py`), round 2: 2017-2023 (superseded by section 12)

**Matching**
- Land Registry Price Paid sales for 2017-2023 in London districts are matched by postcode to 2011 MSOAs.
- The lookup is the **NSPL - 2011 Census edition (August 2024)** (ArcGIS item `c5afedb9204a47e99559a4880feddcb1`).
- Judgement call: the current NSPL (August 2026) carries only 2021 MSOAs, and the August 2024 edition is the last with `msoa11`. It includes postcodes terminated before August 2024, so it covers every sale date in 2017-2023.
- The NSPL LA code and the MSOA's borough disagree for 0 sales.

**Sample**

| Step | Sales |
|---|---|
| Sales in London districts (all categories, including the City), 2017-2023 | 798,102 |
| Category A | 634,527 |
| Detached, semi, terraced or flat | 634,527 |
| Price ≥ £10,000 | 634,525 |
| Postcode matched to a 2011 MSOA in the 32 boroughs | 632,938 (99.75%) |
| Tenure freehold or leasehold | 632,938 |

The 1,587 sales lost at the match step are City of London Category A sales, plus 134 sales (0.02%) whose postcodes are not in the NSPL. All 982 MSOAs have sales.

**Specification**

```
log p_imt = a_m + l_{b(m),t} + Σ_{k≠2019Q4} β_k 1[t=k] D_m + Σ_c Σ_k γ_ck 1[t=k] X_cm + Z_i'φ + e
```

- a_m: MSOA fixed effects. l_bt: borough-by-quarter fixed effects (896).
- Z_i: dummies for semi-detached, terraced and flat (vs detached), new build, and leasehold (vs freehold).
- Periods: 2017Q1-2023Q4. 2019Q4 is omitted.
- Controls (standardised MSOA values) enter one at a time, then all four together.
- Inference:
  - SEs are CR1 clustered by MSOA (982 clusters).
  - Robustness: WCR bootstrap p-values clustered by borough (32 clusters, B = 9,999, Rademacher).
  - Both fixed-effect sets are nested in boroughs, so partialling them out before the borough bootstrap is exact.
- Checks against `pyfixest` (baseline): coefficients agree within 2e-15 and MSOA-clustered SEs within 1e-8 relative.

| Sample | Specs | N | MSOA clusters | K (excluding absorbed FE) |
|---|---|---|---|---|
| All quarters | baseline, +telework, +garden, +age2039, +privrent, +all | 632,938 | 982 | 32 / 59 / 140 |
| Dropping 2021Q2 and 2021Q3 | same 6 | 569,916 | 982 | 30 / 55 / 130 |

There are 12 regressions. Results are in `outputs/event_study/msoa_regression_table.csv`, with plots `es_msoa_prices_all_quarters.png` and `es_msoa_prices_drop_2021Q2_Q3.png`.

**Results**

All are estimates, with log-price effects per SD of log MSOA amenity density, within borough and quarter.

- **Pre-period (2017Q1-2019Q3, 11 quarters):**
  - The baseline coefficients run from −1.5% to 0.0%. None is significant on either the MSOA-clustered or the borough-bootstrap test.
  - They sit slightly below zero on average, so 2019Q4 looks a little high relative to 2017-19.
  - A joint test was not run.
- **Baseline post-period:**
  - Coefficients run from −0.2% to −3.2%, with 6 of 16 quarters below borough-WCB p = 0.05. For example, 2020Q4 is −1.8% (MSOA p = 0.030, WCB p = 0.021) and 2022Q4 is −3.2% (p = 0.001, WCB p < 0.001).
  - By 2023Q4 the effect is −1.7% (p = 0.10, WCB p = 0.13).
  - So, within boroughs, homes in higher-amenity MSOAs lost about 2-3% in relative price after 2020 per SD of amenity density. Part of the gap is still open at the end of 2023.
- **Controls:**
  - One at a time, each control leaves the 2022Q4 effect between −2.6% and −3.1%, all with WCB p ≤ 0.005.
  - With all four controls, 2022Q4 is −2.3% (MSOA p = 0.083, WCB p = 0.054) and no post-period coefficient is below 0.05.
- **Stamp duty check:** dropping 2021Q2 and 2021Q3 changes the remaining coefficients by at most 0.00055 log points. The stamp duty deadline sales do not drive the results.

**Judgement calls**
- **Category and price:** only Category A sales are used, and prices below £10,000 are dropped (2 sales). All 53,017 property-type "O" sales are Category B, so they were already excluded. No upper trim is applied.
- **Hedonic controls:** property type, new build and tenure enter with time-invariant coefficients, as specified.
- **Sample years:** 2017-2023 only, because those are the Land Registry files downloaded at the data stage. Extending to 2015-2016 or 2024-2025 needs those files.
- **Cached sales file:** `data/clean/msoa_sales_2017_2023.parquet` (10 MB) caches the matched sales. Delete it to rebuild from the raw files.

## 11. Things that failed or needed a workaround (round 2)

1. **Current NSPL lacks 2011 MSOAs.** The 2011 Census edition is used (section 10).
2. **Nomis small-area population.** Querying London MSOAs through the region parent (NM_2010_1) returned an empty file. The script pulls all England and Wales 2011 MSOAs (7,201 rows) and filters to London.
3. **HonestDiD run time.** The first attempt (61 Mbar values, default grid points) was stopped after about 10 minutes on the first migration target. It was replaced by the coarse grid with parallel runs and bisection (section 8).
4. **Shared estimator code.** The estimator now lives in `scripts/es_core.py`, shared by `80`, `82` and `87`. Rerunning `80_event_study.py` through it reproduces the earlier regression table: coefficients within 1e-10 and bootstrap p-values identical.

## 12. Round 3: extended MSOA house-price model (`76_msoa_distance.py`, `87_msoa_house_prices.py`)

Run 29 October 2026. This round supersedes the section 10 results. Those files are archived in `outputs/event_study/archive_round2/`. Over 2017-2023 the extended baseline matches the round 2 baseline to within 0.0009 log points.

### Sample extension

- **Data:** Land Registry yearly files for 2024, 2025 and 2026 (2026 is year to date, republished 28 October 2026). The sample now runs from 2017Q1 to **2026Q3**, the last quarter with sales in all three months.
- **Size:** N = 843,269 Category A sales in 982 MSOAs, up from 632,938. The sample-construction steps are in `msoa_sample_construction.csv`.
- **New postcodes:**
  - The 2011-MSOA NSPL (August 2024) does not contain postcodes created after August 2024.
  - Those sales are placed in the 2011 MSOA of the nearest NSPL-2011 postcode in the same borough. Coordinates come from the current NSPL (August 2026); the lookup is a KD-tree on British National Grid.
  - This affects 0.24% of the sample, mostly 2025-26 new builds. The `msoa_match` column in the sales file flags them.
- **Registration lag, a judgement call.** The latest quarters are incomplete. Category A sales against the same quarter two years earlier (`msoa_quarterly_coverage.csv`):

  | Quarter | Sales | Share of same quarter in 2024 | New-build share |
  |---|---|---|---|
  | 2026Q1 | 15,511 | 0.90 | 0.6% |
  | 2026Q2 | 13,520 | 0.70 | 0.3% |
  | 2026Q3 | 10,750 | 0.45 | 0.1% |

  - In 2024-25 the new-build share was 3-8%. New builds are registered late, so the 2026 quarters are both thinner and tilted towards resales.
  - 2026Q3 is kept as the "latest quarter", as specified. **Treat 2026 coefficients as provisional.** The summary table also shows 2025Q4 as the last well-covered quarter.
  - Separately, 2025Q1 has a spike in sales (ratio 1.76) and 2025Q2 a dip (ratio 0.72). This reflects the stamp duty threshold change of 1 April 2025, a timing effect absorbed by the borough-by-quarter fixed effects.

### New controls (each MSOA-level, standardised across the 982 MSOAs, interacted with quarter)

- **Distance (`dist`):** log straight-line distance from the MSOA's 2011 population-weighted centroid to Charing Cross (ONS PWC; Charing Cross taken as 51.50741 N, 0.12783 W, i.e. BNG E 530027, N 180381). Distances run from 0.4 to 28.5 km, median 12.2. Correlation with log amenity density is −0.55 overall and −0.40 within boroughs.
- **2019 price (`price19`):** log of the 2019 median Category A sale price in the MSOA, from the analysis sample. Sales per MSOA: minimum 4, median 77; 2 MSOAs have fewer than 10. Correlation with log amenity density is 0.54 overall and 0.31 within boroughs.
- **Property type × quarter (`ptype`):** semi-detached, terraced and flat dummies, each interacted with every quarter. The time-invariant type dummies stay in.

### Specifications

All use MSOA and borough-by-quarter fixed effects, the property type, new build and leasehold controls, 2019Q4 omitted, MSOA-clustered CR1 SEs, and borough wild cluster bootstrap p-values (B = 9,999).

| Spec | Controls × quarter | N | K |
|---|---|---|---|
| baseline | none | 843,269 | 43 |
| +telework / +garden / +age2039 / +privrent | one each | 843,269 | 81 |
| +all4 | the four census and garden controls | 843,269 | 195 |
| +dist | log distance | 843,269 | 81 |
| +all4+dist | four + distance | 843,269 | 233 |
| +ptype | property type × quarter | 843,269 | 157 |
| +price19 | log 2019 median price | 843,269 | 81 |
| +ptype+price19 | both | 843,269 | 195 |
| +everything | all four + distance + property type + 2019 price | 843,269 | 385 |
| drop 2021Q2-Q3: baseline, +everything | as above | 780,247 | 41 / 365 |

There are 14 regressions. Checked against `pyfixest` (baseline): coefficients agree within 4e-15 and SEs exactly.

**Outputs**
- `msoa_regression_table.csv` (all quarters, all specs).
- `msoa_summary_table.md` and `.csv`.
- `es_msoa_prices_all_quarters.png` (12 panels) and `es_msoa_prices_drop_2021Q2_Q3.png`.

### Summary: amenity coefficient × 100 (log points per SD of log amenity density), borough WCB p in brackets

| Sample | Specification | 2020Q4 | 2021Q4 | 2022Q4 | 2023Q4 | 2025Q4 (last well-covered) | 2026Q3 (latest) | N |
|---|---|---|---|---|---|---|---|---|
| All quarters | Baseline | -1.83 (0.022) | -1.18 (0.162) | -3.24 (0.000) | -1.64 (0.153) | -2.92 (0.000) | -4.33 (0.000) | 843,269 |
| All quarters | + teleworkability | -1.69 (0.078) | -1.72 (0.059) | -3.12 (0.004) | -1.20 (0.360) | -2.66 (0.005) | -3.96 (0.001) | 843,269 |
| All quarters | + garden access | -1.07 (0.083) | -0.12 (0.876) | -2.64 (0.002) | -1.03 (0.273) | -1.40 (0.012) | -2.71 (0.001) | 843,269 |
| All quarters | + share aged 20-39 | -1.77 (0.026) | -0.62 (0.391) | -2.69 (0.002) | -1.20 (0.274) | -2.33 (0.004) | -3.83 (0.000) | 843,269 |
| All quarters | + private renting | -1.88 (0.028) | -0.95 (0.212) | -2.85 (0.005) | -1.32 (0.233) | -2.32 (0.009) | -3.61 (0.001) | 843,269 |
| All quarters | + all four census/garden | -0.92 (0.227) | -0.56 (0.502) | -2.27 (0.052) | -0.35 (0.710) | -0.65 (0.324) | -1.78 (0.059) | 843,269 |
| All quarters | + log distance to Charing Cross | -1.41 (0.081) | -0.88 (0.296) | -2.68 (0.002) | -1.19 (0.092) | -1.66 (0.023) | -3.10 (0.001) | 843,269 |
| All quarters | + all four + distance | -0.81 (0.359) | -0.67 (0.450) | -2.08 (0.102) | -0.22 (0.788) | -0.16 (0.836) | -1.27 (0.238) | 843,269 |
| All quarters | + property type x quarter | -1.60 (0.042) | -0.57 (0.467) | -2.73 (0.001) | -1.09 (0.313) | -1.99 (0.009) | -3.53 (0.000) | 843,269 |
| All quarters | + log 2019 MSOA median price | -0.52 (0.576) | -0.68 (0.531) | -2.39 (0.012) | -0.83 (0.460) | -1.74 (0.034) | -3.07 (0.001) | 843,269 |
| All quarters | + property type + 2019 price | -0.04 (0.965) | 0.34 (0.736) | -1.55 (0.067) | 0.08 (0.942) | -0.39 (0.610) | -1.88 (0.015) | 843,269 |
| All quarters | + everything | -0.33 (0.668) | -0.33 (0.675) | -1.77 (0.135) | -0.00 (0.995) | 0.32 (0.654) | -0.87 (0.370) | 843,269 |
| Drop 2021Q2-Q3 | Baseline | -1.84 (0.025) | -1.20 (0.153) | -3.25 (0.000) | -1.65 (0.151) | -2.92 (0.000) | -4.33 (0.000) | 780,247 |
| Drop 2021Q2-Q3 | + everything | -0.31 (0.686) | -0.32 (0.685) | -1.75 (0.142) | 0.01 (0.991) | 0.34 (0.638) | -0.85 (0.380) | 780,247 |

### What changes (estimates, not causal claims)

**Does the discount reverse?** Not in the baseline.
- The high-amenity discount widens after 2023: −1.6 (2023Q4), −2.9 (2025Q4, p < 0.001), −4.3 (2026Q3, p < 0.001).
- The 2026 values carry the registration-lag caveat. But 2025Q4 is well covered and already below 2022Q4.

**Distance to Charing Cross**
- Alone, it shrinks the coefficient by about 17% in 2022Q4 (−3.24 to −2.68) and by about 43% in 2025Q4 (−2.92 to −1.66). Both stay significant.
- Added to the four census and garden controls, no post-2020 quarter has borough WCB p < 0.05. 2025Q4 is −0.16 (p = 0.84) and 2026Q3 is −1.27 (p = 0.24). The four controls alone leave only 2025Q2 significant.
- Part of the "amenity" discount is a centrality discount: within boroughs, density and centrality move together.

**Property type × quarter**
- Alone, it trims the reported coefficients by 13-52%: 16% in 2022Q4 (−2.73, p = 0.001) and 32% in 2025Q4 (−1.99, p = 0.009).
- So differential repricing of flats explains part, not most, of the discount.

**2019 median price × quarter**
- Alone, it absorbs the 2020-21 coefficients: 2020Q4 −0.52 (p = 0.58). It leaves 2022Q4 −2.39 (p = 0.012) and 2025Q4 −1.74 (p = 0.034).
- With property type × quarter as well, only 2026Q3 stays significant (−1.88, p = 0.015). With the 2019 price alone, the significant quarters are 2022Q4, 2025Q4 and 2026Q1-Q3.
- **Caveat:** with this control, the pre-period coefficients move from slightly negative to slightly positive (+0.2 to +1.4, none significant). The 2019 median is built from 2019 sales, including the omitted quarter, so it is partly a function of the outcome in the base year. That risks regression to the mean and makes it a "bad control" candidate. Read the `price19` specifications as an upper bound on how much an expensive-homes repricing channel could explain.

**Everything**
- With all controls, no post-2020 coefficient has borough WCB p < 0.05: 2022Q4 −1.77 (p = 0.14), 2025Q4 +0.32, 2026Q3 −0.87 (p = 0.37).
- K = 385 against 982 MSOAs and 32 boroughs, with controls that correlate 0.31-0.44 in absolute value with the treatment within boroughs. This specification has little independent amenity variation left.

**Stamp duty deadline check:** dropping 2021Q2-Q3 moves the baseline and full-specification coefficients by at most 0.035 log points × 100.

**Pre-period:** no 2017Q1-2019Q3 coefficient has a borough WCB p below 0.05 in any of the 14 specifications. Single MSOA-clustered rejections appear in 4 specifications.

### Judgement calls (round 3)

1. **Sample end.** It runs through 2026Q3, the latest calendar-complete quarter, as specified, despite the registration lag (above). 2025Q4 is reported alongside it.
2. **New postcodes.** Post-August-2024 postcodes are placed by nearest NSPL-2011 postcode, rather than by an OA21-to-OA11 lookup. A boundary-polygon match would be more exact but needs another download; 0.24% of sales are affected.
3. **2019 median price.** It is unweighted, uses all Category A D/S/T/F sales, and comes from the same sample as the outcome (see the caveat above).
4. **Charing Cross point and distance.** Charing Cross is the statue of Charles I. Distance is straight-line, not travel time.
5. **Stamp duty rerun.** It covers only the baseline and +everything specifications, to save run time. Section 10 showed the check moves nothing in any specification.

### Run-time management

- `run_all.py` now takes `--only STEP ...`, `--from STEP` and `--force-honestdid`.
- HonestDiD is skipped when the SHA-256 of its inputs matches `outputs/event_study/honestdid_cache.json`. The inputs are the R script, the baseline continuous coefficients rounded to 10 decimals, and the two covariance files.
- The cache was seeded on 29 October 2026 from the inputs that produced the current HonestDiD outputs (the full rebuild of 28 October). Rerunning `80_event_study.py` leaves the hash unchanged.
- This round ran only `76_msoa_distance.py` and `87_msoa_house_prices.py`, plus `run_all.py --only 76_msoa_distance.py 83_honestdid.R` to test the runner and the skip. There was no full rebuild.

## 13. Round 4: headline specifications, return measure, price-to-rent and pound values

Run 29 October 2026. Only the changed scripts were run: `82_rent_trend_break.py`, `87_msoa_house_prices.py`, the new `88_price_to_rent.py` and `89_pound_values.py`, and the shared helpers `es_core.py` and `plot_events.py`. There was no full rebuild; HonestDiD is unchanged and cached.

**Division of roles.**
- House prices measure the closure-period effect, before interest rates began rising.
- Rents measure the return once venues reopened, because rents price the use of a home with financing largely stripped out.

### 13.1 Headline house-price specification

```
log p_imt = a_m + l_{b(m),t} + Σ_{k≠2019Q4} β_k 1[t=k] D_m
            + Σ_k 1[t=k] (γ1_k dist_m + γ2_k telework_m + γ3_k garden_m) + Σ_k 1[t=k] type_i'ψ_k + Z_i'φ + e
```

- **Controls, each interacted with quarter:** log distance to Charing Cross, teleworkability, garden access, and property type.
- **Excluded:** age 20-39 and private renting, which are partly outcomes of amenity-driven sorting.
- **Data:** N = 843,269 sales, 982 MSOAs, K = 271 (excluding absorbed fixed effects), 2017Q1-2026Q3, 2019Q4 omitted.
- **Main result:** the average of the eight 2020Q1-2021Q4 coefficients (the closure window), tested as a linear contrast. It uses the same MSOA-clustered CR1 SE and borough WCR bootstrap as the single coefficients.
- **Checks:** the contrast code reproduces the plain average and its delta-method SE exactly. Its bootstrap p equals the single-coefficient p of an equivalent reparameterised regression.

**Main house-price result**
- Closure-window average: **−0.28 log points × 100** per SD of log MSOA amenity density.
- MSOA-clustered 95% CI −1.78 to +1.21; borough WCB p = 0.730.
- **This is a null result.** No quarter in the headline specification has borough WCB p < 0.05. The largest is 2022Q4 at −2.01 (p = 0.090).
- For comparison:
  - The baseline closure-window average is −1.08 (p = 0.081).
  - Distance alone gives −0.86 (p = 0.18); property type alone gives −0.78 (p = 0.22).
  - Almost all of the baseline closure discount is absorbed by the headline controls.
- Every quarter for the headline and mediator-check specifications is in `outputs/event_study/msoa_headline_table.md` (CSV: `msoa_headline_table.csv`). The plot is `es_msoa_headline.png`.

### 13.2 Mediator robustness

- **Specification:** the headline model plus age 20-39 and private renting, each × quarter (K = 347).
- **Result:** closure-window average −0.40 (CI −1.94 to +1.14, WCB p = 0.629). Quarter by quarter it is within 0.33 of the headline, and no quarter has WCB p < 0.05.
- **Mediator note.** The 2011 shares of residents aged 20-39 and of households renting privately are plausibly outcomes of amenity-driven sorting: young renters choose high-amenity areas. Controlling for them may absorb part of the amenity effect it is meant to measure (a "bad control" or mediator). The headline therefore leaves them out, and this column is reported only as a robustness check. Adding them barely moves the estimates here.

### 13.3 Rents as the return measure

This uses the borough rent trend-break model (section 7: baseline continuous treatment, linear pre-2020 trend projected forward). Both averages are linear contrasts of the deviations, with CR1 SEs clustered by borough and WCR bootstrap (B = 9,999). Outputs: `rent_return_summary.csv` and the window rows of `rent_trend_break.csv`.

| Window | Quarters | Average deviation (100 × log points per SD of borough log amenity density) | Borough-clustered 95% CI | WCB p |
|---|---|---|---|---|
| 2022Q1-2026Q3 | 19 | +3.43 | 1.15 to 5.71 | 0.029 |
| Mid-2023 onwards, 2023Q3-2026Q3 | 13 | +4.39 | 1.82 to 6.97 | 0.015 |

**Judgement calls**
- "Mid-2023" is taken as 2023Q3, the first quarter starting after mid-year.
- The latest quarter is 2026Q3. PIPR revises recent months, so 2026 is marked provisional.

**Caveat: the return result depends on the projection.** The pre-2020 rent path is U-shaped:
- It falls from 2015 to mid-2018, then rises to 2019Q4.
- A single linear trend fitted to 2015Q1-2019Q4 slopes downward (−0.20 per quarter) and keeps falling after 2020. The positive post-2022 deviations are measured against that falling line.
- In the raw event study (no trend), high-amenity rents are still below their 2019Q4 relative level in 2026.
- HonestDiD's smoothness bound, which extrapolates the slope near 2019, implies the opposite sign (section 8).
- So the size, and possibly the sign, of the rent return rests on the linear projection of a U-shaped pre-period.

### 13.4 Price-to-rent divergence (`88_price_to_rent.py`)

- **Ratio:** borough median Category A sale price ÷ (12 × PIPR average monthly rent), quarterly, 2017Q1-2026Q3, all 32 boroughs. The smallest borough-quarter has 145 sales.
- **Groups:** the within-zone amenity median split. Inner London has 6 high and 7 low boroughs; Outer London has 9 high and 10 low. Lines are unweighted means of borough ratios.
- **Plot:** `price_to_rent.png` shows levels (years of rent) and an index (each borough's 2019 average = 100). The data are in `price_to_rent_groups.csv` and `data/clean/price_to_rent_borough_quarter.csv`.

Index (2019 = 100), selected quarters:

| Group | 2019Q4 | 2021Q4 | 2022Q4 | 2023Q4 | 2025Q4 | 2026Q3 (provisional) |
|---|---|---|---|---|---|---|
| Inner, high amenity | 102.2 | 113.8 | 98.9 | 92.4 | 74.5 | 63.9 |
| Inner, low amenity | 98.9 | 103.9 | 102.0 | 89.4 | 77.1 | 74.0 |
| Outer, high amenity | 99.3 | 105.8 | 104.0 | 94.6 | 84.2 | 83.0 |
| Outer, low amenity | 100.8 | 102.0 | 107.8 | 98.2 | 88.4 | 87.6 |

**Reading**
- Price-to-rent ratios fall everywhere after 2022, as rents rise and prices stall. The fall is steepest in Inner high-amenity boroughs.
- Inner high-amenity boroughs also show the sharpest spike in 2021Q3-Q4.

**Caveats**
- Neither side is quality-adjusted. The 2021Q3 spike in Inner high-amenity boroughs reflects the mix of homes sold after the stamp duty deadline (section 4). The 2025Q1-Q2 swing reflects the April 2025 threshold change.
- PIPR rents cover all tenancies (a stock measure), while sale prices are new transactions (a flow measure).
- 2026 sales are under-registered (section 12).

### 13.5 Pound values (`89_pound_values.py`, `pound_values.csv`)

| Measure | Effect | Base | Change in pounds (95% CI) |
|---|---|---|---|
| House price, closure-window average, headline spec | −0.28 log points × 100 (WCB p = 0.730) | Median 2019 London sale price £475,000 (83,672 Category A D/S/T/F sales, 32 boroughs) | **−£1,350 (−£8,390 to +£5,800)** |
| Monthly rent, average deviation 2023Q3-2026Q3 | +4.39 log points × 100 (WCB p = 0.015) | Median London monthly rent, October 2018 to September 2019, £1,450 (ONS/VOA Private Rental Market Statistics, Table 1.7, all categories) | **+£65 a month (+£27 to +£105)** |

**Conversion:** (exp(b) − 1) × base, applied to the point estimate and to each CI bound.

**Judgement calls**
- **The two "one SD" units differ.**
  - For house prices, 1 SD of log density across 982 MSOAs is 0.817 log points: 2.26 times the density.
  - For rents, 1 SD across 32 boroughs is 0.567 log points: 1.76 times the density.
  - The two pound figures are therefore not per the same amenity difference.
- **2019 median rent source.** PIPR publishes average (mean) rents, not medians. The London median comes from the last pre-pandemic ONS Private Rental Market Statistics year (October 2018 to September 2019, VOA lettings data). It is a different source from the PIPR index the deviation comes from.
- **Median price.** The 2019 median price is from the analysis sample (Category A, D/S/T/F, 32 boroughs, City excluded).
- **Uncertainty.** The house-price pound interval uses the MSOA-clustered CI; the borough bootstrap gives p = 0.73, and no bootstrap interval was computed.

### 13.6 Plot markers

The headline house-price plot (`es_msoa_headline.png`), the rent trend-break plot (`rent_trend_break.png`) and the price-to-rent plot carry dotted lines:

| Tag | Date | Event | Colour |
|---|---|---|---|
| A | 4 July 2020 | First reopening | Green |
| B | 17 May 2021 | Indoor hospitality reopens | Green |
| C | 19 July 2021 | Remaining restrictions end | Green |
| D | 16 December 2021 | First Bank Rate rise | Violet |
| E | 23 September 2022 | Mini-budget | Violet |

- Dates are placed at their position within the quarter.
- The 2026 quarters are hatched and labelled provisional.
- The helper is `scripts/plot_events.py`.

### 13.7 Implications for the framing (estimates; flagged once)

- Under the headline controls, **the house-price data show no closure-period amenity discount**: −0.28, CI ±1.5. The closure-window premise for prices is not supported in this specification.
- The baseline closure discount (−1.08) is mostly explained by centrality and property mix.
- The rent "return" is positive and significant, but only relative to the linear pre-trend projection (section 13.3).

## 14. Round 5: consumption access instead of own-MSOA density (`77_msoa_access.py`, `92_msoa_access_event_study.py`)

Run 29 October 2026. Only the new scripts were run. No existing script changed apart from `run_all.py`, which now lists the two new steps.

### 14.1 The access measure

**Geography: MSOA**
- MSOA is the finest level Nomis publishes for UK Business Counts (NM_141_1 has no LSOA or point data; see section 9), so the MSOA counts are used and OpenStreetMap was not needed.
- 2019 I+R local units (divisions 55-56 and 90-93) were pulled for **all 7,201 England and Wales MSOAs**, not just London. Rings and access for outer-London MSOAs therefore include units across the GLA boundary.
- The London counts match the earlier London-only pull exactly; the script checks this.

**Placement.** Each MSOA's units are placed at its 2011 population-weighted centroid (ONS PWC, British National Grid).
- **Judgement call:** this treats every unit in an MSOA as sitting at one point.
- The median distance from an MSOA centroid to the next is 0.78 km. 217 of 982 MSOAs have no other centroid within 1 km, so for them the 0-1 km ring is just their own units.
- The 0-1 km ring is therefore close to own-MSOA counts, and ring edges are coarse.

**Measures, for each of the 982 analysis MSOAs (d is centroid distance in km)**
- **Rings:** units at 0-1 km, 1-2 km and 2-5 km. Own units count in the 0-1 km ring.
- **Access index:** A(λ) = Σ_j units_j · exp(−d_ij / λ), with λ = 1.5 km (main) and 1 km and 3 km (robustness).
- Medians: A(1.5) = 415 units, 0-1 km ring = 93, 1-2 km = 270, 2-5 km = 1,815. Three MSOAs have an empty 1-2 km ring.

**Regressors (judgement call)**
- The access index enters as **standardised log A(λ)**, matching the log form of the own-density treatment, because the levels are heavily right-skewed. One SD of log A(1.5) is 0.91 log points, about 2.5 times the access.
- Rings enter as **standardised log(1 + count)**, all three together.
- Counts are not divided by population. Access is the number of venues within reach, not venues per resident.

Outputs: `data/clean/msoa_access_2019.csv` and `outputs/event_study/msoa_access_correlations.csv`.

### 14.2 Correlation with distance to Charing Cross: **flagged**

| Measure | vs log distance to Charing Cross: overall | within borough | vs log own density: within borough |
|---|---|---|---|
| log access, λ = 1.5 km | −0.954 | **−0.850** | 0.448 |
| log access, λ = 1 km | −0.941 | **−0.814** | 0.562 |
| log access, λ = 3 km | −0.945 | **−0.825** | 0.335 |
| log(1 + 0-1 km ring) | −0.808 | −0.515 | 0.560 |
| log(1 + 1-2 km ring) | −0.845 | −0.573 | 0.193 |
| log(1 + 2-5 km ring) | −0.936 | **−0.742** | 0.243 |

**FLAG: the within-borough correlation between the access index and log distance to Charing Cross is −0.85, which exceeds 0.7 in absolute value.** The same holds for all three decay parameters and for the 2-5 km ring.
- Within a borough, access to venues is mostly a function of how central the MSOA is.
- With distance × quarter in the model, the access coefficients rest on the remaining 28% of the variance (1 − 0.85²). Their standard errors are about 3-4 times those of own density: a mean quarterly SE of 3.6 against 1.0, in log points × 100.

### 14.3 Specifications

All specifications use:
- the headline controls from section 13.1 (log distance to Charing Cross, teleworkability, garden access and property type, each × quarter);
- MSOA and borough-by-quarter fixed effects, plus new build and leasehold dummies;
- 2017Q1-2026Q3 with 2019Q4 omitted;
- N = 843,269 and 982 MSOAs;
- MSOA-clustered CR1 SEs and borough WCR bootstrap (B = 9,999).

| Spec | Treatment × quarter | K |
|---|---|---|
| own_density | standardised log own-MSOA density (the round 4 headline, re-run for the lagged window) | 271 |
| access_l15 | standardised log access, λ = 1.5 km (main) | 271 |
| access_l10 | λ = 1 km | 271 |
| access_l30 | λ = 3 km | 271 |
| rings | the three ring terms together | 347 |

The own_density re-run reproduces the section 13 headline closure average (−0.28, p = 0.730).

**Outputs**
- `msoa_access_regression_table.csv` (every quarter and window average).
- `msoa_access_table.md` (every quarter with borough WCB p, plus the window averages).
- `es_msoa_access.png`.

### 14.4 Closure-window averages, with the completion lag

**Land Registry dates are completion dates**, not exchange or agreement dates. Prices agreed in one quarter often complete in the next, typically several weeks to a few months later. A one-quarter-lagged window (2020Q2-2022Q1) is therefore reported next to the original closure window (2020Q1-2021Q4).

Values are log points × 100 per SD of the treatment, with MSOA-clustered 95% CI and borough WCB p.

| Treatment | 2020Q1-2021Q4 average | Lagged 2020Q2-2022Q1 average |
|---|---|---|
| Own-MSOA density | −0.28 (−1.78 to 1.21; p = 0.730) | −0.33 (−1.89 to 1.23; p = 0.697) |
| **Access, λ = 1.5 km (main)** | **−0.75 (−6.27 to 4.78; p = 0.703)** | **−1.60 (−7.85 to 4.66; p = 0.530)** |
| Access, λ = 1 km | +0.25 (−4.13 to 4.62; p = 0.878) | −0.37 (−5.23 to 4.49; p = 0.837) |
| Access, λ = 3 km | −1.22 (−6.85 to 4.42; p = 0.611) | −1.92 (−8.25 to 4.41; p = 0.554) |
| Rings: 0-1 km | +1.69 (−0.36 to 3.74; p = 0.154) | +1.58 (−0.49 to 3.65; p = 0.177) |
| Rings: 1-2 km | −0.08 (−1.54 to 1.39; p = 0.939) | −0.06 (−1.55 to 1.44; p = 0.959) |
| Rings: 2-5 km | −1.22 (−5.82 to 3.37; p = 0.592) | −1.97 (−7.05 to 3.10; p = 0.505) |

**Reading (estimates)**
- **No window average is distinguishable from zero**, whichever treatment or window is used.
- The access-index point estimates are slightly more negative than own density, and more so in the lagged window. But their intervals span about ±6 log points, so the data cannot separate an access effect of a few percent from zero.
- Single quarters with borough WCB p < 0.05:
  - Access λ = 1.5 km: 2021Q4, −6.43 (p = 0.034).
  - Access λ = 3 km: 2021Q4, −6.06 (p = 0.043) and 2026Q2, +5.58 (p = 0.009, provisional).
  - 0-1 km ring: 2020Q3, +3.59 (p = 0.003) and 2020Q4, +2.39 (p = 0.036). It is also significant in two pre-period quarters (2017Q4, 2018Q3), which signals noise rather than an effect.
  - With about 38 quarters per treatment, one or two rejections at 5% are expected by chance.
- **Conclusion for this specification.** Swapping own density for consumption access does not reveal a closure-period house-price effect. Within boroughs, access is too collinear with centrality (section 14.2) for the model to tell an access effect apart from a distance effect.

### 14.5 Judgement calls (round 5)

1. **Geography.** MSOA counts at population-weighted centroids, not point data. OpenStreetMap was not used because Nomis has MSOA counts (as the specification allowed). Point data could sharpen the 0-1 km ring, but would bring its own coverage and classification problems.
2. **Sources from all of England and Wales.** This avoids edge effects at the GLA boundary.
3. **Log forms.** Standardised log access and log(1 + ring count), for skewness and comparability with the log own-density treatment.
4. **Lagged window.** One quarter (2020Q2-2022Q1), as specified. The completion lag varies by sale, and no exchange-date data are available to estimate it.
5. **Distance stays in the model.** The headline controls keep log distance to Charing Cross, as specified, despite the −0.85 correlation. Dropping it would make the access coefficient largely a centrality coefficient.

## 15. Round 6: age heterogeneity in migration and the reversal decomposition (`94_migration_age.py`, `95_reversal.py`)

Run 29 October 2026. Only the two new scripts were run, and `run_all.py` lists them.

**Thesis focus.** The thesis measures the value of consumption variety, identified through the reversal after reopening.

### 15.1 Age groups (`94_migration_age.py`)

**Source**
- The London rows of the ONS detailed origin-destination files already downloaded and cached by `10_migration.py` (`raw/ons_internal_migration/*.london.parquet`), by single year of age and sex.
- Years ending June 2015-2025. Nothing was re-downloaded.

**Outcome**
- Net moves with the rest of the UK: moves in from outside Greater London (the 33 GLA authorities, City included) minus moves out to it, with Scotland and Northern Ireland included.
- Expressed per 1,000 mid-2019 residents **of the same group**.
- Population: ONS mid-2019 estimates rebased to Census 2021 (Nomis NM_2002_1, single year of age, ages 0-89 and 90+), saved as `raw/nomis/mye_population_mid2019_single_age_london.csv`.

**Check:** summed over ages, the borough-year net equals `nonlondon_net` in `migration_panel_borough_year.csv` for all 352 borough-years. The all-ages event study reproduces section 2 exactly (2020: −2.83, p = 0.002).

**Group definitions**

| Group | Ages included |
|---|---|
| 20-29 | 20 to 29 |
| 30-39 | 30 to 39 |
| Family proxy | **0-15 together with 30-49** (children plus the parents' likely age band), summed into one group |
| 50+ | 50 and over (the single-age migration data run to 107) |

**Judgement calls**
- **Overlap.** The family proxy overlaps the 30-39 group, so the two are not independent.
- **Missing ages.** Ages 16-19 and 40-49 appear only in "all ages" and, for 40-49, in the family proxy.
- **Age timing.** Age is ONS's age at 30 June of the year ending, which can be one year older than age at the move.

**Event study:** the borough baseline (borough and year fixed effects, standardised log borough amenity density × year, 2019 omitted, CR1 clustered by borough, WCR bootstrap B = 9,999). N = 352 for each group.

**Outputs**
- `outputs/event_study/migration_age_event_study.csv` and `.md`.
- `migration_age_event_study.png`, with the four groups on one plot.
- `data/clean/migration_net_by_age_group.csv`.

**Coefficient per SD of log borough amenity density** (borough WCB p in brackets)

| Year to June | All ages | 20-29 | 30-39 | Family proxy | 50+ |
|---|---|---|---|---|---|
| 2020 | −2.83 (0.002) | **−6.89 (0.002)** | −2.44 (0.001) | −1.65 (<0.001) | −1.63 (<0.001) |
| 2021 | −1.67 (0.236) | +1.64 (0.603) | −4.65 (0.053) | −2.96 (0.084) | −1.83 (0.001) |
| 2022 | +1.66 (0.085) | **+7.50 (0.005)** | −0.30 (0.760) | −0.57 (0.469) | −0.00 (0.998) |
| 2023 | −0.85 (0.048) | −2.96 (0.019) | −1.06 (0.079) | −0.55 (0.189) | −0.18 (0.491) |
| Mean outcome, 2015-2019 | −11.1 | +22.5 | −24.6 | −21.2 | −11.6 |

**Reading (estimates)**
- **20-29 year olds** carry the reversal: a large relative outflow from high-amenity boroughs in the year to June 2020, then a larger relative inflow in the year to June 2022.
- **30-39 year olds and the family proxy** leave in 2020-21 and do not come back in 2022.
- **50+:** small, persistent outflows in 2020-21.
- **Pre-period:** for 30-39, the family proxy and 50+, the 2015-2016 coefficients are also significantly negative. The pre-period is not flat for these groups.

### 15.2 Reversal decomposition (`95_reversal.py`)

**Model**

```
y_it = a_i + l_t + b_C D_i 1[t ∈ C] + b_R D_i 1[t ∈ R] + b_L D_i 1[t ∈ L] (+ headline controls for house prices) + e_it
```

- The reference is **all periods before the closure period, pooled**, not a single base period.
- b_R − b_C is tested as a linear contrast with the same WCR bootstrap. Bootstrap clusters are boroughs in every model.

**Period definitions**

| Outcome | Closure C | Reopening R | Later L | Reference |
|---|---|---|---|---|
| Migration (years to June) | 2020, 2021 | 2022 | 2023-2025 | 2015-2019 |
| Rents, MSOA house prices (quarters) | 2020Q2-2021Q2 | 2021Q3-2022Q4 | 2023Q1-2026Q3 | up to 2020Q1 |

**Specifications**
- **Migration (all ages and the four groups):** borough-year, N = 352, CR1 clustered by borough.
- **Rents:** 100 × log quarterly PIPR index, borough-quarter, N = 1,504, CR1 clustered by borough.
  - Also shown, as a secondary row: a version with D × linear time added, which projects the pre-2020 trend forward as in section 7.
- **MSOA house prices:** the section 13.1 headline specification, with the D × quarter terms replaced by the three D × period terms.
  - Distance, teleworkability, garden and property type stay interacted with every quarter, plus MSOA and borough-by-quarter fixed effects.
  - N = 843,269. SEs CR1 clustered by MSOA (982); bootstrap clustered by borough (32).
  - 2026 quarters (inside L) are provisional.

**Results.** Coefficient per SD of standardised log amenity density, borough WCB p in brackets. Borough density is used for migration and rents, MSOA density for house prices. House prices are in log points × 100. Full results with CIs are in `outputs/event_study/reversal_decomposition.csv` and `.md`.

| Outcome | Closure b_C | Reopening b_R | Later b_L | **b_R − b_C** (95% CI) |
|---|---|---|---|---|
| Migration, all ages | −1.81 (0.006) | +2.10 (0.013) | −0.03 (0.919) | **+3.91 (2.22 to 5.60; p < 0.001)** |
| Migration, 20-29 | −3.27 (0.049) | +6.86 (<0.001) | −3.28 (0.015) | **+10.13 (4.92 to 15.33; p < 0.001)** |
| Migration, 30-39 | −2.31 (0.080) | +0.92 (0.379) | +1.08 (0.048) | **+3.24 (1.50 to 4.98; p = 0.004)** |
| Migration, family proxy | −1.26 (0.213) | +0.47 (0.587) | +1.09 (0.013) | **+1.73 (0.75 to 2.71; p = 0.002)** |
| Migration, 50+ | −1.15 (<0.001) | +0.58 (0.221) | +0.65 (0.082) | **+1.73 (1.14 to 2.32; p = 0.004)** |
| Rents, no trend | −1.93 (0.003) | −3.50 (<0.001) | −1.67 (0.008) | **−1.57 (−2.33 to −0.81; p < 0.001)** |
| Rents, pre-trend projected (secondary) | +0.01 (0.985) | −0.74 (0.272) | +2.66 (0.042) | −0.75 (−1.54 to 0.04; p = 0.085) |
| MSOA house prices, headline | +0.15 (0.751) | −0.39 (0.276) | +0.03 (0.959) | −0.54 (−1.47 to 0.38; p = 0.257) |

**Reading (estimates)**
- **Migration reverses.** Reopening is significantly above closure for every age group. The reversal is about three times larger for 20-29 year olds (+10.1 per 1,000) than for all ages (+3.9).
  - For 20-29 year olds the reversal is temporary: the later period returns to −3.3.
  - For 30-39, the family proxy and 50+, the "reversal" is mostly a smaller closure outflow ending. Their reopening coefficients alone are not significant.
- **Rents do not reverse in this decomposition.** Without a trend, the high-amenity rent gap is deeper in reopening than in closure (b_R − b_C = −1.57). With the pre-2020 trend projected forward, closure and reopening are both near zero and only the later period is positive (+2.66, p = 0.042).
  - So the rent "return" appears after 2023, not at reopening, and only relative to the projected trend (sections 7 and 13.3).
- **House prices:** under the headline controls, every period coefficient and the difference are near zero. Prices show neither a closure effect nor a reversal.
- **Overall:** the reopening reversal that identifies the value of consumption variety shows up clearly in **migration of 20-29 year olds**. It does not show up in rents (at reopening) or in house prices.

**Judgement calls**
1. **Pooled reference.** The reference is the pooled pre-period, as the three-period model implies. For migration the pre-period is not flat: 2015-2016 coefficients are negative for 30-39, the family proxy and 50+, and +5.1 for 20-29 in 2015. Pooling shifts the reference level relative to the single-base-year event studies.
2. **Rents and 2020Q1.** 2020Q1 sits in the reference period because the closure period starts 2020Q2 (lockdown began 23 March 2020).
3. **Mixed years in the migration periods.** The year to June 2020 is in the closure period but contains about 9 pre-pandemic months. The year to June 2022 (reopening) contains July-December 2021 as well as 2022.
4. **Trend-adjusted rent row.** It is an addition to the specification. It is reported because the no-trend rent result is dominated by the pre-2020 trend.
5. **Units.** House-price coefficients are in log points; the table shows them × 100. The house-price treatment SD (MSOA) differs from the borough SD used for migration and rents (section 13.5).

## 16. Round 7: triple difference, student checks and hospitality-worker control (`96_age_ddd.py`)

Run 29 October 2026. Only the new script was run, and `run_all.py` lists it.

**Outputs**
- `outputs/event_study/age_ddd_student_hospitality.md` and `.csv`.
- `age_ddd.png`.
- `data/clean/migration_net_by_age_group_extended.csv`.
- `data/clean/borough_student_hospitality_2011.csv`.

**Common setup**
- Outcome and treatment:
  - Outcome: net moves with the rest of the UK per 1,000 mid-2019 residents of the age group (section 15.1), for 32 boroughs, years to June 2015-2025.
  - Treatment D: standardised log borough amenity density.
- Inference: CR1 clustered by borough, plus WCR bootstrap clustered by borough (Rademacher, B = 9,999).
- The rebuilt age panel reproduces the section 15 panel for the 20-29, family-proxy and 50+ groups.

### 16.1 Triple difference

**Model.** The young group (20-29, Y = 1) is stacked with one comparison group: the family proxy (0-15 plus 30-49), or 50+. N = 704 (32 boroughs × 2 groups × 11 years).

```
y_bgt = a_bt + c_gt + e_bg + Σ_{k≠2019} θ_k · D_b · Y_g · 1[t = k] + e_bgt
```

- **Fixed effects:**
  - a_bt: borough × year.
  - c_gt: age group × year.
  - e_bg: borough × age group. This was **added beyond the specification as written**, because it is required: without it, the θ_k would absorb the time-invariant level difference in D × Y and would not be measured relative to 2019. Young adults have positive net inflows on average and the comparison groups negative.
- **Period version:** θ_C, θ_R and θ_L on D × Y × period, with the pooled 2015-2019 reference (closure 2020-21, reopening 2022, later 2023-25), and θ_R − θ_C.
- **Yearly version:** it also reports the 2015-2018 average of θ_k as a summary pre-trend test, plus period averages of the yearly coefficients.

**Results** (per 1,000 group residents per SD; borough WCB p)

| | 2015 | 2016 | 2017 | 2018 | 2020 | 2021 | 2022 | 2023 | 2024 | 2025 | Pre-average 2015-18 | Reopening − closure (yearly) |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| 20-29 vs family proxy | **+7.17 (0.026)** | +1.35 (0.341) | −0.26 (0.819) | +0.19 (0.881) | −5.24 (0.002) | +4.60 (0.014) | +8.08 (<0.001) | −2.41 (0.021) | −4.04 (0.001) | −1.59 (0.224) | +2.11 (0.109) | +8.40 (<0.001) |
| 20-29 vs 50+ | +6.04 (0.077) | +0.07 (0.963) | −0.53 (0.645) | +0.55 (0.640) | −5.26 (0.002) | +3.47 (0.426) | +7.50 (<0.001) | −2.78 (0.020) | −3.67 (0.003) | −1.65 (0.181) | +1.53 (0.220) | +8.40 (<0.001) |

**Period model (pooled 2015-19 reference)**

| Comparison | Closure | Reopening | Later | Reopening − closure |
|---|---|---|---|---|
| vs family proxy | −2.01 (0.015) | +6.39 (<0.001) | −4.37 (<0.001) | +8.40 (<0.001) |
| vs 50+ | −2.12 (0.241) | +6.28 (<0.001) | −3.93 (0.011) | +8.40 (<0.001) |

**Pre-period, stated plainly**
- 2016-2018 are small and insignificant against both comparison groups.
- **2015 is large and positive**: +7.2 (p = 0.026) against the family proxy, +6.0 (p = 0.077) against 50+.
- The 2015-2018 average is +2.1 (p = 0.11) and +1.5 (p = 0.22).
- Why the comparison groups don't drive this:
  - The comparison groups' negative 2015-2016 coefficients (section 15.1) do not create a pre-trend in the triple difference, because both groups move together relative to 2019.
  - The 2015 gap comes from the young group itself (its 2015 single-group coefficient is +5.1, p = 0.11).
- Because 2015 is in the pooled reference, the period-model closure coefficient (−2.0) is more negative than the yearly closure average relative to 2019 (−0.3 and −0.9).

**Reading (estimates)**
- Relative to families and to over-50s in the same borough and year, young adults left high-amenity boroughs in the year to June 2020 (−5.2) and returned strongly in the year to June 2022 (+7.5 to +8.1).
- Against the family proxy the return already starts in 2021 (+4.6, p = 0.014).
- After 2022 the young-adult gap turns negative again (−2.4 to −4.0 in 2023-24).
- Borough-level shocks common to all ages are absorbed by the borough × year effects, so the reversal is not a borough-wide migration swing.

### 16.2 Student check

**Student share.** 2011 Census KS501EW (Nomis NM_623_1): "Schoolchildren and full-time students: age 18 and over" ÷ all usual residents aged 16 and over. Borough mean 8.1%, range 3.4-14.9%. It correlates 0.43 with D.
- **Judgement call:** this is the closest available Census measure of full-time students. KS501EW does not split students by age within 18+.

**Specifications** (single-group event studies; borough and year FE; D × year; 2019 omitted):
- 20-24, 25-29, and 20-29 for reference.
- (a) Baseline.
- (b) Plus standardised student share × year.
- (c) Dropping the five boroughs with the highest student share: Newham 14.9%, Camden 13.6%, Tower Hamlets 12.1%, Southwark 11.5%, Islington 10.7%. That leaves N = 297 and 27 clusters; the bootstrap uses 27-cluster weights.
- The reversal decomposition is given as yearly-coefficient contrasts: the closure average (2020-21) and reopening (2022) minus the closure average.

| Age | Specification | 2020 | 2022 | Reopening − closure |
|---|---|---|---|---|
| 20-29 | Baseline | −6.89 (0.002) | +7.50 (0.005) | +10.13 (<0.001) |
| 20-29 | + student share × year | −6.83 (0.009) | **+4.59 (0.048)** | +7.31 (0.003) |
| 20-29 | Drop top-5 student boroughs | −7.42 (0.013) | +6.09 (0.070) | +8.53 (0.003) |
| 20-24 | Baseline | −7.04 (0.003) | +14.06 (<0.001) | +15.60 (<0.001) |
| 20-24 | + student share × year | −7.88 (0.007) | **+9.13 (0.033)** | +10.97 (0.005) |
| 20-24 | Drop top-5 student boroughs | −7.86 (0.010) | +11.49 (0.062) | +12.67 (0.003) |
| 25-29 | Baseline | −6.89 (0.002) | +2.05 (0.131) | +5.63 (0.002) |
| 25-29 | + student share × year | −6.14 (0.008) | +0.80 (0.491) | +4.29 (0.010) |
| 25-29 | Drop top-5 student boroughs | −7.14 (0.013) | +1.73 (0.395) | +5.20 (0.019) |

**Reading (estimates)**
- **The 2020 outflow is stable** across all checks (−6.1 to −7.9) and similar for 20-24 and 25-29.
- **The 2022 return is concentrated among 20-24 year olds** and is partly a student effect:
  - The student-share control cuts it by about 35-40% (20-24: 14.1 to 9.1; 20-29: 7.5 to 4.6).
  - Dropping the top-5 student boroughs cuts it by about a fifth (20-24: 14.1 to 11.5; 20-29: 7.5 to 6.1).
  - It stays positive and significant, or close to it.
- **For 25-29 year olds there is no significant 2022 return.** Their "reversal" is mostly the 2020 outflow ending.
- **Timing confound.** The year to June 2022 contains the autumn 2021 term, when universities returned to in-person teaching. This coincides with the reopening of hospitality, so part of the young-adult return reflects students coming back to campus boroughs. The student control removes the part that scales with student share; it cannot remove a return that lines up exactly with amenity density.
- The 2015 young-adult coefficient is positive in every check: +5.1 to +6.2 for 20-29, +9.3 to +10.7 for 20-24 (p < 0.05 in two of three) and +1.3 to +2.9 for 25-29.

### 16.3 Hospitality-worker control

**Control.** 2011 Census DC6110EW (industry by sex by age; Nomis NM_771_1): the share of **employed residents aged 16-34** working in accommodation and food services (I) **or in "R, S, T, U: Other"**.
- **Judgement calls:**
  - DC6110EW does not publish arts, entertainment and recreation (R) separately by age. The finest available group combines R with other services (S, which includes hairdressing and repair), households as employers (T) and extraterritorial bodies (U).
  - The denominator is employed residents aged 16-34, the table's universe, rather than all residents aged 16-34.
  - An **I-only** variant is reported as a check.
- **Values:** borough mean 14.8% (11.0-20.5%). It correlates 0.08 with D; the I-only share correlates −0.11.
- **Purpose.** This control is meant to absorb the **income shock to young hospitality and leisure workers**: lockdowns cut their jobs and pay, which could push them out of (or keep them in) London for reasons separate from losing access to consumption variety. It enters as share × year in the young-adult event study, and as share × young × year in the triple difference (a borough-level share × year would be absorbed by the borough × year fixed effects).

| Model | Control | 2020 | 2022 | Reopening − closure |
|---|---|---|---|---|
| 20-29 event study | None | −6.89 (0.002) | +7.50 (0.005) | +10.13 (<0.001) |
| 20-29 event study | + I and R-U share × year | −6.69 (0.002) | +7.47 (0.010) | +9.84 (<0.001) |
| 20-29 event study | + I share × year | −7.09 (0.002) | +7.75 (0.004) | +10.61 (<0.001) |
| Triple difference vs family proxy | None | −5.24 (0.002) | +8.08 (<0.001) | +8.40 (<0.001) |
| Triple difference vs family proxy | + I and R-U share × Y × year | −5.08 (0.001) | +8.03 (<0.001) | +8.15 (<0.001) |
| Triple difference vs family proxy | + I share × Y × year | −5.41 (0.002) | +8.30 (<0.001) | +8.85 (<0.001) |
| Triple difference vs 50+ | None | −5.26 (0.002) | +7.50 (<0.001) | +8.40 (<0.001) |
| Triple difference vs 50+ | + I and R-U share × Y × year | −5.07 (0.002) | +7.45 (0.003) | +8.07 (<0.001) |
| Triple difference vs 50+ | + I share × Y × year | −5.42 (0.001) | +7.77 (<0.001) | +8.91 (<0.001) |

**Reading.** The hospitality-worker control moves the 2020 and 2022 coefficients by less than 0.3. Young hospitality workers are spread almost independently of amenity density across boroughs (correlation 0.08), so in these data the income-shock channel does not explain the young-adult reversal. This is a borough-level control from 2011; it cannot capture who actually lost work in 2020.

### 16.4 Judgement calls (round 7)

1. **Borough × age-group fixed effects** in the triple difference, beyond the specification as written (needed for identification; see 16.1).
2. **Pre-period summary.** The 2015-2018 average θ is reported as a summary pre-trend test, alongside the individual years.
3. **Student share** is full-time students aged 18+ over residents aged 16+, from 2011 (16.2).
4. **Hospitality share** is I plus R-U over employed residents aged 16-34, because R alone is not published by age; there is an I-only variant (16.3).
5. **Single-group reversal.** For the single-group models, the reversal is measured as yearly-coefficient contrasts relative to 2019, not with the pooled-reference period model of section 15.2. The yearly closure average is therefore relative to 2019 only.
6. **Fewer clusters when boroughs are dropped.** The top-5 drop leaves 27 clusters; bootstrap weights are drawn for 27 clusters.

## 17. Round 8: pre-period check (`97_preperiod_check.py`)

Run 29 October 2026. The new script was run. `96_age_ddd.py` was rerun after a one-line change, so that its pre-period average uses whichever of 2015-2018 are in the sample; its round 7 results are unchanged.

**What was rerun.** The 20-29 event study, both triple differences (yearly and period models), and the single-group period decomposition for all ages and each age group. Each was estimated on the full sample (years to June 2015-2025) and on a sample starting in the year to June 2016. Outputs: `preperiod_check.csv` and `preperiod_check_decomposition.csv`.

**Results**
- **Yearly coefficients and reopening − closure are identical** in the two samples.
  - The event studies are saturated in years: each year has its own D interaction, and 2019 is the base. Dropping 2015 therefore removes only the 2015 coefficient.
  - The reopening − closure contrasts are unchanged: 20-29 +10.13, triple differences +8.40.
- **Only the pooled-reference period models change.** Their reference moves from 2015-2019 to 2016-2019.

| Model | Closure, 2015 start | Closure, 2016 start | Reopening, 2015 start | Reopening, 2016 start | Later, 2015 start | Later, 2016 start |
|---|---|---|---|---|---|---|
| Triple difference vs family proxy | −2.01 (0.015) | −0.64 (0.606) | +6.39 (<0.001) | +7.76 (<0.001) | −4.37 (<0.001) | −3.00 (0.001) |
| Triple difference vs 50+ | −2.12 (0.241) | −0.92 (0.668) | +6.28 (<0.001) | +7.48 (<0.001) | −3.93 (0.011) | −2.72 (0.027) |
| Migration 20-29 | −3.27 (0.049) | −2.16 (0.335) | +6.86 (<0.001) | +7.97 (<0.001) | −3.28 (0.015) | −2.16 (0.051) |
| Migration, all ages | −1.81 (0.006) | −1.59 (0.078) | +2.10 (0.013) | +2.32 (0.020) | −0.03 (0.919) | +0.19 (0.547) |

**Does 2015 reflect an early-year data issue? No evidence of one was found.**
- **Same source release.** The year to June 2015 file is part of the same revised ONS release as 2016-2021: all are labelled as revised in light of the 2021 Census, a consistent series from mid-2011, published 1 December 2023. Only the 2022 file is a later second version (30 July 2025).
- **London-wide young flows are ordinary in 2015.** Net moves of 20-29 year olds with the rest of the UK, per 1,000 London residents of that age: 31.95 in 2015, 26.01 in 2016, 21.94 in 2017, 24.61 in 2018, 32.01 in 2019.
- **No single borough drives it.** Leave-one-borough-out estimates of the 2015 coefficient (20-29 event study) range from 3.39 (Westminster dropped) to 5.58 (Hammersmith and Fulham dropped), against 5.10 for the full sample. Output: `preperiod_2015_leave_one_out.csv`.
- **It reflects a gradual differential trend.** Moves of 20-29 year olds out of boroughs below the median amenity density rose from 43,275 in 2015 to 44,651 in 2016 and 51,576 in 2017. In above-median boroughs they rose from 54,303 to 57,305 and 59,447. Output: `preperiod_2015_components.csv`. The 2015 coefficient therefore reflects a faster rise in young out-moves from low-amenity boroughs between 2015 and 2017, which had run its course by 2016-2018, where all coefficients are small and insignificant.

**Choice for the report.** The report uses the sample starting in the year to June 2016 for all migration models.
- The yearly coefficients and the reopening − closure contrasts are the same as in the full sample.
- The pooled pre-period reference becomes 2016-2019, a window in which the young-adult event-study and triple-difference coefficients are flat.
- The full-sample 2015 coefficient is reported in the robustness section.

## 18. Research report (`99_report.py`, `report_template.tex`)

Built 29 October 2026.

**Output.** `outputs/report/report.tex` is a single self-contained LaTeX file for Overleaf (pdflatex).
- Packages: amsmath, booktabs, graphicx, caption, tikz, pgfplots, natbib and hyperref, with geometry for the margins.
- The bibliography is a `thebibliography` environment inside the file.
- The figures are drawn natively with pgfplots, and their coordinates are written inline from the output CSVs.

**How it is built.**
- `scripts/report_template.tex` holds the prose.
- `scripts/99_report.py` replaces each `<<KEY>>` placeholder with chart coordinates and booktabs table bodies generated from the CSVs:
  - `report_migration_2016.csv` and `preperiod_check*.csv`;
  - `reversal_decomposition.csv`, `honestdid_breakdown.csv`, `msoa_*` and `rent_*`;
  - `price_to_rent_groups.csv`;
  - the clean data files.
- `run_all.py` runs it as its last numbered step.

**Choices**
- **Migration sample.** It starts in the year to June 2016 (section 17). Every migration model cited is re-estimated on 2016-2025 in `report_migration_2016.csv`. The coefficients equal the full-sample ones; p-values and N reflect the shorter sample (N = 320 per group, 640 for triple differences).
- **HonestDiD.** The breakdown values are from the full-sample event studies (pre-period 2015-2018 for migration). The report states this.
- **Citations.** References were checked against publisher, Crossref, NBER, RePEc, CEP, Centre for Cities and ONS pages.
  - Rosen (1979) stays in the bibliography with a visible TODO, because its page range was confirmed only from secondary sources, and it is not cited in the text.
  - Couture (2016) is cited as an unpublished working paper (University of California, Berkeley), as listed on the author's CV.
  - Callaway, Goodman-Bacon and Sant'Anna is cited as forthcoming in the American Economic Review, with NBER Working Paper 32117.
- **Compilation.** The report was not compiled locally, because no LaTeX distribution is installed on this machine. Automated checks found balanced environments and braces, every reference and citation defined, no leftover placeholders and no non-ASCII characters.
- **Word count.** About 7,400 words of body text, plus a 261-word abstract, excluding tables, figure captions, equations and references. This is a script count on stripped LaTeX.

## 19. Report revision round 1 (`99_report.py`, `report_template.tex`)

**Substantive changes**
- **Framing.** "Measures the value" now reads "reveals that residents value consumption variety". This applies in the abstract, introduction, literature review (2.5), section 6.5 and the conclusion.
- **Lower bound for movers (new section 6.7).**
  - Revealed-preference condition: each young adult who left a high-amenity borough during the closure valued the variety lost over the expected closure at more than their moving cost.
  - Cost side: Shelter/YouGov (2024) mean non-recoverable moving cost for private renters in England, £669 (nominal 2024 £, survey of 2,002 adults, press release of 18 April 2024). Kennan and Walker (2011, Table IV) is cited only to show that structural costs including non-monetary costs are far higher (about $312,000 in 2010 US$ for the average interstate mover), so £669 is conservative.
  - Per month: £669 over 23 March to 4 July 2020 (103 days, 3.4 months) gives about £200 a month. Over 23 March 2020 to 17 May 2021 (420 days, 13.8 months) it gives about £48 a month.
  - Assumptions, each stated in one sentence in the report:
    - the triple-difference excess outflow reflects the loss of variety;
    - the 2024 all-renter mean applies to young adults in 2020;
    - one move is counted per mover;
    - movers expected the closure to last for the stated period.
  - Considered and not used:
    - MHCLG Tenant Fees impact assessment (2018), because letting fees were banned from June 2019;
    - Bayer et al. (2009, 2016), because they report utility units only.
- **Rent and the 2021 coefficient (section 6.3).**
  - The positive 2021 triple-difference coefficient is linked to falling high-amenity rents relative to 2019Q4, from `RENT_CLOSURE` in `99_report.py`: −0.50 (2020Q2), −0.95, −1.32, −1.95, −2.62 (2021Q2).
  - The report also states that, relative to the projected pre-2020 trend, the same quarters lie at +1.30 to −0.02 (`rent_trend_break.csv`). The cheaper central rents therefore follow the pre-2020 trend, and the closures did not push rents below it.
- **Consistent rent sentence.** The abstract, introduction, section 6.5 and conclusion now share one sentence: "high-amenity rents fell relative to other boroughs during the closures and recovered above the projected trend from 2023, with the size of the recovery depending on the trend assumption".
- **Policy paragraph.** The post-2022 house-price and price-to-rent decline is described as consistent with financing and job-access channels, since distance and property-type controls absorb it.
- **Family Spending, FYE 2020, Table A11 (section 3).** The data support the young-adult spending claim only weakly.
  - Catering services share of consumption, by age of household reference person: 8.6% under 30, 8.5% for 30-49, 8.1% for 50-64, 7.7% for 65-74 and 6.6% for 75+.
  - Recreational and cultural services share: 3.5% for under-30s, the lowest of any group.
  - The framework now rests the young-adult response mainly on lower moving costs, with the catering share as a secondary factor.
- **Corrections.**
  - The opening sentence of the 2015 robustness paragraph now matches its conclusion.
  - Rosen (1979) and its TODO are removed.
  - Miyauchi, Nakajima and Redding (2025) is confirmed on Crossref as QJE 140(4), 2507-2570, DOI 10.1093/qje/qjaf038, and keeps the journal citation.

**Layout changes**
- **Tables.**
  - All tables use `tabularx{\linewidth}` at `\small`, with coefficients on one row and the bootstrap p-value in brackets on the row below. There is no `resizebox`.
  - Notes sit in a `\linewidth` parbox (`\tabnote`).
  - Table 5 (triple difference) has Panel A (yearly) and Panel B (period model), each with its own headings.
  - Table 9 (house prices) uses spec columns (1) to (7), defined in the note.
  - The robustness table rows are labelled (1) to (14).
- **Equations.** Equations (1), (3) and (5) are broken with `split`.
- **Figures.** The pgfplots width is 0.95\linewidth.
- **Page numbering and bibliography.** The front matter uses roman page numbers, which removes the hyperref duplicate `page.1` anchor. The bibliography is set ragged-right.

**Compilation.** The report was compiled with pdflatex (TeX Live 2026). After two passes it produces 26 pages and the log shows zero overfull boxes, zero underfull boxes and zero warnings. The PDF is copied to `outputs/report/report.pdf`.

**Word count.** About 8,100 words of prose (8,390 including the 271-word abstract and front matter) (script count, excluding tables, captions, equations and references). This is above the 7,000 target.

## 20. Report revision round 2

**New estimates (`97_preperiod_check.py`, 2016-2025 sample, written to `report_migration_2016.csv`)**
- Two new triple-difference variants for each comparison group:
  - the 2011 student share × year × young-adult indicator;
  - the triple difference with the five highest-student-share boroughs dropped (27 clusters, new Rademacher draws).
- Year to June 2021 coefficients, with wild cluster bootstrap p-values:

| Model | Baseline | Student-share control | Drop five student boroughs |
|---|---|---|---|
| Event study, ages 20-29 | +1.64 (0.603) | +1.39 (0.662) | +2.55 (0.550) |
| Triple difference vs family proxy | +4.60 (0.014) | +4.77 (0.055) | +5.14 (0.165) |
| Triple difference vs ages 50+ | +3.47 (0.426) | +3.61 (0.453) | +4.49 (0.474) |

- Reading: the student checks leave the 2021 triple-difference coefficient in place and raise its p-values. The 2011 student share is a weak proxy for the location of the autumn 2020 intake, so the student explanation remains open.
- The 2022 triple-difference coefficients with the student control are 5.23 (family proxy) and 4.71 (ages 50+). Reopening minus closure is 5.54 and 5.56.
- `99_report.py`: the robustness table's triple-difference rows now filter on `sample == "32 boroughs"`, because the drop-five rows share `control == "none"`.

**Prose changes**
- **Thesis.** Introduction and conclusion: young adults are now described as "the residents with the lowest moving costs and a catering spending share as high as any age group". This replaces "who value variety most".
- **Section 6.3.**
  - Students starting in autumn 2020 and cheaper central rents are presented as candidate explanations for the 2021 coefficient, with the numbers above.
  - The section states that the 2020Q2-2021Q2 rent fall followed the pre-2020 trend, so the closure produced no additional rent decline.
- **Section 6.7.**
  - The moving-cost inequality now bounds the total loss from staying: variety, rent saved, lost social activity and other lockdown effects.
  - The attribution of the triple-difference excess outflow to the variety channel is stated as an explicit assumption.
  - One added sentence: the cost of the original move to London strengthens the bound if location preferences are stable.
  - The introduction's description of the bound is softened to match.
- **Rent sentence.** The abstract, introduction, section 6.5 and conclusion all now read "fell relative to other boroughs during the closures, continuing a pre-2020 trend, and recovered above the projected trend from 2023 ...".
- **Template tidy.** The stray comment rule and blank lines before section 6.7 are removed, and the rule above the Conclusion heading is restored.

**Compilation.** The report compiles to 26 pages with zero overfull boxes, underfull boxes or warnings.

## 21. Report revision round 3

**Section 6.7**
- Renamed to "A lower bound on the loss from staying for movers".
- The £669 figure now bounds only the total loss from staying for young adults who left.
- Under the attribution assumption, the other components of the loss stayed below the moving cost for the excess movers identified by the triple difference, while the variety loss pushed the total above it. Variety is therefore the component that made these residents leave.
- The claim that £669 bounds the value of variety itself is removed, and the introduction's description of the bound is adjusted to match.

**Kennan and Walker (2011), checked against the published paper**
- Table IV (p. 232): $312,146 in 2010 US$ for the average mover, ignoring payoff shocks. The previous text rounded this to "about $312,000", as the authors do in the text.
- The report now states:
  - the exact figure, with table and page;
  - the sample: young white US men with a high-school education;
  - that the figure ignores payoff shocks;
  - the authors' statement that it refers to hypothetical moves to arbitrary locations;
  - that the net cost of moves actually made averages −$80,768 (Table V, p. 236).
- A negative net cost leaves the conclusion that £669 is conservative unchanged. In the framework of the bound, the payoff shocks belong to the loss from staying, and £669 bounds the gross cost.

**Section 3**
- One added sentence: the rent channel depends on the size of the rent response to the loss of variety, which the results subsection "Triple difference" tests. That subsection now carries the label `sec:dddres`.

**Compilation.** The report compiles to 26 pages with zero overfull boxes, underfull boxes or warnings.

**Equation layout (round 3 follow-up).** Equations (2), (3) and (5) each fit on one line now, so the `split` line breaks are removed.
- (2) and (3) group each event-time term in brackets: $(\beta_k D + X'\gamma_k [+ T_i'\psi_k])\mathbf{1}[t=k]$.
- (5) sums over periods $P \in \{C, R, L\}$ with coefficient $b_P$.
- The text now defines $X_b$ as a vector of controls and defines $b_P$.
- The models themselves are unchanged. The report still compiles with zero overfull boxes, underfull boxes or warnings.

## 22. Rent tests (`98_rent_tests.py`)

This step runs only `98_rent_tests.py` (`python run_all.py --only 98_rent_tests.py`), which is registered in `run_all.py` after step 97. Outputs go to `outputs/event_study/rent_tests.csv` and `rent_tests.md`. The report text is unchanged.

**Common settings.** Inference uses CR1 standard errors clustered by borough and the WCR bootstrap clustered by borough (Rademacher, B = 9,999, seed 20261028, 32 clusters). The treatment D is standardised log borough amenity density. The outcome is net moves with the rest of the UK per 1,000 mid-2019 residents of the age group.

**Test 1. Rent-change control in the triple difference**
- Specification:
  - The model is the yearly triple difference of `96_age_ddd.py` on the report's 2016-2025 sample, with 20-29 stacked against the family proxy or ages 50+.
  - The added term is R_b x Y x year for every year except 2019.
  - R_b is 100 x (log PIPR quarterly index 2021Q4 minus 2019Q4), taken from `event_study_rents_quarterly.csv` and standardised across the 32 boroughs.
- Judgement call: R_b is standardised like the other borough controls. Scaling does not change the D x Y x year coefficients.
- R_b has mean 1.0 log points, SD 4.64 and range −12.18 to +8.42. Its correlation with D is −0.761.
- Hard fact: R_b is measured during and after the closure, so it is partly an outcome of the treatment. With a correlation of −0.76 with D, the control absorbs much of the amenity variation, so a smaller coefficient with the control cannot separate a rent channel from an amenity channel.
- Without the control, the coefficients reproduce `report_migration_2016.csv`.

| Comparison | Control | 2020 | 2021 | 2022 | Reopening − closure |
|---|---|---|---|---|---|
| family proxy | none | −5.24 (0.002) | 4.60 (0.014) | 8.08 (0.000) | 8.40 (0.000) |
| family proxy | rent change | −5.08 (0.005) | 4.09 (0.078) | 3.80 (0.117) | 4.30 (0.147) |
| ages 50+ | none | −5.26 (0.002) | 3.47 (0.426) | 7.50 (0.000) | 8.40 (0.000) |
| ages 50+ | rent change | −5.53 (0.021) | 1.83 (0.858) | 2.74 (0.253) | 4.59 (0.240) |

**Test 2. Pre-pandemic rent responsiveness (years to June 2016-2019)**
- Specifications:
  - (a) For 20-29: y_bt = a_b + l_t + beta x_bt + e.
  - (b) A triple difference against the family proxy: y_bgt = a_bt + c_gt + e_bg + beta x_bt Y_g + e.
- The rent change x_bt is in log points of the monthly PIPR all-property index at June.
- Judgement call: the lagged change is 100 x (log index June t−1 minus June t−2). The PIPR borough series start in January 2015, so the lagged change exists only from the year to June 2017. The lagged regressions therefore use 2017-2019, with N = 96 for (a) and 192 for (b).
- Judgement call: a contemporaneous variant, 100 x (log index June t minus June t−1), covers the full 2016-2019 window, with N = 128 for (a) and 256 for (b). It is exposed to reverse causality from migration to rents.
- The within-sample SD of the lagged change is 3.36 log points, and of the contemporaneous change 3.02.

| Model | Rent change | Years | Coefficient (p) | 95% CI (CR1) | N |
|---|---|---|---|---|---|
| 20-29, borough and year FE | lagged | 2017-2019 | 0.034 (0.813) | [−0.265, 0.334] | 96 |
| Triple difference vs family proxy | lagged | 2017-2019 | 0.011 (0.950) | [−0.346, 0.369] | 192 |
| 20-29, borough and year FE | contemporaneous | 2016-2019 | −0.313 (0.235) | [−0.746, 0.120] | 128 |
| Triple difference vs family proxy | contemporaneous | 2016-2019 | −0.371 (0.124) | [−0.775, 0.032] | 256 |

- With three or four years per borough these estimates are imprecise. The upper end of the lagged triple-difference interval, 0.369 per log point, scaled by the 4.64 SD of the 2019Q4-2021Q4 rent change, gives about 1.7 per 1,000. This is a rough scale comparison only.

**Test 3. Ages 30-39 alongside 20-29**
- The coefficients are read from `report_migration_2016.csv` (event study, no extra control, 32 boroughs, 2016-2025).
- Hard fact: the ONS internal-migration estimates have no tenure split, so this group is all residents aged 30-39, not renters aged 30-39.

| Age group | 2021 | 2022 |
|---|---|---|
| 20-29 | 1.64 (0.603) | 7.50 (0.005) |
| 30-39 | −4.65 (0.053) | −0.30 (0.760) |

## 23. Report revision round 4: rent tests in the report

**Section 6.4 (Robustness)**
- Three paragraphs and Table 7 ("Rent tests of the young-adult return", `tab:renttests`) are added after the hospitality-worker paragraph. The table is built by `rent_tests_table()` in `99_report.py` from `rent_tests.csv` and `report_migration_2016.csv`.
- The paragraphs state that net flows measure demand among young adults as a group, which is the object of the thesis, and that the same individuals need not return for the reversal to reflect that demand.
- Test 1 reports that the control more than halves the 2022 coefficient against both comparison groups. The squared correlation of the rent change with D, 0.58, is reported as the share of variation in amenity density that the rent change accounts for.
- Test 2 reports the implied upper scale of about 1.7 per 1,000 as an approximate figure with wide uncertainty.
- Judgement call: the scale is the upper 95 per cent bound of the lagged triple difference times the cross-borough SD of the 2019Q4-2021Q4 rent change, as specified. Scaling by the rent change associated with one SD of amenity density, 0.76 × 4.64 ≈ 3.5 log points, would give about 1.3. The text uses the specified, larger figure.
- Test 3 notes that the age group covers all residents aged 30-39 and that, in the framework, this group faces higher moving costs.

**Limitations.** A paragraph is added stating that aggregate flows cannot identify whether returners were the same individuals. It names Understanding Society under special licence, SN 6666, as the data that could test this.
- Citation verified on the UK Data Service study page: University of Essex, Institute for Social and Economic Research (2025), Understanding Society: Waves 1-15, 2009-2024 and Harmonised BHPS: Waves 1-18, 1991-2009, Special Licence Access, Local Authority District, 17th edition, SN 6666, DOI 10.5255/UKDA-SN-6666-17.

**Compilation.** The report compiles to 27 pages with zero overfull boxes, underfull boxes or warnings. The prose word count is 9,319, including 274 words of abstract and front matter.

## 24. Report revision round 5: agglomeration framing (text only, no new estimation)

**Section 3**
- A new paragraph and equation (2), `eq:share`, follow the price-index paragraph: −d ln e / d ln L = [s/(σ−1)] × d ln N / d ln L.
  - With a constant budget share s, the expenditure needed for a given utility falls by s/(σ−1) per log unit of varieties.
  - The household (demand-side) term is multiplied by the supply term, the elasticity of varieties with respect to local population.
- The paragraph states that the design identifies the demand-side term with the supply term held fixed. The treatment is 2019 density, and the closures set accessible varieties close to zero with no entry or exit response during the closure.
- The estimates are in behavioural units, and Section 6.7 bounds their money value for movers.
- Later equations are renumbered automatically, and all references use `\ref`.

**Wording**
- In the abstract, the introduction thesis, the research gap and the conclusion, "reveals that residents value consumption variety, a household-side sharing mechanism" is replaced. The new wording says the response "measures the demand-side component of the household-side sharing mechanism of agglomeration, in which greater variety lowers the cost of reaching a given level of utility, holding the supply of varieties fixed".
- "Returned" or "return" is replaced by "net inflow recovered" or "recovery" wherever it implied the same individuals. This covers the abstract, introduction, the heading of 6.2 (now "switch-off and recovery"), 6.3, 6.4, the Table 7 caption, 6.5 and the conclusion.
- "Students returning" becomes "the arrival of students".
- Kept unchanged:
  - Couture and Handbury's "return" of graduates, which is their own term;
  - "expect variety to return";
  - universities that "returned to in-person teaching";
  - the two sentences that discuss same-individual returns explicitly.
- The Outcomes subsection adds that the migration estimates are net flows by age and local authority, so the results describe the composition of young adults in each borough.

**Limitations.** One sentence is added: recovering the full magnitude of the mechanism requires estimating venue entry with respect to local population, which is the supply term the design holds fixed.

**Section 6.7.** The sentence on counting one move per mover, and on the return move doubling the bound, is deleted.

**Hard facts flagged**
- The statement that there was "no entry or exit response during the closure" is not tested in the data. Business Counts are used for March 2019 only.
- The reopening coefficients compare boroughs after reopening, when the number of venues may differ from 2019. The supply term is therefore held fixed in the treatment measure, not necessarily in the reopening outcome.

**Compilation.** The report compiles to 28 pages with zero overfull boxes, underfull boxes or warnings. The prose word count is 9,607, including 274 words of abstract and front matter.

## 25. Report revision round 6 (text only)

- **Kennan and Walker (2011)** is removed from Section 6.7 and from the bibliography. The Shelter £669 figure stays as the conservative out-of-pocket cost. The opening sentence now notes that out-of-pocket costs exclude the non-monetary costs of leaving a place.
- **Section 6.7 attribution assumption, weaker form.** The difference between young adults and older residents in the other components of the loss, including rent saved by moving to a parental home, is the same in high-amenity and low-amenity boroughs. The text states that this is the identifying assumption of the triple difference.
- **Conclusion.** The paragraph now names three qualifications:
  - the overlap with students arriving in autumn 2021, where the student control takes the 2022 coefficient from 7.5 to 4.6;
  - a possible modest role for lower rents, with an approximate upper scale of 1.7 per 1,000 and wide uncertainty, against a 2022 triple-difference coefficient of 8.08;
  - aggregate flows cannot show whether the same individuals returned.
  The scope sentence on young adults is kept as a closing statement.
- **Introduction.** The opening sentence of the qualification paragraph lists the three qualifications. The next sentence now reads "The first qualification is that..." for consistency.
- **Section 3.** The text now says that regulation set accessible varieties close to zero regardless of entry or exit, that accessible variety during the closure did not depend on the supply response, and that the treatment uses the 2019 stock. "The estimates" is narrowed to "the closure estimates".
  - A sentence says that permanent exits would lower the variety available at reopening, with a reference to the Limitations subsection, which now carries the label `sec:limits`.
  - The Limitations sentence on an updated treatment measure adds "net of permanent exits during the closure".
- **Compilation.** The report compiles to 27 pages with zero overfull boxes, underfull boxes or warnings. The prose word count is 9,735, including 274 words of abstract and front matter.

## 26. Report revision round 7: final polish (text only)

- **Introduction, contribution.** The paragraph now describes the contribution as a measure of the demand-side term of the household-side sharing mechanism, identified from a reversal within boroughs and years with the supply of varieties held fixed, together with the lower bound on the total loss from staying for movers. The clause on the variety component under the attribution assumption is dropped here but remains in Section 6.7.
- **Introduction, qualifications.** "The first qualification is that" is removed. A new sentence points to the rent tests in Section 6.4 (no detectable pre-pandemic rent response, upper scale of about 1.7 per 1,000) and to the identity limitation in the Limitations subsection.
- **Title page.** The subtitle is now "Evidence on agglomeration from the COVID-19 closures in London". At \LARGE it wraps onto two lines.
- **Lists.** The preamble loads `enumitem` with `\setlist[enumerate]{label=(\roman*)}`. It was not in the earlier package list and is added here. The one ordinal reference now reads "prediction (iv)".
- **Compilation.** The report compiles to 27 pages with zero overfull boxes, underfull boxes or warnings. The prose word count is 9,771, including 274 words of abstract and front matter.

## 27. Within-London moves and a time-varying student control (`98_within_london.py`; student control pending)

**Test 1. Within-London moves (`98_within_london.py`)**
- Registered in `run_all.py` after `98_rent_tests.py`. Outputs: `outputs/event_study/within_london.csv` and `within_london.md`, `within_london_gross_20_29.csv`, and the panel `data/clean/migration_within_london_by_age_group.csv`. The report is unchanged.
- **Outcome.** For each of the 32 boroughs, moves in from the other 31 boroughs minus moves out to them, from the ONS detailed origin-destination estimates (the same parquet files as `96_age_ddd.py`). The outcome is expressed per 1,000 mid-2019 residents of the age group. Age groups follow `96_age_ddd.py`.
- **Judgement call.** Flows to and from the City of London are excluded, so the system is closed over the 32 analysis boroughs, following "the other 31 boroughs" in the specification. Within-borough moves (inla equal to outla) are excluded.
- **Models.** The event study and triple difference of `96_age_ddd.py` with standardised log amenity density, years to June 2016-2025, 2019 omitted, and the WCR bootstrap with B = 9,999 and 32 clusters.

| Model | 2016 | 2017 | 2018 | 2020 | 2021 | 2022 | 2023 | 2024 | 2025 | R − C |
|---|---|---|---|---|---|---|---|---|---|---|
| ES 20-29 | −7.11 (0.001) | −1.25 (0.225) | 0.41 (0.807) | −0.03 (0.985) | 5.71 (0.031) | 1.33 (0.694) | −6.69 (0.003) | −6.36 (0.001) | −2.81 (0.408) | −1.51 (0.119) |
| ES family proxy | −2.29 (0.140) | −0.37 (0.514) | 0.54 (0.403) | 2.01 (0.001) | −1.00 (0.159) | 0.41 (0.627) | −1.03 (0.458) | −0.57 (0.638) | −0.32 (0.810) | −0.10 (0.851) |
| ES 50+ | −0.76 (0.033) | 0.17 (0.711) | 0.29 (0.327) | 0.08 (0.787) | 0.53 (0.158) | 0.03 (0.960) | −0.22 (0.681) | −0.86 (0.064) | −0.74 (0.163) | −0.27 (0.670) |
| DDD vs family | −4.81 (0.001) | −0.88 (0.367) | −0.13 (0.896) | −2.04 (0.048) | 6.72 (0.017) | 0.92 (0.702) | −5.66 (0.007) | −5.79 (0.002) | −2.49 (0.255) | −1.42 (0.150) |
| DDD vs 50+ | −6.35 (0.001) | −1.42 (0.243) | 0.12 (0.916) | −0.11 (0.960) | 5.19 (0.041) | 1.30 (0.614) | −6.47 (0.003) | −5.50 (0.001) | −2.07 (0.458) | −1.24 (0.217) |

- The 2016 coefficients are large and significant (−7.11 for 20-29), so the within-London pre-period is not flat.
- **Gross 20-29 flows.** Boroughs are split at the median D, 16 above and 16 below. Moves from high to low were 28,723 in the year to June 2020, against a 2016-2019 average of 29,135 (−1.4%). Moves from low to high were 25,195 against 26,265 (−4.1%). Net high-to-low moves were 3,528 in 2020, against an average of 2,869, then 523 in 2021 and 2,792 in 2022.

**Test 2. Time-varying student control: pending.** The HESA open-data pages (hesa.ac.uk) return HTTP 403 behind a Cloudflare bot check to automated downloads. The check was not bypassed. The provider enrolment file needs a manual download.

## 28. Ages 25-29 as the young group; HESA student control pending (`98_students_25_29.py`)

- **Script.** Registered in `run_all.py` after `98_within_london.py`. Outputs: `outputs/event_study/students_25_29.csv` and `students_25_29.md`. The script defines `es_tv` and `ddd_tv`, which reproduce `96_age_ddd.es_fit` and `ddd_fit` and add:
  - time-varying controls, entered as S_bt in the event study and as S_bt × Y in the triple difference;
  - the contrast 2022 − 2020, tested with the WCR bootstrap like a single coefficient.
- **Ages 25-29 triple difference.** Years to June 2016-2025, 2019 omitted, 640 observations per comparison.

| Comparison | 2016 | 2017 | 2018 | 2020 | 2021 | 2022 | 2023 | 2024 | 2025 | R − C | 2022 − 2020 |
|---|---|---|---|---|---|---|---|---|---|---|---|
| family proxy | 1.82 (0.104) | −1.35 (0.033) | −1.22 (0.015) | −5.25 (0.002) | 2.69 (0.094) | 2.63 (0.038) | −2.44 (0.002) | −3.66 (0.004) | 0.20 (0.873) | 3.91 (0.008) | 7.87 (<0.001) |
| ages 50+ | 0.54 (0.660) | −1.61 (0.018) | −0.86 (0.129) | −5.26 (0.002) | 1.56 (0.584) | 2.05 (0.104) | −2.81 (0.002) | −3.30 (0.003) | 0.13 (0.912) | 3.90 (0.022) | 7.32 (<0.001) |

- **Period model** (reference 2016-2019 pooled):
  - Against the family proxy: closure −1.09 (0.117), reopening +2.81 (0.017), later −1.78 (0.019), R − C 3.91 (0.008).
  - Against ages 50+: closure −1.37 (0.392), reopening +2.54 (0.031), later −1.51 (0.086), R − C 3.90 (0.022).
- **Hard fact.** The 2017 coefficient for 25-29 (both comparisons) and the 2018 coefficient against the family proxy are negative, with p below 0.05, so the 25-29 pre-period is less flat than the 20-29 one.
- **HESA control: pending.** HESA Table 1 was expected in `raw/hesa/`, but no HESA file was found in the raw data folder, the project folder or the downloads folder. The HESA parts and the 25-29 repeat with the HESA control will run once the file is in place.

**Section 28 addendum. Ages 25-29 with a linear pre-trend (`98_students_25_29.py`)**
- **Specification.** Use the yearly 25-29 triple difference without the HESA control, 2016-2025. Fit a linear trend by unweighted OLS through the pre-period coefficients θ_2016, θ_2017, θ_2018 and θ_2019 = 0. Report θ_2020 and θ_2022 minus the projected trend.
  - The slope and both deviations are linear contrasts of the yearly coefficients, so they are tested with the WCR bootstrap (B = 9,999) like single coefficients.
  - Slope b = Σ(k − 2017.5)θ_k / 5. Projection at t = mean(θ_pre) + b(t − 2017.5).
- **Judgement call.** The trend is fitted through the estimated yearly coefficients. It is not added as a D × Y × t term to the regression. This keeps the yearly model unchanged and makes the deviations exact linear combinations of reported coefficients. Hand check against the family proxy: slope −0.533, projected 2020 −1.52, deviation −3.73; projected 2022 −2.59, deviation +5.21.

| Comparison | Pre-trend slope per year | 2020 | 2020 deviation | 2022 | 2022 deviation |
|---|---|---|---|---|---|
| family proxy | −0.53 (0.109) | −5.25 (0.002) | −3.73 (0.004) | 2.63 (0.038) | 5.21 (0.004) |
| ages 50+ | −0.09 (0.795) | −5.26 (0.002) | −4.56 (0.004) | 2.05 (0.104) | 2.92 (0.173) |

- The trend rests on four points, with 2016 at +1.82, so the projection is imprecise. The slope p-values are 0.109 and 0.795.
- **HESA tests: still pending.** On the second check, `raw/hesa/` does not exist, and no HESA file was found elsewhere.

## 29. Report revision round 8: 25-29 and within-London tests, lower bound removed

- **Section 6.4, ages 25-29.**
  - A new paragraph plus Table 6 ("Triple difference with ages 25 to 29 as the young group", `tab:ddd2529`), built by `ddd2529_table()` in `99_report.py` from `students_25_29.csv` (control none, 2016-2025).
  - The panels are the yearly coefficients 2016-2024, the period model, and the tests of 2022, 2022 − 2020 and the 2020 and 2022 deviations from the linear pre-trend.
  - The text states that the group is mostly past undergraduate age, that its 2020 outflow matches the 20-29 group, and that the 2022 recovery survives the trend adjustment against the family proxy and is positive but imprecise against ages 50+.
  - The closing sentence of the split-by-age paragraph now points to this test.
- **Student qualification.** The introduction adds one sentence on ages 25-29, and the conclusion adds one sentence on ages 25-29.
- **Section 6.4, within-London moves.** One paragraph after the rent tests table, with no table, reports:
  - the 2020 event study and triple differences, the 2021 and 2022 coefficient ranges, and the strong 2016 pre-trend;
  - the gross flows between amenity halves, with the outflow going beyond the Greater London boundary;
  - the sentence that moves to a parental home bundle the loss of variety with rent savings.
  The rest-of-UK comparison range uses the 2020 event-study coefficient −6.89 (`report_migration_2016.csv`) and the triple-difference coefficient −5.24.
- **Section 6.7 removed entirely.** Every reference to it is removed: the introduction's contribution paragraph, and the Section 3 sentence, which now ends "net moves per 1,000 per standard deviation of log density".
  - The abstract had no reference to the bound.
  - The Shelter bibliography entry is removed.
  - With 6.7 removed, the moving-cost and attribution content no longer appears in the report. The estimates and notes in sections 19-25 remain for the record.
- **Future research.** One added sentence says that HESA enrolment data by provider would allow a time-varying student control.
- **Compilation.** The report compiles to 29 pages with zero overfull boxes, underfull boxes or warnings. The prose word count is 9,907, including 274 words of abstract and front matter.

## 30. Report revision round 9 (text only)

- **Within-London paragraph.** "With no matching shift..." is replaced by the net high-to-low 20-29 moves: an average of 2,869 in 2016-2019 and 3,528 in 2020, a shift of about 660 (3,528 − 2,869 = 659).
  - The shift arises mostly from fewer moves into high-amenity boroughs. Low-to-high moves fell by 1,070 (26,265 to 25,195), and high-to-low moves fell by 412 (29,135 to 28,723).
  - The sentence describes this as far smaller than the outflow to the rest of the UK.
- **Introduction.** The 1.7 per 1,000 figure is removed from the opening qualifications sentence. It remains in the conclusion and in Section 6.4.
- **Abstract.** One sentence is added: among 25 to 29 year olds, who are mostly past undergraduate age, the 2020 outflow is the same size as for ages 20 to 29 and the 2022 recovery is smaller. In the 2020 triple difference the figures are −5.25 for 25-29 against −5.24 for 20-29.
- **Compilation.** The report compiles to 29 pages with zero overfull boxes, underfull boxes or warnings. The prose word count is 9,976.
- **Style lint.** It flags "small shift" and "far smaller" as vague. Both are the chosen wording, and the sentence carries the 660 figure.

## 31. Part A: final robustness round (`98_robustness_final.py`, `98_international.py`)

**Summary of Part A results**
- **Teleworkability and garden access (A1).** Both are strongly correlated with log amenity density across boroughs: +0.824 for teleworkability and −0.733 for garden access. Adding either one, interacted with young × year, removes most of the 2020 outflow.
  - For 20-29 against the family proxy, the 2020 coefficient is −1.18 (p 0.595) with teleworkability and −3.22 (p 0.090) with garden access. With both controls it turns positive at +2.08 (p 0.387).
  - The 2022 recovery stays significant with the teleworkability control (+10.80, p 0.001; 2022 − 2020 = 11.98, p 0.010). It does not survive the garden control or both controls together.
  - The 25-29 results follow the same pattern.
  - Hard fact: with correlations of this size, the 32-borough design cannot separate amenity density from teleworkability and garden access. The 2020 outflow is consistent with a working-from-home or space channel as well as a variety channel.
- **2022 − 2020 contrast (A2).** Positive in every existing triple-difference specification.
  - For 20-29 it ranges from 8.26 (rent-change control, against ages 50+, p 0.024) to 13.71 (hospitality I only), with all p-values 0.024 or below.
  - For 25-29 it is 7.87 and 7.32 (p < 0.001).
  - For within-London moves it is 2.96 (p 0.092) and 1.41 (p 0.231).
- **International migration (A3).** Net international migration of young adults into high-amenity boroughs rose in 2020 relative to other boroughs. The coefficient is +8.12 per 1,000 per SD for 20-29 (p 0.002), which offsets the internal outflow.
  - Total net migration (internal plus international) shows no 2020 outflow. The 20-29 triple difference is +1.52 (p 0.278) against the family proxy and +1.86 (p 0.246) against ages 50+.
  - Total net migration does show a 2021-2022 rise (2022 coefficient +22.08 against the family proxy, p 0.002), driven by both components.
  - Hard fact: ONS international migration estimates for 2020 and 2021 are modelled. The International Passenger Survey was suspended from March 2020, and local distribution of migrants rests on administrative data and models. These estimates are less reliable than the internal-migration estimates, and the mid-2022 to mid-2024 figures were revised in July 2026.

**A1 specification**
- **Model.** The yearly triple difference of `96_age_ddd.py` on years to June 2016-2025, estimated with `98_students_25_29.ddd_tv`, which adds the 2022 − 2020 contrast. Inference uses the WCR bootstrap with B = 9,999 and 32 borough clusters.
- **Controls.** `X_telework` and `X_garden` from `event_study_borough_vars.csv` (standardised across the 32 boroughs), each × young × year, alone and together.
  - Teleworkability is the 2011 share of employed residents in occupations scoring below 1.5 on the ONS 2020 homeworking score.
  - Garden access is the April 2020 share of addresses with private outdoor space.
- **Correlations.** These are Pearson correlations of the raw shares with D, the standardised log amenity density, across the 32 boroughs.
- **Results.** Full results are in `outputs/event_study/robustness_final.md` and `.csv`.

| Young | Comparison | Control | 2020 | 2021 | 2022 | R − C | 2022 − 2020 |
|---|---|---|---|---|---|---|---|
| 20-29 | family proxy | none | −5.24 (0.002) | 4.60 (0.014) | 8.08 (<0.001) | 8.40 (<0.001) | 13.32 (<0.001) |
| 20-29 | family proxy | teleworkability | −1.18 (0.595) | 4.13 (0.154) | 10.80 (0.001) | 9.33 (0.012) | 11.98 (0.010) |
| 20-29 | family proxy | garden access | −3.22 (0.090) | 3.77 (0.313) | 2.28 (0.314) | 2.00 (0.483) | 5.49 (0.158) |
| 20-29 | family proxy | both | 2.08 (0.387) | 3.00 (0.360) | 3.86 (0.150) | 1.32 (0.775) | 1.78 (0.653) |
| 20-29 | ages 50+ | none | −5.26 (0.002) | 3.47 (0.426) | 7.50 (<0.001) | 8.40 (<0.001) | 12.76 (<0.001) |
| 20-29 | ages 50+ | teleworkability | −0.29 (0.907) | 7.73 (0.130) | 12.07 (0.001) | 8.35 (0.108) | 12.36 (0.011) |
| 20-29 | ages 50+ | garden access | −3.28 (0.165) | 3.40 (0.510) | 1.74 (0.401) | 1.69 (0.603) | 5.03 (0.176) |
| 20-29 | ages 50+ | both | 3.05 (0.330) | 8.34 (0.297) | 5.48 (0.002) | −0.22 (0.972) | 2.43 (0.570) |
| 25-29 | family proxy | none | −5.25 (0.002) | 2.69 (0.094) | 2.63 (0.038) | 3.91 (0.008) | 7.87 (<0.001) |
| 25-29 | family proxy | teleworkability | −2.72 (0.183) | 2.38 (0.231) | 3.07 (0.080) | 3.23 (0.182) | 5.78 (0.089) |
| 25-29 | family proxy | garden access | −2.53 (0.188) | 0.51 (0.837) | −0.37 (0.807) | 0.64 (0.755) | 2.16 (0.402) |
| 25-29 | family proxy | both | 1.17 (0.620) | −0.45 (0.801) | −0.68 (0.595) | −1.04 (0.680) | −1.85 (0.559) |
| 25-29 | ages 50+ | none | −5.26 (0.002) | 1.56 (0.584) | 2.05 (0.104) | 3.90 (0.022) | 7.32 (<0.001) |
| 25-29 | ages 50+ | teleworkability | −1.83 (0.503) | 5.99 (0.151) | 4.33 (0.030) | 2.25 (0.514) | 6.16 (0.082) |
| 25-29 | ages 50+ | garden access | −2.59 (0.260) | 0.13 (0.977) | −0.90 (0.547) | 0.33 (0.912) | 1.69 (0.540) |
| 25-29 | ages 50+ | both | 2.14 (0.573) | 4.89 (0.395) | 0.94 (0.440) | −2.58 (0.551) | −1.20 (0.720) |

**A2 specification.** Every triple-difference specification the report or the notes cite is re-estimated on 2016-2025 with the 2022 − 2020 contrast. The specifications are:
- 20-29 with no control;
- the hospitality controls (I+RSTU, and I only);
- the 2011 student share;
- the top five student boroughs dropped (27 clusters, with Rademacher weights drawn for 27);
- the 2019Q4-2021Q4 rent change;
- 25-29 with no control;
- within-London 20-29.

Without the extra control the coefficients reproduce `report_migration_2016.csv`.

| Young | Comparison | Specification | 2020 | 2022 | 2022 − 2020 | Clusters |
|---|---|---|---|---|---|---|
| 20-29 | family | none | −5.24 (0.002) | 8.08 (<0.001) | 13.32 (<0.001) | 32 |
| 20-29 | 50+ | none | −5.26 (0.002) | 7.50 (<0.001) | 12.76 (<0.001) | 32 |
| 20-29 | family | hospitality I+RSTU | −5.08 (0.001) | 8.03 (<0.001) | 13.11 (0.001) | 32 |
| 20-29 | 50+ | hospitality I+RSTU | −5.07 (0.002) | 7.45 (0.003) | 12.52 (<0.001) | 32 |
| 20-29 | family | hospitality I only | −5.41 (0.002) | 8.30 (<0.001) | 13.71 (<0.001) | 32 |
| 20-29 | 50+ | hospitality I only | −5.42 (0.001) | 7.77 (<0.001) | 13.19 (<0.001) | 32 |
| 20-29 | family | 2011 student share | −5.38 (0.012) | 5.23 (0.009) | 10.61 (0.005) | 32 |
| 20-29 | 50+ | 2011 student share | −5.30 (0.012) | 4.71 (0.020) | 10.01 (0.007) | 32 |
| 20-29 | family | drop top-5 student | −5.93 (0.013) | 6.26 (0.027) | 12.19 (0.004) | 27 |
| 20-29 | 50+ | drop top-5 student | −5.70 (0.007) | 6.07 (0.058) | 11.77 (0.003) | 27 |
| 20-29 | family | rent change | −5.08 (0.005) | 3.80 (0.117) | 8.88 (0.016) | 32 |
| 20-29 | 50+ | rent change | −5.53 (0.021) | 2.74 (0.253) | 8.26 (0.024) | 32 |
| 25-29 | family | none | −5.25 (0.002) | 2.63 (0.038) | 7.87 (<0.001) | 32 |
| 25-29 | 50+ | none | −5.26 (0.002) | 2.05 (0.104) | 7.32 (<0.001) | 32 |
| 20-29 | family | within-London outcome | −2.04 (0.048) | 0.92 (0.702) | 2.96 (0.092) | 32 |
| 20-29 | 50+ | within-London outcome | −0.11 (0.960) | 1.30 (0.614) | 1.41 (0.231) | 32 |

**A3 specification**
- **Source.** ONS "Estimates of the population for England and Wales", mid-2011 to mid-2025 detailed time series (`myebtablesenglandwales20112025.xlsx`, released 29 July 2026, saved in `raw/ons_mye/`).
  - Sheet MYEB2: components of change by LA (April 2023 boundaries), sex and single year of age, with international_in_t and international_out_t.
  - Single year of age is the finest detail published.
- **Judgement call.** Component year t (mid-(t−1) to mid-t) maps to the year to June t, and age is age at mid-year t, both matching the internal panel.
- **Outcomes.** All per 1,000 mid-2019 residents of the age group, the same denominators as the internal panel:
  - international = international_in − international_out;
  - total = the internal net moves with the rest of the UK from `96_age_ddd.py` plus the international net.
- **Judgement call.** Total combines the pilot's London-boundary internal flows with ONS international flows. The MYE internal component, which includes moves between boroughs, is not used, so that the internal part is unchanged from the main analysis.
- **Check.** The internal outcome rerun inside the script reproduces the main coefficients.
- **London-wide means.** For 20-29, international net per 1,000 was 19.1 in 2019, 3.1 in 2020, 16.4 in 2021 and 49.5 in 2022.
- **Results.** Full results are in `outputs/event_study/international.md` and `.csv`. The new panel is `data/clean/migration_total_by_age_group.csv`.

| Outcome | Model | 2020 | 2021 | 2022 | R − C | 2022 − 2020 |
|---|---|---|---|---|---|---|
| total | ES 20-29 | 1.23 (0.470) | 11.68 (0.007) | 21.93 (0.006) | 15.47 (0.014) | 20.70 (0.010) |
| total | DDD 20-29 vs family | 1.52 (0.278) | 12.47 (<0.001) | 22.08 (0.002) | 15.08 (0.015) | 20.56 (0.005) |
| total | DDD 20-29 vs 50+ | 1.86 (0.246) | 11.11 (0.014) | 19.50 (0.006) | 13.02 (0.018) | 17.65 (0.010) |
| total | ES 25-29 | 1.64 (0.235) | 9.66 (0.021) | 10.49 (0.062) | 4.84 (0.187) | 8.85 (0.092) |
| total | DDD 25-29 vs family | 1.94 (0.123) | 10.44 (<0.001) | 10.64 (0.031) | 4.46 (0.203) | 8.71 (0.050) |
| total | DDD 25-29 vs 50+ | 2.28 (0.160) | 9.08 (0.027) | 8.07 (0.085) | 2.39 (0.429) | 5.80 (0.156) |
| international | ES 20-29 | 8.12 (0.002) | 10.04 (<0.001) | 14.42 (0.012) | 5.34 (0.208) | 6.31 (0.233) |
| international | DDD 20-29 vs family | 6.77 (0.002) | 7.86 (<0.001) | 14.00 (0.010) | 6.68 (0.117) | 7.23 (0.133) |
| international | DDD 20-29 vs 50+ | 7.12 (0.003) | 7.63 (0.001) | 12.00 (0.018) | 4.62 (0.229) | 4.88 (0.285) |
| international | ES 25-29 | 8.54 (0.001) | 9.92 (<0.001) | 8.44 (0.092) | −0.79 (0.831) | −0.10 (0.983) |
| international | DDD 25-29 vs family | 7.18 (0.001) | 7.75 (<0.001) | 8.02 (0.059) | 0.55 (0.872) | 0.83 (0.824) |
| international | DDD 25-29 vs 50+ | 7.54 (0.001) | 7.52 (<0.001) | 6.02 (0.169) | −1.51 (0.658) | −1.52 (0.700) |

- **Pre-period (20-29 triple difference).** The international outcome is not flat before 2019.
  - International, 2016: +6.75 (p 0.001) against the family proxy and +7.50 (p 0.001) against ages 50+.
  - International, 2017 and 2018: +1.60 (p 0.020) and +1.33 (p 0.049) against the family proxy; +0.40 and +0.51 (p above 0.65) against ages 50+.
  - Total, 2016: +8.10 and +7.58 (both p 0.001).
  - Total, 2017 and 2018: between −0.13 and +1.52, with p-values of 0.25 or above.
  - So the positive 2020 international coefficient sits in a series that was already positive and uneven before 2019. The total and international estimates carry less weight than the internal ones.
- **Coincidence checked.** The 2020 internal event-study coefficient is −6.8895 for 20-29 and −6.8923 for 25-29. These are different estimates that happen to agree, confirmed against the borough-level outcome values.

## 32. Report restructured around the full results (report round 10)

- **New thesis.** The introduction, abstract and conclusion use the revised thesis. One wording change: "ranks tourist areas highest" became "ranks tourist areas among the highest outside London", because inner London boroughs top the per-resident measure.
- **London's role.** London is presented as the application of a design that extends to other cities and to England and Wales. No text describes it as a pilot.
- **Structure.**
  - Sections 1-5 are revised, and section 5 gains 5.4, "National designs and the pre-analysis plan", which describes the departure labelling.
  - Results are reorganised as 6.1 London migration, 6.2 Robustness in London, 6.3 Identification limits in London, 6.4 Extension to England and Wales, 6.5 Measuring access to consumption variety and 6.6 Prices.
  - The pound values move to Appendix A.
- **Transparency in the text.**
  - The national headline was registered before estimation, and the per-resident measure was the registered measure.
  - Measures (a) to (c), the density controls and the student check are each stated to have been chosen after the registered results.
  - The registered verdict is presented before the secondary analyses.
- **New tables and figure.** Built by `99_report.py` from `extension/data/clean`: `tab:idlim` (London teleworkability and garden controls), `tab:natreg` (registered national results), `tab:measures` (amenity-measure comparison, with measures (a) and (b) excluding SIC 93191), `tab:dens` (density controls), `tab:pound` (appendix), and `fig:national` (national coefficients for the registered measure and measure (c), drawn natively in pgfplots).
- **Condensed.**
  - The house-price and access material is one paragraph in 6.6. `tab:access` and the continuous-treatment estimator are dropped, and `callaway2024` is removed from the bibliography.
  - The 2015 sample discussion is one sentence in 4.3.
  - The section on the 2021 coefficient is folded into 6.1 and 6.2.
- **Bibliography.** References read and verified for the appendix are added: Diamond (2016), Piyapromdee (2021), Suárez Serrato and Zidar (2016), Monte, Redding and Rossi-Hansberg (NBER WP 21706), Ahlfeldt, Redding, Sturm and Wolf (NBER WP 20354) and Rabe and Taylor (ISER WP 2010-05). Working-paper versions are cited where the working paper was the version read. Every bibitem is cited, and every citation resolves.
- **Fonts.** The preamble now loads `fontenc` (T1) and `lmodern`. The \pounds sign had triggered a bitmap TS1 font, and all fonts are now Type 1.
- **Hard fact added to the text.** Measures (b) and (c) carry pre-period coefficients of about 4 to 7. The text reports the trend-adjusted deviations, 2020 −5.28 and 2022 +9.36 for measure (c), and states that with density controls the trend-adjusted deviations are not significant (p 0.10 and 0.16). Details are under departure 8 in `extension/EXTENSION_NOTES.md`.
- **Compilation.** The report compiles to 30 pages with zero overfull boxes, underfull boxes or warnings. The prose word count is 6,410, including the abstract and front matter, which is under the 10,000 limit.
- **Style lint.** No negation flags remain. Two caption colon flags are false positives, from mathematical notation replaced by N.

## 33. Report rewritten around the final results (report round 11)

- **Title and thesis.** The title is "Valuing urban density: evidence from the COVID-19 closures in London and England and Wales". The abstract, introduction and conclusion carry the revised thesis. London is the main application of a design that extends to other cities, never a pilot.
- **Structure.** Results are 6.1 London migration, 6.2 Robustness in London, 6.3 Identification limits in London, 6.4 The response to density across England and Wales, 6.5 Separating consumption variety, 6.6 Recovery after reopening, 6.7 Prices. New subsections are 2.5 (spatial equilibrium, multiple equilibria and recovery) and 3.2 (single and multiple spatial equilibria, with the Davis and Weinstein coefficient). Methods gain 5.3 (three pre-analysis plans), 5.4 (venue-mix design) and 5.5 (recovery design).
- **Transparency.** For each registered design (national triple difference, tier design, venue-mix design, recovery design) the registered rule and verdict come before any secondary analysis. Measures (a) to (c), the density controls and the student check are labelled as chosen after the registered results. The recovery heterogeneity and the headline-minus-pseudo difference are labelled as registered further estimates outside the decision rule. The London analyses are stated to be unregistered, and the 2016 sample start is stated to have been chosen after the 2015 coefficient was seen.
- **Hard fact flagged.** The thesis text says "Four designs, two registered before estimation". Three of the four separation designs were registered (national triple difference and tier design in the national plan, venue mix in its own plan), in two plans. The report says "four designs, three of them registered in two pre-analysis plans".
- **Judgement call, Census design.** The national plan's Census MSOA design is reported inside 6.5 as the predecessor of the venue-mix design, with its opposite-signed placebo, because the list of four designs omits it.
- **Judgement call, rounding.** Tables are built from the CSVs. The 50+ placebo lower bound is −0.7246, so the report shows −0.72. RECOVERY_NOTES.md had −0.73 and was corrected. The venue-mix headline interval is shown as [−2.25, −0.31], from −2.2549.
- **Removed.** The pound-value appendix, `TAB_POUND`, `pound_table` and `CITE` in `99_report.py`, and the references cited only there (Diamond 2016, Piyapromdee 2021, Suárez Serrato and Zidar 2016, Monte, Redding and Rossi-Hansberg 2015, Ahlfeldt et al. 2014, Rabe and Taylor 2010). The PIPR methodology reference was dropped with the sentence that cited it.
- **Condensed.** London robustness and prices. Dropped from the report: Figure of all-age migration, `tab:decomp`, `tab:ddd2529`, `tab:renttests`, `tab:honest`, `tab:rentret`, `tab:hp`, `fig:hp`, `fig:ptr`. Their key numbers stay in the text. The builder functions remain in `99_report.py` and are unused by the template.
- **New tables and chart.** `tab:designs` and `tab:calendar` (static, from the notes); `tab:vm` (from `extension/venue_mix/data/v5`-`v8`), `tab:rec` and `fig:rec` (from `extension/recovery/data/r4`-`r6`), the chart drawn natively in pgfplots.
- **New references, verified online.** Davis and Weinstein (2002), AER 92(5) 1269-1289; Jedwab, Johnson and Koyama (2019), CEPR DP13523 (no journal version confirmed, so the discussion paper is cited); Monte, Porcher and Rossi-Hansberg (2026), AER 116(8) 3152-3196, whose abstract states that commuting in the largest US cities stabilised at about 60% of pre-pandemic levels while smaller cities fully recovered.
- **No new estimation.** Every figure comes from the four notes files or the CSVs behind them.
- **Compilation.** 26 pages, zero warnings, zero overfull or underfull boxes. Word count (scratch counter: prose, captions and table notes, excluding table bodies and plots): 8,456, plus 660 in the bibliography, 9,116 in all.
- **Brief.** `outputs/report/brief.md`, about 1,300 words.
## 34. Supervision summary (Paper 7, supervision 3, Part A)

- **Files.** `scripts/supervision_template.tex` holds the prose and static tables. `scripts/99_supervision.py` fills the chart placeholders by reusing `build()` from `99_report.py` and writes `outputs/supervision/supervision.tex`, a single file for Overleaf. `outputs/supervision/supervision.pdf` is the local build.
- **Shape.** Pages 1 to 3 hold the question and four findings, with no bibliography; theorists are named in the text. Pages 4 to 7 hold the working: data, measures, the triple difference, the separation designs, the recovery design, registered tests with verdicts, and reproduction steps.
- **Framing.** Findings are stated as contributions: a behavioural valuation of density by young adults; the residential value of density in Britain as one bundle, with local variety mostly food and drink; recovery of young residents outside London. Limits sit in the same sentences. Registered verdicts are in Table 4 of the working.
- **Judgement call, derived figure.** "About a quarter of the average net inflow" is 5.24 / 21.05 = 0.25, from the London 2020 triple-difference coefficient and the 2016 to 2019 mean net inflow of residents aged 20 to 29.
- **Judgement call, scope.** Prices are left out except the national rent test in Table 4.
- **Revisions.** Section 1 opens with the variety story (London against Stirling), then the closures as a switch on access, then the ranking of boroughs by amenity density and the migration comparison; Rosen and Roback, Dixit and Stiglitz, the Black Death and Miyauchi, Nakajima and Redding are dropped from it. Finding 4 now states only the division of labour with Claude Code. The sentence on exceeding the suggested hours is removed.
- **Packages.** `microtype` and `placeins` are loaded; both are standard on Overleaf.
- **No new estimation.** Every figure comes from the notes files or the CSVs behind them.
- **Compilation.** 7 pages, zero warnings, zero overfull or underfull boxes, about 3,400 words including tables.
- **Revisions, round 2.** The opening paragraph of Section 1 is rewritten in a formal register, and the recovery paragraph drops "got back" and "stayed down". Finding 4 is expanded to three paragraphs: the division of labour with Claude Code, three safeguards (checksummed plans, the notes file with labelled post hoc choices, and checks that each closure rule matches its regulation and that the national code reproduces the London estimates exactly), and why the plans mattered when specifications are cheap. The PDF stays at 7 pages with no warnings.
- **Revisions, round 3.** Section 1 now opens with agglomeration benefits for producers and consumers, explains that some residents left large cities when the first lockdown was announced, often to be nearer family, and frames the outflow as the price of giving up family proximity for city consumption and employment. The recovery paragraph asks whether young residents returned once variety was restored, and explains the choice of ages 25 to 34 as mostly past university age (student census measurement, RECOVERY_NOTES.md). Terms are explained at first use (registered test, teleworkability, the instrument, the pseudo-shock test). The section 4 safeguards and the 3.6 plans are each one sentence with a "namely" list, and the closing paragraph of section 4 is dropped. Section 3.7 (reproduction) is removed, since the worksheet asks for sources and code to be recorded in the GitHub repository and no section in the write-up. The working now follows section 4 without a page break; the PDF is 7 pages with no warnings.
- **Revisions, round 4 (final fixes, `outputs/supervision/Paper7_Supo3.tex`).** Built from the hand-edited tex, outside the template pipeline.
  - **Code note.** Added, then removed, since a local folder is inaccessible to the reader.
  - **MSOA counts, checked against the code.** 7,264 MSOAs in England and Wales. The recovery sample is 7,262 in 316 LAs, since the City of London and Isles of Scilly MSOAs are singletons dropped with their districts (`r2_msoa.csv`, `r4_estimation.csv` n_obs). The venue-mix sample is 6,856 English MSOAs, of which 57 lack `dy_2534` (Census 2021 age detail withheld or coarse) and 2 are singleton-LA MSOAs, leaving 6,797 in 294 LAs (`vm_core.msoa_frame`, `drop_singletons`). Section 1 and 3.1 now say 7,262, with a footnote; Table 3 says "6,797 English MSOAs".
  - **Amenity density wording.** The 2.49 to 32.75 range is attributed to the per-1,000 rate, which enters as a standardised log.
  - **FHRS vintage.** Added as a third limit in finding 1, with checks: the 2026 FHRS district counts correlate in logs at 0.94 to 0.96 with UK Business Counts 2019 (B1 validation), and an OSM 2019 version of access gives −6.27 (Census design, against −6.18) and −0.96 (venue mix, against −1.28). The national triple difference has not been rerun with a 2019 source, and the text says so.
  - Float pages are top-aligned. 8 pages, no warnings.
  - **Validation recomputed on 316 districts.** The B1 FHRS-against-UKBC-2019 log correlations were computed on all 318 LAs at the data-assembly stage. Recomputed (read-only, same `b1_validate.py` functions) without the City of London and the Isles of Scilly: restaurants and cafes 0.961, takeaways 0.955, pubs and bars 0.934 (318: 0.962, 0.955, 0.937). The text now says 316 districts, 0.93 to 0.96.
