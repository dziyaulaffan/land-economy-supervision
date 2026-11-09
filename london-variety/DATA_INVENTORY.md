# Data inventory: London consumption-variety pilot

Stage: data gathering and cleaning only. No modelling.
Data pulled 28 October 2026. Every script is in `scripts/`. Run `python scripts/run_all.py` to rebuild from scratch. Each script skips a download when the raw file already exists.

Raw downloads (about 2.5 GB) are kept **outside OneDrive**, in `C:\Users\dziya\research-data\london-variety\raw\`. Only cleaned data, scripts and outputs live in this synced folder. To use another raw location, set the `LONDON_VARIETY_RAW` environment variable.

## Folder layout

| Folder | Contents |
|---|---|
| `C:\Users\dziya\research-data\london-variety\raw\` (outside OneDrive) | Untouched downloads, one subfolder per source. Paths below written `raw/...` are relative to this folder |
| `data/clean/` | Tidy CSVs built by the scripts |
| `scripts/` | Python. `config.py` holds paths, borough lists and the Inner/Outer definitions |
| `outputs/figures/` | Exploratory charts |

## Geography conventions (apply to every dataset)

- **Boroughs.** The analysis panel is the **32 London boroughs, with the City of London excluded**, on April 2023 GSS codes. London boundaries did not change in 2014 to 2025.
- **Why the City is excluded.** It has 8,765 residents and 206 I+R units per 1,000, an extreme value. PIPR publishes no rents for it, and its housing and mobility series are thin.
- **Where the City still appears.** It is dropped from every borough-level clean file and from the amenity split. It still appears as a London counterpart in the migration origin-destination flows, and in `amenity_units_2019_all_las.csv` and the MSOA file.
- **Inner/Outer London.** Two flags are carried:
  - `london_zone` / `inner_ons` is the **main flag**, using the **ONS statistical (ITL) definition**. Inner London is Camden, Hackney, Hammersmith and Fulham, Haringey, Islington, Kensington and Chelsea, Lambeth, Lewisham, Newham, Southwark, Tower Hamlets, Wandsworth and Westminster (13 once the City is excluded). Outer London has 19 boroughs. The charts use this flag.
  - `inner_cfc` is the **secondary flag**, from the **Centre for Cities lookup** (`2024_Inner_London_lookup.xlsx`). It puts Greenwich in Inner London and Haringey in Outer London, and keeps Newham Inner. This is neither the ONS definition nor the London Government Act 1963 definition. It is kept so the CfC briefing can be reproduced.
- **South East and East of England.** These come from the ONS 2023-boundary LA-to-region lookup (`lasregionew2023lookup.xlsx`), which gives 64 South East and 45 East of England authorities.
- **Amenity density.** It is kept both as a continuous variable and as two binary splits. All are computed on the 32 boroughs, in `london_amenity_density_2019.csv`.
  - **Continuous:** `per1k_IR`, `log_per1k_IR`, `z_log_per1k_IR` and `amenity_rank`.
  - **`amenity_group` / `amenity_high`:** the split at the London-wide median, 4.31 I+R units per 1,000. It gives 16 high and 16 low.
  - **`zone_amenity_group` / `amenity_high_within_zone`:** the split at the median within Inner London (7.17) and within Outer London (3.83) separately. Inner gives 6 high and 7 low. Outer gives 9 high and 10 low. With an odd count, the median borough (Southwark in Inner, Hillingdon in Outer) falls in the low group.

> **Collinearity.** The London-wide amenity split nearly reproduces Inner/Outer. 12 of the 13 Inner boroughs are high-amenity (Newham is the exception). Only 4 of the 19 Outer boroughs are high-amenity (Richmond, Kingston, Hounslow and Barnet). Crossing that split with zone would leave one Inner low-amenity borough. The within-zone split exists so the two dimensions can be compared in the charts. Within-zone gaps are small in absolute terms, though: Outer "high" runs from 3.87 (Greenwich) to 7.29 (Richmond) per 1,000.

---

## 1. Internal migration

| | |
|---|---|
| Source | ONS, *Internal migration in England and Wales*, detailed estimates by origin and destination LA, sex and single year of age: https://www.ons.gov.uk/peoplepopulationandcommunity/populationandmigration/populationestimates/datasets/internalmigrationinenglandandwales |
| Repo used | https://github.com/CentreforCities/urban-population-internal-migration (cloned to `raw/cfc_migration/`) |
| Raw files | `raw/ons_internal_migration/detailedestimates{2015..2025}.xlsx` (about 140 MB each), sheet "YYYY on 2023 LAs" |
| Coverage | Years ending 30 June 2015 to 2025, which is mid-2014 to mid-2025. That is 11 annual flows |
| Frequency | Annual (mid-year to mid-year) |
| Geography | 2023 LAs. Counterparts are every LA in England and Wales, plus Scotland and Northern Ireland as country totals |
| Script | `scripts/10_migration.py` |

**What the repo contains, and what it lacks.** The repo ships R scripts, geography lookups and aggregated output workbooks. It does **not** contain the ONS origin-destination data. Its scripts read `detailedestimatesYYYYon2021and2023las.xlsx` from a private Centre for Cities drive. The script therefore downloads those same files from ONS, along with the 2023 to 2025 editions released after the briefing, and uses two repo lookups:
- `Input workbooks/LAtoPUA2024.xlsx` gives the **urban flag**. A destination is urban if it lies in a Centre for Cities Primary Urban Area, and non-urban if its PUA is coded `:`. This is the same rule the repo uses (`":" -> "non_urban"`).
- `Input workbooks/2024_Inner_London_lookup.xlsx` gives the `inner_cfc` flag.

**Clean outputs**

| File | Grain | Key columns |
|---|---|---|
| `migration_panel_borough_year.csv` | borough x year | `all_in/out/net`, `nonlondon_*`, `withinlondon_*`, `urban_nonlondon_*`, `nonurban_*`, `scotni_*` |
| `migration_od_london_boroughs.csv` | borough x year x direction x counterpart LA | `moves`, counterpart name/region/PUA, `cp_urban`, `cp_type` |
| `migration_outflow_destinations.csv` | borough x year x destination LA (out-flows only) | `dest_code`, `dest_la_name`, `dest_region`, `dest_pua`, `dest_urban`, `dest_type` |
| `migration_borough_year_ageband.csv` | borough x year x age band | `in`, `out`, `net` (bands 0-15, 16-24, 25-34, 35-44, 45-64, 65+) |

`cp_type` / `dest_type` takes four values: London, Urban (non-London), Non-urban, and Scotland/NI (country total).

**Gaps and caveats**
- The estimates are built mainly from changes in GP registration, with adjustments (for example for students). Moves by people who do not re-register are missed or delayed. Young men are a known weak spot. Pandemic-era registration behaviour may have shifted.
- Moves to and from Scotland and Northern Ireland appear only as country totals, so they have no urban flag. They are in `all_*` and `nonlondon_*` but not in `urban_nonlondon_*` or `nonurban_*`.
- Flows are non-integer because ONS applies scaling. Moves within a single LA are excluded.
- The series was revised after Census 2021 (published December 2023). The 2015 to 2021 files are the revised versions.
- Within-London moves count in both boroughs' `all_*` totals. Sum `nonlondon_*` across boroughs for London-wide net flows.
- **London here means the GLA, not the Centre for Cities London PUA.** The CfC workbooks report "London" as its London Primary Urban Area: the 33 GLA authorities plus 12 nearby councils (Dartford, Gravesham, Elmbridge, Epsom and Ewell, Runnymede, Spelthorne, Woking, Epping Forest, Broxbourne, Hertsmere, Three Rivers and Watford).
  - Reconciliation: for the year ending June 2015, CfC "Into London" is 264,791. GLA in-moves from the rest of England and Wales computed here total 250,300.
  - In these files those 12 councils count as **Urban (non-London)** destinations, and they carry `dest_pua = "London"`, so they can be regrouped later.
- **Panel totals.** These are summed over the 32 boroughs, from the rest of England and Wales only (Scotland and Northern Ireland excluded):

  | Year ending June | In | Out | Net with urban areas outside London | Net with non-urban areas |
  |---|---|---|---|---|
  | 2015 | 249,918 | 328,135 | -26,511 | -51,706 |
  | 2019 | 267,806 | 366,308 | -36,696 | -61,806 |
  | 2020 | 237,618 | 351,036 | -40,949 | -72,469 |
  | 2021 | 271,881 | 458,177 | -63,892 | -122,404 |
  | 2022 | 273,182 | 401,544 | -49,215 | -79,147 |
  | 2025 | 277,445 | 409,696 | -52,094 | -80,158 |

  The year ending June 2021 is the exodus year. Net out-flow to non-urban areas roughly doubled against 2019.
- `migration_outflow_destinations.csv` has 109,191 borough x year x destination rows. Of these, 58,167 go to non-urban LAs, 39,074 to urban LAs outside London, 11,246 to other London boroughs (including the City) and 704 to Scotland or NI as country totals.

## 2. Private rents

| | |
|---|---|
| Source | ONS, *Price Index of Private Rents, UK: monthly price statistics*, release of 21 October 2026, Table 1: https://www.ons.gov.uk/economy/inflationandpriceindices/datasets/priceindexofprivaterentsukmonthlypricestatistics |
| Raw file | `raw/ons_pipr/pipr_21october2026.xlsx` |
| Coverage | January 2015 to September 2026 |
| Frequency | Monthly |
| Geography | 32 London boroughs, 64 South East and 45 East of England LAs, plus the three region aggregates |
| Script | `scripts/20_rents.py` |

**Clean outputs.** `rents_monthly_la.csv` is wide. It holds the index (January 2023 = 100), monthly and annual change, and average rent (GBP per month), overall and by 1, 2, 3 and 4+ bedrooms and by detached, semi-detached, terraced and flat. `rents_monthly_la_long.csv` is the same data in long form, one row per area x month x category.

**Gaps and caveats**
- **City of London is not published.** PIPR covers exactly the 32-borough analysis panel.
- PIPR is a stock measure. It tracks rents on all existing tenancies, not just new lets, so it reacts slowly to shocks. The pandemic dip in Inner London advertised rents will look much smaller here than in listings data.
- PIPR replaced IPHRP and the Private Rental Market Statistics in March 2024. Its status is "official statistics in development", and it is revised as new data arrive, so pin to a release (here, 21 October 2026).
- Annual change is missing for 2015 (marked `[x]` in the source), because no 2014 base exists.

## 3. House prices

| | |
|---|---|
| Source | HM Land Registry Price Paid Data, yearly files: http://prod.publicdata.landregistry.gov.uk.s3-website-eu-west-1.amazonaws.com/pp-YYYY.csv |
| Raw files | `raw/land_registry/pp-2017.csv` to `pp-2023.csv` (about 180 MB each) |
| Coverage | January 2017 to December 2023 |
| Frequency | Monthly (aggregated from transactions) |
| Geography | 2023 LAs. 32 London boroughs (City excluded), 64 South East and 45 East of England |
| Script | `scripts/30_house_prices.py` |

**Clean outputs.** `house_prices_monthly_la_type_2017_2023.csv` has one row per LA x month x property type. Types are Detached, Semi-detached, Terraced, Flat/maisonette, Other and All. Columns:
- `median_price_catA`, `mean_price_catA` and `n_catA` cover Category A (standard market-value sales) only.
- `n_all` counts all recorded transactions, including Category B.
- The panel is balanced, so a month with no sales has count 0 and a missing price.

`land_registry_district_to_la.csv` records the district-name mapping.

**Gaps and caveats**
- Price Paid has no LA code. The `district` name is matched to ONS 2023 LA names. Districts abolished or renamed during the window are mapped to their 2023 successor: Aylesbury Vale, Chiltern, South Bucks and Wycombe go to Buckinghamshire (2020), Suffolk Coastal and Waveney to East Suffolk, Forest Heath and St Edmundsbury to West Suffolk (2019), and Shepway to Folkestone and Hythe (2018). Every target LA matched at least one district.
- Category B covers repossessions, buy-to-lets, sales to companies and transfers under a power of sale. It is excluded from prices but counted in `n_all`.
- Yearly files reflect the state of the register when downloaded (28 October 2026). Late registrations for 2023 are included. Price Paid excludes most right-to-buy sales, sales below market value and many new-build bulk transfers.
- The stamp duty holiday (8 July 2020 to 30 September 2021, tapered from 1 July 2021) causes large swings in transaction timing. These interact with the pandemic shock.
- Small cells: some borough-months by property type have very few sales, so medians are noisy. City of London sales are dropped.
- Coverage check:
  - 2,774,079 transactions fall in the 141 LAs over 2017 to 2023, 2,349,652 of them Category A.
  - Every borough-month has at least 10 Category A sales for "All" types. The lowest borough total is Kensington and Chelsea, at 11,218 over seven years.
  - Annual Category A counts are 347,741 (2017), 328,761 (2018), 316,001 (2019), 291,481 (2020), 436,539 (2021), 358,727 (2022) and 270,402 (2023). The 2021 peak is the stamp duty holiday.
- **The monthly median is not quality-adjusted.** Composition swings dominate in expensive boroughs around the stamp duty deadline. For example, Kensington and Chelsea had 431 Category A sales at a £1.04m median in June 2021, then 50 sales at a £2.20m median in July 2021. This drives the Inner high-amenity spike in the charts. The method stage will need a type-specific, repeat-sales or hedonic index; ONS/HMLR UKHPI is one published option.
- Property type "Other" holds Category B records only, so it has counts but no Category A price.

## 4. Amenity density

| | |
|---|---|
| Source (units) | ONS UK Business Counts, local units by industry and employment size band, Nomis dataset NM_141_1, 2019 |
| Source (population) | ONS mid-2019 population estimates, Nomis NM_2002_1 (rebased to Census 2021, last revised 29 July 2026) |
| Raw files | `raw/nomis/ukbc_local_units_2019_divisions.csv`, `raw/nomis/mye_population_mid2019.csv` |
| Coverage | 2019. UK Business Counts is an IDBR snapshot taken in March 2019 |
| Geography | All UK LAs on April 2023 boundaries (Nomis TYPE424). London is the focus |
| Script | `scripts/40_amenity_density.py` |

**Industry definition.** NM_141_1 exposes SIC 2007 divisions, not sections, so sections are built from divisions. Section I (accommodation and food services) is divisions 55 and 56. Section R (arts, entertainment and recreation) is divisions 90 to 93. Each division count is kept, along with the all-industries total.

**Clean outputs**
- `london_amenity_density_2019.csv` covers the 32 boroughs. It has units by division and section, the mid-2019 population, units per 1,000 residents (`per1k_I_accom_food`, `per1k_R_arts_rec`, `per1k_IR`), the continuous measures, and both binary splits (see the geography conventions above).
- `amenity_units_2019_all_las.csv` gives the same unit and density measures for every UK LA, including the City of London.
- `london_amenity_units_2019_msoa2011.csv` gives **MSOA-level** 2019 local units for divisions 55, 56 and 90 to 93, sections I and R, and all industries. It covers all 983 London MSOAs (2011 boundaries, including the City's one MSOA). The raw file is `raw/nomis/ukbc_local_units_2019_divisions_london_msoa2011.csv`. It has not been matched to any other data; that is left for the method stage.

**Small-area availability (checked 28 October 2026).**
- NM_141_1 is published down to **MSOA**. It has 2001, 2011 and 2021 MSOAs (TYPE305, TYPE297, TYPE152), and no LSOA or output-area level.
- For 2019, only the **2011 MSOA** geography (TYPE297) returns values. The 2021 MSOAs (TYPE152) return "These figures are missing" for 2019.
- Divisions are available at MSOA level, so sections I and R are built the same way as at LA level.
- MSOA counts are rounded to the nearest 5 independently of LA counts. Summed MSOA I+R totals differ from the LA totals by up to 90 units (Enfield).
- Population is not attached at MSOA level.

**Gaps and caveats**
- Counts are local units (sites), not employment or floorspace. Nomis rounds them to the nearest 5, so small cells are imprecise.
- The **City of London** has 206 I+R units per 1,000 residents (1,805 units, 8,765 residents). This is why it is excluded. Among the 32 boroughs, Westminster is highest at 32.7 and Barking and Dagenham lowest at 2.5. The distribution is right-skewed, so the log is provided.
- Per-resident density favours boroughs with large visitor or worker inflows (Westminster, Camden). Density per km² or per workday population would be an alternative and is not yet built.

## 5. Amenity use (Google mobility)

| | |
|---|---|
| Source | Google COVID-19 Community Mobility Reports, regional CSVs: https://www.gstatic.com/covid19/mobility/Region_Mobility_Report_CSVs.zip |
| Raw files | `raw/google_mobility/Region_Mobility_Report_CSVs.zip`, plus `GB_Region_Mobility_Report_2020_2022.csv` (the 2020 to 2022 GB files combined) |
| Coverage | 15 February 2020 to 15 October 2022 (974 days). Google stopped updating the reports on 15 October 2022 |
| Frequency | Daily, with a monthly mean also provided |
| Geography | 32 boroughs plus the Greater London aggregate (`la_code = E12000007`). City of London is dropped from the clean files but kept in the raw GB extract |
| Script | `scripts/50_mobility.py` |

**Clean outputs.** `mobility_daily_london.csv` holds `retail_recreation` and `workplaces`, each as the percentage change against the 3 January to 6 February 2020 day-of-week median baseline. `mobility_monthly_london.csv` holds monthly means with counts of missing days.

**Gaps and caveats**
- There is **no pre-2020 data and nothing after October 2022**. The 2017 to 2023 charts show this series only for its live window.
- The baseline is a single winter month for each borough, so levels are not comparable across boroughs. Only changes within a borough are comparable. Seasonality is not removed, which is why summer looks high.
- Missing days (Google suppresses data below its anonymity threshold):
  - City of London workplaces: 299 days missing (City excluded from the panel).
  - Sutton retail and recreation: 16 days missing.
  - Fewer than 7 days missing for each of Harrow, Richmond, Camden, Hammersmith and Fulham, Islington, Kensington and Chelsea, Kingston and Westminster.
- The data cover only Google users with Location History turned on, and they are visits, not spending.
- The reports are archived and no longer maintained. The download still worked on 28 October 2026.

## 6. Charts

`scripts/60_charts.py` writes the charts to `outputs/figures/`:
- `exploratory_panel.png` has four rows: rents, house prices, net migration with outside London, and retail and recreation mobility. It has two columns: Inner vs Outer, and high vs low amenity (London-wide median).
- `exploratory_within_zone.png` shows the same four measures split four ways: Inner high, Inner low, Outer high and Outer low, using the within-zone medians. Hue marks the zone and line style marks amenity.
- Supporting charts are `rent_levels.png`, `sales_volume.png`, `net_migration_all.png` and `workplaces_mobility.png`.
- The data behind each chart are written to `data/clean/chartdata_*.csv`.

Each group line is an unweighted mean across the boroughs in the group (32 boroughs, City excluded). Every borough's series is indexed to its own base before averaging:
- Rents: January 2020 = 100.
- House prices: 3-month rolling median, with the 2019 mean = 100.
- Migration: net flow per 1,000 mid-2019 residents.
- Mobility: 7-day rolling mean.

## 7. Controls (garden access, teleworkability, age, tenure)

Script: `scripts/70_controls.py`.

**Clean outputs**
- `controls_borough.csv`: 32 boroughs.
- `controls_msoa2011.csv`: all 983 London 2011 MSOAs. This file includes the City's one MSOA, and has no missing values.
- `telework_ons2020_soc4.csv` and `telework_ons2020_soc3.csv`: the occupation scores.

| Control | Source | Definition | Borough range |
|---|---|---|---|
| `garden_share` | ONS, *Access to gardens and public green space in Great Britain*, **April 2020 edition**, private outdoor space reference tables (`raw/ons_gardens/osprivateoutdoorspacereferencetables.xlsx`). Built from OS AddressBase Plus epoch 74. https://www.ons.gov.uk/economy/environmentalaccounts/datasets/accesstogardensandpublicgreenspaceingreatbritain | Addresses with private outdoor space ÷ all residential addresses (houses + flats, "Total" block). Sheets "LAD gardens" and "MSOA gardens" | 0.603 (Tower Hamlets) to 0.897 (Havering) |
| `telework_share` | 2011 Census QS606EW, occupation by SOC 2010 minor group (Nomis NM_561_1), × ONS 2020 "ability to homework" score by SOC 2010 unit group ("Which jobs can be done from home?", 21 July 2020; chart data https://www.ons.gov.uk/visualisations/dvc890/chart1/data.xlsx, saved as `raw/ons_homeworking/ons_whichjobscanbedonefromhome_2020_data.xlsx`) | Share of usual residents aged 16-74 in employment whose occupation can be done from home (definition below the table) | 0.334 (Barking and Dagenham) to 0.668 (Kensington and Chelsea) |
| `age20_39_share` | 2011 Census QS103EW, age by single year (Nomis NM_503_1) | Residents aged 20-39 ÷ all usual residents | 0.248 (Havering) to 0.494 (Tower Hamlets) |
| `private_rent_share` | 2011 Census KS402EW, tenure (Nomis NM_619_1) | Households renting privately (private landlord or letting agency, plus other private rented) ÷ all households | 0.106 (Havering) to 0.397 (Westminster) |

**How the teleworkability share is built**
- **Route.** The ONS 2020 occupation-level measure exists, so it was used. **The Dingel-Neiman crosswalk route was not needed.**
- **Score.** ONS publishes a score from 0 to 5 for 365 unit groups. It is the sum of five O*NET-based barrier scores, and a higher score means the job is less able to be done from home. ONS gives no cut-off.
- **Threshold.** A unit group counts as teleworkable if its score is **below 1.5**. That covers 44% of UK employment, using ONS's own employment weights.
- **Aggregation.** Unit-group shares are aggregated to the 90 Census minor groups with ONS employment weights. Every minor group in QS606EW has at least one scored unit group.
- **Alternatives saved alongside:** `telework_share_alt2` uses a threshold of 2.0, which covers 63% of employment. `homework_score_mean` is the employment-weighted mean score.

**Gaps and caveats**
- The Census controls describe 2011, nine years before the shock. London's age and tenure mix shifted between 2011 and 2020, especially in Tower Hamlets, Newham and Southwark.
- The homeworking score is US O*NET task content mapped to UK SOC through ISCO. ONS notes it was computed before the pandemic.
- The garden measure counts shared gardens for flats as private outdoor space, following the ONS definition.
- For the 32 boroughs, the controls are strongly correlated with log amenity density:

  | Control | Correlation with log amenity density |
  |---|---|
  | Teleworkability | 0.82 |
  | Garden access | −0.73 |
  | Private renting | 0.68 |
  | Share aged 20-39 | 0.61 |

## 8. Estimation software

| Item | Status |
|---|---|
| Event study, CR1 SEs, wild cluster bootstrap | Own implementation in `scripts/80_event_study.py` (numpy/scipy). Checked against `pyfixest` 0.60 and `wildboottest` 0.3.2 (see `ESTIMATION_NOTES.md`) |
| Callaway, Goodman-Bacon and Sant'Anna continuous DiD | **Exists.** R: `contdid` 0.1.1 on CRAN (`cont_did()`), written by Callaway, Goodman-Bacon and Sant'Anna, installed to the R 4.6.1 user library. Python ports also exist on PyPI: `moderndid` 0.4.1 (`cont_did`, J. DeKlerk) and `contdid` 0.1.0 (X. Cai and W. Xu). Neither was installed or tested. The authors' R package was used Run on rents as a robustness check by `scripts/85_contdid.R`, which `run_all.py` calls through Rscript. The package needs a zero-dose comparison group, so the bottom within-zone amenity tercile plays that role (see `ESTIMATION_NOTES.md` section 5). Covariates are not supported |
| HonestDiD (Rambachan and Roth) | R `HonestDiD` 0.2.8 from CRAN, run by `scripts/83_honestdid.R` (relative magnitudes and smoothness). It uses `doParallel` for the Mbar grid. Run time is about 50 minutes |
| run_all flags | `--only STEP ...`, `--from STEP` and `--force-honestdid`. HonestDiD is skipped when the hash of its inputs matches `outputs/event_study/honestdid_cache.json` |
| R location | `run_all.py` finds Rscript through the `RSCRIPT` environment variable, then PATH, then `%LOCALAPPDATA%\Programs\R\R-*\bin` |

## 9. MSOA data for the house-price analysis

| Item | Source | Raw file | Clean file / use |
|---|---|---|---|
| Postcode to 2011 MSOA lookup | ONS **National Statistics Postcode Lookup, 2011 Census edition, August 2024** (ArcGIS item `c5afedb9204a47e99559a4880feddcb1`, https://www.arcgis.com/sharing/rest/content/items/c5afedb9204a47e99559a4880feddcb1/data). Columns used: `pcds`, `laua`, `msoa11` | `raw/nspl/NSPL_2011CENSUS_AUG_2024.zip` (195 MB) | Used in `87_msoa_house_prices.py` |
| MSOA population, mid-2019 | ONS small-area population estimates, 2011-based series, 2011 MSOAs (Nomis NM_2010_1), all persons | `raw/nomis/sape_mid2019_msoa2011_ew.csv` (7,201 MSOAs in England and Wales) | Denominator for MSOA amenity density in `75_msoa_amenity.py` |
| Matched sales | Land Registry Price Paid 2017-2023 (section 3) joined to the NSPL | n/a | `data/clean/msoa_sales_2017_2023.parquet` (798,102 London-district sales, all categories) |
| MSOA analysis file | Sections 4 and 7 plus the population row above | n/a | `data/clean/msoa_amenity_controls.csv` (982 MSOAs, City excluded) |

**Gaps and caveats**
- **Why an older NSPL edition.** The current NSPL (August 2026, ArcGIS item `9d8364ebae8b4439aa66cda440e54fc8`) carries only 2021 geographies, with no `msoa11`. The August 2024 2011-Census edition is the last that has 2011 MSOAs. It includes terminated postcodes, so it covers sales back to 2017.
- **Match quality.** 99.98% of Category A sales outside the City match to an MSOA; 134 sales have postcodes not in the NSPL. The NSPL LA code and the MSOA's borough never disagree.
- **Mixed vintages.** The MSOA population estimates are the 2011-based series, not rebased to Census 2021. The borough-level density uses the rebased estimates, so the two measures are not on the same population vintage.
- **Zero counts.** Three MSOAs report 0 I+R units (Nomis rounds to the nearest 5) and are set to 1 unit before taking logs.


**Round 3 additions (29 October 2026)**

| Item | Source | Raw file | Clean file / use |
|---|---|---|---|
| Land Registry Price Paid 2024, 2025 and 2026 (2026 is year to date) | Same yearly-file URLs as section 3, republished 28 October 2026 | `raw/land_registry/pp-2024.csv`, `pp-2025.csv`, `pp-2026.csv` | Extend the MSOA sample to 2026Q3. The borough-level file `house_prices_monthly_la_type_2017_2023.csv` is unchanged |
| Current NSPL (August 2026) | ArcGIS item `9d8364ebae8b4439aa66cda440e54fc8` | `raw/nspl/NSPL_AUG_2026.zip` | Coordinates for postcodes created after August 2024, placed by nearest NSPL-2011 postcode |
| MSOA 2011 population-weighted centroids | ONS, "Middle layer Super Output Areas (December 2011) EW Population Weighted Centroids", ArcGIS item `c0e3f920e20e41b3a994dd7fc7333c91`, queried in BNG (EPSG:27700) | `raw/ons_geography/msoa2011_pwc_bng.json` (7,201 points) | `data/clean/msoa_distance_charing_cross.csv` (distance to Charing Cross, km and log) |
| 2019 MSOA median price | Computed from the matched Category A sales | n/a | `data/clean/msoa_median_price_2019.csv` |
| Matched sales 2017-2026 | Land Registry + NSPL | n/a | `data/clean/msoa_sales_2017_2026.parquet`, which replaces `msoa_sales_2017_2023.parquet` |

**Gaps and caveats (round 3)**
- **Registration lag in 2026.** Category A sales in 2026Q1, Q2 and Q3 are 90%, 70% and 45% of the same quarters in 2024. The new-build share falls to 0.1-0.6%, against 3-8% in 2024-25. The coverage table is in `outputs/event_study/msoa_quarterly_coverage.csv`.
- **Post-2024 postcodes.** These are placed in MSOAs by nearest neighbour, not by boundary polygon. This affects 0.24% of matched sales.


**Round 4 additions (29 October 2026)**

| Item | Source | Raw file | Use |
|---|---|---|---|
| London median monthly private rent, October 2018 to September 2019 | ONS, *Private rental market summary statistics in England*, release of 13 December 2019 (VOA lettings data), Table 1.7, all categories, London, median £1,450. https://www.ons.gov.uk/peoplepopulationandcommunity/housing/datasets/privaterentalmarketsummarystatisticsinengland | `raw/ons_prms/prms_oct2018_sep2019.xls` | Base for the rent pound value (`89_pound_values.py`). PIPR publishes means only. The PRMS series ended when PIPR replaced it |
| Borough price-to-rent ratios | Matched Land Registry sales (borough quarterly median) and PIPR average rents | n/a | `data/clean/price_to_rent_borough_quarter.csv` |


**Round 5 additions (29 October 2026): consumption access**

| Item | Source | Raw file | Clean file / use |
|---|---|---|---|
| I+R local units 2019, all 2011 MSOAs in England and Wales | UK Business Counts, Nomis NM_141_1, TYPE297, divisions 55, 56 and 90-93, paged through `recordoffset` (Nomis caps calls at 25,000 rows) | `raw/nomis/ukbc_local_units_2019_divisions_msoa2011_ew.csv` (7,201 MSOAs × 6 divisions); page files in `raw/nomis/pages/` | Sources for the access measures. The London MSOA counts match `london_amenity_units_2019_msoa2011.csv` exactly |
| Consumption access, 982 analysis MSOAs | Built in `77_msoa_access.py` from the units above, placed at the 2011 MSOA population-weighted centroids (section 9) | n/a | `data/clean/msoa_access_2019.csv` |

The access file holds:
- ring counts at 0-1, 1-2 and 2-5 km;
- access indices Σ units · exp(−d/λ) for λ = 1, 1.5 and 3 km;
- their standardised log forms;
- the number of MSOA centroids within 1 km;
- the distance to the nearest other centroid.

**Gaps and caveats**
- **Coarse geography.** MSOA is the finest geography Nomis publishes for Business Counts, so units are placed at centroids, not at their addresses. The median distance to the next MSOA centroid is 0.78 km, and 217 of 982 MSOAs have no other centroid within 1 km.
- **Collinearity with centrality.** The access index correlates −0.85 with log distance to Charing Cross within boroughs (`outputs/event_study/msoa_access_correlations.csv`).
- **Not used:** OpenStreetMap or any other point dataset.


**Round 6 additions (29 October 2026)**

| Item | Source | Raw file | Clean file / use |
|---|---|---|---|
| Mid-2019 population by single year of age, 32 boroughs | ONS mid-year estimates rebased to Census 2021, Nomis NM_2002_1, c_age 101-191 (ages 0-89 and 90+) | `raw/nomis/mye_population_mid2019_single_age_london.csv` | Denominators for the age-group migration rates |
| Net migration with the rest of the UK by age group | Cached London rows of the ONS detailed origin-destination files (section 1) | n/a | `data/clean/migration_net_by_age_group.csv`: borough × year × group (all, 20-29, 30-39, family proxy 0-15 + 30-49, 50+), with net moves, mid-2019 group population, and rate per 1,000 |


**Round 7 additions (29 October 2026)**

| Item | Source | Raw file | Clean file / use |
|---|---|---|---|
| Full-time student share, 32 boroughs | 2011 Census KS501EW (Nomis NM_623_1): cell 9 "Schoolchildren and full-time students: Age 18 and over" ÷ cell 0 (usual residents aged 16+) | `raw/census2011/ks501ew_students_la.csv` | `data/clean/borough_student_hospitality_2011.csv` (`student_share`). Mean 8.1%, range 3.4-14.9% |
| Young hospitality-worker share, 32 boroughs | 2011 Census DC6110EW, industry by sex by age (Nomis NM_771_1): employed residents aged 16-34 (age bands 16-19, 20-21, 22-24, 25-29, 30-34) in I (accommodation and food) or "R, S, T, U Other", ÷ all employed residents aged 16-34 | `raw/census2011/dc6110ew_industry_age16_34_la.csv` | Same file (`hosp_share_I_RSTU`; I-only variant `hosp_share_I`). Mean 14.8%, range 11.0-20.5% |
| Age panel incl. 20-24 and 25-29 | Section 1 cached origin-destination rows and the round 6 single-age population | n/a | `data/clean/migration_net_by_age_group_extended.csv` |

**Gap.** Arts, entertainment and recreation (section R) is not published separately by age in the 2011 Census industry tables at LA level. It is only available combined with S, T and U.

## Manual steps and failures

No source needed a manual browser download. Every file above was fetched by script on 28 October 2026. Problems and workarounds:

| Issue | What happened | Handling |
|---|---|---|
| Centre for Cities repo lacks raw migration data | Its R scripts read ONS files from a private drive. The repo ships only lookups and aggregated outputs | Downloaded the same ONS detailed-estimates files directly, plus the 2023 to 2025 editions. Used the repo's `LAtoPUA2024.xlsx` and `2024_Inner_London_lookup.xlsx` |
| ONS file server is slow and cannot resume | About 12 MB/min in total, and range requests are not honoured, so interrupted downloads restart from zero | Parallel downloads. Total about 1.3 GB for 11 workbooks, which took about 40 minutes |
| ONS internal migration contents sheet | The "Contents" sheet labels the 2021 and 2023 geography sheets the wrong way round | Sheets are picked by their actual names ("YYYY on 2023 LAs") |
| PIPR has no City of London | Not published | City excluded from the analysis panel anyway |
| Nomis has no LSOA business counts, and 2021 MSOAs are empty for 2019 | Checked the geography types for NM_141_1 | Used 2011 MSOAs (TYPE297) |
| Nomis has no SIC sections in NM_141_1 | Only divisions and finer levels | Sections I and R built as the sum of divisions 55-56 and 90-93 |
| Google mobility is archived | Reports ended 15 October 2022. The zip still downloads from gstatic | Kept a copy in `raw/google_mobility/`, in case the URL is withdrawn |
| Price Paid has no LA code | District names only | Matched by name, with 2018 to 2020 reorganisations mapped to 2023 successors. The mapping is saved in `land_registry_district_to_la.csv` |
| Nomis API row cap | Census MSOA occupation (QS606EW, 983 × 125 cells) was silently truncated at 25,000 rows | `70_controls.py` pages through results with `recordoffset`. Page files are in `raw/census2011/pages/` |
| ONS homeworking data only in a chart download | The 2020 article has no dataset page. The occupation table sits behind the article's interactive chart | Downloaded the chart's `data.xlsx` directly |
| `contdid` install | The first CRAN binary install timed out on dependency `BMisc` | Retried with `options(timeout = 900)` |
| Current NSPL lacks 2011 MSOAs | The August 2026 NSPL has 2021 geographies only | Used the NSPL 2011 Census edition (August 2024). See section 9 |
| Nomis NM_2010_1 region-parent query | Asking for London MSOAs under the London region code returned an empty file | Pull all 7,201 England and Wales MSOAs and filter to London |

**Re-running.** Delete a raw file to force a fresh download. Migration parsing caches the London rows as `raw/ons_internal_migration/*.london.parquet`, so delete those too if the xlsx files change. Python dependencies are pandas, numpy, scipy, matplotlib, openpyxl, pyarrow, requests and (optional, about 5x faster on the migration workbooks) python-calamine. `pyfixest` and `wildboottest` were used only for one-off checks. R 4.6.1 with `contdid` is needed for `85_contdid.R`, and with `HonestDiD` and `doParallel` for `83_honestdid.R`. `pyfixest` is also used by `87_msoa_house_prices.py` (for demeaning and a check).
