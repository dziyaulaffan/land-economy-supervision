# Outputs

| File | Description | Created by |
| --- | --- | --- |
| [`Paper7_Supo3.pdf`](../london-variety/outputs/supervision/Paper7_Supo3.pdf) | Supervision summary, eight pages | `Paper7_Supo3.tex`, compiled with pdflatex |
| [`report.pdf`](../london-variety/outputs/report/report.pdf) | Full research report, 26 pages | `scripts/99_report.py`, then pdflatex |
| [`brief.md`](../london-variety/outputs/report/brief.md) | Two-page research brief | Written from the notes files |
| `outputs/event_study/preperiod_check.csv` | London triple-difference coefficients, Figure 1a and Table 2 | `scripts/97_preperiod_check.py` |
| `extension/data/clean/s2_national_ddd.csv` | Registered national triple difference, Figure 1b and Table 2 | `extension/scripts/s2_national_ddd.py` |
| `extension/data/clean/s8_urban_ddd.csv` | National triple difference with access to food venues, Figure 1b and Table 2 | `extension/scripts/s8_urban_measures.py` |
| `extension/data/clean/s8b_density_check.csv` | Access with job and resident density held fixed, Table 2 | `extension/scripts/s8b_density_check.py` |
| `extension/data/clean/s8d_pretrend_check.csv` | Deviations from the pre-2020 trend, Table 2 | `extension/scripts/s8d_pretrend_check.py` |
| `extension/data/clean/s3_tier_design.csv`, `s4_census_msoa.csv`, `s5_national_rents.csv` | Tier, Census and rent designs, Tables 3 and 4 | `extension/scripts/s3_tier_design.py`, `s4_census_msoa.py`, `s5_national_rents.py` |
| `extension/venue_mix/data/v1_regulation_calendar.csv` | Closure calendar for seven venue types | `extension/venue_mix/scripts/v1_closure_calendar.py` |
| `extension/venue_mix/data/v5_main.csv` to `v8_robustness.csv` | Venue-mix design, Tables 3 and 4 | `extension/venue_mix/scripts/v5_main.py` to `v8_robustness.py` |
| `extension/recovery/data/r4_estimation.csv`, `r5_heterogeneity.csv`, `r6_placebos.csv` | Recovery coefficients, Figure 2 and Table 4 | `extension/recovery/scripts/r4_estimation.py` to `r6_placebos.py` |
| `outputs/event_study/*.png` | Event-study charts for London migration, rents and house prices | `scripts/90_event_study_plots.py` and the estimation scripts |

Paths without a link are relative to `london-variety/`. Most estimation `.csv` files in the extension folders have a `.md` file of the same name with the table in readable form.
