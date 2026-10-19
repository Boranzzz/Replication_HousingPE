# Data folders

`public/` contains inputs that are city or survey aggregates and are included in the shareable archive. The only public input used by the included results is `public/income_gap/`, the 2018 urban and rural income ratios for the matched cities in Figure 6.

`local_only/` is for authorized copies of restricted inputs. It is omitted from `Replication_Package.zip`. Put the following there, or point `REPLICATION_LOCAL_DATA` at a directory with the same layout:

```text
city/R1_estimation_sample_2014_2019.xlsx
city/strict.xlsx
household/cfps_mechanism.csv
cfps_geo/countyid_baseline162.dta
cfps/                       official CFPS wave folders, only for the rebuild stage
```

`CFPS_MECHANISM_CSV` and `CFPS_RAW_DIR` override the household analysis file and the raw CFPS directory.
