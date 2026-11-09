# Extension: national and point-level analysis

## Results summary (Steps 1-5, against PRE_ANALYSIS_PLAN.md)

The pre-analysis plan was written and fingerprinted (SHA-256 `c6dd084c…`, check file `PRE_ANALYSIS_PLAN.sha256`) before any national estimation. It was not changed afterwards, and the checksum still matches. Departures are listed in their own section below.

All coefficients are estimates with real uncertainty. The p-values are wild cluster restricted bootstrap p-values (Rademacher, B = 9,999), clustered by LA.

**Overall reading under the plan's rule.**
- **Variety channel: not supported.** Design 1, the national triple difference, does not meet its support criterion. It meets its "against" criterion.
  - Design 3, the Census MSOA design, meets its support criterion, but its evidence carries a mean-reversion caveat set out below.
  - Designs 2 and 4 are null.
- **Space and remote-working channel: partly supported.**
  - Nationally there was no amenity-related outflow of young adults in 2020.
  - Garden access × young × 2020 is positive and significant in every specification: young adults moved, relative to older residents, towards LAs with more private outdoor space.
  - Teleworkability × young × 2020 is negative without region-by-year effects and not significant with them.
- **Student check (departure 7).** Adding the student share, dropping the 30 most student-heavy LADs or leaving out any single LAD does not change this reading.
- **Post-hoc urban measures (departure 8, chosen after the registered results).** Density and access measures reproduce the London pattern nationally (2020 coefficient −5.54, 2022 − 2020 +11.14 for population-weighted FHRS access). They leave the registered verdict unchanged and cannot separate variety from other urban attributes. With job and resident density controlled, the result holds when London is included (2020 −5.47, contrast +10.61) but not outside it (2020 −3.98, p 0.126), because measure (c) correlates at about 0.9 with both densities.
- **The London result does not generalise.** The London closure outflow and reopening recovery do not appear in the 316-LA panel, and outside London the pattern is the reverse.

| Design | Headline coefficient (plan) | Estimate (WCB p) | Survives teleworkability and garden controls? | Units / clusters | Reading under the plan |
|---|---|---|---|---|---|
| 1. National triple difference | θ_2022 − θ_2020, ages 20-29 vs family proxy, both controls + region × young × year | −1.53 (0.191); θ_2020 = +1.82 (0.030) | No amenity effect to survive. Without controls the contrast is +3.12 (0.113) and θ_2020 −1.29 (0.183); with controls the sign reverses. | 316 LAs × 10 years / 316 clusters | Against variety. Space channel partly: garden × Y × 2020 = +4.34 (<0.001). |
| 2. Tier closures | β2, extra closure days × amenity density, ages 20-29 vs family proxy | +0.24 (0.847); β1 = −2.03 (0.139) | Controls are in the headline model | 316 LAs / 316 | Against (null). The cross-section first stage fails (p 0.581); the quarterly first stage holds (−1.13 points per 10 days, p < 0.001). |
| 3. Census MSOA | β on FHRS access, change in mover rate 2011 to 2021, ages 20-34, LA FE + six controls | −6.18 per 1,000 per SD (<0.001) | Yes. It shrinks from −12.29 (LA FE only) to −9.36 with teleworkability, and −12.37 with garden. Flat share and private renting take most of it. | 7,201 MSOAs / 316 LAs | Support under the plan: placebo 2001 to 2011 is opposite in sign (+3.74, 0.002), and 25-34 has the same sign (−3.94, 0.001). Caveat: mean reversion, see below. |
| 4. National rents | Average trend-break deviation 2020Q2-2021Q2, region × quarter FE + six controls × quarter | +0.15 log points (0.569) | Null in every specification | 316 LAs × 47 quarters / 316 | Against both channels (null). High-amenity rents follow a pre-2020 relative decline of −0.064 log points a quarter (0.021). The 2023Q3-latest deviation is +0.14 (0.835). |

**Mean-reversion caveat for Design 3.**
- The 2011 mover rate enters the main outcome with a minus sign and the placebo with a plus sign.
- Noise or transitory shocks in 2011 rates would therefore produce exactly the observed pattern: a negative main coefficient and a positive placebo coefficient.
- The opposite-signed placebo is consistent with the variety channel, but it does not rule out mean reversion.
- The 2001 MSOA rates by age are themselves model estimates built from ward rates. In a test of the method on 2011 data, the median error was 33 per 1,000 at ages 20-24.
- The 2021 census was taken while many students were away from term-time addresses. The 25-34 band, which is less affected, has the same sign (−3.94).

## Step 2. National triple difference (`scripts/s2_national_ddd.py`; `data/clean/s2_national_ddd.md`, `.csv`)

- **Estimation form.** Estimated in differenced form (`e_core.ddd_diff`). On the London sample it reproduces the pilot's estimates exactly: −5.24 (0.002), 4.60 (0.014), 8.08 (<0.001) and 13.32 (<0.001) against the family proxy.
- **Outcome.** The `all` counterpart: net moves with all other UK LAs, per 1,000 mid-2019 group residents, years to June 2016-2025.

**Ages 20-29 against the family proxy, all 316 LAs**

| Spec | 2016 | 2017 | 2018 | 2020 | 2021 | 2022 | 2022 − 2020 | Telework × 2020 | Garden × 2020 |
|---|---|---|---|---|---|---|---|---|---|
| (a) none | −1.05 (0.187) | −0.14 (0.899) | 0.11 (0.877) | −1.29 (0.183) | 1.55 (0.306) | 1.83 (0.160) | 3.12 (0.113) | | |
| (b) teleworkability | −0.40 (0.636) | 0.27 (0.828) | 1.13 (0.132) | 0.59 (0.484) | 1.86 (0.237) | 2.63 (0.064) | 2.05 (0.216) | −4.54 (<0.001) | |
| (c) garden | −0.91 (0.352) | −0.77 (0.541) | 0.25 (0.764) | 2.12 (0.017) | 2.47 (0.107) | −0.48 (0.671) | −2.60 (0.034) | | 6.38 (<0.001) |
| (d) both | −0.65 (0.491) | −0.50 (0.701) | 0.66 (0.436) | 2.41 (0.006) | 2.47 (0.114) | 0.20 (0.855) | −2.20 (0.078) | −2.17 (0.032) | 5.25 (<0.001) |
| (e) region × year | −0.96 (0.228) | 0.23 (0.819) | 0.47 (0.509) | −0.32 (0.650) | 2.03 (0.185) | 1.59 (0.156) | 1.91 (0.155) | | |
| (f) both + region × year | −0.79 (0.400) | −1.36 (0.313) | 0.04 (0.964) | 1.82 (0.030) | 2.63 (0.093) | 0.30 (0.785) | −1.53 (0.191) | −1.42 (0.170) | 4.34 (<0.001) |

**Other combinations, specification (f)**

| Sample | Young | Comparison | 2020 | 2022 − 2020 | Garden × 2020 |
|---|---|---|---|---|---|
| all 316 | 20-29 | 50+ | 1.70 (0.048) | −1.25 (0.306) | 3.32 (0.002) |
| all 316 | 25-29 | family | 2.64 (0.001) | −1.68 (0.087) | 5.08 (<0.001) |
| all 316 | 25-29 | 50+ | 2.52 (0.003) | −1.41 (0.186) | 4.05 (<0.001) |
| outside London (284) | 20-29 | family | 2.88 (0.005) | −3.79 (0.005) | 3.81 (0.013) |
| outside London (284) | 20-29 | 50+ | 2.53 (0.013) | −3.63 (0.010) | 2.86 (0.070) |
| outside London (284) | 25-29 | family | 4.15 (<0.001) | −3.61 (0.001) | 5.10 (<0.001) |
| outside London (284) | 25-29 | 50+ | 3.80 (<0.001) | −3.46 (0.004) | 4.16 (0.005) |

- **Outside London without controls (a), 20-29 against the family proxy:** θ_2020 = +2.11 (0.038) and 2022 − 2020 = −3.10 (0.020). High-amenity LAs outside London gained young adults in 2020 and lost them by 2022, the reverse of the London pattern.
- **Pre-period:** the 2016-2018 coefficients have p ≥ 0.077 in every internal specification.
- **Total net migration, internal plus international, specification (f):**
  - 20-29 against the family proxy: θ_2020 = +4.54 (<0.001), 2022 − 2020 = −5.86 (0.002).
  - Outside London: −9.46 (<0.001).
  - The 2020-2021 international figures are modelled. Against ages 50+, the 25-29 total outcome has 2016 and 2017 pre-period coefficients with p near 0.02.
  - Full table in `s2_national_ddd.md`.

## Step 3. Tier design (`scripts/s3_tier_design.py`; `data/clean/s3_tier_design.md`)

- **Extra closure days E_b.** Days from 1 July 2020 to 30 June 2021 with indoor hospitality closed, excluding days closed in every LA of the nation. England has 161 national closure days and Wales 198.
  - E_b has mean 21.1, SD 12.8 and range 0-65; Leicester is at 65.
  - 294 of 316 LAs have E_b > 0.
  - Quarterly means: 2020Q3 0.2, 2020Q4 16.2, 2021Q1 4.6, 2021Q2 0.0.
- **First stage.**
  - Cross-section: the mean retail and recreation change over 2020Q3-2021Q2 on E (per SD), with region FE and six controls, is +0.195 (0.581).
  - Quarterly panel with LA FE and region × quarter FE: −1.134 percentage points per 10 extra days (<0.001).
  - Within an LA, extra closure days lower visits. Across LAs, a year's total of extra days does not predict the year's mean fall once region and controls are held fixed.
- **Outcome.** Δ = (young − comparison) in 2021 minus its 2016-2019 mean, with region FE, six controls and the case rate. All regressors are per SD.

| Comparison | Model | E | E × D | D | Case rate |
|---|---|---|---|---|---|
| family proxy | E only | −2.10 (0.120) | | 0.52 (0.769) | −0.71 (0.665) |
| family proxy | headline | −2.03 (0.139) | 0.24 (0.847) | 0.58 (0.753) | −0.74 (0.646) |
| ages 50+ | E only | −2.76 (0.043) | | 0.88 (0.669) | 0.40 (0.825) |
| ages 50+ | headline | −2.60 (0.055) | 0.49 (0.715) | 1.00 (0.642) | 0.34 (0.852) |

- **Reading.** More extra closure days go with a lower young-adult net inflow relative to older residents (weak against the family proxy, p 0.12-0.14; p 0.04-0.06 against ages 50+). There is no larger response where amenity density is higher.
- **Balance.** E is predicted by the case rate (+0.48 SD per SD, <0.001) and teleworkability (+0.11, 0.035), as the tiers were set on case rates. It is not predicted by:
  - the pre-2020 young-minus-family trend (−0.02, 0.552);
  - amenity density (−0.01, 0.917).
- **Case rates.** England from the UKHSA dashboard API; Wales from the archived coronavirus dashboard, with October 2020 rebuilt from cumulative totals. Hackney and City of London, and Cornwall and Isles of Scilly, share combined rates (`notes/S3_S4_cases_censuses.md`).

## Step 4. Census MSOA design (`scripts/s4_census_msoa.py`; `data/clean/s4_census_msoa.md`)

- **Outcome.** Movers per 1,000 residents of the band, all censuses on 2021 MSOAs. "No usual address one year before" is excluded, because only 2001 records it.
- **Bands.**
  - 20-34 is the main band: 2011 publishes no 20-29 band, and 20-34 is the common band that contains 20-29.
  - 20-24 and 25-34 are reported alongside.
- **Mean rates.** 20-34: 231.4 (2001), 248.1 (2011), 228.3 (2021).

**Amenity coefficient as controls are added (FHRS, 2021 − 2011, LA FE; per SD of access)**

| Spec | 20-34 | 20-24 | 25-34 |
|---|---|---|---|
| LA FE only | −12.29 (<0.001) | −14.63 (<0.001) | −10.63 (<0.001) |
| + teleworkability | −9.36 (<0.001) | −11.10 (<0.001) | −8.36 (<0.001) |
| + garden | −12.37 (<0.001) | −15.58 (<0.001) | −10.42 (<0.001) |
| + flat share | −7.92 (<0.001) | −10.58 (<0.001) | −6.54 (<0.001) |
| + private renting | −8.79 (<0.001) | −11.08 (<0.001) | −6.45 (<0.001) |
| + age 20-39 share | −13.58 (<0.001) | −18.45 (<0.001) | −9.74 (<0.001) |
| + student share | −14.49 (<0.001) | −17.89 (<0.001) | −10.72 (<0.001) |
| all six (headline) | −6.18 (<0.001) | −8.64 (<0.001) | −3.94 (0.001) |
| OSM 2019 check, all six | −6.27 (<0.001) | −9.66 (<0.001) | −3.71 (0.002) |
| Placebo 2011 − 2001, all six | +3.74 (0.002) | −3.17 (0.070) | +5.72 (<0.001) |

The 20-24 placebo has the same sign as the main estimate (−3.17, p 0.070), so in that band a pre-existing trend cannot be excluded.

## Step 5. National rents (`scripts/s5_national_rents.py`; `data/clean/s5_national_rents.md`)

The sample is 316 LAs, 2015Q1-2026Q3, with base 2019Q4.

| Model | Spec | 2020Q2 | 2021Q2 | Closure avg 2020Q2-2021Q2 | Avg 2023Q3-latest | Pre-trend per quarter |
|---|---|---|---|---|---|---|
| event | (i) LA + quarter FE | −0.10 (0.594) | −0.86 (<0.001) | −0.43 (0.002) | −1.36 (<0.001) | |
| event | (ii) region × quarter FE | −0.13 (0.310) | −0.76 (<0.001) | −0.42 (<0.001) | −1.35 (<0.001) | |
| event | (iii) + six controls × quarter | −0.12 (0.217) | −0.68 (<0.001) | −0.43 (<0.001) | −1.51 (<0.001) | |
| trend | (i) | 0.23 (0.130) | −0.29 (0.169) | 0.02 (0.897) | 0.12 (0.819) | −0.061 (0.002) |
| trend | (ii) | 0.26 (0.087) | −0.15 (0.454) | 0.08 (0.661) | 0.09 (0.870) | −0.055 (0.002) |
| trend | (iii) headline | 0.33 (0.126) | 0.02 (0.946) | 0.15 (0.569) | 0.14 (0.835) | −0.064 (0.021) |

- **Reading.** Rents in high-amenity LAs fell relative to other LAs through the period, at the pace of their pre-2020 trend. There is no closure-specific deviation and no later one. This matches the London finding.
- **Pre-period.** The event-study 2019 coefficients in (iii) are −0.13 to −0.19, with p 0.03-0.09, consistent with that trend.

## Step 1. National controls (`notes/S1_controls.md`)

- **LA controls.** Built from Census 2011 tables via a 2011-to-2023 LA lookup: 348 Nomis LAs, each mapping whole into one 2023 LAD. The garden measure is ONS April 2020.
- **London check.** For the 32 London boroughs, every share reproduces the pilot to 1e-16.
- **MSOA controls.** Built from Census 2021 tables. Teleworkability is the share employed in SOC major groups 1-4, whose ONS homeworking scores are 1.06-1.40. Summed to LAs, this correlates at 0.954 with the 2011 LA measure.

**Correlations with log amenity density**

| Control | LA national (316) | LA within region | MSOA national (7,262) | MSOA within LA |
|---|---|---|---|---|
| Teleworkability | .414 | .365 | .053 | −.217 |
| Garden access | −.534 | −.491 | −.403 | −.228 |
| Flat share | .482 | .447 | .712 | .511 |
| Private renting | .472 | .391 | .575 | .469 |
| Age 20-39 share | .174 | .044 | .687 | .514 |
| Student share | .219 | .158 | .395 | .274 |

Across 316 LAs, amenity density correlates with teleworkability at .41. Among the 32 London boroughs the figure is .82. The national design therefore separates the two far better than the London design.

## Departures from the pre-analysis plan

1. **Outside-London sample.** It has 284 LAs. The plan said 283 (316 − 32 = 284).
2. **Sign criteria for the space channel.** The plan's stated signs contradict its own wording.
   - The plan says the teleworkability coefficient should be "positive (more teleworkable areas lose young residents)". Losing residents is a negative coefficient.
   - The plan's garden criterion has the same reversal.
   - The criteria are applied by their stated meaning: teleworkable areas losing young adults is a negative teleworkability coefficient, and garden-rich areas gaining them is a positive garden coefficient.
3. **Design 3 band.**
   - The plan says "the closest common band to ages 20-29". 20-24 and 20-34 are equally distant from it, so 20-34, the band that contains 20-29, is used as the main band, with 20-24 and 25-34 reported alongside.
   - The 2001 MSOA rates are model estimates; no measured table exists publicly.
   - The outcome excludes "no usual address".
   - The placebo uses the 2021 MSOA controls, the only MSOA controls built.
   - The OSM check is run in the LA-FE-only and headline specifications only.
4. **Design 2 first stage.** The plan lists a cross-section and a quarterly first stage, and treats the design as uninformative if "a first-stage WCB p ≥ 0.10". The cross-section fails (0.581) and the quarterly panel passes (<0.001). Both are reported, and the outcome results are reported regardless.
5. **Design 2 case rates.**
   - The mean weekly rate per 100,000 over 1 July 2020-30 June 2021 is used, as planned.
   - The Welsh October 2020 figures are rebuilt.
   - Two pairs of LAs share combined rates.
6. **Design 4 sample.** Restricted to quarters with three published months and to quarters in which at least 300 LAs report. That gives 2015Q1-2026Q3, with no quarters lost.

7. **Student check (added after Step 2, not in the plan).** Script: `scripts/s2b_student_check.py`. Output: `data/clean/s2b_student_check.md`, `.csv` and `s2b_loo_2020_outside_london.csv`.
   - The headline specification (f) is ages 20-29 against the family proxy, with teleworkability and garden × young × year and region × young × year effects.
   - The check adds the 2011 full-time student share × young × year, drops the 30 LADs with the highest student share, and runs a leave-one-out of the 2020 coefficient outside London.

**Headline (f) plus the student share × young × year, against the family proxy**

| Sample | Young | Spec | 2020 | 2021 | 2022 | 2022 − 2020 | Garden × 2020 | Student × 2020 | LAs |
|---|---|---|---|---|---|---|---|---|---|
| all 316 | 20-29 | (f) | 1.82 (0.030) | 2.63 (0.093) | 0.30 (0.785) | −1.53 (0.191) | 4.34 (<0.001) | | 316 |
| all 316 | 20-29 | (f) + student | 1.98 (0.022) | 1.74 (0.212) | 1.04 (0.342) | −0.94 (0.415) | 5.25 (<0.001) | 1.28 (0.247) | 316 |
| all 316 | 25-29 | (f) | 2.64 (0.001) | 2.24 (0.060) | 0.96 (0.184) | −1.68 (0.087) | 5.08 (<0.001) | | 316 |
| all 316 | 25-29 | (f) + student | 2.62 (0.002) | 1.52 (0.168) | 0.95 (0.193) | −1.67 (0.092) | 4.98 (<0.001) | −0.14 (0.848) | 316 |
| outside London | 20-29 | (f) | 2.88 (0.005) | 1.04 (0.430) | −0.91 (0.487) | −3.79 (0.005) | 3.81 (0.013) | | 284 |
| outside London | 20-29 | (f) + student | 2.95 (0.005) | 0.52 (0.673) | −0.31 (0.786) | −3.27 (0.009) | 4.74 (0.010) | 0.93 (0.444) | 284 |
| outside London | 25-29 | (f) | 4.15 (<0.001) | 1.34 (0.215) | 0.54 (0.526) | −3.61 (0.001) | 5.10 (<0.001) | | 284 |
| outside London | 25-29 | (f) + student | 4.10 (<0.001) | 0.93 (0.386) | 0.57 (0.496) | −3.53 (0.002) | 4.46 (0.004) | −0.65 (0.469) | 284 |

**Headline (f) without the 30 LADs with the highest 2011 student share**

| Sample | Young | 2020 | 2021 | 2022 | 2022 − 2020 | Garden × 2020 | LAs |
|---|---|---|---|---|---|---|---|
| all 316 minus 30 | 20-29 | 2.11 (0.015) | 3.05 (0.055) | −0.31 (0.803) | −2.42 (0.060) | 5.68 (<0.001) | 286 |
| all 316 minus 30 | 25-29 | 2.68 (0.003) | 2.27 (0.052) | 0.62 (0.418) | −2.07 (0.048) | 5.12 (0.002) | 286 |
| outside London minus 25 | 20-29 | 3.19 (0.001) | 1.65 (0.163) | −2.05 (0.086) | −5.24 (<0.001) | 5.28 (0.003) | 259 |
| outside London minus 25 | 25-29 | 4.41 (<0.001) | 1.58 (0.129) | 0.04 (0.963) | −4.36 (<0.001) | 4.63 (0.003) | 259 |

**Excluded LADs** (2011 full-time students aged 18+ per resident aged 16+). Five of them are in London.
- Oxford 23.6%; Cambridge 23.1%; Nottingham 18.4%; Manchester 17.3%; Newcastle upon Tyne 16.2%; Ceredigion 15.3%.
- Newham 14.9% (London); Canterbury 14.6%; Exeter 14.4%; Southampton 14.4%; Camden 13.6% (London); Welwyn Hatfield 13.1%.
- Cardiff 12.8%; Portsmouth 12.7%; Leicester 12.4%; Sheffield 12.2%; Tower Hamlets 12.1% (London); Lincoln 12.1%.
- Liverpool 11.9%; Brighton and Hove 11.9%; Lancaster 11.8%; Norwich 11.6%; Coventry 11.5%; Southwark 11.5% (London).
- Charnwood 11.4%; York 11.4%; Bath and North East Somerset 10.9%; Islington 10.7% (London); Preston 10.6%; Bristol 10.2%.

**Leave-one-out, 2020 coefficient outside London** (headline, 20-29 against the family proxy)
- The full estimate is 2.876. Leave-one-out estimates range from 2.574 to 3.291 across the 284 LADs, so no single LAD drives the positive 2020 coefficient.
- Contribution = full estimate minus the estimate without that LAD. The ten largest contributions:

| LAD | Region | D | Student share | 2020 without it | Contribution |
|---|---|---|---|---|---|
| South Hams | South West | 1.79 | 2.3% | 2.574 | +0.302 |
| Ceredigion | Wales | 1.47 | 15.3% | 2.615 | +0.262 |
| Isle of Anglesey | Wales | 1.24 | 3.4% | 2.685 | +0.191 |
| Rutland | East Midlands | 0.64 | 2.5% | 2.719 | +0.157 |
| Elmbridge | South East | 1.09 | 2.9% | 2.737 | +0.139 |
| Harlow | East of England | −1.38 | 2.9% | 2.747 | +0.130 |
| Rother | South East | 0.93 | 2.2% | 2.748 | +0.129 |
| Torfaen | Wales | −1.57 | 2.9% | 2.749 | +0.127 |
| Stratford-on-Avon | West Midlands | 1.49 | 2.5% | 2.752 | +0.124 |
| Salford | North West | −0.47 | 6.9% | 2.760 | +0.116 |

- Six of the ten are high-amenity rural or coastal LADs with low student shares: South Hams, Anglesey, Rutland, Rother, Stratford-on-Avon and Elmbridge.
- Outside London, a high count of hospitality and leisure units per resident partly marks tourist and rural areas. That count is the LA-level measure of amenity density.
- The positive 2020 coefficient is therefore consistent with young adults moving to such areas in 2020, including to parental homes. It is not consistent with a loss of urban variety. This reading is an interpretation; it was not tested.

**Does the national verdict change?** No.
- **Students.** Adding the student share leaves the 2020 coefficient positive (1.98, p 0.022) and the headline 2022 − 2020 contrast negative and insignificant (−0.94, p 0.415). Dropping the 30 most student-heavy LADs moves the contrast further negative (−2.42, p 0.060).
- **Outside London.** Students do not explain the reversed pattern: the 2020 coefficient stays at 2.9 to 4.4 and the contrast at −3.3 to −5.2, all with p ≤ 0.009.
- **Garden access.** The garden interaction stays positive and significant in every variant (3.8 to 5.7). The plan's reading stands: the variety channel is not supported nationally, and the space and remote-working channel is partly supported through garden access.
- **Caveat.** These are estimates with real uncertainty. Outside London, the amenity measure partly captures tourist and rural areas, so the national test of variety is weaker than its sample size suggests.

8. **Urban amenity measures and pound values. Decided after seeing the registered results; not in the plan.**
   - Scripts: `scripts/s8_urban_measures.py` and `scripts/s8_pound_values.py`.
   - Outputs: `data/clean/s8_urban_measures.md`, `s8_urban_ddd.csv`, `s8_loo_2020_measure_c_outside_london.csv`, `s8_pound_values.md` and `.csv`.
   - Literature: `notes/S8_calibration_elasticities.md` and `data/clean/s8_elasticities.csv`.
   - These measures were chosen after the registered measure produced a null. The results carry the forking-paths risk of any post-hoc choice of measure, and they do not change the registered verdict.

**Departure 8 summary**

No urban measure changes the registered verdict. The registered measure and the plan's reading stand, and the plan file is unchanged (checksum OK). Post hoc, two of the three urban measures reproduce the London pattern across England and Wales.
- **Measures (b) and (c)** are food, drink, arts and leisure units per km² and population-weighted FHRS access within 1.5 km. In the headline model (teleworkability and garden × young × year, region × young × year), ages 20-29 against the family proxy:
  - The 2020 coefficient is −4.15 for (b) and −5.54 for (c), both p < 0.001.
  - The 2022 − 2020 contrast is +8.74 and +11.14, both p < 0.001.
  - Both hold outside London (−4.00 and −5.19 in 2020; +8.45 and +10.59 in the contrast).
- **Ages 25-29** show the same 2020 outflow (−3.81 and −5.34), but little 2022 recovery (+0.48 and +0.13). The reopening return of 20-29 year olds on these measures is therefore concentrated among ages 20-24 and may partly reflect students.
- **Measure (a)**, the per-resident count without accommodation, behaves like the registered measure (correlation 0.98) and shows no closure outflow.
- **Garden access.** With measure (c) the garden interaction falls to +0.76 (p 0.468). The garden effect in the registered model is therefore partly picking up non-urban LADs.
- **What the urban measures cannot separate.** Measures (b) and (c) track urban density in general. They cannot separate consumption variety from other urban attributes that changed in 2020, such as offices, public transport, crowding and infection risk, and universities.
- **Pound values.** The verified elasticities fall into two families that differ by two orders of magnitude, so the range is wide.
  - Garden access (+4.34 per 1,000 per SD) is equivalent to a rent change of £1.03 to £9.96 a month (median £2.34) using long-run stock elasticities, and £203 to £608 a month (median £338) using the British annual-flow estimates of Rabe and Taylor.
  - Measure (c) (−5.54 per 1,000 per SD) is equivalent to £1.32 to £12.71 a month (median £2.98) with stock elasticities, and £258 to £775 a month (median £431) with annual-flow elasticities.
  - The flow-based figures are the like-for-like comparison with a one-year net flow. They rest on a house-price elasticity estimated for British regions and heads of household; the private-renter version is not significant (t = 0.64).

**Step 1. Urban measures (316 LADs)**

| Measure | Corr. with registered D | Corr. with teleworkability | Corr. with garden access |
|---|---|---|---|
| (a) SIC 56 + 90-93 units per 1,000 residents | .981 | .508 | −.588 |
| (b) same units per km² of land | .087 | .461 | −.601 |
| (c) population-weighted FHRS access, λ = 1.5 km | .168 | .441 | −.658 |
| registered D (SIC 55-56 + 90-93 per 1,000) | 1 | .414 | −.534 |

Correlations among the new measures: (a)-(b) .196, (a)-(c) .265, (b)-(c) .928. Total land area is 151,043 km².

Top 20 LADs on each measure:
- **(a) units per 1,000 residents:**
  - Westminster 29.5, Camden 17.1, Kensington and Chelsea 10.9, Islington 10.4, North Northamptonshire 8.4
  - Hackney 8.1, Hammersmith and Fulham 8.1, Cotswold 7.1, Richmond upon Thames 7.0, Brighton and Hove 7.0
  - Southwark 6.9, Derbyshire Dales 6.7, Tower Hamlets 6.2, Lambeth 5.8, South Hams 5.7
  - Gwynedd 5.7, Pembrokeshire 5.6, Stratford-on-Avon 5.6, Elmbridge 5.5, Wandsworth 5.5
  - The North Northamptonshire value is high and should be checked against its local-unit records.
- **(b) units per km²:**
  - Westminster 286.7, Camden 170.0, Islington 154.8, Kensington and Chelsea 131.9, Hackney 113.0
  - Tower Hamlets 95.9, Hammersmith and Fulham 92.9, Southwark 74.3, Lambeth 71.2, Wandsworth 53.7
  - Haringey 50.4, Lewisham 37.7, Brent 30.9, Newham 28.8, Ealing 26.7
  - Waltham Forest 26.4, Richmond upon Thames 24.3, Brighton and Hove 23.6, Merton 23.5, Portsmouth 23.5
- **(c) population-weighted FHRS access:**
  - Westminster 1,677, Islington 1,509, Camden 1,490, Kensington and Chelsea 1,195, Southwark 1,169
  - Tower Hamlets 1,158, Hackney 1,096, Lambeth 856, Hammersmith and Fulham 851, Wandsworth 642
  - Haringey 488, Newham 485, Lewisham 458, Brent 423, Waltham Forest 403
  - Manchester 388, Ealing 366, Brighton and Hove 320, Merton 319, Bristol 296

**Step 2. Headline model (f) with each measure in place of D, against the family proxy**

| Measure | Sample | Young | 2020 | 2021 | 2022 | 2022 − 2020 | Garden × 2020 | LAs |
|---|---|---|---|---|---|---|---|---|
| (a) | all 316 | 20-29 | 1.23 (0.154) | 2.71 (0.108) | 0.26 (0.819) | −0.97 (0.412) | 4.04 (<0.001) | 316 |
| (a) | all 316 | 25-29 | 2.48 (0.004) | 2.66 (0.034) | 1.03 (0.181) | −1.45 (0.158) | 4.99 (<0.001) | 316 |
| (a) | outside London | 20-29 | 2.36 (0.041) | 0.77 (0.580) | −1.21 (0.384) | −3.56 (0.014) | 3.54 (0.020) | 284 |
| (a) | outside London | 25-29 | 4.28 (<0.001) | 1.62 (0.151) | 0.55 (0.562) | −3.74 (0.003) | 5.03 (<0.001) | 284 |
| (b) | all 316 | 20-29 | −4.15 (<0.001) | −1.89 (0.216) | 4.59 (0.002) | 8.74 (<0.001) | 1.78 (0.065) | 316 |
| (b) | all 316 | 25-29 | −3.81 (<0.001) | −1.71 (0.193) | 0.48 (0.635) | 4.29 (<0.001) | 2.23 (0.022) | 316 |
| (b) | outside London | 20-29 | −4.00 (<0.001) | −1.63 (0.283) | 4.45 (0.001) | 8.45 (<0.001) | 0.77 (0.598) | 284 |
| (b) | outside London | 25-29 | −3.60 (<0.001) | −1.43 (0.274) | 0.46 (0.660) | 4.06 (<0.001) | 1.77 (0.182) | 284 |
| (c) | all 316 | 20-29 | −5.54 (<0.001) | −3.85 (0.046) | 5.60 (0.001) | 11.14 (<0.001) | 0.76 (0.468) | 316 |
| (c) | all 316 | 25-29 | −5.34 (<0.001) | −2.07 (0.194) | 0.13 (0.916) | 5.46 (<0.001) | 1.17 (0.242) | 316 |
| (c) | outside London | 20-29 | −5.19 (<0.001) | −3.83 (0.046) | 5.40 (0.002) | 10.59 (<0.001) | −0.13 (0.936) | 284 |
| (c) | outside London | 25-29 | −4.96 (<0.001) | −2.02 (0.202) | −0.07 (0.960) | 4.89 (0.001) | 0.81 (0.563) | 284 |

**Leave-one-out for measure (c), 2020 coefficient outside London (20-29 against the family proxy)**
- The full estimate is −5.194. Leave-one-out estimates range from −5.635 to −4.769 across the 284 LADs, so no single LAD drives it.
- The ten largest absolute contributions, where contribution = full estimate minus the estimate without the LAD:
  - Malvern Hills +0.440, South Hams −0.425, Ceredigion −0.357, Rutland −0.348, Norwich +0.328
  - Exeter +0.278, Oadby and Wigston +0.265, Isle of Anglesey −0.215, Forest of Dean +0.215, West Lindsey −0.209
- Positive contributions make the estimate less negative. Rural LADs with low access sit at both ends.

**Step 3. Verified calibration elasticities** (`notes/S8_calibration_elasticities.md`)

21 estimates were verified against the papers and 18 could be converted to the percentage change in population per 1% rent.

| Source | Population | Converted elasticity |
|---|---|---|
| Diamond (2016 AER), Table 4A cols 3-4 | US non-college and college workers | −2.94, −2.50, −2.16, −1.31 |
| Piyapromdee (2021 REStud), Table 1 Panel II | US natives | −0.31 to −0.63 |
| Piyapromdee (2021 REStud), Table 1 Panel II | US immigrants | −0.44 to −1.31 |
| Suárez Serrato and Zidar (2016), Table 6A col 1 | US county groups, with the paper's housing share | −0.36 |
| Monte, Redding and Rossi-Hansberg (2018) | US counties, assumed housing share 0.40 | −1.32 |
| Ahlfeldt, Redding, Sturm and Wolf (2015), Table 5 col 3 | Berlin blocks, housing share 0.25 | −1.67 |
| Rabe and Taylor (2010 ISER WP), Tables 5 and 8; slides | British regions, annual moves per 1% house-price gap | −0.015 pp (all tenures, t 2.53); −0.009 pp (slides, t 1.39); −0.005 pp (private renters, t 0.64) |

- **Unconverted** (verified, but not convertible without more assumptions): Fajgelbaum et al. (2019), Bayer et al. (2016), Ahlfeldt et al. (2020).
- **TODO, excluded:**
  - Bayer, Ferreira and McMillan (2007): no price coefficient in the open version.
  - Rabe and Taylor (2012): published version paywalled.
  - Murphy, Muellbauer and Cameron (2006), Cameron and Muellbauer (1998), Jackman and Savouri (1992): full texts not opened.
- **Caveat.** None of the verified estimates is specific to young adults or renters, apart from the insignificant Rabe and Taylor private-renter interaction.

**Step 4. Pound values** (`s8_pound_values.md` has every row with its 95% CI range)

| Response (20-29 vs family proxy, all 316 LADs, 2020) | Coefficient | Stock elasticities: £/month, range (median) | Annual-flow elasticities: £/month, range (median) |
|---|---|---|---|
| Garden access × young × 2020, registered model | +4.34 (<0.001) | £1.03-£9.96 (£2.34) | £203-£608 (£338) |
| Measure (c) × young × 2020 | −5.54 (<0.001) | £1.32-£12.71 (£2.98) | £258-£775 (£431) |

Only measure (c) is valued, although (b) also survives the garden control (garden × 2020 at p 0.065 with (b)). Measure (c) has the larger and more precise 2020 coefficient.

Assumptions, one sentence each:
1. The base is the England median monthly private rent for October 2018 to September 2019, £700, from ONS/VOA Private Rental Market Statistics Table 1.7. It is applied to every LA, including the 22 in Wales, which that series does not cover.
2. The triple-difference response, young adults relative to the family proxy, is treated as the young-adult response to the amenity measure.
3. The response is in net moves per 1,000 group residents per SD and is read as a change of R/1,000 in the log of the local young-adult population.
4. A stock elasticity ε converts the response to a rent change of (R/1,000)/ε. This assumes that one year's net flow equals the full equilibrium population response, which overstates the response per year of adjustment and so understates the pound value.
5. The annual-flow elasticity of Rabe and Taylor converts the response at 10 × the percentage-point coefficient per 1,000 residents per year per 1% housing cost. It treats a house-price differential between British regions as a rent differential between LAs.
6. The value per month is the absolute rent-equivalent change times the base rent, using a linear approximation.
7. The housing shares used to convert the location-choice parameters are those set or estimated in each paper, as recorded in the S8 notes.
8. Working-paper or author versions were read for most papers, so published numbers may differ.

**Judgement calls**
- **Measure (a)** uses mid-2019 residents, as in the registered measure.
- **Measure (b)** takes land area as Census 2021 usual residents divided by TS006 population density (persons per km², rounded to 0.1), summed over 2021 MSOAs. The total, 151,043 km², matches England and Wales land area.
- **Measure (c)** is the log of the Census 2021 population-weighted mean of the point-based FHRS access sum (restaurants/cafés, pubs/bars/clubs, takeaways) with λ = 1.5 km. FHRS is a 2026 snapshot.
- **Standardisation.** All measures enter as logs, standardised over the 316 LADs, so coefficients are per SD.
- **Model.** The headline controls and fixed effects are unchanged from the registered model (f).
- **Leave-one-out ranking.** For measure (c), contributions are ranked by absolute size, because the full estimate is negative. For the earlier student check they were ranked in the direction of the estimate.
- **Pound-value responses.** These use all 316 LADs, ages 20-29 against the family proxy, the plan's headline sample and comparison.
- **Annual-flow elasticities.** All three Rabe and Taylor figures enter the range as verified figures, including the insignificant private-renter and slide estimates.

**Departure 8, final check: density controls and the North Northamptonshire value.** Decided after the registered results. Script: `scripts/s8b_density_check.py`. Outputs: `data/clean/s8b_density_check.md`, `.csv` and `s8b_density_measures_la.csv`.

**Does measure (c) survive the density controls? Partly.**
- **All 316 LADs, ages 20-29.** The pattern survives. Adding job density, resident density or both (each × young × year, with teleworkability and garden access):
  - leaves the 2020 coefficient between −5.31 and −5.58 (p 0.021 to 0.024, against −5.54 without them);
  - leaves the 2022 − 2020 contrast between +10.08 and +11.01 (p < 0.001).
- **All 316 LADs, ages 25-29.** The 2020 outflow survives (−4.33 to −4.97, p ≤ 0.037), but the contrast weakens to p 0.062 to 0.085.
- **Outside London, ages 20-29.** The 2020 outflow loses significance: −3.66 to −4.15, p 0.111 to 0.148. The contrast stays at +7.8 to +8.2 (p ≤ 0.010), but it now rests mainly on a negative 2021 coefficient (−8.4 to −9.3) and not on a 2022 recovery (2022 p ≥ 0.14).
- **Outside London, ages 25-29.** Nothing is significant.
- **Why identification is weak.** Measure (c) correlates at 0.90 with log job density and 0.89 with log resident density, and measure (b) at 0.98 with both. With density held fixed, the amenity coefficient rests on the remaining tenth or so of variation, and outside London that is not enough to separate access to variety from density.
- **Reading.** The national London-like pattern on measure (c) is robust to density controls when London is included, and fragile outside it. The pattern cannot be attributed to variety as distinct from density.

**Densities**
- **Job density.** BRES 2019 employment from Nomis NM_189_1 ("Employment" = employees plus working owners, LADs April 2023), divided by land area.
  - BRES figures at LA level are rounded, mostly to the nearest 1,000 jobs.
  - Median 305 jobs per km²; maximum 35,217 in Westminster.
- **Resident density.** Mid-2019 residents divided by land area; median 688 per km².
- **Land area.** As for measure (b): Census 2021 usual residents divided by TS006 density, summed over MSOAs.
- Both densities enter as standardised logs over the 316 LADs.

| | Measure (b) | Measure (c) | Teleworkability | Garden access | Job density | Resident density |
|---|---|---|---|---|---|---|
| Job density | .982 | .904 | .425 | −.563 | 1 | .981 |
| Resident density | .979 | .892 | .365 | −.492 | .981 | 1 |

**Measure (c) with density controls** (headline model (f) with measure (c) in place of D, against the family proxy)

| Sample | Young | Added controls | 2020 | 2021 | 2022 | 2022 − 2020 | LAs |
|---|---|---|---|---|---|---|---|
| all 316 | 20-29 | none | −5.54 (<0.001) | −3.85 (0.046) | 5.60 (0.001) | 11.14 (<0.001) | 316 |
| all 316 | 20-29 | job density | −5.31 (0.023) | −7.64 (0.021) | 4.77 (0.066) | 10.08 (<0.001) | 316 |
| all 316 | 20-29 | resident density | −5.58 (0.021) | −6.10 (0.089) | 5.43 (0.042) | 11.01 (<0.001) | 316 |
| all 316 | 20-29 | both | −5.47 (0.024) | −6.86 (0.047) | 5.14 (0.052) | 10.61 (<0.001) | 316 |
| all 316 | 25-29 | none | −5.34 (<0.001) | −2.07 (0.194) | 0.13 (0.916) | 5.46 (<0.001) | 316 |
| all 316 | 25-29 | job density | −4.33 (0.037) | −0.40 (0.882) | 0.63 (0.791) | 4.95 (0.062) | 316 |
| all 316 | 25-29 | resident density | −4.97 (0.019) | 0.46 (0.866) | −0.43 (0.855) | 4.54 (0.085) | 316 |
| all 316 | 25-29 | both | −4.68 (0.027) | 0.20 (0.940) | 0.00 (1.000) | 4.68 (0.080) | 316 |
| outside London | 20-29 | none | −5.19 (<0.001) | −3.83 (0.046) | 5.40 (0.002) | 10.59 (<0.001) | 284 |
| outside London | 20-29 | job density | −3.66 (0.148) | −8.44 (0.012) | 4.17 (0.140) | 7.83 (0.010) | 284 |
| outside London | 20-29 | resident density | −4.15 (0.111) | −9.33 (0.007) | 4.00 (0.168) | 8.15 (0.007) | 284 |
| outside London | 20-29 | both | −3.98 (0.126) | −9.20 (0.008) | 4.02 (0.165) | 7.99 (0.008) | 284 |
| outside London | 25-29 | none | −4.96 (<0.001) | −2.02 (0.202) | −0.07 (0.960) | 4.89 (0.001) | 284 |
| outside London | 25-29 | job density | −2.58 (0.246) | −0.97 (0.694) | −0.21 (0.935) | 2.37 (0.414) | 284 |
| outside London | 25-29 | resident density | −3.39 (0.135) | −1.66 (0.514) | −1.84 (0.486) | 1.55 (0.591) | 284 |
| outside London | 25-29 | both | −3.10 (0.167) | −1.44 (0.566) | −1.38 (0.596) | 1.72 (0.556) | 284 |

**North Northamptonshire, measure (a)**
- **Cause: an error in the source counts, not real venues.**
  - In 2019, Business Counts record 2,020 local units in SIC division 93 for North Northamptonshire.
  - 1,845 of them are in subclass 93191, "activities of racehorse owners", almost all micro units. In 2017 there were 15.
  - The next highest LAD for 93191 in 2019 is North Yorkshire, with 200.
  - West Northamptonshire has 20, and North Northamptonshire's other division 93 subclasses are in line with their 2017 values.
  - This is consistent with a bulk registration of racehorse-owning entities, which are not consumer venues.
- **Correction.** Subclass 93191 is excluded from measure (a) for every LAD. North Northamptonshire falls from 8.38 to 3.18 per 1,000, against a national median of 3.65. Corrected and uncorrected measure (a) correlate at .978 across LADs.
- **Measure (a), corrected** (headline (f), against the family proxy):

| Sample | Young | 2020 | 2021 | 2022 | 2022 − 2020 | Garden × 2020 |
|---|---|---|---|---|---|---|
| all 316 | 20-29 | 1.59 (0.067) | 2.88 (0.112) | 0.75 (0.521) | −0.85 (0.502) | 4.26 (<0.001) |
| all 316 | 25-29 | 2.83 (0.001) | 2.93 (0.025) | 1.48 (0.063) | −1.36 (0.220) | 5.24 (<0.001) |
| outside London | 20-29 | 3.00 (0.009) | 0.84 (0.577) | −0.69 (0.645) | −3.69 (0.017) | 3.86 (0.011) |
| outside London | 25-29 | 5.03 (<0.001) | 1.95 (0.098) | 1.15 (0.242) | −3.88 (0.006) | 5.45 (<0.001) |

  The conclusions on measure (a) are unchanged: no closure outflow, and the reverse pattern outside London.
- **The registered measure D carries the same 1,845 units.**
  - Recomputing D without subclass 93191 (correlation .983 with the registered D) and rerunning the registered headline (f) gives 2020 = 2.12 (p 0.010) and 2022 − 2020 = −1.47 (p 0.224), against 1.82 (0.030) and −1.53 (0.191) as registered.
  - The registered results are left as registered, and this run is a sensitivity check only. The registered verdict is unchanged.

**Data correction: SIC 93191 excluded from measures (a) and (b) for every LAD.** Script: `scripts/s8c_corrected_ab.py`. Output: `data/clean/s8c_corrected_ab.md` and `.csv`.

- **The error.** UK Business Counts (Nomis NM_141_1, LADs April 2023) record local units in subclass 93191, "activities of racehorse owners", as follows:
  - North Northamptonshire: 15 in 2017 and 1,845 in 2019.
  - North Yorkshire, the next highest LAD in 2019: 160 in 2017 and 200 in 2019.
  - The 2019 North Northamptonshire count is about nine times the next highest. It is almost entirely micro units, and the area's other division 93 subclasses are in line with 2017. It is treated as a registration artefact, not consumer venues.
- **The correction.** 93191 is removed from the units in measures (a) and (b) for every LAD, not only North Northamptonshire, so that the definition is the same everywhere. Racehorse owners are not consumer-facing amenities.
- **Effect on North Northamptonshire.** Measure (a) falls from 8.38 to 3.18 per 1,000, and measure (b) from 3.02 to 1.15 units per km².
- **Effect across LADs.** Corrected and uncorrected versions correlate at .978 for (a) and .999 for (b).
- **Measure (c) is unaffected.** It is built from FHRS food premises, not Business Counts.
- **The registered D also contains these units.** It is left as registered; the sensitivity run without them is reported above.

**Headline (f), as published and with 93191 excluded, against the family proxy (WCB p)**

| Measure | Version | Sample | Young | 2020 | 2021 | 2022 | 2022 − 2020 | Garden × 2020 |
|---|---|---|---|---|---|---|---|---|
| (a) | as published | all 316 | 20-29 | 1.23 (0.154) | 2.71 (0.108) | 0.26 (0.819) | −0.97 (0.412) | 4.04 (<0.001) |
| (a) | 93191 excluded | all 316 | 20-29 | 1.59 (0.067) | 2.88 (0.112) | 0.75 (0.521) | −0.85 (0.502) | 4.26 (<0.001) |
| (a) | as published | all 316 | 25-29 | 2.48 (0.004) | 2.66 (0.034) | 1.03 (0.181) | −1.45 (0.158) | 4.99 (<0.001) |
| (a) | 93191 excluded | all 316 | 25-29 | 2.83 (0.001) | 2.93 (0.025) | 1.48 (0.063) | −1.36 (0.220) | 5.24 (<0.001) |
| (a) | as published | outside London | 20-29 | 2.36 (0.041) | 0.77 (0.580) | −1.21 (0.384) | −3.56 (0.014) | 3.54 (0.020) |
| (a) | 93191 excluded | outside London | 20-29 | 3.00 (0.009) | 0.84 (0.577) | −0.69 (0.645) | −3.69 (0.017) | 3.86 (0.011) |
| (a) | as published | outside London | 25-29 | 4.28 (<0.001) | 1.62 (0.151) | 0.55 (0.562) | −3.74 (0.003) | 5.03 (<0.001) |
| (a) | 93191 excluded | outside London | 25-29 | 5.03 (<0.001) | 1.95 (0.098) | 1.15 (0.242) | −3.88 (0.006) | 5.45 (<0.001) |
| (b) | as published | all 316 | 20-29 | −4.15 (<0.001) | −1.89 (0.216) | 4.59 (0.002) | 8.74 (<0.001) | 1.78 (0.065) |
| (b) | 93191 excluded | all 316 | 20-29 | −4.06 (<0.001) | −1.89 (0.216) | 4.64 (0.002) | 8.70 (<0.001) | 1.81 (0.061) |
| (b) | as published | all 316 | 25-29 | −3.81 (<0.001) | −1.71 (0.193) | 0.48 (0.635) | 4.29 (<0.001) | 2.23 (0.022) |
| (b) | 93191 excluded | all 316 | 25-29 | −3.74 (<0.001) | −1.68 (0.196) | 0.55 (0.586) | 4.29 (<0.001) | 2.25 (0.021) |
| (b) | as published | outside London | 20-29 | −4.00 (<0.001) | −1.63 (0.283) | 4.45 (0.001) | 8.45 (<0.001) | 0.77 (0.598) |
| (b) | 93191 excluded | outside London | 20-29 | −3.91 (<0.001) | −1.62 (0.285) | 4.50 (0.001) | 8.42 (<0.001) | 0.81 (0.579) |
| (b) | as published | outside London | 25-29 | −3.60 (<0.001) | −1.43 (0.274) | 0.46 (0.660) | 4.06 (<0.001) | 1.77 (0.182) |
| (b) | 93191 excluded | outside London | 25-29 | −3.54 (<0.001) | −1.40 (0.283) | 0.54 (0.604) | 4.08 (<0.001) | 1.79 (0.175) |

- **Measure (b)** moves by at most 0.09 per 1,000 on any coefficient, because one LAD's units barely shift a density measure.
- **Measure (a)** moves more, with 2020 coefficients up by 0.35 to 0.75. Its conclusions are unchanged: no closure outflow nationally, and the reverse pattern outside London.
- **The departure 8 reading is unchanged by the correction.**

**Departure 8, pre-trend check for measures (b) and (c).** Decided after the registered results. Script: `scripts/s8d_pretrend_check.py`. Output: `data/clean/s8d_pretrend_check.md` and `.csv`.
- **The pre-trends.** Measures (b) and (c) carry large positive pre-period coefficients in the headline model (f), ages 20-29 against the family proxy.
  - Measure (c), all 316 LADs: 2016 +4.99, 2017 +7.03, 2018 +4.47, all with p ≤ 0.003.
  - Measure (b) has the same pattern.
  - So the young-adult net inflow into dense districts was already falling, relative to other districts, from 2017 to 2019. These coefficients were not reported in the departure 8 summary above; this entry corrects that omission.
- **The trend check.** Deviations of the 2020, 2021 and 2022 coefficients from a linear trend fitted through the 2016-2019 coefficients:

| Measure | Sample | Young | Density controls | Slope per year | 2020 deviation | 2022 deviation |
|---|---|---|---|---|---|---|
| (b), 93191 excluded | all 316 | 20-29 | none | −1.57 (<0.001) | −3.94 (<0.001) | +7.89 (<0.001) |
| (b), 93191 excluded | outside London | 20-29 | none | −1.58 (<0.001) | −3.69 (0.001) | +7.90 (<0.001) |
| (c) | all 316 | 20-29 | none | −1.75 (0.001) | −5.28 (<0.001) | +9.36 (<0.001) |
| (c) | all 316 | 20-29 | job and population density | −0.83 (0.485) | −4.94 (0.102) | +7.33 (0.156) |
| (c) | all 316 | 25-29 | none | −1.37 (<0.001) | −3.68 (0.003) | +4.52 (0.017) |
| (c) | outside London | 20-29 | none | −1.92 (<0.001) | −4.72 (0.001) | +9.71 (<0.001) |
| (c) | outside London | 20-29 | job and population density | −1.56 (0.216) | −2.88 (0.368) | +8.22 (0.135) |
| (c) | outside London | 25-29 | job and population density | −1.67 (0.045) | −0.75 (0.775) | +4.31 (0.270) |

- **Reading.**
  - Without density controls, the outflow and the reversal on measures (b) and (c) hold against a linear pre-trend.
  - With job and population density controlled, the pre-period coefficients are no longer significant, and no 2020 or 2022 deviation is significant.
- **After 2022.** For measure (c) the coefficient is negative again in 2023-2025: −4.69, −9.35 and −9.94, with p ≤ 0.01.

---

## Feasibility report (B6)

**What was obtained.** All five data blocks were assembled, and no regressions were run. Source detail, data dictionaries and every judgement call are in `notes/`: `B1_amenities.md`, `B2_census_migration.md`, `B3_B5_panel_mobility.md` and `B4_restrictions.md`.

| Block | Data | Coverage | Quality |
|---|---|---|---|
| B1a | FSA Food Hygiene Rating Scheme points, current snapshot downloaded 29 Oct 2026: restaurants and cafés, pubs/bars/nightclubs, takeaways | 225,858 points, 320 authorities, 96.8% geocoded after NSPL filling | Unlocated records are mostly home caterers with withheld addresses (up to 31% in Redbridge). Restaurant/café counts are about twice Business Counts because FHRS includes canteens and caterers. It is a 2026 snapshot, not 2019. |
| B1b | OpenStreetMap full history via ohsome, as at 31 Dec 2019 and 31 Dec 2022: restaurant, café, fast food, pub, bar, nightclub, cinema, theatre, arts centre, fitness centre | 119,158 points (2019), 139,770 (2022), 99.9% assigned to an MSOA | Growth from 2019 to 2022 is mostly mapping effort (fitness centres +93%, pubs +1%). Theatre and arts tags cover about 15% of the matching SIC units, and fitness tags about 33%. |
| B1c | Counts per 2021 MSOA and 2023 LA, and exp(−d/λ) access indices with λ = 1, 1.5 and 3 km from 2021 MSOA population-weighted centroids | 7,264 MSOAs, 318 LAs | The 90 index variants include point-based indices (30 km cut-off) and pilot-style centroid-to-centroid indices. |
| B2 | Census 2021 address one year ago (March 2020 to March 2021), public origin-destination and topic-summary tables | LA: in, out and net by 22 age bands (318 LAs). MSOA: in and out for all ages (7,264); inflows by 22 bands (7,205) and by single year (7,158) | Totals match TS019 within 0.004%. 59 MSOAs have no age data because of disclosure rules, and they are not random (below-median migration). Outflows abroad are not observed. |
| B3 | National LA panel: internal migration by age group 2015-2025 (four counterpart definitions), PIPR rents quarterly, Business Counts 2019 I+R density, Google mobility | 318 LAs. Rents 316 (no City of London or Isles of Scilly). Mobility 317 (no Isles of Scilly). | The 32 London boroughs reproduce every pilot file exactly. The Google-to-LA mapping is 1:1 for 308 LAs and built from old districts for 5; Shropshire also covers Telford and Wrekin. |
| B4 | Legal hospitality restrictions by LA and day, 1 Mar 2020 to 31 Dec 2021, built from legislation.gov.uk (367 regulation texts); 0-1 intensity plus eight component flags; quarterly means | 318 LAs (296 England, 22 Wales), 213,378 LA-days | No single compiled dataset exists. December 2020 tiers agree 100% with Abel and Siraj (10,920 LTLA-days). Commons Library snapshots agree apart from a 3-day Carlisle lag in the Library table. July-September 2020 English local measures, Wales and 2021 rest on the regulations alone. |
| B5 | Google retail and recreation, mean % change from Google's 3 Jan-6 Feb 2020 baseline, LA × quarter 2020Q1-2022Q3 | 3,487 of 3,498 LA-quarters; 23 under 50% coverage (Isles of Scilly, Rutland, Anglesey) | The baseline is winter, so summer quarters in tourist areas reach +137%. 2020Q1 covers 15 Feb to 31 Mar only. |

**Failed, blocked or needing an application**
- **ohsome v1.** The `/elements/centroid` and `/geometry` endpoints returned HTTP 403. Points were taken from the openly served `/elements/bbox` endpoint, using box centres for ways and relations (no box over 2 km).
  - v1 shuts down on 30 Nov 2026, and v2 needs an API key. To rerun, register at ohsome.org and follow the steps in `notes/B1_amenities.md`.
- **Census 2021 MSOA outflows by age: safeguarded.**
  - ODMG10EW at MSOA (7 age bands by sex) needs the UK Data Service End User Licence. Download it through WICID at https://wicid.ukdataservice.ac.uk/flowdata/cider/wicid/downloads.php, which timed out during this run, so logging in is needed to confirm it is there.
  - The full MSOA by 22-band matrix (ODMG02EW at MSOA) is secure: Integrated Data Service, accredited researcher.
  - All safeguarded and secure tables are listed in `notes/B2_census_migration.md`.
- **Dead or unusable sources.** The UK coronavirus dashboard API (`alertLevel`) is no longer served, and the one archived copy has an empty column. OxCGRT has nation-level data only. The IfG timeline has no data file.
- **Not built nationally.** The 2011 Census teleworkability, student and hospitality-worker controls need a lookup from 2011 to 2023 LA boundaries.

**Usable units**
- **LA level:** 318 LAs (2023 codes). 316 have every block, excluding City of London and Isles of Scilly. Migration covers 11 years ending June 2015-2025; rents and mobility are quarterly; restrictions are daily.
- **MSOA level:** 7,264 2021 MSOAs. The new amenity counts and access indices cover 7,259 with FHRS, 7,023 with OSM 2019 and 7,096 with OSM 2022. The Census 2021 migration cross-section covers 7,264 for all-ages inflows and outflows, and 7,205 for inflows by age.

**Validation against Business Counts 2019**

Pearson correlations across 318 LAs, from `B1_amenities.md`:

| Category | SIC | Levels | Per 1k | Log per 1k |
|---|---|---|---|---|
| FHRS restaurant/café | 56101+56102 | .966 | .963 | .880 |
| FHRS takeaway | 56103 | .944 | .736 | .558 |
| FHRS pub/bar/club | 56301+56302 | .937 | .820 | .883 |
| OSM restaurant+café | 56101+56102 | .938 | .926 | .777 |
| OSM fast food | 56103 | .802 | .338 | .146 |
| OSM pub+bar+nightclub | 5630 | .966 | .864 | .880 |
| OSM cinema | 59140 | .799 | .569 | .472 |
| OSM theatre+arts centre | 90010+90040 | .749 | .750 | .442 |
| OSM fitness centre | 93130 | .651 | .312 | .209 |

**Correlations between amenity measures, mobility and restrictions**

The figures below come from `scripts/b6_feasibility.py` and `data/clean/b6_feasibility_correlations_la.csv`. The sample is 316 LAs, or 315 for mobility after low-coverage quarters are excluded. Amenity measures are log(1 + units per 1,000 residents).

| | BC I+R per 1k | FHRS restaurant/café | OSM 2019 restaurant+café |
|---|---|---|---|
| BC I+R per 1k (2019) | 1 | .830 | .817 |
| Google retail+rec change, 2020Q2 | −.533 | −.542 | −.595 |
| Google retail+rec change, 2020Q4 | −.380 | −.462 | −.481 |
| Google retail+rec change, 2021Q1 | −.548 | −.564 | −.608 |
| Legal hospitality intensity, 2020Q3 | −.063 | .065 | −.118 |
| Legal hospitality intensity, 2020Q4 | −.279 | −.130 | −.198 |

- LAs with higher 2019 amenity density saw larger falls in retail and recreation visits during the closures, with correlations from −.38 to −.61 across the three measures and quarters. The closure shock to high-amenity areas is therefore visible in behaviour across England and Wales, not only in London.
- Other amenity measures against BC I+R: FHRS pub/bar/club .376, FHRS takeaway .047, OSM pub+bar+club .621, OSM arts venue .711, OSM fitness .264.
- Legal intensity and the Google fall correlate weakly across LAs within a quarter: .116 to .139 for 2020Q3 intensity, and −.179 to .127 for 2020Q4. National lockdowns dominate the variation, so cross-LA differences in legal closure exist only in 2020Q3-Q4 (Leicester, local measures, tiers, Welsh firebreak).
- Across the 316 LAs, log I+R density correlates at −.534 with garden access (−.733 within London), +.376 with the 2021 private-renting share and +.119 with the share aged 20-39. Outside London, amenity density is less tied to garden access.

**Estimation designs these data would support**
1. **National triple difference.** Young against older net internal migration × 2019 amenity density across 316 LAs (B3), years to June 2016-2025. There are about ten times as many clusters as the London pilot, and region × year effects can be added.
2. **Dose-response with legal closure intensity.** Amenity density × B4 hospitality intensity, using the variation across LAs in 2020Q3-Q4 (Leicester, local measures, tiers, Welsh firebreak). Quarterly outcomes would be PIPR rents and Google mobility (B3/B5); migration would use exposure summed over each year to June.
3. **Mobility first stage.** The Google retail and recreation fall (B5) regressed on amenity density, as the behavioural channel through which closures removed variety, with intensity as an instrument or as a dose.
4. **MSOA cross-section from Census 2021.** Inflows by age (March 2020 to March 2021) on MSOA amenity access (FHRS, OSM 2019), with LA fixed effects. This separates access to variety from centrality inside each LA. Outflows by age need the safeguarded ODMG10EW.
5. **Separating amenity density from garden access and teleworkability nationally.** Their correlation is weaker outside London (−.53 for gardens), so the confounding found in the London A1 test can be tested. This needs a national teleworkability control built on 2023 boundaries.
6. **Supply response.** Change in OSM venue counts from 2019 to 2022, or FHRS against Business Counts over time, as a measure of the supply term d ln N / d ln L. This needs a control for OSM mapping completeness before any use.
7. **National rent capitalisation.** Quarterly PIPR × amenity density × closure intensity, with LA and region × quarter effects.

---

## File index

- **Run file:** `extension/run_all.py` runs every step in order (`--only`, `--start`). `PRE_ANALYSIS_PLAN.md` and its checksum are at the extension root.
- **Scripts** (`extension/scripts/`):
  - `ext_config.py`: shared paths.
  - `b1_*.py` (8): FHRS, OSM, geography, assignment, access, validation.
  - `b2_*.py` (4): Census 2021 migration.
  - `b3_*.py` and `b5_*.py`: national panel and mobility.
  - `b4_01`-`b4_05` and `b4_common.py`: restrictions.
  - `b6_feasibility.py`: correlations above.
  - `s1_*.py`: national controls. `s3_download_cases.py` and `s3_build_case_rates.py`: case rates. `s4_download_*.py` and `s4_build_census_inflows.py`: census movers.
  - `e_core.py`: estimators. `s2_national_ddd.py`, `s3_tier_design.py`, `s4_census_msoa.py`, `s5_national_rents.py`: pre-registered estimation.
- **Clean data** (`extension/data/clean/`, plus large files in `~/research-data/london-variety-extension/clean/`): see the file tables in each notes file.
- **Raw downloads:** `~/research-data/london-variety-extension/raw/`.
