# B3 national LA panel and B5 closure intensity (data assembly only, no regressions)

Built 29 October 2026. Scripts in `extension/scripts/` (run in this order): `b3_migration.py`, `b3_rents.py`,
`b3_crosssection.py`, `b3_mobility.py`, `b5_closure_intensity.py`, `b3_quarter_panel.py`, `b3_validate_london.py`.
Geography: the 318 local authorities of England (296) and Wales (22) on April 2023 boundaries, as listed in the ONS
internal migration lookup `lasregionew2023lookup.xlsx`. Nothing in the pilot's `scripts/`, `data/`, `outputs/` or
report files was changed; pilot raw files were read only.

## Files

| File | Unit | Rows | Coverage |
|---|---|---|---|
| `extension/data/clean/b3_migration_la_year_by_age_group.csv` | LA x year ending June x age group (long) | 24,486 | 318 LAs x 11 years (2015-2025) x 7 groups |
| `research-data/london-variety-extension/clean/b3_migration_la_year_single_age.parquet` | LA x year x single year of age | 352,729 | 318 LAs, ages 0-111 (top-coded 100+ from 2022) |
| `extension/data/clean/b3_la_quarter_panel.csv` | LA x quarter, 2015Q1-2026Q3 | 14,946 | rents 316 LAs; mobility 317 LAs (2020Q1-2022Q4) |
| `extension/data/clean/b3_rents_quarterly_la.csv` | LA x quarter (rents only) | 14,852 | 316 LAs |
| `research-data/london-variety-extension/clean/b3_rents_monthly_la.csv` | LA x month, Jan 2015-Sep 2026, all PIPR columns | 44,556 | 316 LAs |
| `extension/data/clean/b3_rents_las_not_published.csv` | LAs PIPR does not publish | 2 | City of London, Isles of Scilly |
| `extension/data/clean/b3_mobility_quarterly_lad.csv` | LA x quarter (mobility only) | 3,804 | 317 LAs x 12 quarters |
| `extension/data/clean/b3_mobility_daily_lad.parquet` | LA x day, 15 Feb 2020-15 Oct 2022 | 308,758 | 317 LAs x 974 days |
| `extension/data/clean/b3_mobility_google_to_lad_map.csv` | one row per 2023 LAD: Google source and mapping type | 318 | |
| `extension/data/clean/b3_mobility_google_regions_not_used.csv` | E&W Google regions not used, with reason | 48 | |
| `extension/data/clean/b3_la_crosssection.csv` | LA cross-section (Business Counts 2019 and controls) | 318 | 318 LAs |
| `extension/data/clean/b5_closure_intensity_la_quarter.csv` | LA x quarter, 2020Q1-2022Q3 | 3,498 | 318 LAs x 11 quarters (317 with data) |
| `extension/data/clean/b3_validation_london.csv` | one row per London validation check | 32 | |

New raw downloads (extension raw folder): `nomis/pages/mye2019_single_age_TYPE424_*.csv` and
`nomis/mye_population_mid2019_single_age_all_las.csv` (NM_2002_1, mid-2019 single year of age, all April 2023 LADs),
`nomis/census2021_ts054_tenure_TYPE424.csv` (Census 2021 TS054), `nomis/census2011_qs103_total_pre2023_districts.csv`
(Census 2011 usual residents of 15 pre-2023 districts, mobility weights). Per-year migration aggregates are cached in
`raw/ons_internal_migration_agg/agg{year}.parquet`, with a one-line file check per year in `info{year}.csv`.

## Source facts (stated precisely)

- Migration files contain only moves between different LAs: in every year 2015-2025 there are no rows with origin
  equal to destination, so moves within an LA are excluded by construction.
- Moves between England and Wales LAs and Scotland or Northern Ireland are in the files, but only with the country
  as the counterpart (S92000003 Scotland, N92000002 Northern Ireland; about 2,500 rows a year). Moves within Scotland,
  within Northern Ireland and between the two are not in the files (no rows with both ends in Scotland/NI).
- Scotland/NI moves are 1.4% of all moves into or out of E&W LAs (all years, all ages).
- Within E&W, `ew_net` sums to zero nationally in every group, as it must; `all_net` sums to the net balance with
  Scotland and Northern Ireland (-105,873 over 2015-2025, all ages).
- Age is age at 30 June of the year ending (ONS definition). Single-age columns run to age 108-111 in 2015-2021 and
  are top-coded at 100+ from 2022; none of the groups is affected.
- Population: NM_2002_1, mid-2019, rebased to Census 2021, single year of age codes 101-191 (ages 0-89 and 90+), the
  same table and query as `scripts/94_migration_age.py`, with `geography=TYPE424` (all April 2023 LADs) in place of
  the London code list and paged with `recordoffset` (Nomis returns at most 25,000 rows per call).
- PIPR (release 21 October 2026, Table 1) publishes 316 of the 318 E&W LAs; it does not publish City of London or
  the Isles of Scilly. Every published LA has an unbroken index from January 2015 to September 2026.
- UK Business Counts 2019 (NM_141_1, TYPE424): all 318 LAs present, every value flagged "Normal Value".
- Google's baseline is the median for the same day of the week over 3 January-6 February 2020 in the same area, so
  each LA series is already relative to its own pre-pandemic level. The baseline is a winter baseline: summer
  quarters in tourist areas show large positive values (2021Q3 maximum +137%), so the series mixes closure with
  ordinary seasonality.

## Mapping Google regions to 2023 LADs

| Mapping type | LADs | Detail |
|---|---|---|
| direct (1:1) | 308 | Google district, unitary, metropolitan or London borough series whose area is the LAD (includes City of London; Cornwall = GB-CON; Dorset = the sub_region_2 "Dorset" series) |
| county_equals_lad | 3 | Buckinghamshire (GB-BKM), North Yorkshire (GB-NYK), Somerset (GB-SOM): Google county series whose area equals the 2023 unitary |
| composite (many-to-one) | 5 | Cumberland (Allerdale, Carlisle, Copeland); Westmorland and Furness (Barrow-in-Furness, Eden, South Lakeland); North Northamptonshire (Corby, East Northamptonshire, Kettering, Wellingborough); West Northamptonshire (Daventry, Northampton, South Northamptonshire); East Suffolk (Suffolk Coastal, Waveney) |
| broader_region (one Google region covering several LADs) | 1 | Shropshire: Google's only Shropshire series is the ceremonial-county aggregate, which also covers Telford and Wrekin; assigned to Shropshire and flagged; Telford and Wrekin keeps its own series |
| missing | 1 | Isles of Scilly: no Google series |

Not used (48 E&W Google regions, listed with reasons in `b3_mobility_google_regions_not_used.csv`): 31 county or
metropolitan-county aggregates (including Greater London), 16 pre-2023 district series inside Buckinghamshire,
North Yorkshire and Somerset, and the sub-LA town "Penryn" (Cornwall). The 43 Scottish and Northern Irish regions
are out of scope.

## B5 coverage

3,498 LA-quarters (318 x 11). 3,487 have a value. 23 are flagged under 50% coverage: Isles of Scilly in all 11
quarters (no series), Rutland in 10 quarters (2020Q2-2022Q3; 151 valid retail days in total) and Isle of Anglesey in
2021Q3 and 2022Q3. 2020Q1 is 15 February-31 March 2020 only (46 days). Mean coverage is 97.9%; most of the shortfall is
a gap of about 25 days that Google left in most series.

## London validation (32 analysis boroughs; all checks exact, maximum absolute difference under 1e-11)

- `migration_net_by_age_group.csv` (all, 20-29, 30-39, family, 50+; 1,760 rows) and `..._extended.csv` (20-29,
  20-24, 25-29, family, 50+; 1,760 rows): `xregion_net`, `pop_mid2019` and `xregion_net_per1k` reproduce `net_moves`,
  `pop_mid2019` and the rate exactly. For London boroughs, crossing the region boundary is crossing the Greater London
  boundary.
- `migration_panel_borough_year.csv` (352 rows): `all_in`, `all_out`, `all_net` (all counterparts, within-London
  included), `xregion_in/out/net` (= `nonlondon_*`) and `scotni_in/out` all match exactly.
- `event_study_rents_quarterly.csv` (1,504 rows): quarterly mean index and 100 x log index match exactly.
- `london_amenity_density_2019.csv` (32 rows): all unit counts, populations, densities and log densities match; the
  London-only standardisation recomputed from the national file matches `z_log_per1k_IR` exactly. The national
  `z_log_per1k_IR` is a different standardisation (all E&W LAs), so its values differ from the pilot's.
- `controls_borough.csv` garden share: exact. `mobility_daily_london.csv`: 31,168 borough-days match exactly for
  both series.

## Judgement calls (one per line)

- National outcome is net moves with all other LAs including Scotland and Northern Ireland (`all_net`), as the brief asked; `ew_net` (excluding them) is also given.
- The London measure "moves crossing the Greater London boundary" is generalised to "moves crossing the LA's own region boundary" (`xregion_*`), so London boroughs keep the pilot's outcome exactly; this is not the London-only counterfactual for other LAs.
- Scotland and Northern Ireland count as outside every English and Welsh region in `xregion_*`, as in the pilot's `nonlondon_*`.
- Wales is treated as one region for `xregion_*`, following the ONS lookup.
- The ONS lookup carries a stray character after the codes for North and West Northamptonshire; codes are cleaned to the nine-character GSS code.
- Moves are summed over sex; single-year-of-age totals are kept so other groupings can be built without re-reading the workbooks.
- City of London and Isles of Scilly are kept in every file and flagged, not dropped; the pilot dropped City of London from its analysis panel.
- Population denominators are fixed at mid-2019 for every year, as in the pilot.
- PIPR uses April 2024 codes for Barnsley (E08000038) and Sheffield (E08000039) after a minor boundary change between them; these are recoded to the 2023 codes E08000016 and E08000019 without adjustment.
- A quarter counts as complete only when all three months have a non-missing index (the pilot counted rows; for London the two rules give the same result).
- Average rent per quarter is the mean of the three monthly average rents, missing if any month is missing.
- National standardised log amenity density (`z_log_per1k_IR`) uses the 316 LAs other than City of London and Isles of Scilly (resident population under 10,000, densities 206 and 24 per 1,000); `z_log_per1k_IR_all318` uses all 318.
- No London-only standardisation is stored; it is recomputed in the validation script.
- Controls kept cheap: region, country, mid-2019 age shares, Centre for Cities PUA urban flag, ONS private outdoor space share (April 2020) and Census 2021 private-renting share; the 2011 Census telework, student and hospitality controls were not rebuilt nationally because 2011 LA boundaries need a further lookup.
- Garden share for the seven post-2020 unitaries is rebuilt from their predecessor districts by summing addresses and addresses with private outdoor space.
- Census 2021 tenure is taken directly on April 2023 LADs from Nomis (TYPE424), so no aggregation is needed.
- Google regions are matched to LADs by normalised names (prefixes such as "London Borough of" and suffixes such as "District" removed), with two hand fixes (Bristol City, Rhondda Cynon Taff); every E&W LAD was checked to have exactly one match or a stated exception.
- For Buckinghamshire, North Yorkshire and Somerset the Google county series is used because its area equals the 2023 unitary; the pre-2023 district series inside them are not used.
- For Cumberland, Westmorland and Furness, North and West Northamptonshire and East Suffolk the Google county does not equal the LAD, so the daily series is a population-weighted mean of the predecessor district series.
- Composite weights are Census 2011 usual residents (Nomis NM_503_1) because Nomis returns no mid-2019 estimates for abolished district codes.
- On days when a component district has no value, the composite uses the districts that have one, with weights renormalised; the share of weight present is stored (`*_weight_share`). This happened on 1 day for North Northamptonshire, 25 for West Northamptonshire and 6 for Cumberland.
- A weighted mean of Google % changes is an approximation: Google's own aggregation is by visits, not residents.
- Shropshire is given Google's Shropshire aggregate (which includes Telford and Wrekin) and flagged `broader_region`, rather than left missing.
- The Isles of Scilly are left without a series rather than given Cornwall's.
- The Cornwall sub-area "Penryn" is ignored because it is a town, not an LA.
- Mobility quarterly means in the B3 panel use all valid days in the quarter window; 2022Q4 covers 1-15 October only.
- B5 uses retail_and_recreation only, with no further normalisation, as Google's baseline is already the area's own.
- B5 coverage is valid days over calendar days in the quarter window (46 for 2020Q1); the 50% flag is set below 0.5.
- The two largest outputs (single-age migration, monthly rents) are written to the research-data clean folder to keep the OneDrive folder small; no single file exceeds 50 MB.

## Data dictionary

### b3_migration_la_year_by_age_group.csv (and the single-age parquet, same flow columns)
- `la_code`, `la_name`, `region`, `country`: 2023 LAD code and name, ONS region (Wales as one region), country.
- `year_ending_june`: t = year ending 30 June t; `period`: "mid-(t-1) to mid-t".
- `group`: `all`, `age20_29`, `age20_24`, `age25_29`, `age30_39`, `family_0_15_30_49` (0-15 plus 30-49; overlaps 30-39), `age50plus`.
- `all_in`, `all_out`, `all_net`: moves into, out of, and net (in minus out) with every other LA in E&W plus Scotland and Northern Ireland (country level). Within-LA moves are not in the source.
- `ew_in`, `ew_out`, `ew_net`: same, other E&W LAs only.
- `xregion_in`, `xregion_out`, `xregion_net`: moves whose counterpart is outside the LA's own region (Scotland and NI included). For London boroughs = the pilot's outcome (`nonlondon_*`).
- `scotni_in`, `scotni_out`, `scotni_net`: moves with Scotland and Northern Ireland.
- `pop_mid2019`: mid-2019 residents of the group (NM_2002_1, rebased to Census 2021).
- `*_per1k`: the flow divided by `pop_mid2019`, times 1,000. Pilot London outcome = `xregion_net_per1k`; national analogue = `all_net_per1k`.
- Parquet only: `age` (single year, age at 30 June; 0-111, top-coded 100+ from 2022); no population column.

### b3_la_quarter_panel.csv
- `quarter`: calendar quarter, 2015Q1-2026Q3.
- `rent_index_qmean`: mean of the three monthly PIPR indices (January 2023 = 100); `rent_y` = 100 x log(`rent_index_qmean`), the pilot outcome; `avg_rent_qmean`: mean monthly average rent (GBP); `rent_n_months`: months with an index (3 where present).
- `rent_published`: False for City of London and Isles of Scilly.
- `mob_retail_recreation`, `mob_workplaces`: mean daily % change from Google's baseline over valid days in the quarter (2020Q1-2022Q4 only).
- `mob_rr_valid_days`, `mob_wp_valid_days`: days with a value; `mob_window_days`: calendar days in the Google window (46 in 2020Q1, 15 in 2022Q4); `mob_mapping_type`: see mapping table.

### b3_mobility_daily_lad.parquet
- `date`, `retail_recreation`, `workplaces` (% change from baseline); `*_weight_share`: share of composite population weight with data that day (1 or 0 for single-region LADs); `mapping_type`.

### b3_mobility_google_to_lad_map.csv
- `mapping_type`: `direct`, `county_equals_lad`, `composite`, `broader_region`, `missing`; `google_sub_region_1`, `google_sub_region_2` (districts joined by "; " for composites); `n_google_regions`; `note`; `rr_valid_days`, `wp_valid_days`, `window_days` (974).

### b3_la_crosssection.csv
- `units_div55` ... `units_div93`, `units_all_industries`: UK Business Counts 2019 local units (NM_141_1); `units_I_accom_food` = 55+56; `units_R_arts_rec` = 90-93; `units_IR` = I + R.
- `pop_mid2019`: all-age mid-2019 residents; `per1k_*`: units per 1,000 residents; `log_per1k_IR`: natural log.
- `z_log_per1k_IR`: standardised over 316 LAs (City of London and Isles of Scilly excluded, missing for them); `z_log_per1k_IR_all318`: standardised over all 318; `small_pop_excluded_from_z`.
- `age20_29_share`, `age20_39_share`, `age65plus_share`: mid-2019 shares of residents.
- `pua`, `urban_pua` (LA inside a Primary Urban Area), `combined_authority`: Centre for Cities LAtoPUA2024.
- `garden_share`: share of residential addresses with private outdoor space (ONS, April 2020); `garden_merged_from_districts`.
- `households_2021`, `private_rent_share_2021`: Census 2021 households and share privately rented (TS054).
- `london`, `city_of_london`: flags.

### b5_closure_intensity_la_quarter.csv
- `quarter`: 2020Q1-2022Q3; `closure_rr_mean`: mean daily retail_and_recreation % change from baseline over valid days; `rr_valid_days`; `window_days` (46 in 2020Q1, else days in the quarter); `coverage` = valid / window days; `low_coverage`: coverage under 0.5; `rr_weight_share_mean`: mean daily composite weight share; `mapping_type`; `quarter_note`.

## Failures and blocks

None. No source was blocked; the only new downloads were Nomis API calls. Nomis returns no mid-2019 population for
abolished district codes, so Census 2011 populations were used as composite weights (see above).
