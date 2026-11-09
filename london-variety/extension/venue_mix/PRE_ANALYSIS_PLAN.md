# Pre-analysis plan: venue mix, closures and young-adult migration

Written on 30 October 2026, after Steps 1 to 3 (closure calendar, treatment, design diagnostics) and before any
migration outcome was opened for this extension. A SHA-256 checksum of this file is saved in
`PRE_ANALYSIS_PLAN.sha256`. The file is not to be revised after estimation begins. Any departure is reported
separately in `VENUE_MIX_NOTES.md` under "Departures from the plan".

## 0. Prior exposure to the outcome data (disclosure)

The outcome files used here were built earlier for the national extension (`extension/data/clean/s4_msoa_inflows_on_msoa21.csv`,
`extension/data/clean/b3_migration_la_year_by_age_group.csv`). Earlier work regressed the 2011 to 2021 change in MSOA
inflow rates at ages 25 to 34 on a measure of the level of hospitality and arts access (Departure 4 of the national
plan, about -6 per 1,000 per SD), and estimated the national LA triple difference with the registered amenity
measure. The venue-mix treatment defined below has not been related to any outcome. The diagnostics of Step 3
show that the treatment correlates -0.92 across English MSOAs with the takeaway share of food and leisure access
(takeaways never closed and are a quarter of access on average), so the treatment is close to an inverse takeaway
share. This was known when the plan was written.

## 1. Treatment

`vdl_main_fhrs_l15` from `extension/venue_mix/data/v2_treatment_msoa.csv`: variety-days lost between 23 March 2020
and 22 March 2021, for each 2021 MSOA, equal to 365 times the access-weighted mean of the share of days each venue type
was closed in the MSOA's local authority. Access uses 1.5 km exponential decay from the MSOA population-weighted
centroid. Pubs and bars, restaurants and cafes and takeaways come from the food hygiene register (FHRS, extract of
October 2026), with OSM nightclub access subtracted from FHRS pubs, bars and nightclubs. Cinemas, theatres and arts
centres, gyms and nightclubs come from OpenStreetMap at 31 December 2019. Closure shares come from the regulation
calendar in `v1_closure_shares_lad23.csv`.

Coefficients are reported per 10 variety-days lost (treatment divided by 10) and, in addition, per standard
deviation of the treatment in the estimation sample.

## 2. Headline specification

Sample: 2021 MSOAs in England with Census 2011 and Census 2021 counts for ages 25 to 34 in the harmonised file
(the 59 MSOAs that the ONS API blocked for 2021 bands, and the 2 with coarse bands only, are absent). Local
authorities with a single MSOA (City of London, Isles of Scilly) are dropped because a local authority fixed
effect absorbs them.

Outcome: `rate_per_1000` for age band 25-34 in Census 2021 minus the same in Census 2011 (one-year-ago movers, all
movers, per 1,000 residents of that age), from `s4_msoa_inflows_on_msoa21.csv`.

Regression, unweighted OLS:

    dy_m = beta * VDL_m / 10 + gamma' X_m + alpha_l(m) + e_m

X_m: log total access (FHRS, 1.5 km), log population density (Census 2021 TS006), log job density (BRES 2019),
teleworkability, garden access, share of households in flats, private renting share, share aged 20 to 39, student
share (the Step 3 controls, file `v3_controls_msoa.csv`). alpha_l: 2023 local authority fixed effects.

Inference: CR1 standard errors clustered by local authority; 95% confidence interval from t with G - 1 degrees of
freedom; wild cluster restricted bootstrap p-value (Rademacher weights, B = 9,999, seed 20261028), clustered by
local authority. The bootstrap p-value is the one used in the decision rule.

## 3. Registered decision rule

The evidence supports the variety channel only if all three conditions hold.

1. Headline: beta < 0 with bootstrap p < 0.05.
2. Placebo near zero: the same specification on the 2001 to 2011 change at ages 25 to 34 gives a coefficient with
   bootstrap p >= 0.10 and an absolute value no larger than half the absolute headline coefficient. The 2001 rate
   excludes people with no usual address one year before (`rate_excl_nua_per_1000`), because the 2011 census has
   no such category; the version including them is reported alongside.
3. Smaller response at ages 50 and over: the same specification on the 2011 to 2021 change for ages 50 and over
   (migrants and residents summed over the 50-64, 65-74 and 75+ bands) gives a coefficient smaller in absolute
   value than the headline, and the stacked difference (Section 4.3) is negative.

A null headline (p >= 0.05) or a positive headline coefficient counts against the variety channel. A negative and
significant headline with condition 2 or 3 failing is reported as "not supported under the registered rule".

## 4. Further estimates (reported, not part of the decision rule)

4.1 Step 5. The headline specification for ages 20 to 24 and 20 to 34; the headline with no controls (LA fixed
effects only) and then adding each control on its own; the headline dropping MSOAs in the top decile of student
share (decile computed over the English estimation sample); the headline with the OSM version of the treatment
(`vdl_main_osm_l15`, with log total OSM access as the access control).

4.2 Step 6 placebo: as in condition 2, also for ages 20 to 34.

4.3 Step 6 stacked comparison: rows are MSOA by age group (25 to 34 and 50+), outcome the 2011 to 2021 change.
Regressors: MSOA fixed effects, an age-group fixed effect, VDL/10 x young, and each Step 3 control x young. The
coefficient on VDL/10 x young is the difference (young minus 50+). Clustered by local authority, bootstrap as
above. A second version adds local-authority-by-age-group fixed effects; the first version (as specified in the
task) is the one used in condition 3.

4.4 Step 7 local authority panel. The national panel of net internal migration per 1,000 mid-2019 residents of
each age group, years ending June 2016 to 2025, 316 local authorities (City of London and Isles of Scilly dropped as
in the national extension), young adults 20 to 29 against the family proxy (0 to 15 and 30 to 49). The treatment
is the local authority version of variety-days lost over the year to June 2021 (`vdl_yr_jun2021_fhrs_l15` in
`v2_treatment_lad.csv`, population-weighted mean over MSOAs), divided by 10. Differenced triple difference
(`e_core.ddd_diff`) with treatment x year (2019 omitted), region-by-year fixed effects, and teleworkability x year
and garden access x year (the national controls, which in the differenced form are the controls interacted with
the young-adult indicator and year). The coefficient of interest is treatment x 2021 (year ending June 2021); a
negative value is in the direction of the variety channel. Wild cluster bootstrap p-values clustered by local
authority.

4.5 Step 7 reopening test. The same model with the reopening treatment (`vdl_reopen_fhrs_l15`, share of variety
closed 1 April to 31 July 2021, in days over that window scaled to 365, divided by 10) in place of the main
treatment. The test is the contrast reopening x 2022 minus reopening x 2021; a negative contrast means a smaller
young-adult recovery in the year to June 2022 where more variety stayed closed, in the direction of the variety
channel. A second version includes both treatments together. In England the reopening treatment varies only
through the venue mix, because the 2021 steps were national; Welsh authorities add calendar variation.

4.6 Step 8 robustness of the headline: adding Welsh MSOAs (Welsh closure dates); 1 km and 3 km decay (with log
total access at the same decay); excluding London.

## 5. Things fixed in advance

- No weights. No trimming or winsorising of outcomes.
- Missing controls: none expected; any MSOA with a missing control is dropped and the count reported.
- All coefficients are reported whatever their sign or significance.
- The verdict in VENUE_MIX_NOTES.md applies only the rule in Section 3.
