# Regression 2 construction chain

Raw CFPS modules, read by `cleaning/cfps_load.py` for every wave listed in `cleaning/cfps_config.py`:

- 2012 adult, famecon, famconf, and the separate respondent-id file
- 2014 and 2016 adult, famecon, famconf, with the 2016 cross-year file supplying the earlier migrant flag
- 2018, 2020, and 2022 person, famecon, and famconf

`variables/cfps_mechanism.py` then defines:

- `own_house`: response in {1, 2} is ownership; {3–7, 77} is not
- `migrant`: hukou location relative to the current residence, with backfill when the skip flag says the location is unchanged
- child indicators from the financial respondent's own children in famconf

`merging/cfps_household_panel.py` stacks the waves and writes the panel under local-only rebuild storage.

`merging/cfps_strict.py` keeps an exact province-city-year match to `strict.xlsx` for 2014, 2016, and 2018. The county crosswalk supplies the prefecture. Cities absent from the hukou file are dropped. The retained rows are urban and have nonmissing `own_house`, `migrant`, and `school_age`.

The prepared `cfps_mechanism.csv` is the estimation input for Table 2 and Figure 4. Rebuilding it is a separate command and does not overwrite that file. The estimation sample further restricts the financial respondent to ages 25–50 and, in columns 2–5 and Figure 4, to cities above a full-sample strictness quantile.
