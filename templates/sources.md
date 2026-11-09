# Sources

Every dataset is public and downloaded by a script. Raw downloads (about 2.5 GB) are kept outside the repository, and the cleaned files are in `london-variety/data/clean/` and `london-variety/extension/data/clean/`. Full detail on each source, including manual steps and failed downloads, is in [`london-variety/DATA_INVENTORY.md`](../london-variety/DATA_INVENTORY.md) for London and [`london-variety/extension/EXTENSION_NOTES.md`](../london-variety/extension/EXTENSION_NOTES.md) for England and Wales.

## Internal migration

- Provider and URL: ONS, Internal migration in England and Wales, detailed estimates by origin, destination and single year of age, https://www.ons.gov.uk/peoplepopulationandcommunity/populationandmigration/populationestimates/datasets/internalmigrationinenglandandwales
- Version / dates: Years ending June 2015 to 2025, on 2023 local authority boundaries
- Download steps: `london-variety/scripts/10_migration.py` and `london-variety/extension/scripts/b3_migration.py`
- Coverage and unit of observation: Moves between local authorities by age and year
- Variables and units: Inflows, outflows and net flows, expressed per 1,000 mid-2019 residents of the age group
- Access / reuse terms: Open Government Licence

## Hospitality and leisure units

- Provider and URL: ONS UK Business Counts, local units by SIC subclass, via Nomis (dataset NM_141_1), https://www.nomisweb.co.uk
- Version / dates: March 2019
- Download steps: `london-variety/scripts/40_amenity_density.py` and `london-variety/extension/scripts/b1_ukbc_download.py`
- Coverage and unit of observation: Local units in SIC divisions 55, 56 and 90 to 93, by borough, district and MSOA
- Variables and units: Units per 1,000 residents, entered as a standardised logarithm
- Access / reuse terms: Open Government Licence

## Food venues

- Provider and URL: Food Standards Agency, Food Hygiene Rating Scheme open data, https://ratings.food.gov.uk/open-data
- Version / dates: Register as held on 29 October 2026, the only version the FSA serves
- Download steps: `london-variety/extension/scripts/b1_fhrs_download.py`, then `b1_fhrs_clean.py` and `b1_assign_access.py`
- Coverage and unit of observation: 225,858 restaurants, cafes, takeaways and pubs, 96.8 per cent geocoded
- Variables and units: Distance-weighted access index for each MSOA, exp(-d/1.5) with d in kilometres
- Access / reuse terms: Open Government Licence

## Cinemas, theatres, gyms and nightclubs

- Provider and URL: OpenStreetMap, through the ohsome API, https://api.ohsome.org
- Version / dates: Snapshots at 31 December 2019 and 31 December 2022
- Download steps: `london-variety/extension/scripts/b1_osm_ohsome.py`
- Coverage and unit of observation: Points for England and Wales
- Variables and units: Access index by venue type, as for food venues
- Access / reuse terms: Open Database Licence, © OpenStreetMap contributors

## Population

- Provider and URL: ONS mid-year population estimates and small area population estimates (2021 based), via Nomis, https://www.nomisweb.co.uk
- Version / dates: Districts mid-2011 to mid-2025; MSOAs mid-2011 to mid-2024
- Download steps: `london-variety/extension/recovery/scripts/r1_population.py`
- Coverage and unit of observation: Single year of age by district and MSOA
- Variables and units: Persons, used in logs for the recovery design
- Access / reuse terms: Open Government Licence

## Census migration

- Provider and URL: 2001, 2011 and 2021 Censuses, address one year before the census, via Nomis and the UK Data Service WICID, https://wicid.ukdataservice.ac.uk/
- Version / dates: Census days in 2001, 2011 and 2021
- Download steps: `london-variety/extension/scripts/b2_download_census_migration.py` and `s4_download_census.py`
- Coverage and unit of observation: Inflows by age band and MSOA
- Variables and units: Movers per 1,000 residents of the age band
- Access / reuse terms: Open Government Licence

## Closure rules

- Provider and URL: Coronavirus regulations for England and Wales, https://www.legislation.gov.uk/
- Version / dates: 1 March 2020 to 31 December 2021, 367 regulation texts
- Download steps: `london-variety/extension/scripts/b4_01_fetch_legislation.py` to `b4_05_validate.py`, and `london-variety/extension/venue_mix/scripts/v1_closure_calendar.py`
- Coverage and unit of observation: District by day, and seven venue types coded from 42 rules
- Variables and units: 1 for closure to the public, 0.5 for partial closure, 0 for opening
- Access / reuse terms: Open Government Licence

## Case rates and mobility

- Provider and URL: UK Health Security Agency COVID-19 dashboard archive, https://ukhsa-dashboard.data.gov.uk/covid-19-archive-data-download, and Google COVID-19 Community Mobility Reports, https://www.gstatic.com/covid19/mobility/Region_Mobility_Report_CSVs.zip
- Version / dates: 2020 to 2022
- Download steps: `london-variety/extension/scripts/s3_download_cases.py` and `b3_mobility.py`
- Coverage and unit of observation: Lower-tier local authority by day or week
- Variables and units: Cases per 100,000; percentage change in visits from the January 2020 baseline
- Access / reuse terms: Open Government Licence; Google terms of service

## Controls and jobs

- Provider and URL: 2011 and 2021 Census tables, ONS access to gardens (April 2020), ONS homeworking score (July 2020), ONS Business Register and Employment Survey, mostly via Nomis
- Version / dates: 2011, 2019, 2020 and 2021
- Download steps: `london-variety/scripts/70_controls.py` and `london-variety/extension/scripts/s1_download.py`
- Coverage and unit of observation: Borough, district and MSOA
- Variables and units: Shares of addresses with private outdoor space, of workers in occupations that can be done from home, of flats, private renters and students; jobs and residents per square kilometre
- Access / reuse terms: Open Government Licence
