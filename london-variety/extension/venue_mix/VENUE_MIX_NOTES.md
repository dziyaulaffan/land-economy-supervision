# Venue-mix extension: variety-days lost and young-adult migration

## Summary

All figures are estimates with sampling uncertainty. Coefficients are per 10 variety-days lost unless stated, and
outcomes are one-year-ago movers per 1,000 residents of the age group. The headline rule is the one registered in
`PRE_ANALYSIS_PLAN.md` (SHA-256 `5dd46661ed98078221bec8ed924f62ef71652a0e8d28c28dcc26dad1c1b0e0ae`, verified
unchanged after estimation).

**Step 3 design diagnostics (England, 6,856 MSOAs, 296 LAs, run before any outcome was opened).** The main
treatment has mean 171 days and SD 17.9 days. LA fixed effects alone explain 52% of its variance, and LA effects
plus the nine controls explain 67%. The residual SD is 10.4 days, 58% of the raw SD and 69% of the within-LA
variance, so the pre-set stopping rule (residual SD under 2 days or under 10% of the raw SD) was not triggered.
Within LAs, the treatment correlates +0.41 with teleworkability, -0.33 with log population density, -0.22 with
garden access, -0.21 with log total access and +0.15 with the student share. It correlates -0.92 with the takeaway
share of access. Takeaways never closed, nightclubs were closed every day of the window, and cinemas, theatres,
gyms and nightclubs together are about 2% of access, so the measure behaves almost as an inverse takeaway share.
Residual maps for London, Greater Manchester and the West Midlands metropolitan county are in `data/figures/`
(residual SD 6.9, 7.5 and 9.1 days).

**Headline (registered).** Change in the 25-34 inflow rate between Census 2011 and Census 2021, LA fixed effects and
all Step 3 controls, 6,797 MSOAs in 294 LAs: **-1.28 per 10 days (95% CI -2.26 to -0.31; bootstrap p 0.011)**, or
-2.29 per SD of the treatment (95% CI -4.04 to -0.55). The mean change in the outcome is -13.8 per 1,000 (SD 38.7).
The sign depends on the controls. With LA effects alone the coefficient is +0.65 (p 0.173). Teleworkability alone
moves it to -1.97, while garden access, flats or private renting alone move it to between +1.03 and +1.32.

**Placebo and age comparison.** The same specification on the 2001 to 2011 change at ages 25-34 gives **+3.28
(95% CI 2.27 to 4.29; p < 0.001)**, opposite in sign to the headline and more than twice its size. Ages 50 and over
give +0.24 (95% CI -0.06 to 0.55; p 0.116), smaller in absolute value than the headline. The registered stacked
difference (25-34 minus 50+, MSOA and age-group effects) is -0.19 (95% CI -1.29 to 0.90; p 0.743). With LA-by-age
effects it is -1.53 (95% CI -2.51 to -0.54; p 0.004).

**Reopening test (LA panel, 316 LAs, 20-29 against the family proxy).** A smaller young-adult recovery in the year to
June 2022 where more variety stayed closed from April to July 2021 would give a negative contrast. The estimate is
**-0.50 (95% CI -9.39 to 8.38; p 0.926)**. The year-to-June-2021 treatment gives -1.19 in the year ending June
2021 (95% CI -3.88 to 1.50; p 0.398) and +1.90 in the year ending June 2020 (p 0.028).

**Verdict under the registered rule: not supported.** Condition 1 holds (negative headline, p 0.011) and condition
3 holds (the 50+ coefficient is smaller and the registered stacked difference is negative, though far from
significant). Condition 2 fails: the placebo is large, positive and precisely estimated. MSOAs with more
variety-days lost saw 25-34 inflow rates rise faster between 2001 and 2011 and then rise more slowly between 2011
and 2021. Mean reversion or a long-running cycle in these neighbourhoods fits that pattern at least as well as the
2020-21 closures. The LA panel and reopening test add nothing in favour. The robustness checks (Step 8) keep the
headline sign but cannot repair the placebo.

## Results tables

Full tables: `data/v5_main.md`, `data/v6_placebo_age.md`, `data/v7_la_panel.md`, `data/v8_robustness.md` (CSV
versions alongside). Wild cluster restricted bootstrap p-values (Rademacher, B = 9,999, seed 20261028), clustered
by LA; 95% CIs from CR1 standard errors with t(G - 1).

### Step 5 (England, 25-34 unless stated)
| Specification | Coef | 95% CI | p (WCB) | Per SD |
|---|---|---|---|---|
| Headline, all controls | -1.28 | [-2.25, -0.31] | 0.011 | -2.29 |
| 20-24, all controls | -2.08 | [-3.54, -0.62] | 0.006 | -3.72 |
| 20-34, all controls | -1.46 | [-2.42, -0.51] | 0.004 | -2.62 |
| LA FE only | +0.65 | [-0.29, 1.59] | 0.173 | +1.17 |
| + log total access only | -0.33 | [-1.30, 0.63] | 0.492 | -0.60 |
| + log population density only | -0.84 | [-1.81, 0.13] | 0.090 | -1.51 |
| + log job density only | -0.06 | [-0.99, 0.88] | 0.903 | -0.10 |
| + teleworkability only | -1.97 | [-2.99, -0.96] | <0.001 | -3.53 |
| + garden access only | +1.03 | [0.13, 1.93] | 0.024 | +1.84 |
| + flat share only | +1.32 | [0.44, 2.20] | 0.003 | +2.36 |
| + private renting only | +1.17 | [0.29, 2.05] | 0.009 | +2.10 |
| + share aged 20-39 only | +0.54 | [-0.40, 1.48] | 0.267 | +0.96 |
| + student share only | +0.85 | [-0.06, 1.76] | 0.066 | +1.53 |
| Top student-share decile dropped (> 8.5%) | -1.02 | [-1.95, -0.10] | 0.034 | -1.81 |
| OSM treatment (per 10 days; OSM SD 22.9 days) | -0.96 | [-1.59, -0.33] | 0.004 | -2.19 |

### Step 6
| Specification | Coef | 95% CI | p (WCB) |
|---|---|---|---|
| Placebo 2001-2011, 25-34 (2001 excl. no usual address; registered) | +3.28 | [2.27, 4.29] | <0.001 |
| Placebo 2001-2011, 25-34 (2001 incl. no usual address) | +2.70 | [1.69, 3.71] | <0.001 |
| Placebo 2001-2011, 20-34 | +2.40 | [1.36, 3.43] | <0.001 |
| Ages 50+, 2011-2021 | +0.24 | [-0.06, 0.55] | 0.116 |
| Stacked 25-34 minus 50+, MSOA and age-group FE (registered) | -0.19 | [-1.29, 0.90] | 0.743 |
| Stacked, LA-by-age-group FE | -1.53 | [-2.51, -0.54] | 0.004 |

### Step 7 (LA panel; treatment SD across LAs 10.2 days for D, 6.9 days for R)
| Model | Term | Coef | 95% CI | p (WCB) |
|---|---|---|---|---|
| D, year to June 2021 | year ending June 2021 | -1.19 | [-3.88, 1.50] | 0.398 |
| D | year ending June 2020 | +1.90 | [0.27, 3.53] | 0.028 |
| D | 2022 minus 2021 | +0.94 | [-3.03, 4.91] | 0.706 |
| D | pre-period average 2016-18 | -0.20 | [-1.87, 1.47] | 0.809 |
| R, reopening (registered test) | 2022 minus 2021 | -0.50 | [-9.39, 8.38] | 0.926 |
| R | year ending June 2020 | +3.83 | [0.62, 7.04] | 0.023 |
| D and R jointly | D, 2021 | -2.65 | [-5.86, 0.56] | 0.111 |
| D and R jointly | R, 2022 minus 2021 | -4.41 | [-14.28, 5.47] | 0.406 |
| D, OSM version | 2021 | -0.07 | [-1.49, 1.35] | 0.922 |

### Step 8 (25-34, all controls)
| Specification | Coef | 95% CI | p (WCB) | Per SD | MSOAs / LAs |
|---|---|---|---|---|---|
| Headline (England, 1.5 km) | -1.28 | [-2.25, -0.31] | 0.011 | -2.29 | 6,797 / 294 |
| England and Wales, Welsh dates | -1.30 | [-2.22, -0.38] | 0.007 | -2.34 | 7,201 / 316 |
| 1 km decay | -0.94 | [-1.67, -0.21] | 0.013 | -2.02 | 6,797 / 294 |
| 3 km decay | -1.47 | [-3.16, 0.22] | 0.088 | -1.93 | 6,797 / 294 |
| England excluding London | -1.37 | [-2.38, -0.35] | 0.012 | -2.47 | 5,796 / 262 |

## Step 1. Closure calendar by venue type

Files: `data/v1_regulation_calendar.csv` (42 rules, each with regulation, provision and an automatic check against
the downloaded legislation.gov.uk text, all passing), `data/v1_closure_daily_ltla20.csv.gz` (336 LTLAs x 671 days,
1 March 2020 to 31 December 2021), `data/v1_closure_daily_lad23.csv.gz`, `data/v1_closure_shares_lad23.csv`,
`data/v1_validation.csv` (16 spot checks, all passing). Scripts: `scripts/v1_fetch_regs.py`,
`scripts/v1_closure_calendar.py`. Extra texts saved under
`C:\Users\dziya\research-data\london-variety-extension\raw\venue_mix\legislation\`.

Closure value per venue type and day: 1 closed to the public for the main service (takeaway or delivery only for
food venues); 0.5 partial (indoor closed with outdoor service allowed for pubs, bars, restaurants and cafes; or, for
pubs and bars only, drink-led trade banned by the substantial-meal rule or the Welsh 18:00 close with no alcohol);
0 open. The hospitality states and flags come from the B4 panel, which was read from the same regulations.

England (regulation; dates inclusive):
- All six venue types closed (takeaways open): 21 Mar to 3 Jul 2020 (uksi/2020/327, 2pm 21 Mar; uksi/2020/350
  from 26 Mar); 5 Nov to 1 Dec 2020 (uksi/2020/1200); 6 Jan to 11 Apr 2021 (uksi/2021/8, Tier 4 everywhere;
  uksi/2021/364 Step 1 from 29 Mar).
- Pubs, bars, restaurants, cafes, cinemas, theatres and concert halls reopened 4 Jul 2020 (uksi/2020/684 Schedule 2
  lists none of them). Gyms stayed closed to 24 Jul and reopened 25 Jul 2020 (uksi/2020/788). Nightclubs stayed
  closed to 18 Jul 2021 under every regime (uksi/2020/684 Sch. 2; 1103-1105; 1374; 2021/364 Steps 1-3).
- Leicester: every type closed 4 Jul to 2 Aug 2020 (uksi/2020/685; Oadby and Wigston to 31 Jul). Leicester gyms
  stayed closed under uksi/2020/824 to 7 Sep 2020 (point-in-time texts show them listed on 7 Sep and gone on 8 Sep).
- Bolton: pubs, bars, restaurants and cafes takeaway only 10 Sep to 2 Oct 2020 (uksi/2020/974).
- October tiers: Very High areas, pubs and bars 0.5 (substantial-meal rule, uksi/2020/1105). Liverpool City Region
  gyms closed 17 to 23 Oct 2020 (uksi/2020/1131 inserting Schedule 2A; gone from the point-in-time text on 24 Oct).
- December tiers (uksi/2020/1374): Tier 2 pubs and bars 0.5; Tier 3 pubs, bars, restaurants, cafes, cinemas,
  theatres and concert halls closed, gyms open; Tier 4 from 7am 20 Dec (uksi/2020/1611) adds gyms.
- Step 2, 12 Apr to 16 May 2021: pubs, bars, restaurants, cafes 0.5 (outdoors only); cinemas, theatres, concert
  halls and nightclubs closed; gyms open. Step 3 from 17 May (uksi/2021/585): nightclubs only. Step 4 from
  19 Jul 2021 (uksi/2021/848): all open.

Wales (applies to every Welsh LA; the 2020 local health protection areas closed none of these venue types):
- All closed 21 Mar to 12 Jul 2020 (wsi/2020/326, 353).
- Pubs, bars, restaurants, cafes: outdoors 13 Jul to 2 Aug 2020 (0.5; wsi/2020/725), indoors from 3 Aug
  (wsi/2020/820); closed in the firebreak 23 Oct to 8 Nov (wsi/2020/1149); pubs and bars 0.5 from 4 to 19 Dec
  (18:00 close, no alcohol, wsi/2020/1409); all closed 20 Dec 2020 to 25 Apr 2021 (wsi/2020/1609, Alert Levels 4
  then 3); outdoors 26 Apr to 16 May (0.5, wsi/2021/502); open from 17 May (wsi/2021/583).
- Cinemas: closed to 26 Jul 2020, open from 27 Jul (wsi/2020/803 reg. 3), closed 23 Oct to 8 Nov, closed again
  from 4 Dec 2020 (wsi/2020/1409) to 16 May 2021.
- Theatres and concert halls: closed from 21 Mar 2020 to 16 May 2021 without a break (wsi/2020/725, 1149, 1219,
  1609).
- Gyms: closed to 9 Aug 2020 (open in the wsi/2020/725 text in force 10 Aug), closed 23 Oct to 8 Nov, closed
  20 Dec 2020 to 2 May 2021 (Alert Level 4, then the Level 3 temporary modification to 2 May), open from 3 May
  (wsi/2021/542).
- Nightclubs: closed 21 Mar 2020 to 6 Aug 2021; open from 7 Aug (wsi/2021/925, Alert Level 0).

Shares of days closed, 23 Mar 2020 to 22 Mar 2021 (England mean over LAs, range; Wales): pubs and bars 0.65
(0.56-0.74; 0.66); restaurants and cafes 0.63 (0.56-0.74; 0.64); takeaways 0 (0; 0); cinemas 0.63 (0.56-0.74; 0.69);
theatres and concert venues 0.63 (0.56-0.74; 1.00); gyms 0.65 (0.62-0.76; 0.69); nightclubs 1.00 (1.00; 1.00).
In the April to July 2021 window the English shares are the same in every LA (national Steps): pubs, bars,
restaurants, cafes 0.23; cinemas and theatres 0.38; gyms 0.09; nightclubs 0.89. Welsh shares are 0.29, 0.38, 0.26
and 1.00.

## Step 2. Treatment

Files: `data/v2_access_msoa.csv`, `data/v2_treatment_msoa.csv`, `data/v2_treatment_lad.csv`,
`data/v2_validation_ukbc.csv`. Script: `scripts/v2_treatment.py`.

- Access: A_mv = sum over points of type v of exp(-d/lambda), d from the 2021 MSOA population-weighted centroid,
  lambda 1, 1.5 and 3 km, 30 km cut-off (the B1 function, reused).
- Variety-days lost: VDL_m = 365 x sum_v A_mv s_lv / sum_v A_mv, with s_lv the share of days type v was closed in
  LA l. It is a weighted mean of closure shares, so it does not change when every type is scaled up.
- Main version: FHRS for pubs and bars (FHRS "Pub/bar/nightclub" minus OSM nightclub access, floored at 0),
  restaurants and cafes, and takeaways; OSM 2019 for cinemas, theatres plus arts centres, gyms (fitness centres) and
  nightclubs. Check version: OSM 2019 for every type.
- Main window 23 Mar 2020 to 22 Mar 2021; LA version for the year to June 2021 (1 Jul 2020 to 30 Jun 2021); reopening
  version for 1 Apr to 31 Jul 2021. Both LA versions are Census-2021-population-weighted means of the MSOA measures.
- England and Wales MSOAs, main version: mean 171 days, SD 18.0. Correlation of the FHRS and OSM versions 0.45.
  Mean mix of access (FHRS, 1.5 km): restaurants and cafes 52%, takeaways 26%, pubs and bars 20%, theatres and arts
  centres 0.6%, gyms 0.6%, nightclubs 0.4%, cinemas 0.3%.
- LA versions: year to June 2021 mean 126 days (SD 10.2); reopening mean 65 days (SD 6.9). Correlation of the two
  across LAs 0.74.

UK Business Counts validation (OSM 2019 against UKBC 2019 local units, 318 LADs):

| Comparison | OSM total | UKBC total | r (levels) | r (log) | Spearman | r per 1,000 residents excl. City |
|---|---|---|---|---|---|---|
| Nightclubs vs 56301 Licensed clubs | 935 | 6,605 | 0.53 | 0.52 | 0.46 | 0.29 |
| Theatres vs 90040 Operation of arts facilities | 1,120 | 760 | 0.79 | 0.53 | 0.48 | 0.71 |
| Theatres vs 90010 + 90040 | 1,120 | 10,320 | 0.77 | 0.59 | 0.56 | 0.76 |
| Theatres + arts centres vs 90040 | 1,534 | 760 | 0.79 | 0.57 | 0.51 | 0.73 |
| Cinemas vs 59140 | 647 | 665 | 0.80 | 0.68 | 0.68 | 0.58 |
| Fitness centres vs 93130 | 1,382 | 4,175 | 0.65 | 0.51 | 0.52 | 0.32 |

No SIC class matches nightclubs alone: 56301 "Licensed clubs" also holds social and working men's clubs, so the
nightclub match is weak by construction as well as through OSM gaps. OSM theatres track performing-arts units
moderately well. 70% of LADs show zero 90040 units in the UKBC file (counts are rounded to 5), so the 90040
comparisons rest on few LAs with positive counts. OSM fitness centres cover about a third of UKBC fitness units.

## Step 3. Design diagnostics

Files: `data/v3_controls_msoa.csv`, `data/v3_diagnostics.csv`, `data/v3_diagnostic_coefs.csv`,
`data/v3_correlations.csv`, `data/v3_correlations_within_la.csv`, `data/v3_residual_msoa.csv`,
`data/figures/v3_residual_map_{london,greater,west}.png`. Script: `scripts/v3_diagnostics.py`.

| Treatment | Sample | MSOAs | LAs | Raw SD | Within-LA SD | R2 LA FE | R2 full | Residual SD | Resid./raw |
|---|---|---|---|---|---|---|---|---|---|
| FHRS 1.5 km (main) | England | 6,856 | 296 | 17.9 | 12.4 | 0.52 | 0.67 | 10.4 | 0.58 |
| FHRS 1.5 km | England and Wales | 7,264 | 318 | 18.0 | 12.6 | 0.51 | 0.66 | 10.5 | 0.58 |
| OSM 1.5 km | England | 6,856 | 296 | 22.9 | 16.1 | 0.50 | 0.60 | 14.4 | 0.63 |
| FHRS 1 km | England | 6,856 | 296 | 21.5 | 16.4 | 0.42 | 0.62 | 13.4 | 0.62 |
| FHRS 3 km | England | 6,856 | 296 | 13.2 | 7.4 | 0.68 | 0.76 | 6.4 | 0.49 |

Coefficients of the controls in the main diagnostic regression (days of VDL): log total access -3.0, log population
density -2.5, log job density +0.6, teleworkability +38.8, garden -4.6 (p 0.17), flats +22.1, private renting
+21.0, share aged 20-39 -41.7, students +35.4. Correlations with VDL in England (raw, within LA): teleworkability
+0.45, +0.41; log population density -0.26, -0.33; garden -0.23, -0.22; flats +0.16, +0.13; log job density -0.13,
-0.16; log total access -0.13, -0.21; students +0.14, +0.15; private renting +0.08, +0.10; age 20-39 -0.01, -0.04.

### Stopping rule (written before v3_diagnostics.py was first run)
The residual variation of the main treatment is judged too small to support estimation if, in England, the
residual SD from the Step 3 regression (controls plus LA fixed effects) is below 2 days, or below 10% of the raw SD
of the treatment. If so, the extension stops after Step 4. Outcome: residual SD 10.4 days, 58% of the raw SD; not
triggered.

## Step 4. Pre-analysis plan

`PRE_ANALYSIS_PLAN.md`, checksum in `PRE_ANALYSIS_PLAN.sha256`, written after Steps 1-3 and before the outcome files
were opened for this extension. `sha256sum -c PRE_ANALYSIS_PLAN.sha256` passes after estimation.

## Departures from the plan and corrections

- No departures in estimation. Every registered estimate was run as written.
- Correction to the plan's disclosure (Section 0). It calls the earlier national Census MSOA result "Departure 4 of
  the national plan, about -6 per 1,000 per SD". That result was Design 3 (Step 4 of the national plan), at ages
  20-34 (-6.18 per SD, with 25-34 at -3.94); its 2001-2011 placebo was +3.74. The plan file was left unedited.
- Implementation note (not a departure): the registered stacked model (MSOA by age group, MSOA and age-group fixed
  effects) is estimated in its exact differenced form, the 25-34 change minus the 50+ change on a constant, VDL and
  the controls. The LA-by-age version adds LA fixed effects to that regression.

## Judgement calls

1. **Legal measures only.** Closures follow what the regulations required, as in B4. English theatres and concert
   halls count as open from 4 Jul 2020, because uksi/2020/684 did not list them, although government guidance
   advised against indoor performances until 15 Aug 2020. The English theatre closure share may therefore
   understate effective closure in July and August 2020.
2. **Partial closures at 0.5.** Outdoor-only service (England Step 2; Wales July 2020 and late April 2021) counts as
   0.5 for food and drink venues. The substantial-meal rule (October Very High, December Tier 2) counts as 0.5 for
   pubs and bars only, since restaurants could trade. The Welsh 18:00-no-alcohol rule of 4-19 Dec 2020 counts as 0.5
   for pubs and bars and 0 for restaurants and cafes.
3. **Takeaways never closed.** Takeaway and delivery service was allowed in every regime; the 22:00 curfew of
   autumn 2020 limited hours but did not close premises, so takeaways are 0 throughout.
4. **Day rule** from B4: the state in force at the end of the day. 2pm 21 Mar 2020 counts as a closed day.
5. **Local areas.** Leicester postcode-area fringes of Blaby and Charnwood (4-17 Jul 2020) are not coded, as in B4.
   Partial-ward local measures change only the mixing rules, which do not enter this calendar.
6. **Amending SIs not identified by number.** The end of the Leicester gym closure (8 Sep 2020) and the reopening
   of Welsh gyms (10 Aug 2020) are dated from point-in-time texts of uksi/2020/824 and wsi/2020/725; the calendar
   cites those texts.
7. **Venue mapping.** OSM arts centres join theatres and concert venues. OSM leisure=fitness_centre stands for gyms
   (about a third of UKBC fitness units). FHRS restaurants and cafes include canteens.
8. **FHRS vintage.** The FHRS file is the October 2026 extract held from B1; the FSA API serves only the current
   register, so no 2019 snapshot exists in the project. Venues that closed after 2019 are missing and new ones are
   included. If venue survival after 2020 relates to neighbourhood demand, this could bias the main measure in an
   unknown direction. The OSM 2019 version is the check, and it gives a similar headline (-0.96 per 10 days,
   -2.19 per SD).
9. **Nightclubs in FHRS.** OSM nightclub access is subtracted from FHRS "Pub/bar/nightclub" access, floored at zero,
   so that nightclubs are not counted twice.
10. **LA versions** are Census-2021-population-weighted means of MSOA VDL, so they measure what residents faced.
11. **Job density.** BRES 2019 employment is published at 2011 MSOAs (the 2021 MSOA query returns no 2019 values). It
    was moved to 2021 MSOAs with the S4 population shares (exact for the 7,080 unchanged MSOAs) and divided by land
    area implied by Census 2021 TS006 (residents divided by residents per km2).
12. **Singleton LAs** (City of London, Isles of Scilly) drop from LA-fixed-effect regressions.
13. **50+ outcome** sums migrants and residents over the 50-64, 65-74 and 75+ bands, and requires all three bands.
14. **Headline sample** has 6,797 MSOAs in 294 LAs. The 59 MSOAs blocked by the ONS API in 2021 and 2 with coarse
    bands only are absent, as in S4.

## What a reader should take from this

The cross-sectional design finds a negative association between variety-days lost and the change in young-adult
inflow rates, but only once teleworkability and related controls are included, and the same neighbourhoods show
a large opposite movement in the decade before. The pre-registered placebo therefore attributes the headline to a
pre-existing dynamic in these neighbourhoods at least as plausibly as to the closures. The LA panel, where the
national triple difference can separate years, shows no effect in the year to June 2021 and no slower recovery
where more variety stayed closed in spring 2021. Because the treatment is close to an inverse takeaway share,
any residual association also carries whatever the takeaway share proxies for, which the controls may not fully
capture.

## File index

- `PRE_ANALYSIS_PLAN.md`, `PRE_ANALYSIS_PLAN.sha256`
- `scripts/vm_common.py` (paths), `scripts/vm_core.py` (estimators and data loaders)
- `scripts/v1_fetch_regs.py`, `scripts/v1_closure_calendar.py` (Step 1)
- `scripts/v2_treatment.py` (Step 2)
- `scripts/v3_diagnostics.py` (Step 3)
- `scripts/v5_main.py`, `scripts/v6_placebo_age.py`, `scripts/v7_la_panel.py`, `scripts/v8_robustness.py` (Steps 5-8)
- All are registered at the end of `extension/run_all.py`, for example
  `python run_all.py --start ../venue_mix/scripts/v1_fetch_regs.py`.
