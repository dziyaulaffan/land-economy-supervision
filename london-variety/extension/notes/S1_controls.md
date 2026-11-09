# S1 national controls: LA (2023 boundaries) and MSOA (2021) (data assembly only, no regressions)

Built 29 October 2026. Scripts in `extension/scripts/`, run in this order: `s1_download.py`, `s1_controls_la.py`,
`s1_controls_msoa.py`, `s1_correlations.py`. Nothing in the pilot's `scripts/`, `data/`, `outputs/` or report files
was changed; pilot raw files were read only. No regressions were run.

## Files

| File | Unit | Rows | Coverage |
|---|---|---|---|
| `extension/data/clean/s1_controls_la2023.csv` | April 2023 LAD | 318 | all 318 LAs, no missing values; X_* standardised over 316 (City of London and Isles of Scilly excluded, flagged `excluded_from_z`) |
| `extension/data/clean/s1_controls_msoa21.csv` | 2021 MSOA | 7,264 | all 7,264 MSOAs, no missing values; X_* standardised over all 7,264 |
| `extension/data/clean/s1_control_correlations.csv` | one row per control | 7 | correlations with log amenity density (table below) |
| `extension/data/clean/s1_lookup_la2011_lad23.csv` | 2011 Census LA | 348 | 2011 LA (Nomis TYPE464 codes) to 2023 LAD, with 2011 population |
| `extension/data/clean/s1_validation_london.csv` | one row per variable | 5 | 32 London boroughs against the pilot |
| `extension/data/clean/s1_validation_msoa_vs_la.csv` | one row per comparison | 11 | 2021 MSOA counts summed to LADs against the 2011 LA controls |
| `extension/data/clean/s1_homework_score_soc2010_major.csv` | SOC 2010 major group | 9 | ONS 2020 homeworking score by major group |

LA file columns: `la_code`, `la_name`, `region`, the six shares (`telework_share`, `garden_share`, `flat_share`,
`private_rent_share`, `age20_39_share`, `student_share`), `X_*` for each, `telework_share_alt2` (pilot's 2.0
threshold), `homework_score_mean`, `n_la2011` (2011 LAs merged), `n_garden_districts`, and denominators.
MSOA file columns: `msoa21cd`, `lad23cd`, `region`, the six shares and `X_*`, `telework_share_frac` and
`X_telework_share_frac` (alternative rule), `garden_share_whole_msoa11`, `n_msoa11`, and all numerators and
denominators, so any share can be re-aggregated.

Raw downloads (in `research-data/london-variety-extension/raw/s1/`): `census2011_la/*_la2011_ew.csv` (Nomis
NM_503_1 QS103EW, NM_619_1 KS402EW, NM_561_1 QS606EW, NM_623_1 KS501EW, NM_534_1 QS402EW, geography TYPE464, all
348 England and Wales LAs, paged at 25,000 rows); `census2021_bulk/census2021-ts044|ts054|ts063|ts066|ts068.zip`
(Nomis bulk); `ons_api/msoa_economic_activity_status_7a_resident_age_7a.csv` (ONS custom-dataset API, 355,936 rows,
no MSOA blocked); `nspl_msoa11_msoa21_postcodes.csv` (postcode counts by 2011 x 2021 MSOA). Reused without
downloading: pilot `ons_gardens/osprivateoutdoorspacereferencetables.xlsx`, pilot
`ons_homeworking/ons_whichjobscanbedonefromhome_2020_data.xlsx`, pilot NSPL (Aug 2024 2011-Census edition and Aug
2026), and TS007A from `raw/census2021_migration/`.

## Definitions

| Control | LA (2011, summed to 2023 LADs) | MSOA (2021) |
|---|---|---|
| telework_share | QS606EW minor groups, each weighted by its ONS-employment share in SOC 2010 unit groups scoring below 1.5; over residents in employment (pilot formula) | TS063: share of residents in employment in SOC major groups 1-4 (rule below) |
| garden_share | ONS April 2020 LAD sheet, addresses with private outdoor space over all addresses (houses + flats), counts summed | ONS April 2020 MSOA (2011) sheet, counts apportioned to 2021 MSOAs by postcode weights |
| flat_share | QS402EW: purpose-built flats + converted/shared house + commercial building, over all households | TS044: purpose-built + converted/shared house + other converted building + commercial building, over all households |
| private_rent_share | KS402EW cell 300 over all households | TS054 private rented (landlord or agency + other) over all households |
| age20_39_share | QS103EW ages 20-39 over usual residents | TS007A ages 20-39 over usual residents |
| student_share | KS501EW full-time students aged 18+ (cell 9) over residents aged 16+ (cell 0) | ONS API: full-time students aged 18+ (active or inactive) over residents aged 16+ |

## MSOA teleworkability rule

ONS 2020 homeworking score by SOC 2010 major group (employment-weighted over unit groups, ONS weights): 1 managers
1.355, 2 professional 1.234, 3 associate professional 1.403, 4 administrative 1.058, 5 skilled trades 2.929, 6 caring
and leisure 1.969, 7 sales 1.660, 8 operatives 2.641, 9 elementary 2.363. Groups 1-4 fall below 1.5, so
`telework_share` is the share of residents in employment in SOC 2020 major groups 1-4. The alternative
`telework_share_frac` weights each group by its share of employment in unit groups scoring below 1.5 (1 .606,
2 .712, 3 .603, 4 .820, 5 .020, 6 .250, 7 .334, 8 .031, 9 .007).

Correlations across 316 LAs, MSOA counts summed to 2023 LADs:

| Comparison | r |
|---|---|
| 2021 MSOA threshold rule vs 2011 LA pilot measure | .954 |
| 2021 MSOA fractional rule vs 2011 LA pilot measure | .951 |
| 2011 LA threshold rule at major-group resolution vs 2011 LA pilot measure | .974 |
| 2011 LA fractional rule at major-group resolution vs 2011 LA pilot measure | .975 |
| 2021 MSOA threshold rule vs 2011 LA same rule | .987 |

The two rules are almost equally close to the pilot measure. Coarser occupation groups cost about .025 in
correlation and the move from 2011 to 2021 (and SOC 2010 to SOC 2020) about another .02. Levels differ: the threshold
rule averages .55 against .39 for the pilot measure, so only the standardised `X_` versions are comparable.

## Validation

**London (32 boroughs, City of London excluded) against the pilot's `event_study_borough_vars.csv` and
`borough_student_hospitality_2011.csv`.** All five reproduce exactly. The maximum absolute differences are
floating-point noise: telework_share 5.6e-17, garden_share 0, private_rent_share 8.3e-17, age20_39_share
8.3e-17, student_share 9.7e-17.

**2021 MSOA counts summed to 2023 LADs against the 2011 LA controls (316 LAs).** garden_share r = 1.000 (maximum
difference .0001, from postcode apportioning), flat_share .998, private_rent_share .975 (mean .158 in 2011, .192 in
2021), age20_39_share .977, student_share .975, telework_share .954. Full-time students aged 16+ from the ONS API
match TS066 exactly in total and by MSOA (r = 1.000).

## Correlations with log amenity density

LA: 316 LAs, `log_per1k_IR` (Business Counts 2019 I+R units per 1,000). Within region: both variables demeaned by
region. MSOA: 7,262 MSOAs (City of London and Isles of Scilly MSOAs excluded), log(1 + FHRS restaurant/café + pub/
bar/club + takeaway access, λ = 1.5 km). Within LA: both demeaned by `lad23cd`. Pearson correlations, not causal
estimates.

| Control | LA national | LA within region | MSOA national | MSOA within LA |
|---|---|---|---|---|
| telework_share | .414 | .365 | .053 | −.217 |
| garden_share | −.534 | −.491 | −.403 | −.228 |
| flat_share | .482 | .447 | .712 | .511 |
| private_rent_share | .472 | .391 | .575 | .469 |
| age20_39_share | .174 | .044 | .687 | .514 |
| student_share | .219 | .158 | .395 | .274 |
| telework_share_frac (MSOA only) | | | .083 | −.187 |

- Across LAs, amenity density goes with teleworkable jobs, flats, renting and less garden access. The share aged
  20-39 is nearly unrelated within regions (.044).
- Within LAs, MSOAs with more amenity access have *fewer* teleworkable residents (−.217): town centres in most LAs
  house more service and elementary workers. The LA-level link between amenity and teleworkability does not carry
  over to neighbourhoods.
- Flats, private renting and the share aged 20-39 are the strongest MSOA correlates (.47 to .51 within LAs).

## Judgement calls

- 2011 LA tables come from Nomis geography TYPE464 (348 LAs), which already uses post-2013 codes (Gateshead E08000037, Northumberland E06000057, the four Hertfordshire districts), so the 2013 minor boundary changes are as Nomis assigned them.
- Every 2011 LA maps whole to one 2023 LAD; 11 2023 LADs are unions of 2 to 7 2011 LAs, and no best-fit splits were needed.
- Chains were followed: Taunton Deane and West Somerset to Somerset West and Taunton (2019) and then to Somerset (2023).
- Counts were summed before forming shares at both levels, never averaged.
- The April 2020 garden LAD sheet is on 2019-2020 codes; Buckinghamshire, Northamptonshire, Cumbria, North Yorkshire and Somerset districts were summed into 2023 LADs, as in `b3_crosssection.py`.
- The Isles of Scilly has its own row in every 2011 table and in the garden data, so it was not merged with Cornwall.
- flat_share in 2011 uses QS402EW (households by accommodation type), not KS401EW, which counts household spaces including empty ones.
- 2011 flat_share counts shared dwellings (0.3% of households in England and Wales) in the denominator but not the numerator; 2021 TS044 has no shared-dwelling category.
- 2021 flat_share includes "part of another converted building", which 2011 folded into converted flats.
- MSOA teleworkability uses SOC 2020 major groups in TS063 with scores built on SOC 2010; major-group headings are unchanged between the two, but unit-group content moved slightly.
- The threshold rule (groups 1-4) is the main MSOA measure, as the brief specified; the fractional rule is kept as `telework_share_frac` because it is the pilot formula at coarser resolution and correlates almost equally (.951 against .954).
- Occupation at SOC 2020 minor-group level (ONS API, 105 categories) was not used because the ONS score is on SOC 2010 and no unit-group crosswalk was built.
- The MSOA student share needs ages 18+, which TS066 and TS068 do not split; it was taken from the ONS custom-dataset API (economic activity 7 categories by age 7 categories), with no MSOA withheld.
- Students in the MSOA measure are economically active full-time students plus economically inactive full-time students, matching KS501EW's full-time students aged 18+.
- The MSOA residents-aged-16+ denominator comes from the same API query, not TS007, so numerator and denominator share one set of cell perturbations.
- MSOA garden data are on 2011 MSOAs; they were moved to 2021 MSOAs by the share of each 2011 MSOA's small-user postcodes (NSPL, live in April 2020) in each 2021 MSOA, applied to both address counts.
- Postcodes approximate addresses for the garden weights; 6,399 of 7,264 2021 MSOAs take at least 90% of their apportioned addresses from 2011 MSOAs wholly inside them.
- The 2011 MSOA postcode assignment comes from the NSPL August 2024 2011-Census edition and the 2021 assignment from the August 2026 NSPL, joined on the 7-character postcode; all 1,467,210 postcodes matched.
- MSOA X_* are standardised across all 7,264 MSOAs; the LA X_* exclude City of London and the Isles of Scilly, as in B3.
- MSOA correlations exclude the City of London and Isles of Scilly MSOAs, in line with the LA exclusions.
- The ONS homeworking file was read from the pilot raw folder and processed with the pilot's code, so the London values match the pilot exactly.

## Failures

None. No source was blocked; all Nomis and ONS API calls succeeded (one connection reset on the first Nomis call,
which succeeded on rerun).
