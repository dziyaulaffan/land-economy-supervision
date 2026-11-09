# S3 COVID-19 case rates and S4 census one-year-ago inflows (2001, 2011, 2021)

Data assembly only. No regressions were run. England and Wales only.

Scripts (in `extension/scripts/`):
- `s3_download_cases.py`: UKHSA dashboard API pulls (LTLA and England), and ONS mid-2020 populations (Nomis). Run with no argument, then `nation`, then `population`.
- `s3_build_case_rates.py`: builds the S3 files and checks.
- `s4_download_census.py`: Nomis API pulls for the 2011 and 2001 tables, paged at 25,000 rows.
- `s4_download_lookups.py`: ONS Open Geography Portal lookups.
- `s4_build_census_inflows.py`: builds the S4 files, lookups and checks.

Raw files are in `~/research-data/london-variety-extension/raw/`: `covid_cases\ukhsa\` (one JSON per LTLA and year), `covid_cases\archive\cases.zip`, `nomis\s4\`, `nomis\mye_population_mid2020_la2023.csv` and `ons_geography\s4_lookups\`.

---

## S3 COVID-19 cases by specimen date

### Sources
- **England.** UKHSA data dashboard API, metric `COVID-19_cases_casesByDay`. This is cases by specimen date for each Lower Tier Local Authority, 2020 and 2021. Base URL: https://api.ukhsa-dashboard.data.gov.uk/themes/infectious_disease/sub_themes/respiratory/topics/COVID-19/geography_types/Lower%20Tier%20Local%20Authority/geographies/{name}/metrics/COVID-19_cases_casesByDay. The England national series from the same API is used for checks.
- **Wales.** The UKHSA dashboard API carries no Welsh areas. The Public Health Wales (PHW) page https://phw.nhs.wales/data/wales-rapid-covid-19-surveillance-dashboard/ offers only an interactive Tableau dashboard, with no file download. The old PHW workbook URL (www2.nphs.wales.nhs.uk ... Rapid COVID-19 surveillance data.xlsx) now returns an HTML page. Tableau CSV export URLs returned 404.
  - So the Welsh series come from the UKHSA archive of the former coronavirus dashboard: https://archive.ukhsa-dashboard.data.gov.uk/coronavirus-dashboard/cases.zip (389 MB). The file used is `Cases/ltla_newCasesBySpecimenDate.csv`. Its Welsh LTLA figures are the PHW figures that the old dashboard republished.
  - Manual route to the original data: open the PHW Tableau dashboard (https://public.tableau.com/app/profile/public.health.wales.health.protection/viz/RapidCOVID-19virology-Public/Headlinesummary) and use Download > Data on the local-authority sheet.
- **Population.** ONS mid-2020 population estimates for April 2023 LADs, from Nomis NM_2002_1 (geography TYPE424). Nomis now serves the series rebased to Census 2021.
- **Geography.** `b4_ltla20_to_lad23.csv`. The API reports 2020 LTLAs for Cumbria, North Yorkshire and Somerset; their cases are summed into the 2023 unitaries. It reports North and West Northamptonshire (2021) and Buckinghamshire directly. Hackney with the City of London, and Cornwall with the Isles of Scilly, are reported only as combined areas.

### Files
| File | Rows | Content |
|---|---|---|
| `extension/data/clean/s3_case_rates_la2023_weekly.csv` | 32,754 (318 LADs x 103 weeks) | la_code, la_name, week_ending (Sunday; Monday to Sunday weeks; complete weeks from 12 Jan 2020 to 26 Dec 2021), cases, population, rate_per_100k, source, imputed_days, combined_with |
| `extension/data/clean/s3_case_rates_la2023_year_to_june2021.csv` | 318 | Mean weekly rate per 100,000, 1 Jul 2020 to 30 Jun 2021; quarterly means for 2020Q3, 2020Q4, 2021Q1 and 2021Q2; cases over the year; imputed_days |
| `extension/data/clean/s3_validation.csv` | 20 | National totals compared |
| `extension/data/clean/s3_wales_oct2020_rebuild.csv` | 22 | October 2020 Welsh rebuild, by LA |

Mean weekly rate = 7 x cases in the period / days in the period / population x 100,000. It is computed from daily data, so it does not depend on where the week boundaries fall.

### Wales, October 2020
Every Welsh LTLA series in the archive is missing 1 to 31 October 2020. The other LTLA files in the archive have the same gap, and the cumulative count file holds only 11 of the 22 Welsh LAs.

For each LA, the October total is the cumulative count on 1 November 2020, minus all non-October daily cases up to that date. Where the cumulative count is missing, the cumulative rate per 100,000 is multiplied by a population implied from September 2020; for the 11 LAs that have both, the two methods agree exactly. The total is then spread over the days of October using the Wales national daily profile by specimen date.

These 31 days are flagged in `imputed_days`. The weekly figures for those weeks are estimates; the monthly total rests on published cumulative figures.

### Validation (`s3_validation.csv`)
| | 2020 | 2021 | Jul 2020 to Jun 2021 |
|---|---|---|---|
| England, sum of LAs | 2,301,483 | 9,394,287 | 4,038,815 |
| England, national series (API) | 2,327,697 (LAs -1.1%) | 9,461,198 (-0.7%) | 4,071,854 (-0.8%) |
| Wales, sum of LAs | 149,016 | 487,380 | 191,532 |
| Wales, national series (archive) | 156,512 (LAs -4.8%) | 515,112 (-5.4%) | 203,312 (-5.8%) |

- National totals include cases that cannot be placed in an LA. For Wales this also covers cases whose residence is outside Wales or unknown.
- Welsh LAs are 5.2% below the national figure in September 2020, 8.7% below in October and 4.9% below in November. So the October rebuild may understate by about 3 to 4% (roughly 1,000 cases across Wales), or October had more unallocated cases. I cannot tell which.
- The England API national series matches the archived England national series to within 35 cases a year.
- Median mean weekly rate, July 2020 to June 2021: England 131, Wales 125 per 100,000. Range: Torridge 33 to Blackburn with Darwen 286.

### Testing-regime caveats
- **Spring 2020.** Until mid-April 2020, testing in England was mostly Pillar 1: hospital patients and, later, health and care workers. Community (Pillar 2) testing for symptomatic people opened in stages, reaching everyone with symptoms on 18 May 2020. Cases from March to May 2020 are therefore a small and changing fraction of infections. They are not comparable with later months or across areas with different hospital loads. Wales followed a similar sequence.
- **September 2020.** Capacity was short in England in mid-September 2020, and some areas had test sites rationed.
- **Lateral flow tests.** Lateral flow device (LFD) testing of people without symptoms grew from December 2020, with twice-weekly tests offered to everyone in England from 9 April 2021. England counts LFD-positive cases. From 30 March 2021, an LFD positive followed by a negative confirmatory PCR within three days is removed. So case rates in 2021Q2 partly reflect the volume of asymptomatic testing.
- **Wales definitions.** PHW case definitions, the inclusion of LFD results and the de-duplication rules were set separately from England, and the dates of changes differ. Treat England-Wales level differences with care, especially in 2021.
- **Reinfections.** The current UKHSA API counts infection episodes, including reinfections (90-day rule), applied back in time. Before Omicron (December 2021), reinfections were a small share. The archived Welsh series is the old dashboard's final version.
- **Residence.** Cases are placed by residential postcode. Students were counted where they were tested in autumn 2020, which raises rates in university towns.
- **Denominators.** These are the rebased mid-2020 estimates, so rates differ slightly from the rates UKHSA published, which used the original mid-2020 estimates.

---

## S4 Census one-year-ago migrants by age at MSOA

### Definition
All three censuses use **all movers**, matching B2's `in_total`. This means usual residents on Census Day whose usual address one year before was different. It includes moves within the same MSOA and arrivals from abroad.

All movers is residents minus those at the same address, so it can be summed from smaller areas and does not depend on the area level. Every census provides it, so the alternative "inflow from outside the MSOA" definition was not needed for any year.

Remaining differences:
- **2001** includes people with "no usual address one year ago". There were 420,110 in England and Wales: 6.6% of movers overall, 6.1% at 20-24 and 7.2% at 25-34. The harmonised file therefore also gives `migrants_excl_nua` and `rate_excl_nua_per_1000`. For 2011 and 2021 these equal `migrants` and `rate_per_1000`, because neither census has that category.
- **2021** covers ages 1 and over, because under-1s have no migration status. So its 0-4 band is ages 1 to 4, and "All ages" means ages 1+. In 2001 and 2011, under-1s are included with an assigned status.
- **2021** counts are perturbed by cell-key perturbation; 2001 counts were randomly adjusted; 2011 counts are unadjusted (record swapping only).

### Census 2011
- Table: **UKMIG001 "Migration by sex by age"** (Nomis NM_1280_1), 2011 MSOA (7,201), both sexes.
- Categories:
  - lived at same address
  - lived elsewhere, within same area (here, a move within the MSOA)
  - Inflow: Total, which equals inflow from the associated area + rest of the UK + outside the UK (checked exactly)
- migrants = within-area + inflow total; residents = all three categories.
- Age bands: 0-4, 5-15, 16-19, 20-24, 25-34, 35-49, 50-64, 65-74, 75+. The Nomis label "Age 65 to 64" is a typo for 65-74.
- This is the finest public MSOA table with this definition.
  - The WICID/Nomis origin-destination tables (WU01EW at MSOA; Nomis MU01BUK/MM01CUK at LA) give flows by age as origin-destination pairs. They would add nothing to an inflow count.
  - The table was not downloaded.
- Output: `extension/data/clean/s4_census2011_msoa_inflows_by_age.csv` (72,010 rows). Columns: msoa11cd, age_band, migrants, residents, rate_per_1000, moved_within_msoa, inflow_from_outside_msoa, inflow_from_outside_uk, source.

### Census 2001
**No public table gives migration by detailed age at MSOA or at an area that nests in MSOAs.**

What exists (Nomis):
| Table | Geography | Age | Migration detail |
|---|---|---|---|
| ST008 "Resident type and sex and age by migration" | 2003 ST wards (8,800), districts, regions | 23 bands (under 1, 1-3, 4, 5-9, 10-14, 15, 16-17, 18-19, then five-year bands to 85-89, 90+) | full: same address, within area, no usual address, inflow by origin |
| CS008 "Resident type and age by migration" | output areas, CAS wards | 0-9, 10-19, 20-64, 65+ only | stayers lumped with moves within the area, so all movers cannot be derived |
| KS024 "Migration" | output areas and above | none | all people, migrants, no usual address, within area, from UK, from abroad |
| UV023 "Migration" | output areas and above (MSOA listed) | none | as KS024 |
| UV004 "Age" | output areas, MSOA | single year to 74, then five-year bands | none |
| TT033 theme table | districts | 14 bands | full |

2001 ST wards do not nest in 2001 MSOAs. 2001 output areas nest in CAS wards. ST wards are the CAS wards, except that 50 small CAS wards are merged into neighbours.

The 2001 MSOA by-age file is therefore an **estimate** (`estimated = True`):
- For MSOA m and band b, estimated migrants = residents(m, b) x mean rate(m, b), then scaled within the MSOA so the bands sum to the published all-age migrant count.
  - residents(m, b) comes from UV004 at 2001 MSOA (published).
  - The mean rate is the all-mover rate from ST008, averaged over the ST wards that overlap the MSOA. The weights are the 2001 OA populations (KS024) in each overlap. Ward of an OA = first six characters of its 2001 code.
  - The published all-age count is KS024 "People who are migrants", summed over the MSOA's output areas.
- The 148 OAs (44,961 people) in the 50 merged CAS wards use their district's ST008 rate.
- The same is done excluding "no usual address" (`migrants_excl_no_usual_address`).
- "All ages" rows are published values (`estimated = False`).

Output: `extension/data/clean/s4_census2001_msoa_inflows_by_age.csv` (172,656 rows; 7,194 MSOAs x 24 rows). Columns: msoa01cd, age_band (ST008 bands), migrants, migrants_excl_no_usual_address, residents, rate_per_1000, estimated, source, share_pop_district_rate, rake_factor.

How good the estimate is (it carries real uncertainty):
- National totals by band match ST008 England and Wales to within 0.4% for ages 5 to 79 (20-24: 361.8 per 1,000 estimated against 360.5; 25-29: 277.6 against 276.6). They are within 1.4% for 15 to 19, and are lower by 3.8% at 85-89 and 6.6% at 90+.
- The scaling factor has median 1.00 and 5th to 95th percentile 0.85 to 1.14; the extremes are 0.58 and 2.03. Large factors mark MSOAs whose wards' age profile of moving does not match their own.
- Out-of-sample test on 2011, where true MSOA values exist. The same method was run with **district** rates, a harder test than ward rates. Correlation between estimated and true MSOA rates: 0.90 at 20-24 and 0.90 at 25-34. Median absolute error: 32.6 per 1,000 at 20-24 (true median 253) and 17.4 per 1,000 at 25-34 (true median 212).
  - Ward rates should do better, but could not be tested.
  - Treat 2001 band-level MSOA rates as model estimates. Differences of a few tens per 1,000 between nearby MSOAs are within the error.

**Route to measured 2001 MSOA data by age:**
- The 2001 Special Migration Statistics on the UK Data Service flow-data service, WICID (https://wicid.ukdataservice.ac.uk/). Level 1 covers wards and districts with age; Level 2 covers output areas with few variables. Access needs a UKDS login, and some levels need a licence. Neither gives MSOA by detailed age directly, but Level 2 OA flows could be aggregated if their age detail suffices.
- A commissioned table from ONS (census customer services), if ONS still runs 2001 commissions.
- WICID timed out from this machine in B2, so the SMS variable lists were not checked.

### Lookups and harmonisation
- ONS Open Geography Portal services used:
  - OA01_LSOA01_MSOA01_EW_LU
  - OA01_OA11_LAD11_EW_LU (change indicator U/S/M/X)
  - MSOA01_MSOA11_LAD11_EW_LU
  - OA11_LSOA11_MSOA11_LAD11_EW_LU
  - OA11_OA21_LAD22_EW_LU_Exact_fit_V3 (CHNGIND)
  - "MSOA (2011) to MSOA (2021) to LAD (2022) Lookup for EW v2" (exact, CHNGIND: U 7,080, S 159, M 38, X 9)
  - OA_LSOA_MSOA_EW_DEC_2021_LU_v3
  - The service named MSOA11_MSOA21_LAD22_EW_LU_v2 is the best-fit version. It was saved as `_bestfit` and not used.
- Method (both steps):
  - Each old MSOA is shared out to new MSOAs in proportion to the old-census population of its OAs that fall in each new MSOA. 2001 OA population comes from KS024; 2011 OA population from KS101EW.
  - An old OA split between several new OAs is divided by the new-census populations of those OAs. 2011 OA population comes from KS101EW; 2021 OA population from TS007A.
  - Where the official MSOA lookup marks an MSOA unchanged (U) or merged (M), its official one-to-one target is used. The OA-based weights put no share outside that target for any U or M MSOA.
  - The same shares apply to every age band.
  - 2001 to 2021 multiplies the 2001-2011 and 2011-2021 shares.
- Lookup outputs (in `extension/data/clean/`):
  - `s4_lookup_msoa01_msoa11.csv`: 7,231 rows; 94 MSOA01s apportioned.
  - `s4_lookup_msoa11_msoa21.csv`: 7,287 rows; 83 MSOA11s apportioned.
  - `s4_lookup_msoa01_msoa21.csv`: 7,322 rows.
  - Columns: codes, share, exact.

### Harmonised file
`extension/data/clean/s4_msoa_inflows_on_msoa21.csv` (239,102 rows, 23 MB).
- Columns: msoa21cd, lad23cd, census_year, age_band, migrants, residents, rate_per_1000, migrants_excl_nua, rate_excl_nua_per_1000, estimated, share_apportioned, definition.
- Common bands are the 2011 bands: 0-4, 5-15, 16-19, 20-24, 25-34, 35-49, 50-64, 65-74, 75+. The file also has "All ages" and an aggregate "20-34" (20-24 plus 25-34).
- **20-29 is not available in 2011**, so the closest common bands are 20-24 and 20-34. **25-34 is common to all three censuses.**
- Coverage:
  - 2001 and 2011: all 7,264 MSOA21s.
  - 2021 bands: 7,203 MSOAs. The 59 MSOAs blocked by the ONS API are missing, and 2 MSOAs with only 8 bands are dropped from the bands.
  - 2021 "All ages": all 7,264, from ODMG01EW.
- `share_apportioned` is the share of the row's residents that came through a split (S/X) MSOA. Rows with any such share: 2001, 295 MSOA21s; 2011, 165; 2021, none.
- Rates for England and Wales as a whole:
  - 20-24: 2001 361.8, 2011 352.8, 2021 329.6 per 1,000. Excluding "no usual address", 2001 is 339.9.
  - 25-34: 2001 226.5 (210.1 excluding "no usual address"), 2011 239.0, 2021 221.1.
  - All ages: 2001 121.8, 2011 122.0, 2021 110.1 (ages 1+).
- Correlation of MSOA21 rates at 25-34 across censuses: 2001-2011 0.82, 2011-2021 0.82, 2001-2021 0.77.

### Validation (`extension/data/clean/s4_validation.csv`)
- **2011.** Summed over MSOAs: residents 56,075,912 and migrants 6,841,130. These equal the published UKMIG008 England + Wales figures exactly, and residents equal KS101EW.
- **2001.**
  - Residents 52,041,916 equal KS024 (and the published Census 2001 England and Wales population).
  - Migrants summed over OAs are 6,338,051 against the published England and Wales figure of 6,338,041 (+0.0002%, from OA-level adjustment).
  - Excluding "no usual address": 5,917,165 against 5,917,931.
  - UV004 MSOA residents summed: 52,041,852 (-0.0001%).
- **2021.** All-ages migrants 6,493,460 against TS019's 6,493,688 (-0.004%), as in B2.
- **Mapping.** Totals by year and band are preserved after moving to 2021 MSOAs (differences under 0.001 persons).

---

## Judgement calls (one line each)
- England case series come from the live UKHSA API rather than the archive, because the archive's English LTLA files have imputed or recoded October 2020 values and mixed geography vintages.
- Welsh case series come from the archived coronavirus dashboard, because the UKHSA API has no Welsh areas and PHW publishes no file download.
- Welsh October 2020 daily cases are rebuilt from cumulative figures and spread with the Wales national daily profile, and are flagged in `imputed_days`.
- Where the cumulative count is missing for a Welsh LA, the cumulative rate is converted with the population implied by September 2020 counts and rates.
- Combined UKHSA areas (Hackney with City of London; Cornwall with Isles of Scilly) are split by mid-2020 population, so both members get the same rate; `combined_with` flags them.
- Cases are cases by specimen date (`casesByDay`), as the UKHSA API serves them; that series counts episodes including reinfections.
- Denominators are ONS mid-2020 estimates on 2023 LADs as served by Nomis now (rebased to Census 2021), not the b4 file's 2018-based projections, which are placeholders (1) for Wales.
- Weeks run Monday to Sunday, labelled by the Sunday; only weeks wholly inside 2020-2021 are kept (12 Jan 2020 to 26 Dec 2021).
- Days before an LA's first reported case are set to zero.
- Year and quarter means are computed from daily counts (7 x cases / days), not by averaging weekly rates.
- The 2023 LAD rate for merged authorities sums the predecessors' cases and divides by the 2023 LAD's mid-2020 population.
- The census migration definition is all movers in every year, because each census supports it; no fallback to inflows from outside the MSOA was needed.
- For 2011, the migrant count is UKMIG001 "within same area" plus "Inflow: Total"; residents add "same address".
- For 2001, migrants include "no usual address one year ago" in the main columns, as in KS024; a version without them is given alongside.
- The 2001 MSOA by-age figures are a model estimate, because no public table gives detailed age at MSOA or at an area that nests in MSOAs; all-age figures are published values.
- The 2001 estimator uses ST ward rates weighted by the OA population of each ward-MSOA overlap; it uses district rates for the 50 CAS wards merged in ST wards.
- The 2001 estimator scales bands to the published MSOA all-age migrant total (KS024 summed over OAs).
- The 2001 ward-to-MSOA mixing uses all-age OA population weights, not band-specific ones, because OA age data would need about 14 million cells.
- The 2001 estimator was tested on 2011 truth using district rates only, a harder test than the ward rates used for 2001.
- Six Nomis district codes recoded in 2013-14 (Gateshead, Northumberland and four Hertfordshire districts) are mapped from their LAD11 codes.
- Harmonised bands follow 2011, the coarsest census: 0-4, 5-15, 16-19, 20-24, 25-34, 35-49, 50-64, 65-74, 75+, plus "20-34" and "All ages".
- 20-24 and 20-34 stand in for 20-29, which 2011 does not publish.
- The 2021 0-4 band is ages 1-4, and 2021 "All ages" is ages 1+.
- 2021 "All ages" comes from ODMG01EW (all 7,264 MSOAs), so it is not the sum of the 2021 bands, which miss 59 blocked MSOAs.
- The two 2021 MSOAs with only 8 coarse bands are left out of the 2021 band rows.
- MSOA apportionment uses OA-level chains weighted by old-census OA population; an OA split between new OAs is divided by new-census OA population.
- Where the official MSOA lookup says U or M, the official one-to-one target overrides the OA weights; they agree in every case.
- The same apportionment shares apply to all age bands.
- 2001-to-2021 shares are the product of 2001-2011 and 2011-2021 shares.
- The best-fit MSOA11-MSOA21 service was saved but not used; the exact lookup with change indicators was used.
- Under-1s are kept in 2001 and 2011 because both censuses gave them a migration status; 2021 cannot include them.

## Failures and blocks
- PHW publishes no downloadable local-authority case file; the old workbook URL returns HTML, and Tableau CSV export URLs return 404. The manual step is Tableau's Download > Data.
- The archived coronavirus dashboard has no Welsh LTLA data for October 2020, and its cumulative count file covers only 11 Welsh LAs.
- The ONS lookup service MSOA11_MSOA21_LAD22_EW_LU_v2 is the best-fit version without change indicators; the exact version sits under a different service name, found through the ArcGIS item search.
- An early scan of Nomis geography type codes was too aggressive and the server reset some connections; it was stopped. No CAPTCHA or bot check was met.
- WICID (2001 Special Migration Statistics) was not tried again, after it timed out in B2.
