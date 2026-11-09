# Pre-analysis plan: recovery of young-adult populations after the 2020-21 closures

Written on 30 October 2026, after Steps 1 and 2 (population stocks; shock, recovery and exposure descriptives) and
before any recovery regression was estimated. A SHA-256 checksum is saved in `PRE_ANALYSIS_PLAN.sha256`. This file
is not to be revised after estimation begins. Departures are reported separately in `RECOVERY_NOTES.md`.

## 0. What was seen before writing

- Step 2 descriptives (`data/r2_summary.md`): means, SDs and percentiles of the shock, recovery, trend and pseudo
  variables, and the correlation of each shock with each exposure measure (raw and within LA or region). Across
  MSOAs the within-LA correlation of the 25-34 shock with measure (c) is -0.11, and with variety-days lost +0.07.
  The shock-recovery correlation was not computed.
- Earlier work in this project related measure (c) and variety-days lost to migration flows and census inflow
  rates, but never to population stocks or to the 2021 to 2024 change.

## 1. Data and variables

- MSOA stocks: Nomis NM_2014_1 (small area estimates, 2021 based, 2021 MSOAs), mid-2011 to mid-2024. Their sums
  equal the MYE25 local authority series exactly for 2011 to 2021. For 2022 to 2024 they predate the MYE25
  revision for international migration and differ from it by up to 12% in some LAs (mean 1% at 25-34). With
  local authority fixed effects this difference is an LA constant in log changes and drops out of MSOA models.
- LA stocks: MYE25 detailed time series (MYEB1), mid-2011 to mid-2025, 2023 LADs, City of London and Isles of
  Scilly excluded (316 LADs).
- For group g: shock = ln P(2021) - ln P(2019); recovery = ln P(latest) - ln P(2021), latest = 2024 for MSOAs and
  2025 for LADs; trend = (ln P(2019) - ln P(2015)) / 4.
- Instrument, MSOA: measure (c) at MSOA level, the log of FHRS access (restaurants and cafes, pubs, bars and clubs,
  takeaways; 1.5 km decay; point-based), standardised over the 7,264 MSOAs (`Z_c` in `data/r2_msoa.csv`).
- Instrument, LA: M_c, the log of the population-weighted mean of the same index, standardised over 316 LADs.
- Alternative instrument: variety-days lost, 23 Mar 2020 to 22 Mar 2021, from `extension/venue_mix/` (FHRS,
  1.5 km), divided by 10 (`Z_vdl`).
- Controls: the group's own pre-pandemic trend, teleworkability, garden access, student share (S1 MSOA or LA
  versions).

## 2. Headline specification

Sample: 2021 MSOAs in England and Wales; LAs with a single MSOA (City of London, Isles of Scilly) drop out under LA
fixed effects. Unweighted 2SLS:

    recovery_m = beta * shock_m + g1 trend_m + g2 telework_m + g3 garden_m + g4 student_m + a_l(m) + e_m
    shock_m    = pi * Z_c,m + (same controls) + a_l(m) + v_m

for ages 25 to 34. beta is the Davis and Weinstein coefficient.

Inference: CR1 standard errors clustered by local authority; 95% confidence interval from t with G - 1 degrees of
freedom. Each benchmark (beta = -1 and beta = 0) is tested two ways: the Wald t-test with CR1 standard errors, and
the Anderson-Rubin test (regress recovery - b0 * shock on the instrument and controls with LA fixed effects; test
the instrument coefficient), with CR1 p-values and wild cluster restricted bootstrap p-values (Rademacher,
B = 9,999, seed 20261028). The Anderson-Rubin 95% confidence set is found by inverting the CR1 Anderson-Rubin test
over a grid of b0 from -5 to 5 in steps of 0.005. First stage: coefficient, CR1 SE and the cluster-robust F
(the squared t, equal to the Kleibergen-Paap Wald F with one instrument).

## 3. Registered decision rule

The interval used is the 95% Wald interval if the first-stage cluster-robust F is at least 10, and the 95%
Anderson-Rubin set otherwise.

- Full recovery, consistent with a single stable equilibrium: the interval contains -1 and excludes 0.
- Lasting shift, consistent with multiple equilibria: the interval contains 0 and excludes -1.
- Partial recovery: the interval excludes both -1 and 0, with the point estimate between -1 and 0.
- Inconclusive: the interval contains both -1 and 0, or is unbounded.
- Outside the benchmarks: the interval excludes both and the point estimate lies below -1 (over-recovery) or above
  0 (the shock deepened afterwards). These are reported as such.

The verdict applies to the headline only. Every other estimate is reported with its classification but does not
change the verdict.

## 4. Further estimates (Step 4 to Step 6)

4.1 OLS: the headline equation by OLS (no instrument).
4.2 VDL instrument: the headline with Z_vdl in place of Z_c.
4.3 Ages 20 to 29: the headline, the OLS version and the VDL-instrument version for 20 to 29 (its own shock,
    recovery and trend).
4.4 Local authority level: the same equations across 316 LADs with region fixed effects in place of LA fixed
    effects and heteroskedasticity-robust (each LA its own cluster, CR1) standard errors; instrument M_c, or
    Z_vdl; ages 25-34 and 20-29; IV and OLS. Recovery to mid-2025; the version to mid-2024 is reported alongside.
4.5 First stage reported for every instrumented model.
4.6 Heterogeneity (Step 5), headline IV specification within: terciles of log population density (Census 2021
    TS006; terciles over the headline sample); terciles of Z_c (over the headline sample); London against the rest
    of England and Wales. LA fixed effects within each subsample. Splitting on Z_c narrows the instrument's range
    within each tercile, so weak first stages are expected there; they are reported regardless.
4.7 Placebos (Step 6): (i) ages 50 and over with their own shock, recovery and trend, instrument Z_c; (ii) pseudo
    shock: shock = ln P(2017) - ln P(2015), recovery = ln P(2019) - ln P(2017), trend = (ln P(2015) - ln P(2011)) / 4,
    ages 25 to 34, instrument Z_c, otherwise as the headline. The pseudo coefficient measures ordinary two-year
    reversion; the difference between the headline and the pseudo coefficient is reported with a CR1 confidence
    interval from the joint cluster-robust covariance of the two IV estimates (same MSOAs, clustered by LA).

## 5. Fixed in advance

- No weights, trimming or winsorising. MSOAs with a missing variable are dropped and counted.
- All estimates are reported whatever their sign or significance.
- Logs are natural; changes are in log points (a coefficient of -1 means the recovery exactly reverses the shock).
