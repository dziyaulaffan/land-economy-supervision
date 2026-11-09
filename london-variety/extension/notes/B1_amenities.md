# B1 Amenities: FHRS, OpenStreetMap history, MSOA/LA counts, access indices, Business Counts validation

Data assembly and validation only. No regressions were run. Status and numbers below are from the run on 29 October 2026.

## Scripts (extension/scripts), run in this order

| Script | What it does |
|---|---|
| b1_nspl_extract.py | England and Wales postcode extract from the pilot's NSPL August 2026 (read only) -> big clean/nspl_ew.parquet |
| b1_fhrs_download.py | FHRS authority list (API) and one open data XML file per English and Welsh authority -> raw/fhrs |
| b1_fhrs_clean.py | Parses the XML, keeps three categories, fills missing coordinates from NSPL -> big clean/fhrs_points_ew.parquet |
| b1_osm_ohsome.py | ohsome API v1 snapshots at 2019-12-31 and 2022-12-31, 0.5 degree tiles -> raw/ohsome/<date>/ |
| b1_geography.py | 2021 MSOA boundaries (BFE V8) and 2021 MSOA population-weighted centroids (V2) from the ONS Open Geography Portal, and Census 2021 MSOA population (Nomis TS001) -> raw/ons_geography, raw/nomis |
| b1_ukbc_download.py | UK Business Counts local units by SIC subclass, LAs on April 2023 boundaries, 2019, 2022 and 2026, and mid-2019 and mid-2022 population -> raw/nomis |
| b1_assign_access.py | Assigns points to MSOA and LA, builds counts and access indices |
| b1_validate.py | LA-level correlations against Business Counts |

Pilot raw files were read only (NSPL). Nothing in scripts/, outputs/ or the main project's notes was touched.

## Output files

Small files, `extension/data/clean/`:

| File | Rows | Content |
|---|---|---|
| msoa21_amenity_counts_ew.csv | 7,264 | One row per 2021 MSOA: LA (2023 code), Census 2021 residents, counts for 3 FHRS categories and, for 2019 and 2022, 10 OSM tags plus 3 OSM groups |
| la2023_amenity_counts_ew.csv | 318 | The same counts summed to LAs, plus FHRS counts by inspecting authority (`*_by_authority`, which include records with no address) |
| msoa21_amenity_access_ew.csv | 7,264 | 90 access indices: {pt, pwc} x {lambda 1, 1.5, 3 km} x 15 categories (3 FHRS; for 2019 and 2022, OSM restaurant_cafe, fast_food, pub_bar_club, cinema, arts_venue, fitness_centre) |
| msoa21_ew_lookup_pwc.csv | 7,264 | MSOA21 -> LAD26 and LAD23 codes, population-weighted centroid (BNG), Census 2021 residents |
| b1_point_assignment_summary.csv | 39 | Points, geocoded, assigned, MSOAs and LAs covered, by source and category |
| b1_validation_correlations_la.csv | 45 | Correlations against Business Counts (see below) |
| fhrs_geocode_summary.csv, fhrs_business_type_counts_ew.csv, fhrs_authority_to_la2023.csv, b1_ukbc_sic_subclasses_used.csv | small | FHRS geocoding counts, all FHRS business types, FHRS authority -> LA map, SIC subclass labels |

Point files (large), `~/research-data/london-variety-extension/clean/`:

| File | Rows |
|---|---|
| fhrs_points_ew.parquet / fhrs_points_ew_assigned.parquet (adds easting, northing, msoa21cd, lad23cd, assign_method) | 225,858 |
| osm_points_2019_assigned.parquet | 119,158 |
| osm_points_2022_assigned.parquet | 139,770 |
| nspl_ew.parquet (helper postcode extract) | 2,413,799 |

Column names: `fhrs_*` = FHRS; `osm2019_*`, `osm2022_*` = OSM snapshot; `access_pt_l15_*` = lambda 1.5 km to points; `access_pwc_l15_*` = lambda 1.5 km, units placed at MSOA centroids (pilot method). `l10` = 1 km, `l30` = 3 km.

## a. FHRS

- Source: FHRS API authority list (https://api.ratings.food.gov.uk/Authorities, header x-api-version 2) and one open data XML file per authority (https://ratings.food.gov.uk/api/open-data-files/FHRS{code}en-GB.xml). 320 authorities in England and Wales, all downloaded on 29 Oct 2026 without errors.
- FHRS is a current register snapshot, not a 2019 or 2022 stock. Download date 29 Oct 2026; the XML extract dates run 29 Sep to 29 Oct 2026, apart from two port health authorities (Hull and Goole Port, River Tees: 8 records, April 2026). About 10% of kept records have a rating date before 2020.
- All types: 538,717 establishments. Kept: restaurant_cafe 125,336; pub_bar_club 45,562; takeaway 54,960 (225,858 in total, no duplicate FHRSIDs).
- Missing coordinates before filling: 24,632 (10.9%). Filled from NSPL by postcode: 17,451. Missing after filling: 7,181 (3.2%). 96.8% geocoded (pubs 99.3%, restaurants/cafés 96.1%, takeaways 96.4%).
- Almost all of the 7,181 unfilled records have no address or postcode at all. These are addresses the FSA withholds, mostly home-based caterers. Only 174 have a postcode that does not match. Withholding varies a great deal between authorities: Redbridge 31% unlocated, Havering 22%, and several others 19-21%.
- 99.75% of located records fall in the LA that most of their inspecting authority's records fall in.

## b. OpenStreetMap history (ohsome)

- Source: ohsome API v1, https://api.ohsome.org/v1/elements/bbox, time=2019-12-31 and 2022-12-31 (00:00 UTC). Filter `(amenity in (restaurant,cafe,bar,pub,nightclub,cinema,theatre,arts_centre,fast_food) or leisure=fitness_centre) and (geometry:point or geometry:polygon)`, properties tags and metadata, clipGeometry=false.
- Blocked or failed: https://api.ohsome.org/v1/elements/centroid and /v1/elements/geometry returned HTTP 403 Forbidden (Apache) on 29 Oct 2026, for both POST and GET. /elements/count and /elements/bbox still worked.
- The ohsome documentation (https://docs.ohsome.org/ohsome-api/v2/migration_guide.html) says v1 will be shut down on 30 November 2026. v2 (https://api.heigit.org/ohsome-api/v2-rc/) needs an API key, and getting one means signing up for an account, which was not done. To rerun after v1 closes: sign up for a free key at the link in the v2 docs, then port b1_osm_ohsome.py to the v2 extraction endpoint (JSON POST body, `aoi` in place of `bboxes`, key in the request).
- Geofabrik history files were not tried, because ohsome worked. Geofabrik's full-history files need an OSM login (https://osm-internal.download.geofabrik.de).
- Tiling: 0.5 degree tiles; 118 tiles contain at least one England and Wales postcode, times 2 snapshots = 236 requests, all HTTP 200, 3 s apart. Responses took 8-140 s each. Raw features: 119,206 (2019) and 139,831 (2022), de-duplicated by OSM id to 119,158 and 139,770.
- Counts, 2019 -> 2022: restaurant 24,271 -> 28,781; cafe 23,428 -> 29,070; fast_food 26,397 -> 33,766; pub 36,263 -> 36,662; bar 4,292 -> 5,374; nightclub 936 -> 963; cinema 648 -> 697; theatre 1,124 -> 1,287; arts_centre 415 -> 498; fitness_centre 1,384 -> 2,672 (counts before assignment).
- Geometry: 64% nodes, 35% ways, 0.2% relations (2019). No way or relation bounding box is more than 2 km across (one in 2022 is over 0.5 km), so the bbox-centre approximation is harmless. 33% (2019) and 46% (2022) of features carry an `fhrs:id` tag, which links them to FHRS.

## c. Assignment, counts and access

- MSOA: 2021 MSOA BFE V8 boundaries, point in polygon in BNG (ONS ArcGIS service Middle_layer_Super_Output_Areas_December_2021_Boundaries_EW_BFE_V8, generalised at 2 m). Points outside every polygon but within 500 m of one are snapped to the nearest; the rest are dropped.
- Centroids: MSOA_December_2021_EW_PWC_V2.
- Assigned: FHRS 218,674 of 225,858 (96.82%, 11 snapped). OSM 2019: 119,003 of 119,158 (99.87%). OSM 2022: 139,547 of 139,770 (99.84%). The unassigned OSM points lie in Scotland or the sea.
- Coverage: FHRS points fall in 7,259 of 7,264 MSOAs; OSM 2019 in 7,023 and 2022 in 7,096. All 318 LAs have data from each source. Coverage of small categories is thinner: in 2019, cinemas are present in 264 LAs, arts centres in 160 and fitness centres in 268.
- LA vintage: April 2023 LAD codes (318 in England and Wales, the Nomis TYPE424 set the pilot uses). They come from the NSPL Aug 2026 LAD26 field via the MSOA, since every 2021 MSOA nests in one LAD. The only differences are Barnsley E08000038 -> E08000016 and Sheffield E08000039 -> E08000019.
- Access indices: A_m = sum_j units_j exp(-d_mj / lambda) for lambda = 1, 1.5 and 3 km, from each 2021 MSOA population-weighted centroid. There are two versions:
  - `pt`: to the exact points, truncated at 30 km. Checked against brute force on 3 London MSOAs: matches to 4 significant figures.
  - `pwc`: units placed at their own MSOA's centroid, with own-MSOA units at d = 0, all 7,264 MSOAs as sources (pilot method).
  - The correlation of log pt with log pwc at 1.5 km is 0.90-0.99 by category. Pubs are lowest (0.90). `pt` totals are 89-95% of `pwc`, because own-MSOA points are no longer at zero distance.

## d. Validation against UK Business Counts (LA level, 318 LAs)

SIC 2007 subclass mapping (NM_141_1 local units, March of each year):

| New category | Business Counts counterpart |
|---|---|
| FHRS restaurant_cafe; OSM restaurant + cafe | 56101 licensed restaurants + 56102 unlicensed restaurants and cafés |
| OSM restaurant / cafe separately | 56101 / 56102 |
| FHRS takeaway; OSM fast_food | 56103 take-away food shops and mobile food stands |
| FHRS pub_bar_club; OSM pub + bar + nightclub | 56301 licensed clubs + 56302 public houses and bars |
| OSM pub / nightclub separately | 56302 / 56301 |
| OSM cinema | 59140 motion picture projection |
| OSM theatre + arts_centre ("arts_venue") | 90010 performing arts + 90040 operation of arts facilities |
| OSM fitness_centre | 93130 fitness facilities |

Pearson correlations against Business Counts 2019. Logs are log(1+x). Per-1k uses mid-2019 population, shown excluding City of London (with the City, the per-1k level correlations are 0.97-0.998 for every food and drink category because the City dominates them). Ratio = new total / Business Counts total.

| Category | Ratio | Levels | Logs | Per 1k (ex City) | Log per 1k (ex City) |
|---|---|---|---|---|---|
| FHRS restaurant_cafe | 2.07 | 0.966 | 0.962 | 0.963 | 0.880 |
| FHRS takeaway | 1.50 | 0.944 | 0.955 | 0.736 | 0.558 |
| FHRS pub_bar_club | 1.08 | 0.937 | 0.937 | 0.820 | 0.883 |
| OSM 2019 restaurant + cafe | 0.82 | 0.938 | 0.875 | 0.926 | 0.777 |
| OSM 2019 restaurant (56101) | 0.77 | 0.966 | 0.899 | 0.959 | 0.804 |
| OSM 2019 cafe (56102) | 0.88 | 0.857 | 0.782 | 0.785 | 0.628 |
| OSM 2019 fast_food | 0.75 | 0.802 | 0.753 | 0.338 | 0.146 |
| OSM 2019 pub + bar + nightclub | 0.98 | 0.966 | 0.939 | 0.864 | 0.880 |
| OSM 2019 pub (56302) | 1.02 | 0.963 | 0.942 | 0.900 | 0.900 |
| OSM 2019 nightclub (56301) | 0.14 | 0.528 | 0.518 | 0.280 | 0.171 |
| OSM 2019 cinema | 0.97 | 0.799 | 0.684 | 0.569 | 0.472 |
| OSM 2019 theatre + arts_centre | 0.15 | 0.749 | 0.630 | 0.750 | 0.442 |
| OSM 2019 fitness_centre | 0.33 | 0.651 | 0.511 | 0.312 | 0.209 |

Supplementary comparisons (full table in b1_validation_correlations_la.csv):
- FHRS against Business Counts 2026, the year closest to the snapshot: the takeaway per-1k correlation rises to 0.78 and log per-1k to 0.83.
- OSM 2022 against Business Counts 2022: fitness logs 0.65, per-1k 0.51; fast food per-1k 0.38; pubs/bars per-1k 0.94.
- FHRS by inspecting authority (records with withheld addresses included): correlations slightly lower than by location.

## Data-quality concerns

- FHRS restaurant_cafe is about twice Business Counts 56101+56102. FHRS counts premises, including canteens, clubs, church halls and home caterers. Business Counts counts VAT/PAYE local units, rounded.
- FHRS is a 2026 snapshot. Using it for 2019 assumes the 2019-2026 change was the same everywhere.
- FHRS withheld addresses (3.2% of records, up to 31% in Redbridge) make location-based counts too low in some authorities.
- OSM 2019 -> 2022 growth is largely mapping effort, not openings: fitness centres +93%, fast food +28%, cafés +24%, while pubs are +1%. OSM changes over time should not be read as amenity change without a completeness control.
- OSM completeness varies by place. The per-resident correlations for fast food (0.34), fitness (0.31) and nightclubs (0.28) are weak; restaurants (0.96) and pubs (0.90) are strong.
- OSM tagging gaps: theatre/arts_centre cover only about 15% of SIC 9001+9004 units, which are mostly companies rather than venues. Many gyms are tagged leisure=sports_centre with sport=fitness and are missed.
- The cinema SIC class is small (665 units) and multiplex-heavy; correlations are noisy.
- Polygon points are bounding-box centres, not true centroids (the centroid endpoint was blocked).

## Judgement calls

- The FHRS English-language XML open data files are used in place of paging the API, since they give the same records in fewer, larger requests.
- Only the three named FHRS business types are kept; "Other catering premises", "Mobile caterer" and hotels are left out but counted in fhrs_business_type_counts_ew.csv.
- FHRS coordinates outside a 49.8-56.0 N, 6.5 W-2.0 E box were treated as missing (none or almost none were).
- Missing FHRS coordinates are filled by exact postcode from NSPL Aug 2026, preferring live postcodes and falling back to terminated ones.
- FHRS records with no address are not geocoded and are kept in the point file without coordinates.
- amenity=fast_food is added to the OSM filter, so there is an OSM counterpart to FHRS takeaways and SIC 56103.
- Because the centroid and geometry endpoints returned 403, ohsome /elements/bbox is used, with the bounding-box centre taken as the point for ways and relations. That endpoint is openly served; no authentication or bot check was involved.
- OSM nodes, closed ways and multipolygon relations are counted (geometry:point or geometry:polygon); unclosed ways were left out.
- The OSM snapshot timestamps are 00:00 UTC on 31 Dec 2019 and 31 Dec 2022.
- Where an OSM feature has both an amenity and leisure=fitness_centre, it is classified by its amenity tag.
- The two OSM snapshots were run as two concurrent processes, so there were at most two simultaneous requests. One process crashed on a file-lock clash on a tile both were writing; the other completed every tile, and nothing was lost.
- 2021 MSOA BFE (full extent) boundaries are used in place of BFC, so riverside and coastal venues fall inside an MSOA, and points within 500 m of an MSOA are snapped to the nearest one.
- LA is taken from the MSOA, not from the FHRS inspecting authority. Inspecting-authority counts are given as an alternative.
- LAs are reported on 2023 codes (pilot vintage), with the two 2024 code changes for Barnsley and Sheffield recoded back.
- Access is computed to the exact points (`pt`) and also as the pilot-style MSOA-centroid version (`pwc`). The `pt` sum is truncated at 30 km.
- Grouping for access indices: restaurant + cafe, pub + bar + nightclub, theatre + arts_centre.
- Business Counts match for restaurants is 56101+56102, leaving out 56210 (event catering) and 56290 (other food service, which includes canteens).
- Arts venues are matched to 90010+90040, leaving out 90020 and 90030 (support activities and artistic creation, which are rarely venues).
- Mid-2019 population is used for per-1k measures (mid-2022 for the 2022 comparisons), and Census 2021 residents at MSOA level.
- The per-1k log correlations use log(per1k + 0.01) to keep zeros. City of London is reported both with and without, because it dominates per-resident levels.
- No regressions were run.
