# Pre-analysis plan: national extension

Written 29 October 2026, before any estimation on the national data. Data assembly (B1-B5) and the London results are known. National outcome regressions have not been run.

This file is not revised after estimation begins. Any departure from it is reported separately, in the "Departures from the pre-analysis plan" section of `EXTENSION_NOTES.md`.

## Common elements

- **Units.** 2023 local authority districts (LADs) in England and Wales: 318 LADs, of which 316 enter the analysis. City of London (E09000001) and Isles of Scilly (E06000053) are excluded for their small resident populations, as in `b3_la_crosssection.csv`.
- **Amenity density, LA level.** `z_log_per1k_IR`: the log of UK Business Counts 2019 local units in SIC divisions 55, 56 and 90-93 per 1,000 mid-2019 residents, standardised across the 316 LADs. It is called D below.
- **National controls (Step 1).**
  - LA level: the 2011 teleworkability share, the April 2020 garden access share, the 2011 flat share, the 2011 private renting share, the 2011 share aged 20-39 and the 2011 full-time student share, each standardised across the 316 LADs.
  - MSOA level: the 2021 Census versions of the same measures plus the 2020 garden access share.
- **Inference.** CR1 standard errors clustered by LA, and the wild cluster restricted bootstrap clustered by LA (Rademacher weights, B = 9,999, seed 20261028), as in the pilot's `es_core.fit_cluster`.
- **Thresholds.** Support and opposition use two-sided WCB p-values at 0.05. Results with p between 0.05 and 0.10 are described as weak. All results are reported, including nulls. With several designs and specifications, no single test is decisive.

## Design 1: national triple difference (Step 2)

- **Outcome.** Net internal migration of each LA with all other UK local authorities (the `all` counterpart in `b3_migration_la_year_by_age_group.csv`, which includes Scotland and Northern Ireland as counterparts), per 1,000 mid-2019 residents of the age group. Years to June 2016-2025, with 2019 as the omitted year.
- **Groups.**
  - Young group: ages 20-29 (main) and 25-29 (secondary).
  - Comparison groups: the family proxy (ages 0-15 and 30-49), which is the main comparison, and ages 50 and over.
- **Model.** The London triple difference: y_bgt = a_bt + c_gt + e_bg + Σ_{k≠2019} θ_k D_b Y_g 1[t=k] + controls + ε.
  - Two groups per LA-year means the LA-by-year effects make this numerically equivalent to a regression of the young-minus-comparison difference on LA effects, year effects and D × year.
  - It is estimated in that differenced form, and the equivalence is verified on the London sample.
- **Specifications.**
  - (a) No controls.
  - (b) Teleworkability × Y × year.
  - (c) Garden access × Y × year.
  - (d) Both.
  - (e) Region × Y × year effects.
  - (f) Both controls and region × Y × year effects.
  - Each is run for all 316 LADs and for the 283 LADs outside London.
- **Headline coefficient.** θ_2022 − θ_2020 for ages 20-29 against the family proxy in specification (f), all 316 LADs.
- **Reported alongside.** θ_2020, θ_2021, θ_2022, the 2022 − 2020 contrast and the pre-period coefficients θ_2016, θ_2017 and θ_2018, for every specification.
- **Secondary outcome.** Total net migration: the internal outcome above plus net international migration from ONS mid-year estimates MYEB2. Run in specification (f) only. The 2020-2021 international figures are modelled, so this outcome carries less weight.
- **Counts as support for the variety channel.**
  - In (f), the headline contrast is positive with p < 0.05 and θ_2020 is negative.
  - The pre-period coefficients 2016-2018 each have p ≥ 0.05, or are smaller in absolute value than θ_2020.
- **Counts against.**
  - The headline contrast is not positive, or has p ≥ 0.10 in (f), while it is positive in (a). The amenity response is then attributed to teleworkability, garden access or regional shocks.
  - Pre-period coefficients as large as the post-period ones.
- **Counts as support for the space and remote-working channel.**
  - θ_2020 is negative in (a) and shrinks towards zero in (b)-(d).
  - The teleworkability × Y × 2020 coefficient is positive (more teleworkable areas lose young residents), or the garden access × Y × 2020 coefficient is negative.
  - No reversal in 2022.

## Design 2: tier closures (Step 3)

- **Treatment.** Extra closure days, E_b: the number of days from 1 July 2020 to 30 June 2021 on which indoor hospitality was legally closed in LA b (`indoor_closed` = 1 in `b4_restrictions_daily_lad23.csv`) and was not closed in every LA of the same nation on that day.
  - National lockdown days are therefore excluded.
  - Population-weighted partial areas enter with their weighted values.
  - E_b is standardised across the 316 LADs.
  - A quarterly version, E_bq, uses the same rule within each quarter from 2020Q3 to 2021Q2.
- **First stage.** The mean Google retail-and-recreation change (B5) over 2020Q3-2021Q2, regressed on E_b with region fixed effects and the six national controls.
  - Also a quarterly panel of the B5 change on E_bq, with LA effects and region × quarter effects.
  - The expected sign is negative.
  - A first-stage WCB p ≥ 0.10 means the design is treated as uninformative.
- **Outcome.** Δ_b = (y_young − y_comp)_{b,2021} − mean_{2016-2019}(y_young − y_comp)_b, using the Design 1 outcome. Young is ages 20-29; the comparison is the family proxy (main) or ages 50+ (secondary). This is the young-relative-to-older change in the year to June 2021, measured against the LA's own pre-period.
- **Model.** Δ_b = region FE + β1 E_b + β2 E_b × D_b + β3 D_b + γ' X_b + δ C_b + u_b.
  - X_b holds the six national controls.
  - C_b is the mean weekly COVID-19 case rate per 100,000 over 1 July 2020 to 30 June 2021.
  - Because Δ_b is already a young-minus-older difference, every regressor is effectively interacted with the young-adult indicator.
  - Each LA is its own cluster.
- **Headline coefficient.** β2, the interaction of extra closure days with amenity density. β1 is reported alongside.
- **Counts as support for the variety channel.** β2 < 0 with p < 0.05: extra closure days lowered young-adult net migration more where amenity density was higher.
- **Counts against.** β2 ≥ 0, or p ≥ 0.10.
- **Balance check.** E_b regressed on:
  - the pre-2020 trend in the young-minus-comparison outcome (OLS slope over 2016-2019);
  - D_b;
  - C_b;
  - the six controls;
  - region FE.

  A pre-trend coefficient with p < 0.05 is reported as a threat to the design.

## Design 3: Census MSOA design (Step 4)

- **Outcome.** R_m,c: residents of MSOA m at census c whose usual address one year before was different, aged in the young band, per 1,000 residents of that band.
  - The definition is matched across censuses, as documented in `S3_S4_cases_censuses.md`.
  - All censuses are mapped to 2021 MSOAs.
  - The main band is the closest common band to ages 20-29. The secondary band is the closest common band to ages 25-34.
  - The main outcome is ΔR_m = R_m,2021 − R_m,2011.
- **Amenity measure.** A_m: log(1 + FHRS access with λ = 1.5 km, summing restaurants/cafés, pubs/bars/clubs and takeaways), standardised across MSOAs.
  - The check measure uses OSM 2019 restaurants, cafés, fast food, pubs, bars and nightclubs with the same λ.
- **Model.** ΔR_m = LA FE + β A_m + γ' X_m + ε_m.
  - X_m holds the six 2021 MSOA controls.
  - The controls are added one at a time, then all together. The six controls include the MSOA full-time student share, so "with the student share as a control" is covered both alone and within the full set.
- **Headline coefficient.** β for the main band, with LA fixed effects and all six controls.
- **Placebo.** The same model with ΔR_m = R_m,2011 − R_m,2001, where 2001 data exist at MSOA level or can be aggregated to it.
- **Counts as support for the variety channel.**
  - β < 0 with p < 0.05 in the headline model: high-amenity MSOAs drew fewer young movers in the pandemic year relative to 2011, within LA.
  - The placebo β has p ≥ 0.10 or is opposite in sign.
  - The 25-34 band gives the same sign.
- **Counts against.**
  - β ≥ 0, or p ≥ 0.10.
  - A placebo β of the same sign and similar size, which would indicate a pre-existing trend.
- **Caveats.**
  - FHRS is a 2026 snapshot, so amenities may have grown where young adults moved after 2021. OSM 2019 is the pre-period check.
  - The 2011-2021 change also contains ten years of trends unrelated to the pandemic. The placebo tests this only in part.

## Design 4: national rents (Step 5)

- **Outcome.** 100 × log of the PIPR index, averaged over complete quarters, 2015Q1 to the latest complete quarter, for 316 LADs (PIPR does not publish City of London or Isles of Scilly).
- **Event study.** y_bq = LA FE + region × quarter FE + Σ_{k≠2019Q4} θ_k D_b 1[q=k] + Σ_k X_b' γ_k 1[q=k] + ε.
- **Trend break.** As in the pilot's `82_rent_trend_break.py`: δ D_b τ_q with τ = quarters since 2019Q4, plus D_b × quarter dummies for 2020Q1 onwards, with the same fixed effects and controls.
- **Headline coefficient.** The average trend-break deviation over 2020Q2-2021Q2 (the closure period), with region × quarter FE and the six controls × quarter.
- **Reported alongside.** The average deviation from 2023Q3 to the latest quarter.
- **Counts as support for the variety channel.** The closure-period deviation is negative with p < 0.05, and the 2023Q3-latest deviation is not significantly below zero (p ≥ 0.05, or a positive point estimate). That pattern is a temporary fall that reverses.
- **Counts as support for a persistent channel (space, remote working or financing).** A negative closure deviation that persists, with the 2023Q3-latest deviation negative at p < 0.05.
- **Counts against both.** A closure-period deviation with p ≥ 0.10.

## Overall reading

- **The variety channel is supported** if Design 1 meets its support criterion and at least one of Designs 2-4 does, with no design meeting its "against" criterion with p < 0.05 of the opposite sign.
- **The space and remote-working channel is supported** if the Design 1 amenity effect disappears with the teleworkability and garden controls and the controls carry the 2020 response.
- **Otherwise** the evidence supports neither channel clearly, and this will be stated.
