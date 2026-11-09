# B2 Census 2021 migration (address one year before the census)

Reference period: usual address on 21 March 2020 compared with usual address on Census Day, 21 March 2021. England and Wales only. Data assembly only; no regressions were run.

Scripts (in `extension/scripts/`):
- `b2_download_census_migration.py`: Nomis bulk zips (ODMG, ODST, TS019, TS007, TS007A) and ONS census-observations API pulls (migrant indicator by age).
- `b2_lookup_msoa_lad23.py`: MSOA (2021) to LAD (April 2023) best-fit lookup from the ONS Open Geography Portal.
- `b2_build_census_migration.py`: builds the tidy long files.
- `b2_validate_census_migration.py`: totals and identity checks; writes `data/clean/b2_validation_summary.csv`.

Raw files: `~/research-data/london-variety-extension/raw/census2021_migration/`.

## 1. Tables found

### Public (Open Government Licence; downloaded)
Source: Nomis Census 2021 origin-destination bulk page, https://www.nomisweb.co.uk/sources/census_2021_od, and the ONS dataset specification spreadsheet (saved as `raw/census2021_migration/census2021_od_dataset_specifications.xlsx`).

| Table | Content | Geographies (public) | Age detail |
|---|---|---|---|
| ODMG01EW | Origin and destination of migrants (basic flow) | MSOA, LTLA, UTLA, region | none (all aged 1+) |
| ODMG01EW_NON_UK | International migrants by country one year ago (60 categories) | LTLA, UTLA, region | none |
| ODMG02EW | Origin and destination of migrants by age | LTLA, UTLA | RESIDENT_AGE_23B (22 bands from age 1) |
| ODMG02EW_NON_UK | International migrants by age, country one year ago (10 categories) | LTLA, UTLA | 22 bands |
| ODMG10EW | Origin and destination of migrants by age and sex | LTLA, UTLA | RESIDENT_AGE_7F (7 bands) |
| ODST01EW | Moved from a student term-time or boarding school address | MSOA, LTLA, UTLA, region | none |
| ODST02EW | As ODST01EW, by age | LTLA, UTLA | RESIDENT_AGE_5E (5 bands) |
| ODMG03/04/07/09EW (and _NON_UK) | By ethnic group, NS-SEC, tenure, general health | LTLA, UTLA | not downloaded (no age) |
| TS019 | Migrant indicator (same address; student term-time address; within UK; outside UK) | OA to country | none |
| TS007 / TS007A | Age by single year / five-year bands (population checks) | MSOA to country | single year / 5-year |
| ONS "Create a custom dataset" (api.beta.ons.gov.uk census-observations) | Migrant indicator (5 categories) by any resident age classification | OA to country, subject to the API's disclosure rules | single year (101 or 86 categories), 23 bands, etc. |

The custom-dataset API gives inflows only (migrant indicator of the current resident). It has no origin dimension, so it cannot give outflows or same-area moves.

### Safeguarded (need an application)
Route: UK Data Service, safeguarded data under the UK Data Service End User Licence (register with UKDS, agree the licence, then download origin-destination flow data via the UKDS flow-data service WICID, https://wicid.ukdataservice.ac.uk/). Commercial use needs a licence and fee. ONS says UKDS published the safeguarded OD data on 2 November 2023.
Migration and student tables listed as safeguarded in the ONS specification:
- ODMG01EW: Origin and destination of migrants, OA to OA.
- ODMG01EW_NON_UK: International migrants by country (60 categories), MSOA.
- ODMG05EW_LTLA: Migrants by economic activity, LTLA/UTLA.
- ODMG06EW and ODMG06EW_NON_UK: Migrants by industry, MSOA.
- **ODMG10EW: Origin and destination of migrants by age and sex, MSOA to MSOA (RESIDENT_AGE_7F by sex).** This is the table that would give MSOA outflows by age (7 bands).
- ODMG10EW_NON_UK: International migrants by age and sex, country (60 categories), LTLA/UTLA.
- ODMG11EW: Migrants by passport held and sex, LTLA/UTLA.
- ODMG14EW: Migrants by NS-SEC by sex, MSOA.
- ODST01EW: Student-address movers, OA to OA.
- ODST05EW: Student-address movers by economic activity, LTLA/UTLA.
- ODST07EW: Student-address movers by age, sex and student status, MSOA (RESIDENT_AGE_5E).

### Secure (accredited researchers only)
Route: ONS Integrated Data Service (formerly the Secure Research Service). It needs Accredited Researcher status under the Digital Economy Act and an accredited project. Access is through the SafePod Network or Assured Organisational Connectivity. Outputs are checked for disclosure before release. Details are at https://www.ons.gov.uk/aboutus/whatwedo/statistics/requestingstatistics/secureresearchservice/becomeanaccreditedresearcher.
Migration and student tables listed as secure:
- **ODMG02EW: Origin and destination of migrants by age, MSOA to MSOA (22 bands).** This is the full MSOA by-age matrix with inflows and outflows.
- ODMG02EW_NON_UK: International migrants by age (60 countries), MSOA.
- ODMG01EW_NON_UK (OA), ODMG11EW_NON_UK (OA), ODMG12EW (disability by residence type, OA), ODMG13EW (economic activity by age (7F) and sex, OA), ODMG15EW (general health by age (6F), OA), ODMG16EW and _NON_UK (industry by sex, OA), ODMG17EW and _NON_UK (occupation by sex, OA), ODMG18EW and _NON_UK (ethnic group by sex, OA), ODMG19EW_NON_UK (intended length of stay by age, OA), ODST08EW, ODST09EW and ODST10EW (OA).

## 2. Files produced

| File | Rows | Geography | Age detail | Content |
|---|---|---|---|---|
| `extension/data/clean/b2_la_migration_by_age.csv` | 164,197 | LAD 2021 (331, Census LTLA) and LAD 2023 (318) | 22 bands (ODMG02EW) plus "All ages 1+" (ODMG01EW) | inflows split same LA / other E&W LA / Scotland / NI / outside UK; outflows to other E&W LAs; net |
| `extension/data/clean/b2_la_inflows_single_year.csv` | 323,500 | LAD 2021 (330) and LAD 2023 (317); Isles of Scilly blocked by the API | single year 1 to 99, then 100+ | inflows only: from UK (split student-address / other), from outside UK |
| `extension/data/clean/b2_msoa_migration_all_ages.csv` | 79,904 | MSOA 2021 (7,264) | all ages 1+ only (ODMG01EW) | inflows split same MSOA / other E&W MSOA / Scotland / NI / outside UK; outflows to other E&W MSOAs; net |
| `~/research-data/london-variety-extension/clean/b2_msoa_inflows_by_age.csv` (68 MB) | 792,410 | MSOA 2021 (7,205 of 7,264) | 22 bands (7,188 MSOAs from the 23-band API query; 15 from the single-year query collapsed to 22 bands; 2 in 8 bands) | inflows only, as in the LA single-year file |
| `~/research-data/london-variety-extension/clean/b2_msoa_inflows_single_year.csv.gz` (26 MB gzipped) | 3,042,150 | MSOA 2021 (7,158; 106 blocked) | single year 1 to 84, then 85+ | inflows only |
| `extension/data/clean/b2_lookup_msoa21_lad21_lad23.csv` | 7,264 | MSOA 2021 to LAD 2021 and LAD 2023 | | lookup |
| `extension/data/clean/b2_msoa_no_age_data.csv` | 59 | MSOAs with no by-age migration data from the API | | list |
| `extension/data/clean/b2_validation_summary.csv` | 26 | | | validation checks |

LA vintage: Census 2021 LTLAs use the April 2021 LAD codes (331 in England and Wales). The 2023 file (318 LADs, as used by the pilot) aggregates them. Cumberland (E06000063), Westmorland and Furness (E06000064), North Yorkshire (E06000065) and Somerset (E06000066) replace 17 districts; nothing else changed. In the 2023 file, flows between merged districts count as same-area moves. So `in_same_area` is 11,497 higher than in the 2021 file, and `in_other_ew` and `out_other_ew` are lower by the same amount.

## 3. Data dictionary (tidy long files)

Common columns:
- `geo_level`: `lad21`, `lad23` or `msoa21`.
- `geo_code`, `geo_name`: area code and name (LA names as in the Census 2021 release).
- `lad21_code`, `lad23_code`: the MSOA's parent LAD (best fit; MSOAs nest within LADs).
- `age_band`: `1-2`, `3-4`, `5-7`, `8-9`, `10-14`, `15`, `16-17`, `18-19`, `20-24`, then five-year bands to `80-84`, then `85+`, or `All ages 1+`. In the single-year files, `age` is the single year (`85+` for MSOA, `100+` for LA).
- `age_classification` (MSOA by-age file): the API classification behind each row.
- `measure`: see below.
- `count`: persons, as published (perturbed).
- `denom_pop`: Census 2021 usual residents aged 1 and over, same age band, same area, on Census Day. It is the sum of all migrant-indicator categories, or of all origins in the OD table. Under-1s are excluded because they have no address one year ago, so the `1-2` band means ages 1 to 2.
- `rate_per_1000` = 1000 x count / denom_pop. Outflows use the same census-day denominator. A population-at-risk alternative (residents a year earlier) is not observable, because emigrants and deaths are unknown.
- `source`: table used.

Measures in the OD-based files (`b2_la_migration_by_age`, `b2_msoa_migration_all_ages`):
- `in_same_area`: moved within the same LA or MSOA (address one year ago in the same area).
- `in_other_ew`: address one year ago in another LA or MSOA in England and Wales.
- `in_scotland`, `in_ni`: address one year ago in Scotland or Northern Ireland.
- `in_elsewhere_uk` = in_other_ew + in_scotland + in_ni.
- `in_from_uk` = in_same_area + in_elsewhere_uk.
- `in_outside_uk`: address one year ago outside the UK.
- `in_total` = in_from_uk + in_outside_uk (all migrants now resident in the area).
- `out_same_area`: identical to in_same_area (the same moves, seen from the origin side).
- `out_other_ew`: people now resident in another E&W LA or MSOA whose address one year ago was in this area.
- `net_other_ew` = in_other_ew - out_other_ew.
- Not observed and not included: outflows to Scotland, Northern Ireland and abroad. The E&W census enumerates only E&W residents, and Scotland's 2022 census and NI flows are not linked in.

Measures in the API-based files (inflows only, no origin geography):
- `in_uk_nonstudent`: TS019 "Migrant from within the UK". It includes moves within the same area, which public data cannot separate by age at MSOA.
- `in_student_termtime`: address one year ago was a student term-time or boarding-school address in the UK.
- `in_from_uk` = in_uk_nonstudent + in_student_termtime. This matches the OD tables, which count student-address movers with their UK origin.
- `in_outside_uk`, `in_total`: as above.

Finest public age bands:
- LA, origin-destination (in and out): 22 bands (ODMG02EW). ODMG10EW has 7 bands by sex (raw only).
- LA, inflows: single year (API).
- MSOA, origin-destination: all ages 1+ only (ODMG01EW).
- MSOA, inflows: 22 bands for 7,205 MSOAs, single year for 7,158 MSOAs (API).
- MSOA outflows by age need the safeguarded ODMG10EW (7 bands, MSOA) or the secure ODMG02EW (22 bands, MSOA).

## 4. Validation (from `b2_validation_summary.csv`)

- Usual residents aged 1+, summed over areas: LA 58,990,370; MSOA 58,990,007; TS019 England and Wales 58,990,218. All differences are under 0.001%.
- Migrants (in_total), summed: LA 6,493,859; MSOA 6,493,460; TS019 6,493,688 (student-address 349,072 + within UK 5,599,520 + outside UK 545,096). Differences are under 0.004%.
- Outside UK: LA 545,090; MSOA 545,030; TS019 545,096.
- Summed in_other_ew equals summed out_other_ew exactly for LA (both vintages, all ages and 22 bands) and for MSOA.
- The 22 bands summed (ODMG02EW) are 314 above ODMG01EW all ages (0.005%), which is perturbation.
- LAD 2023 and LAD 2021 totals are identical.
- MSOA all ages summed to LAD 2021, compared with the LA file (in_total): median absolute difference 0.12%, maximum 1.56%.
- MSOA by age (API), summed: 6,462,632 migrants, 0.48% below TS019 because 59 MSOAs are missing. Rates by band agree with the LA ODMG02EW rates to within 1 per 1,000 (20-24: LA 328.6, MSOA 329.6; 25-29: 257.9 and 258.4).
- MSOA single year collapsed, against the 22-band query for the same MSOAs: +0.12% (more cells perturbed).
- LA single year (API), summed: 6,493,366 migrants (-0.005%).

## 5. Caveats

- Pandemic timing: the year to 21 March 2021 covers the first lockdowns, travel restrictions and fewer international arrivals. The Brexit transition ended on 31 December 2020. ONS advises caution in treating these flows as typical. Respondents were told: "If the coronavirus pandemic affected your usual address one year ago, select where you were living before your circumstances changed."
- Students are counted at their term-time address on Census Day. Many lived at the parental home during 2020-21 teaching, so student flows, and inflows at 18-24 in university MSOAs, are atypical. Movers from a student term-time address count as within-UK migrants in the OD tables, and appear separately as `in_student_termtime` in the API files.
- Statistical disclosure control means targeted record swapping and cell key perturbation. Small cells are noisy, tables do not add exactly to each other, and zeros and small counts at MSOA by single year are unreliable. ONS advises taking totals from tables with fewer cells at higher geographies.
- The ONS custom-dataset API also blocks whole areas when a query fails its disclosure rules. That leaves 59 MSOAs with no by-age data, 106 with no single-year data, and Isles of Scilly with no single-year LA data. The blocked MSOAs are not random. Their all-ages migration rate (median 72 per 1,000) is below the national MSOA median (90), and they cluster in places such as South Tyneside and Barnsley.
- Under-1s have no migration status in Census 2021; ONS did not impute it as in 2011.
- Outflows abroad, to Scotland and to NI are not observed.
- Each person is counted once, comparing the address a year ago with the census address. Intermediate moves are missed, as are people who moved in and later left or died before Census Day.

## 6. Failures and blocks

- The UK Data Service WICID flow-data site (https://wicid.ukdataservice.ac.uk/flowdata/cider/wicid/downloads.php) timed out from this machine, so the safeguarded list comes from the ONS dataset specification spreadsheet, not the UKDS catalogue. Manual step: log in to UKDS, open WICID and confirm the safeguarded 2021 migration tables (in particular ODMG10EW at MSOA).
- https://www.ons.gov.uk/census/aboutcensus/censusproducts/origindestinationdata returns 404. The current page is https://www.ons.gov.uk/census/aboutcensus/censusproducts/origindestinationflowdata.
- The API returns 403 "Too many rows" above about 50,000 observations, so queries were chunked. It returns 400 when every area in a request is blocked (resident_age_6a for the last 72 MSOAs).
- No CAPTCHA or bot check was met.

## 7. Judgement calls (one line each)

- The denominator is Census-day usual residents aged 1+ in the same band and area, from the same table as the counts, so rates are internally consistent.
- Under-1s are dropped from all denominators because they cannot be migrants in Census 2021.
- MSOA by-age inflows use the API's 23-band classification with "65" and "66-69" merged, so the bands match ODMG02EW's 22 bands exactly.
- MSOAs blocked at 23 bands use single-year data collapsed to the same 22 bands (15 MSOAs), then coarser native bands (2 MSOAs, 8 bands); each MSOA uses one classification.
- The 59 MSOAs with no by-age data are left out of the by-age file rather than imputed; they remain in the all-ages OD file.
- Student-address movers are counted as UK inflows (`in_from_uk`), matching ODMG, and also shown separately.
- Origins in Scotland (intermediate zones or council areas) and NI (LGDs) are grouped as `in_scotland` and `in_ni`, since their geographies differ from E&W.
- "All ages 1+" rows come from ODMG01EW, not from summing bands, following ONS advice to take totals from tables with fewer cells.
- LAD 2023 figures sum LAD 2021 OD flows after recoding origins and destinations, so moves between merged districts become same-area moves.
- MSOA to LAD 2021 comes from MSOA names, which ONS takes from the LAD in force at the census. Four name mismatches (Hull, Herefordshire, Bristol, Rhondda Cynon Taf) took the unchanged 2023 code.
- Outflow rates use the same census-day denominator, because an at-risk population a year earlier cannot be built while emigration is unobserved.
- The 22-band and single-year MSOA files are in the external clean folder because they exceed 50 MB uncompressed; the single-year file is gzipped.
- ODST01EW/02EW (student-address movers) and ODMG10EW (age by sex) were downloaded but not reshaped, since ODMG02EW and the API give finer age detail.
- ODMG03/04/07/09EW (ethnic group, NS-SEC, tenure, health; no age) were not downloaded, because the task asks for age.
- Isles of Scilly is missing from the LA single-year file (API block) but present in the 22-band LA file.
