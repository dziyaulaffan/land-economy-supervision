# B4 Local COVID-19 restrictions affecting hospitality, England and Wales, 1 March 2020 to 31 December 2021

Data assembly only. No regressions were run.

## 1. What was produced

| File (extension/data/clean/) | Rows | Content |
|---|---|---|
| `b4_restrictions_daily_lad23.csv` | 213,378 (318 LAs x 671 days) | Main panel. One row per 2023 LAD per day: restriction `state`, `tier`, `hosp_intensity` (0-1), eight component flags, `local_share`, `partial_local_measure`, `n_pred`, `predecessors_differ`, `source` (SI reference) |
| `b4_restrictions_quarterly_lad23.csv` | 2,544 (318 x 8 quarters) | `hosp_intensity_q` = mean daily intensity over the calendar quarter, 2020Q1-2021Q4; also `hosp_intensity_panel_days`, `days_full_closure`, `days_any_restriction`, day counts |
| `b4_restrictions_daily_ltla20.csv.gz` | 225,456 (336 x 671) | The same panel on the 2020 LTLA geography on which the regulations were written (used for verification) |
| `b4_legal_areas.csv` | 16,056 | Every (date, local measure, 2020 LTLA) read from the regulations, with population share covered and SI |
| `b4_ltla20_to_lad23.csv` | 336 | 2020 LTLA to 2023 LAD lookup with population weights |
| `b4_validation_summary.csv` | 59 checks | All checks in section 7 (all pass) |
| `b4_validation_tier_mismatches.csv` | 4 | The only tier disagreements with compiled sources, all explained in section 7 |

Scripts (extension/scripts/, run in order): `b4_01_fetch_legislation.py`, `b4_02_fetch_compiled.py`,
`b4_03_parse_legislation.py`, `b4_04_build_panel.py`, `b4_05_validate.py`; shared helpers in `b4_common.py`.
Raw downloads: `C:\Users\dziya\research-data\london-variety-extension\raw\restrictions\`.

## 2. Sources checked

| Source | URL | What it covers | Used for |
|---|---|---|---|
| UK coronavirus dashboard API, metric `alertLevel` | https://api.coronavirus.data.gov.uk/v2/data?areaType=ltla&metric=alertLevel | Tier by LTLA from 14 Oct 2020 | **Not usable.** The API host no longer resolves (dashboard decommissioned). The Wayback Machine holds one archived UTLA call (11 May 2021, `raw/restrictions/wayback/utla_alertlevel_20210511.csv`) but its `alertLevel` column is empty for every row. No LTLA call is archived (CDX search on `api.coronavirus.data.gov.uk/*` filtered on `alertLevel`). Manual route if wanted: the UKHSA archive page https://ukhsa-dashboard.data.gov.uk/covid-19-archive-data-download, which I did not find to carry alert levels. |
| OxCGRT, subnational | https://github.com/OxCGRT/covid-policy-dataset (`data/OxCGRT_compact_subnational_v1.csv`) | UK nations only (England, Wales, Scotland, NI); no local authority detail and no hospitality-specific indicator | Nation-level sanity check only (check 8). The old repo `OxCGRT/UK-covid-policy-tracker` no longer exists. |
| Institute for Government timeline | https://www.instituteforgovernment.org.uk/data-visualisation/timeline-coronavirus-lockdowns | Narrative timeline Mar 2020 - Dec 2021, no LA breakdown, no data file (PDF only) | Not used as data. |
| House of Commons Library local restrictions table, as mirrored by ODI Leeds | https://github.com/odileeds/covid-19/blob/main/LocalAuthorities/data/commonslibrary-coronavirus-restrictions-data.csv | Snapshot of restrictions by LA. The git history holds 23 versions, 7 Oct 2020 - 21 Dec 2020 (extracted to `raw/restrictions/odileeds/snapshots/`) | Verification of tiers and of local measures on 7 Oct 2020 (checks 4, 6) |
| Gibbs, Jarvis & Eggo (LSHTM), `uk_tier_data` v0.0.2, Zenodo 4421649 | https://zenodo.org/records/4421649 | Daily scrapes of the Commons Library table and the Wikipedia tier table, 25 Oct - 29 Nov 2020 | Verification of October tiers (check 5) |
| Abel & Siraj, "Covid-19 UK government, winter 2020, Tiered restrictions data", Zenodo 8191880 (CC-BY 4.0) | https://zenodo.org/records/8191880 | Tier by LTLA by day, 2 Dec 2020 - 5 Jan 2021 (dashboard LTLA geography, 315 areas) | Verification of December tiers (check 3). The linked GitHub repo (github.com/allocatrix/DRSA_Covid19, formerly prioritization/DRSA_Covid19) holds only a README. |
| legislation.gov.uk, made and point-in-time (revised) texts | https://www.legislation.gov.uk/ (paths below) | The regulations themselves, with the area schedules in force on each date | **Primary source for the panel** |
| ONS LTLA (Dec 2020) to UTLA lookup | https://services1.arcgis.com/ESMARspQHYMw9BZ9/arcgis/rest/services/LTLA20_UTLA20_EW_LU_3791afa41dcc4daeab025767e16fcb93/FeatureServer/0 | 336 LTLAs, county membership | Expanding county councils in schedules to districts |
| ONS ward (Dec 2020) to LAD lookup | services1.arcgis.com/.../WD20_LAD20_CTY20_OTH_UK_LU_v2_.../FeatureServer/0 | Wards of 7 LAs with ward-defined areas | Partial-area population shares |
| ONS mid-2019 ward population estimates | https://www.nomisweb.co.uk/api/v01/dataset/NM_2010_1 (geography TYPE395) | 2019 wards, E&W | Partial-area population shares |
| ONS 2018-based subnational population projections (ODI Leeds copy, `LocalAuthorities/data/populations.csv`) | same GitHub repo | 2020 projected population by (pre-2019) English district | Weights for 2023 mergers; population-by-tier check. Nomis mid-2020 estimates were tried first but return blank values for English districts at the 2019/2021 geographies. |

**Conclusion on "verified compiled dataset":** no single compiled dataset covers all of England and Wales,
by LA and day, for 2020-21. The compiled sources cover only Oct-Dec 2020 tiers in England (and one snapshot of
local measures on 7 Oct 2020). So the panel is **constructed from the regulations** for the whole period, and the
compiled datasets are used to verify it where they overlap (section 7). The agreement is complete apart from four
explained cases, so for the tier period the panel and the compiled datasets corroborate each other.

## 3. Construction

### 3.1 Day rule
A day takes the state in force at the end of that day (23:59). Measures starting in the evening (Welsh firebreak
6pm 23 Oct 2020; Welsh 6pm-closing rule 6pm 4 Dec 2020; Caerphilly 6pm 8 Sep 2020) therefore count from that day;
measures starting at 00:01 count from that day.

### 3.2 Local areas read from the regulations (script b4_03)
Point-in-time texts were downloaded for every day of each tier period and for every coming-into-force date of the
local regulations, so all amendments are included without reading each amending SI by hand.

| Measure | Regulation (legislation.gov.uk path) | Dates read | Notes |
|---|---|---|---|
| October tiers: High (Tier 2) | uksi/2020/1104, Schedule 2, point in time each day | 14 Oct - 4 Nov 2020 | Medium (Tier 1, uksi/2020/1103) is every other English area |
| October tiers: Very High (Tier 3) | uksi/2020/1105, Schedule 2 (Schedule 2A local closures checked: betting, casinos, soft play etc., no hospitality) | 14 Oct - 4 Nov 2020 | Amended by 2020/1128, 1131, 1154, 1176, 1183, 1189, 1192 |
| December tiers 2, 3, 4 | uksi/2020/1374, Schedule 4, point in time each day | 2 Dec 2020 - 5 Jan 2021 | Tier 1 is every other area. Amended by 2020/1533 (16 Dec), 1572 (19 Dec), 1611 (20 Dec, Tier 4), 1646 (26 Dec), 1654 (31 Dec) |
| Leicester lockdown, hospitality closed | uksi/2020/685 (as amended by 2020/754, 787, 823) | 4 Jul - 2 Aug 2020 | Protected area 4-17 Jul defined by postcodes (Leicester, Oadby and Wigston, fringes of Blaby and Charnwood); 18 Jul: Leicester and Oadby and Wigston; 1 Aug: Leicester only; revoked 3 Aug |
| Leicester (No. 2): gatherings ban in private dwellings | uksi/2020/824 (+875, 987, 1019) | 3 Aug - 13 Oct 2020 | Oadby and Wigston added 22 Sep (SI 2020/1019) |
| Blackburn with Darwen and Luton | uksi/2020/800 | 25-31 Jul 2020 | Leisure closures and >30 gatherings only; no hospitality or household rule, so coded at the national level |
| Blackburn with Darwen and Bradford | uksi/2020/822 (+898, 930, 935) | 1 Aug - 21 Sep 2020 | Private-dwelling gatherings ban; ward-only areas from 26 Aug (BwD) and 2 Sep (Bradford); revoked 22 Sep (areas moved to 2020/828 and 2020/1010) |
| North of England gatherings ban | uksi/2020/828 (+846, 865, 897, 931, 954, 1019, 1041, 1057, 1074) | 5 Aug - 13 Oct 2020 | Greater Manchester, East Lancashire, West Yorkshire; Calderdale and Kirklees ward-only 2-21 Sep; from 30 Sep (SI 2020/1057) the ban covers all indoor places, including hospitality |
| Bolton, hospitality takeaway only, 22:00-05:00 closure | uksi/2020/974 (+1029, 1041) | 10 Sep - 2 Oct 2020 | Revoked 3 Oct (SI 2020/1074), Bolton moved into 2020/828 |
| Birmingham, Sandwell and Solihull (+ Wolverhampton from 22 Sep) | uksi/2020/988 (+1019) | 15 Sep - 13 Oct 2020 | Private-dwelling gatherings ban |
| North East (from 22 Sep "North East and North West") | uksi/2020/1010 (+1012, 1019, 1041, 1057, 1074) | 18 Sep - 13 Oct 2020 | Gatherings ban plus 22:00 closure and table service (from 18 Sep, before the national rule); NW areas 22-29 Sep, Liverpool City Region, Warrington, Hartlepool, Middlesbrough from 3 Oct |
| Welsh local health protection areas | wsi/2020/725, Schedule 4A, point in time each day | 8 Sep - 22 Oct 2020 | Caerphilly 8 Sep (6pm); RCT 17 Sep; Blaenau Gwent, Bridgend, Merthyr, Newport 22 Sep; Llanelli (electoral divisions of Carmarthenshire) 26 Sep; Cardiff, Swansea 27 Sep; NPT, Torfaen, Vale of Glamorgan 28 Sep; Conwy, Denbighshire, Flintshire, Wrexham 1 Oct; Bangor (divisions of Gwynedd) 10 Oct. Superseded by the firebreak |

URL pattern: made text `https://www.legislation.gov.uk/<type>/<year>/<number>/made/data.xml`; point in time
`https://www.legislation.gov.uk/<type>/<year>/<number>[/schedule/<n>]/<YYYY-MM-DD>/data.xml`.

### 3.3 National timelines (dates from the coming-into-force provisions)

England (`uksi`):

| From | State | Hospitality | Regulation |
|---|---|---|---|
| 1 Mar 2020 | E_open | open | - |
| 21 Mar 2020 | E_lockdown1 | closed (takeaway only) | 2020/327 Business Closure (2pm 21 Mar); 2020/350 |
| 4 Jul 2020 | E_reopened | open, guidance only | 2020/684 (00:01 4 Jul) |
| 14 Sep 2020 | E_rule_of_six | open, legal group limit of six | 2020/986 |
| 24 Sep 2020 | E_curfew | 22:00 closure, table service | 2020/1029 (05:00 24 Sep); 2020/1008, 1046 |
| 14 Oct 2020 | tiers (Medium by default) | see coding | 2020/1103-1105 |
| 5 Nov 2020 | E_lockdown2 | closed | 2020/1200 |
| 2 Dec 2020 | tiers (Tier 1 by default) | see coding | 2020/1374 |
| 6 Jan 2021 | E_lockdown3 | closed (Tier 4 applied to all England, coded tier 4) | 2021/8 |
| 29 Mar 2021 | E_step1 | closed | 2021/364 Steps, Schedule 4 Step 1 area = all England |
| 12 Apr 2021 | E_step2 | outdoor only | 2021/364 Schedule 4, Step 2 area = all England from 12 Apr (point-in-time check) |
| 17 May 2021 | E_step3 | indoor open, table service, rule of six / two households | 2021/585 |
| 19 Jul 2021 | E_step4 | open | 2021/848 revoked the Steps Regulations at 23:55 on 18 Jul |

Wales (`wsi`):

| From | State | Hospitality | Regulation |
|---|---|---|---|
| 1 Mar 2020 | W_open | open | - |
| 21 Mar 2020 | W_lockdown1 | closed | 2020/326 Business Closure; 2020/353 |
| 13 Jul 2020 | W_outdoor_hospitality | outdoor only | 2020/725 (No. 2), "all other purposes" from 13 Jul |
| 3 Aug 2020 | W_indoor_reopened | indoor open; indoor gathering only within an extended household (law) | 2020/820 |
| 24 Sep 2020 | W_curfew | seated service, 22:00 close | 2020/1035 (6pm 24 Sep) |
| 23 Oct 2020 | W_firebreak | closed | 2020/1149 (6pm 23 Oct to end of 8 Nov) |
| 9 Nov 2020 | W_post_firebreak | alcohol sales end 22:00, premises close by 22:20 (reg 20) | 2020/1219 |
| 4 Dec 2020 | W_6pm_no_alcohol | close 18:00-06:00, no alcohol | 2020/1409 (6pm 4 Dec) |
| 20 Dec 2020 | W_alert4 | closed | 2020/1609 as amended by 2020/1610 (Alert Level 4 from 20 Dec) |
| 26 Apr 2021 | W_outdoor_hospitality | outdoor only | 2021/502 (6am 26 Apr) |
| 17 May 2021 | W_alert2_1 | indoor open; meeting away from homes limited to six people (group limit) | 2021/583 (Level 2); 2021/668 (Level 1, 7 Jun); 2021/862 (17 Jul) |
| 7 Aug 2021 | W_alert0 | open | 2021/925 (6am 7 Aug, no alert level) |
| 26 Dec 2021 | W_alert2 | groups of six, 2 m distancing, specific measures on licensed premises (new reg 16ZA) | 2021/1485 (6am 26 Dec) |

## 4. Hospitality closure intensity: coding rule

The intensity is computed from eight flags (`indoor_closed`, `outdoor_closed`, `meal_req`, `mix_ban`,
`early_close_no_alcohol`, `curfew`, `table_service`, `group_limit`), which are kept in the panel so the index can
be recoded.

| Value | Rule | Periods | Justification |
|---|---|---|---|
| 1.00 | indoor and outdoor hospitality closed (takeaway / delivery only) | national lockdowns; Leicester 4 Jul - 2 Aug 2020 (and Oadby and Wigston to 31 Jul); Bolton 10 Sep - 2 Oct 2020; Welsh firebreak; Dec Tier 3 and 4; Wales Alert Level 4; England Step 1 | No on-premises trade at all |
| 0.75 | indoor closed, outdoor service allowed | England 12 Apr - 16 May 2021; Wales 13 Jul - 2 Aug 2020 and 26 Apr - 16 May 2021 | Trade limited to outdoor space and weather; most covers lost |
| 0.50 | open, but with a legal ban on indoor mixing between households, or a substantial-meal requirement for alcohol (wet-led pubs closed), or 18:00 closing with no alcohol | Oct High and Very High; Dec Tier 2; English local gatherings bans Aug - Oct 2020; Welsh local health protection areas; Wales 4 - 19 Dec 2020 | Venues may open but a large share of normal custom (groups across households, drinking-led visits, evenings) is removed |
| 0.25 | open with a curfew / early closing, compulsory table service, or a legal group-size limit | England 14 Sep - 13 Oct 2020 (outside local areas), Oct Medium, Dec Tier 1, England 17 May - 18 Jul 2021; Wales 3 Aug - 22 Oct 2020 (outside local areas), 9 Nov - 3 Dec 2020, 17 May - 6 Aug 2021, 26 - 31 Dec 2021 | Restricts how and when people are served, not whether they can come |
| 0.00 | open, no hospitality-specific legal restriction | England 1 - 20 Mar 2020, 4 Jul - 13 Sep 2020, from 19 Jul 2021; Wales 1 - 20 Mar 2020, from 7 Aug to 25 Dec 2021 | Guidance only (e.g. the PM's advice of 16 Mar 2020 to avoid pubs, or England Plan B in December 2021, which affected nightclubs only) |

Where several measures apply, the flags are combined and the highest level applies. Where a local measure covered
only listed wards / electoral divisions, the LA value is the population-weighted mix of the local level and the
surrounding level (`local_share` gives the covered share; `partial_local_measure` names the measure), and `state`
shows the measure covering the majority.

## 5. Geography (2020 LTLA to 2023 LAD)

The regulations name councils as they were in 2020-21. County councils in the schedules are expanded to their
districts using the ONS LTLA20-UTLA20 lookup. The panel is built on the 336 LTLAs of December 2020 (England 314,
Wales 22) and aggregated to the 318 LADs of 2023:

- North Northamptonshire E06000061 = Corby, East Northamptonshire, Kettering, Wellingborough; West Northamptonshire
  E06000062 = Daventry, Northampton, South Northamptonshire (April 2021).
- Cumberland E06000063 = Allerdale, Carlisle, Copeland; Westmorland and Furness E06000064 = Barrow-in-Furness,
  Eden, South Lakeland (April 2023).
- North Yorkshire E06000065 = Craven, Hambleton, Harrogate, Richmondshire, Ryedale, Scarborough, Selby (April 2023).
- Somerset E06000066 = Mendip, Sedgemoor, South Somerset, Somerset West and Taunton (April 2023).
- Buckinghamshire E06000060 was already a unitary authority in April 2020, so there is nothing to map for it.
- Wales: no changes.

Merged LADs take the 2020-population-weighted mean of the intensity and flags of their predecessors. `state`,
`tier` and `source` are those of the largest predecessor; `predecessors_differ` = 1 marks days when the
predecessors differed. This happens only 17 Oct - 4 Nov 2020 in Westmorland and Furness (Barrow-in-Furness in High
from 17 Oct) and 31 Oct - 4 Nov 2020 in Cumberland (Carlisle in High from 31 Oct). Weights: ONS 2018-based SNPP 2020
projection; the projections are on pre-2019 districts, so Somerset West and Taunton = Taunton Deane + West Somerset
(and similarly for Bucks, BCP, Dorset, East and West Suffolk where population is needed for the tier check).

## 6. Judgement calls

1. **Legal measures only.** Coding follows what the regulations required, not guidance. Examples: England 4 Jul -
   13 Sep 2020 is 0 although guidance limited indoor mixing to two households; the voluntary pub avoidance of
   16-20 Mar 2020 is 0.
2. **Start of the first lockdown** is 21 Mar 2020 (hospitality closure in force 2pm 21 Mar in England and Wales),
   not 23 Mar (stay-at-home announcement) or 26 Mar (Restrictions Regulations). Pubs were asked to close on the
   evening of 20 Mar, but the closure became law only the next day, so 20 Mar is coded 0.
3. **Private-dwelling gatherings bans count as 0.5.** The task's rule puts "household mixing ban indoors" at 0.5.
   The English local bans of Aug - Sep 2020 (SIs 822, 824, 828, 988, 1010) and the Leicester (No. 2) ban applied in
   law to private dwellings; hospitality was covered by guidance until 30 Sep 2020, when SI 2020/1057 extended the
   ban to all indoor places in the North of England, North East and North West areas. I code all of them 0.5, as
   the rule says. The Birmingham, Sandwell, Solihull, Wolverhampton and Leicester bans stayed private-dwelling-only
   in law. Anyone wanting the stricter reading can recode with `mix_ban` and the source column (0.25 instead).
4. **October Very High = 0.5**, the same as High. It had both a substantial-meal requirement and the mixing ban,
   so it is more restrictive than High. I kept the five-level scale as stated rather than inventing an extra step;
   `meal_req` separates the two.
5. **Wales extended households (3 Aug - 13 Sep 2020) = 0.25**: indoor gatherings were legally limited to an
   extended household of up to four households. That is a group limit, not a ban on mixing; the local health
   protection areas, which removed extended households, are 0.5.
6. **Rule of six = 0.25** (14 Sep 2020 in England). It is a legal group limit that applied in pubs and restaurants.
7. **Wales 4-19 Dec 2020 (18:00 closing, no alcohol) = 0.5**: venues could open, but evening and drinking trade was
   removed, which I judged closest to the substantial-meal level.
8. **Partial areas.** The Leicester postcode area (4-17 Jul 2020) included suburban fringes of Blaby and Charnwood.
   The postcode lists were not converted to population, so those two LAs are not coded as covered (they stay at the
   national level, which was 1 until 3 Jul and 0 afterwards). All ward / electoral-division areas are weighted by
   mid-2019 ward population: Blackburn with Darwen 49% (26 Aug - 21 Sep), Bradford 77% then 74% (2 Sep - 21 Sep),
   Calderdale 50% and Kirklees 23% (2 - 21 Sep), High Peak (Glossop wards) 36% (14 - 30 Oct, Tier 2), Llanelli 30%
   of Carmarthenshire, Bangor 12% of Gwynedd.
9. **January to March 2021 England** is coded tier 4 in the `tier` column because SI 2021/8 applied the Tier 4
   rules to all of England (the "third lockdown" was legally Tier 4 everywhere).
10. **Christmas relaxations** (25 Dec 2020 bubbles) did not change hospitality rules and are ignored.
11. **2020Q1 quarterly mean** is over the full calendar quarter, counting 1 Jan - 29 Feb 2020 as 0 (no restrictions
    existed). `hosp_intensity_panel_days` gives the mean over the panel days only (March).
12. **Welsh alert levels 2 and 1 (17 May - 6 Aug 2021)** are both 0.25: indoor hospitality open, with a legal limit
    of six people meeting away from homes; level 1 relaxed private-home rules but not that limit. Whether table
    service was required at these levels was not checked clause by clause; the 0.25 rests on the group limit.
13. Nightclubs, covid passes and face coverings are not part of the index (it measures restaurants, pubs, bars and
    cafes).

## 7. Validation (b4_05; all 59 checks pass)

1. **National lockdowns:** every LA has intensity 1 on 15 Apr 2020 (E, W), 15 Nov 2020 (E), 30 Oct 2020 (W,
   firebreak), 20 Jan, 15 Feb and 1 Apr 2021 (E, W). On 15 Aug 2021 every LA is 0 in both nations.
2. **Leicester spike:** mean intensity 4-31 Jul 2020 is 1 in Leicester and Oadby and Wigston and 0 in every other
   English LA. In 2020Q3 Leicester has the highest quarterly intensity in England (0.68), then Bolton (0.46),
   Oadby and Wigston (0.41).
3. **Abel & Siraj (Zenodo 8191880):** 10,920 LTLA-days, 2 Dec 2020 - 5 Jan 2021, same tier on 100%. (Before
   aligning geography there were 11 disagreements, all the Isles of Scilly 26 Dec - 5 Jan: Abel & Siraj merge it with
   Cornwall; the regulations and contemporary reports keep Scilly in Tier 1 when Cornwall moved to Tier 2 and
   then 3.) Abel & Siraj still use the four pre-2020 Buckinghamshire district codes; these were mapped to E06000060.
4. **Commons Library table (ODI Leeds snapshots):** 13 snapshots, 14 Oct - 21 Dec 2020, 69 to 314 English LAs each:
   100% agreement except Carlisle on 31 Oct 2020.
5. **Gibbs et al. daily scrapes:** 25 Oct - 2 Nov 2020, 100% except Carlisle 31 Oct - 2 Nov. **Carlisle:**
   SI 2020/1192 put Carlisle in High from 31 Oct 2020; the Commons Library table had not caught up. The panel
   follows the regulation.
6. **Local measures on 7 Oct 2020:** the set of English LAs with a household-mixing ban and Welsh local health
   protection areas in the Commons Library snapshot (50 English and 16 Welsh areas; Llanelli matched to
   Carmarthenshire as a partial area) is identical to the panel's set.
7. **Published counts:** population on 2 Dec 2020 (2018-based SNPP for 2020): Tier 3 23.5m against 23.3m
   published (PA, 26 Nov 2020), Tier 2 32.5m against 32.2m, Tier 1 0.72m against 0.714m (Cornwall, Isle of Wight,
   Isles of Scilly). 119 LTLAs in Tier 3 on 2 Dec 2020, as in Abel & Siraj. Tier 4 on 31 Dec 2020: 44.4m against
   "44 million, 78%" published (PA, 30 Dec 2020); Isles of Scilly the only Tier 1 area, as reported. Sources:
   https://www.expressandstar.com/news/health/swathes-of-england-to-face-toughest-tier-3-coronavirus-curbs-6005592
   and https://expressandstar.com/news/uk-news/2020/12/30/at-a-glance-guide-to-tier-changes-in-england.
8. **OxCGRT (nation level):** workplace closing (C2M) = 3 on every national-lockdown check date in the relevant
   nation, 0 on 15 Aug 2021. On 30 Oct 2020 England shows 2 (tiers) and Wales 3 (firebreak), consistent with the
   panel.

Not compiled-dataset verified: July - October 2020 English local measures other than on 7 Oct, the Welsh national
timeline, and 2021. For these the regulations are the only source used (texts downloaded and cited); the panel's
dates were read from the coming-into-force clauses.

## 8. Gaps and cautions

- Intensity is a coding of legal restrictions, not of actual trading. Voluntary closures, reduced demand and
  local enforcement are not measured.
- The scale is ordinal; the 0.25 steps are a convention, not an estimate of lost trade.
- Partial-area weights use 2019 ward populations and 2020 ward boundaries; a few ward names were matched by
  normalised name. Blaby and Charnwood fringe areas (4-17 Jul 2020) are not coded.
- England Steps 2021 were national: the Steps Regulations' Schedule 4 put all of England in one step on every date
  checked. The local "variant" advice of May-June 2021 (for example Bolton, Bedford) was guidance and is not coded.
- The archived dashboard `alertLevel` data, which would have been an independent source for Oct 2020 - Mar 2021,
  is not recoverable from the Wayback copy checked.
