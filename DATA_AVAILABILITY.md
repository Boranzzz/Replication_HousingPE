# Data availability

The shareable archive contains code, documentation, public city-income aggregates, and aggregated regression and calibration output. It does not contain CFPS microdata, CREPRICE rent and price fields, or the household analysis file built from them.

Set `REPLICATION_LOCAL_DATA` to a directory with the layout below, or place the same files in `data/local_only/`. `scripts/make_archive.py` drops `data/local_only/`, Stata `.dta` files, and the named restricted workbooks.

| Input | What it is | In the ZIP | How to obtain it |
| --- | --- | --- | --- |
| `data/public/income_gap/` | 2018 urban and rural income for 51 matched cities | Yes | Statistical-yearbook city aggregates. No household records. |
| `code/03_calibration/archived_checks/` | Saved valuation schedules used to check Figures 5 and 6 | Yes | Model output. No microdata. |
| `city/R1_estimation_sample_2014_2019.xlsx` | 85 cities, 506 city-years, 2014–2019 | No | CREPRICE-derived rent and price joined to the hukou index. |
| `city/R1Full_Rent.xlsx` and `city/R1Full_Rent_2014_2019.xlsx` | Source workbooks for that sample | No | Kept with the estimation sample. The city script reads the merged sample. |
| `city/strict.xlsx` | City-year hukou index, `h`, `h2`, and `strict` | No | Author-constructed index. Required only to rebuild the household file. |
| `household/cfps_mechanism.csv` | Prepared urban household analysis file, 6,855 rows | No | Built from CFPS. Cleaning does not make it public. |
| `cfps_geo/countyid_baseline162.dta` | County-to-prefecture crosswalk | No | Required by the household merge. This package does not build it. |
| Official CFPS `.dta` files | 2012–2022 person, famecon, and famconf modules | No | Peking University CFPS. Set `CFPS_RAW_DIR` for the rebuild only. |

`strict` in the city sample equals `h * (1 + h2)`. Person-level CFPS records and raw CREPRICE extracts are not included. Coefficient tables and figures under `outputs/` are aggregated results.
