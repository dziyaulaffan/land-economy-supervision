# Recovery extension: did young-adult populations return after the 2020-21 closures?

## Summary

All figures are estimates with sampling uncertainty. Coefficients are Davis and Weinstein recovery coefficients:
the change in log population from mid-2021 to the latest year regressed on the change from mid-2019 to mid-2021,
so -1 means the recovery exactly reversed the shock and 0 means none of it was reversed. The rule applied is the one
registered in `PRE_ANALYSIS_PLAN.md` (SHA-256 `a65e97a49fd14f0aa9e1d6e3ad56218a7d7300dcbc6d3d4b51f2b88aa611e569`,
verified unchanged after estimation).

**Headline (registered).** 2021 MSOAs in England and Wales, ages 25 to 34, recovery to mid-2024, shock instrumented
by measure (c) access, controls for the pre-pandemic trend, teleworkability, garden access and student share, LA
fixed effects, clustered by LA (7,262 MSOAs, 316 LAs): **beta = -0.51 (95% CI -1.11 to 0.10)**.
- Against -1: Wald p 0.111; Anderson-Rubin p 0.181 (CR1), 0.178 (wild cluster bootstrap).
- Against 0: Wald p 0.103; Anderson-Rubin p 0.057 (CR1), 0.058 (wild cluster bootstrap).
- First stage: -0.0082 log points of shock per SD of access (SE 0.0014), cluster-robust F 33.0. The Anderson-Rubin
  95% set is [-1.31, 0.01].
- The OLS coefficient is +0.35 (95% CI 0.30 to 0.40). Areas whose young-adult population fell further in 2019-21
  kept falling, so the instrument changes the answer completely.

**Heterogeneity.** The instrument is weak within most subsamples, so most cells carry little information.
- Outside London (6,261 MSOAs, F 27.9): -0.71 (95% CI -1.37 to -0.05). This excludes 0 and contains -1, which
  reads as full recovery.
- London (1,001 MSOAs, F 1.3): +0.15 with an unbounded Anderson-Rubin set. The data cannot say whether London
  persisted.
- Density terciles (F 1.7, 7.4, 0.2) and access terciles (F 0.6, 6.9, 0.2) are weak in five of six cells.
  - Low and middle density: point estimates -2.28 and -2.04, Anderson-Rubin sets (-inf, -0.14] and (-inf, -0.77].
  - High density: an empty Anderson-Rubin set, which signals that the instrument is related to recovery other
    than through the shock in the densest MSOAs.
- The pattern "persistence in the largest cities, recovery elsewhere" fits the point estimates for London against
  the rest, but the London estimate is uninformative and cannot support it.

**Placebos.**
- Ages 50 and over: -0.31 (95% CI -0.72 to 0.11; F 55.8; corrected from -0.73, the exact bound is -0.7246). This excludes -1 and contains 0.
- Pseudo shock 2015-17 with recovery 2017-19: **+1.28 (95% CI 0.81 to 1.76; F 28.8)**. This is not ordinary mean
  reversion. In normal years, high-access MSOAs whose young-adult growth slowed kept slowing, beyond their
  2011-15 trend.
- Headline minus pseudo: -1.79 (95% CI -2.54 to -1.04). Relative to how these places moved before the pandemic,
  the 2021-24 rebound was large.

**Verdict under the registered rule: inconclusive.** The first-stage F exceeds 10, so the Wald interval applies.
At [-1.11, 0.10] it contains both -1 (full recovery, single equilibrium) and 0 (lasting shift, multiple
equilibria).
- The point estimate sits midway, at partial recovery.
- The Anderson-Rubin test rejects neither benchmark at 5%, though zero is close (p 0.058).
- The pseudo-shock placebo shows that measure (c) predicts two-year growth in ordinary years, after the
  pre-pandemic trend control. The exclusion restriction (access affects 2021-24 growth only through the 2019-21
  shock) is therefore doubtful. The headline beta mixes recovery from the closures with whatever dynamic access
  already carried.

## Step 4: all estimates

`data/r4_estimation.md` (CSV alongside). Wald CI from CR1 with t(G - 1); Anderson-Rubin set by grid inversion
(-5 to 5, step 0.005).

| Model | beta | 95% CI | p vs -1 | p vs 0 | First stage (SE); F | AR set | Reading |
|---|---|---|---|---|---|---|---|
| **MSOA 25-34, IV measure (c) (headline)** | -0.51 | [-1.11, 0.10] | 0.111 | 0.103 | -0.0082 (0.0014); 33.0 | [-1.31, 0.01] | inconclusive |
| MSOA 25-34, OLS | +0.35 | [0.30, 0.40] | <0.001 | <0.001 | - | - | shock deepened |
| MSOA 25-34, IV VDL | +0.56 | [-0.39, 1.51] | 0.001 | 0.249 | -0.0020 (0.0007); 8.9 | [-0.68, 1.86] | lasting shift (AR, F < 10) |
| MSOA 20-29, IV measure (c) | -0.72 | [-1.69, 0.26] | 0.564 | 0.149 | -0.0068 (0.0017); 15.3 | [-2.46, 0.01] | inconclusive |
| MSOA 20-29, OLS | +0.32 | [0.26, 0.38] | <0.001 | <0.001 | - | - | shock deepened |
| MSOA 20-29, IV VDL | +0.26 | [-2.26, 2.78] | 0.327 | 0.840 | -0.0009 (0.0008); 1.2 | unbounded | inconclusive |
| LA 25-34, IV M_c, to 2025 | -0.14 | [-0.68, 0.40] | 0.002 | 0.612 | -0.020 (0.002); 82.1 | [-0.73, 0.36] | lasting shift |
| LA 25-34, OLS, to 2025 | +0.66 | [0.42, 0.90] | <0.001 | <0.001 | - | - | shock deepened |
| LA 25-34, IV VDL, to 2025 | -1.08 | [-2.72, 0.56] | 0.921 | 0.195 | +0.0040 (0.0013); 10.0 | [-4.49, 0.20] | inconclusive |
| LA 25-34, IV M_c, to 2024 | -0.17 | [-0.63, 0.29] | <0.001 | 0.461 | -0.020 (0.002); 82.1 | [-0.69, 0.26] | lasting shift |
| LA 25-34, OLS, to 2024 | +0.56 | [0.36, 0.77] | <0.001 | <0.001 | - | - | shock deepened |
| LA 20-29, IV M_c, to 2025 | -0.52 | [-1.08, 0.04] | 0.091 | 0.068 | -0.021 (0.003); 45.5 | [-1.15, 0.02] | inconclusive |
| LA 20-29, OLS, to 2025 | +0.17 | [-0.03, 0.37] | <0.001 | 0.103 | - | - | lasting shift |
| LA 20-29, IV VDL, to 2025 | -2.39 | [-5.43, 0.64] | 0.367 | 0.122 | +0.0032 (0.0015); 4.8 | (-inf, -0.45] | inconclusive (unbounded) |
| LA 20-29, IV M_c, to 2024 | -0.62 | [-1.11, -0.13] | 0.128 | 0.013 | -0.021 (0.003); 45.5 | [-1.20, -0.17] | full recovery |
| LA 20-29, OLS, to 2024 | +0.17 | [-0.01, 0.35] | <0.001 | 0.065 | - | - | lasting shift |

LA models use region fixed effects and each LA as its own cluster. Across LAs, measure (c) is a strong instrument
(F 82 at 25-34), and the 25-34 coefficient is near zero with -1 rejected. At 20-29 it is closer to -1. The variety-days-lost
instrument is weak at both levels (F 1.2 to 10.0) and its first stage changes sign between MSOAs and LAs.

## Step 5: heterogeneity (MSOA, 25-34, IV measure (c), LA fixed effects within each subsample)

`data/r5_heterogeneity.md`.

| Subsample | beta | 95% CI | F | AR set | AR p vs -1 / vs 0 (WCB) | Reading | MSOAs / LAs |
|---|---|---|---|---|---|---|---|
| Density low (< 1,261 per km2) | -2.28 | [-6.92, 2.37] | 1.7 | (-inf, -0.14] | 0.400 / 0.033 | inconclusive (unbounded) | 2,397 / 246 |
| Density middle | -2.04 | [-4.14, 0.06] | 7.4 | (-inf, -0.77] | 0.162 / <0.001 | inconclusive (unbounded) | 2,395 / 279 |
| Density high (> 3,910 per km2) | +24.8 | [-80.4, 130.1] | 0.2 | empty | <0.001 / <0.001 | inconclusive (empty set) | 2,394 / 212 |
| Access low (Z_c < -0.31) | -3.66 | [-14.8, 7.5] | 0.6 | (-inf, -0.10] U [2.64, inf) | 0.304 / 0.042 | inconclusive (unbounded) | 2,394 / 225 |
| Access middle | -0.46 | [-1.59, 0.68] | 6.9 | [-3.33, 0.56] | 0.442 / 0.395 | inconclusive | 2,404 / 263 |
| Access high (Z_c > 0.39) | +13.1 | [-38.4, 64.6] | 0.2 | (-inf, -2.41] U [2.91, inf) | 0.017 / 0.002 | inconclusive (unbounded) | 2,405 / 150 |
| London | +0.15 | [-2.71, 3.00] | 1.3 | unbounded | 0.595 / 0.922 | inconclusive (unbounded) | 1,001 / 32 |
| Rest of England and Wales | -0.71 | [-1.37, -0.05] | 27.9 | [-1.65, -0.17] | 0.444 / 0.008 | full recovery | 6,261 / 284 |

## Step 6: placebos (MSOA, LA fixed effects)

`data/r6_placebos.md`.

| Model | beta | 95% CI | F | AR set | Reading |
|---|---|---|---|---|---|
| Ages 50+, IV measure (c) | -0.31 | [-0.72, 0.11] | 55.8 | [-0.80, 0.07] | lasting shift |
| Ages 50+, OLS | +0.17 | [0.07, 0.27] | - | - | shock deepened |
| Pseudo 2015-17 / 2017-19, 25-34, IV measure (c) | +1.28 | [0.81, 1.76] | 28.8 | [0.88, 1.93] | shock deepened |
| Pseudo, OLS | +0.34 | [0.28, 0.39] | - | - | shock deepened |

Headline minus pseudo (common sample, joint cluster-robust covariance): -1.79 (95% CI -2.54 to -1.04; p < 0.001).

## Step 1: population stocks and rebasing

Files: `data/r1_pop_la.csv`, `data/r1_pop_msoa.csv`, `data/r1_check_msoa_vs_la.csv`; script `scripts/r1_population.py`.

- **Local authorities.** ONS "Population estimates and components of change, detailed time series 2011 to 2025"
  (release MYE25, published 29 July 2026; workbook `myebtablesenglandwales20112025.xlsx`, sheet MYEB1).
  - It holds single year of age 0-90+ by sex, 318 April 2023 LADs, mid-2011 to mid-2025. The copy downloaded for
    the national extension was reused (URL in the script).
  - The cover sheet states that the series is "consistent with the results of the 2021 Census".
  - Mid-2012 to mid-2020 are rebased: the notes say that for 2012 to 2021 the "other change" component includes
    unattributable change introduced by rebasing to Census 2021.
  - Mid-2022 to mid-2024 were revised in MYE25 for updated international migration.
- **MSOAs.** Nomis NM_2014_1, "Population estimates - small area (2021 based) by single year of age", 7,264 2021
  MSOAs, persons, mid-2011 to mid-2024. Mid-2024 is the latest year; the dataset was first released 20 June 2024
  and last updated 7 November 2025.
  - The 2011-based small area series (NM_2010_1) was not used: it stops at mid-2020, is on 2011 geography and
    is not rebased.
- **Comparability.**
  - For 2011 to 2021, MSOA sums equal the MYE25 LA figures exactly, for every LA, year and group. So the MSOA
    series is the rebased one, and mid-2021 rests on Census 2021 at both levels.
  - For 2022 to 2024 the MSOA sums differ from MYE25. The mean absolute difference at 25-34 is 0.4%, 0.7% and 1.0%;
    the maximum is 6.2%, 11.6% and 6.3%. The likely reason is that the MSOA series was last updated in November
    2025, before MYE25 revised mid-2022 to mid-2024 for international migration.
  - In log changes with LA fixed effects the gap is an LA constant and drops out of every MSOA model.
- **What rebasing means for the shock.** The rebasing spreads the intercensal error over 2012 to 2021, so the
  2019 to 2021 change is not one step from a rolled-forward 2019 figure to a census-based 2021 figure.
  - The 2021 figures still rest on a census taken in March 2021, during the third lockdown.
  - Students were counted at term-time addresses by the census rules, but many were living elsewhere. So the
    20-29 group around universities may be measured with error that differs from other years.
  - That error sits in both the shock and the recovery with opposite signs, which pushes OLS (not IV) towards -1.
    The OLS estimates here are positive, so this bias is not visibly dominating.
- **Groups.** 25-34 (single years 25-34), 20-29 (single years 20-29), 50 and over (LA: single years 50-90+; MSOA:
  the published bands 50-64 plus 65+).
- England and Wales totals (millions): 25-34 8.05 (2019), 8.03 (2021), 8.40 (2024), 8.33 (2025); 20-29 7.69,
  7.48, 7.78, 7.77; 50+ 22.23, 22.78, 23.57, 23.77.

## Step 2: shock, recovery and exposure

Files: `data/r2_msoa.csv`, `data/r2_la.csv`, `data/r2_summary.md`; script `scripts/r2_shock_exposure.py`.

- 25-34 across MSOAs (log points x 100):
  - shock mean -0.10 (SD 6.57);
  - recovery to 2024 mean +3.07 (SD 8.67);
  - pre-trend mean +0.83 a year (SD 2.56).
- 25-34 across LAs: shock +0.41 (SD 3.18); recovery to 2025 +2.66 (SD 4.94).
- 20-29 across MSOAs: shock -2.22 (SD 6.82); recovery +1.57 (SD 9.58).
- Correlation of the 25-34 shock with measure (c):
  - MSOAs: -0.28 raw, -0.11 within LA;
  - LAs: -0.55 raw, -0.40 within region.
- Correlation of the 25-34 shock with variety-days lost: +0.13 raw and +0.07 within LA (MSOAs); +0.27 raw (LAs).
  The sign is opposite to the closure story: more variety-days lost goes with a larger young-adult gain in
  2019-21. The two exposure measures correlate -0.15 across MSOAs.

## Step 3: pre-analysis plan

`PRE_ANALYSIS_PLAN.md`, written after Steps 1-2 and before any recovery regression. Its checksum still verifies.

## Departures from the plan

None. Every registered estimate was run as written.

## Judgement calls

1. **Latest year.** MSOAs: mid-2024, the latest small-area year. LAs: mid-2025, as the instruction asks for the
   latest year, with a mid-2024 version alongside so the two levels can be compared.
2. **MSOA series not raked to MYE25** for 2022-24. With LA fixed effects raking would change nothing; without them
   (no MSOA model here) it would matter.
3. **Measure (c) at MSOA level** is the log of the MSOA's own FHRS access index (the input to the LA measure),
   standardised over all 7,264 MSOAs. At LA level it is M_c from Departure 8 of the national extension.
4. **Variety-days lost** is the main-window measure (23 Mar 2020 to 22 Mar 2021) at both levels, the window closest
   to the 2019-21 shock.
5. **LA-level models** use region fixed effects (LA effects are impossible with one row per LA) and
   heteroskedasticity-robust errors, City of London and Isles of Scilly excluded (316 LADs).
6. **Pseudo-shock trend control** is 2011-15, so that it does not overlap the pseudo shock.
7. **50+ at MSOA level** uses the published 50-64 and 65+ bands, which match the single-year sum by definition.
8. **Instrument scaling.** First-stage coefficients are per SD of measure (c), or per 10 variety-days lost.
9. **Anderson-Rubin bootstrap.** The bootstrap partials out LA effects by demeaning, which commutes with
   cluster-level weights because LA effects nest in LA clusters. The controls stay in the bootstrap regression.

## Hard caveats

- **Exclusion restriction.** Davis and Weinstein's design needs the instrument to move recovery only through the
  shock. Access to food and drink venues plausibly affects young-adult growth in any period: the pseudo-shock
  placebo shows exactly that in 2015-19. The headline therefore cannot be read cleanly as recovery from the
  closures.
- **Weak instruments in subsamples.** Most heterogeneity cells have F below 10, and London's is 1.3. The
  production-side pattern (large cities persist) cannot be tested with this instrument inside London.
- **Census timing.** The mid-2021 anchor rests on a census taken in lockdown (see Step 1).

## File index

- `PRE_ANALYSIS_PLAN.md`, `PRE_ANALYSIS_PLAN.sha256`
- `scripts/rc_common.py` (paths), `scripts/rc_core.py` (2SLS, Anderson-Rubin, classification rule)
- `scripts/r1_population.py` (Step 1), `scripts/r2_shock_exposure.py` (Step 2), `scripts/r4_estimation.py`
  (Step 4), `scripts/r5_heterogeneity.py` (Step 5), `scripts/r6_placebos.py` (Step 6)
- Raw MSOA downloads: `C:\Users\dziya\research-data\london-variety-extension\raw\recovery\nm2014_msoa21_<year>.csv`
- All steps are registered at the end of `extension/run_all.py`.
