# Decomposing Urban Housing Values in China: An Intergenerational Migration Hedge Model

Replication package for the city regression, the CFPS household regression, and the two-period partial-equilibrium housing valuation.

This archive does not reproduce every figure in the manuscript. Figures 1–3, the international and monthly rent-to-price charts and the PBoC expectations chart, are outside this package.

## What is covered

| Manuscript item | Execution script | Input data | Output file | Status |
| --- | --- | --- | --- | --- |
| Table 1. City regression | `scripts/run_regression1.py` | Local city sample, 506 rows | `outputs/tables/table01_city_regressions.csv` | Local-only input |
| Appendix Table 5. Alternative fixed effects | Same script | Same sample | Same table, TWFE rows | Local-only input |
| Wild cluster bootstrap | Same script | Same sample | `outputs/diagnostics/wild_cluster_bootstrap.json` | Local-only input |
| Appendix Figure 7. Leave-one-city-out | Same script | Coefficient file written by the city script | `outputs/figures/loo_city_trends_only.pdf` | Local-only input |
| Table 2. Five homeownership columns | `scripts/run_regression2.py` | Local `cfps_mechanism.csv` | `outputs/tables/household/cfps_reg2_column_results.csv` | Prepared local file |
| Figure 4. Child-age interactions | Same script | Same prepared file | `outputs/figures/fig04_child_age_interaction.pdf` | Prepared local file |
| CFPS file construction | `scripts/rebuild_household_inputs.py` | Official CFPS `.dta`, `strict.xlsx`, county crosswalk | Separate rebuilt CSV under local-only storage | Local raw inputs; does not replace the prepared file |
| Table 3. Calibration parameters | `scripts/run_calibration.py` | Parameters in `code/03_calibration/solve_housing_valuation.py` | `outputs/tables/table03_calibration_parameters.csv` | Distributed code |
| Table 4. Valuation decomposition | Same script | Same solver, including the altruism grid | `outputs/tables/table04_valuation_results.csv` | Distributed code |
| Figure 5. Rental-cost sensitivity | Same script | Solver and saved schedule checks | `outputs/figures/fig05_rental_cost_sensitivity.pdf` | Distributed code |
| Figure 6. Low-productivity and rural-income sensitivity | Same script | Solver and `data/public/income_gap/` | `outputs/figures/fig06_institutional_access_premium.pdf` | Distributed public input |
| Alternative rent, q = 0.129 and q = 0.209 | Same script | Table 4 | `outputs/tables/rental_cost_q129_vs_q209.csv` | Distributed code |

## Software

Python 3.12 and the packages in `requirements.txt`: pandas 2.2.2, numpy 1.26.4, statsmodels 0.14.6, patsy 0.5.6, scipy 1.17.1, matplotlib 3.9.2, and openpyxl 3.1.5. The verification run used Anaconda Python 3.12.7. Figures 5, 6, and 7 use Times New Roman when that font is installed.

```bash
pip install -r requirements.txt
```

## How to run

From `Replication_Package/`:

```bash
python scripts/run_calibration.py
python scripts/run_regression1.py
python scripts/run_regression2.py
python scripts/run_all.py
```

`run_all.py` runs those three stages in that order. It does not rebuild the CFPS file. A missing restricted input prints `INCOMPLETE` and does not stop the other stages.

Restricted inputs are read from `data/local_only/` unless `REPLICATION_LOCAL_DATA` points at another directory with the same layout. `CFPS_MECHANISM_CSV` overrides the prepared household file. `CFPS_RAW_DIR` overrides the official CFPS directory used only by the rebuild.

```bash
python scripts/rebuild_household_inputs.py
```

The rebuild writes a new CSV beside the prepared file and compares them. It does not replace `cfps_mechanism.csv`.

Calibration and the public income file do not need restricted data. Regression 1 needs the city sample. Regression 2 estimation needs the prepared household file. The rebuild also needs the official CFPS files, `strict.xlsx`, and `countyid_baseline162.dta`.

## Layout

```text
code/01_city_regression/          Table 1, Appendix Table 5, bootstrap, Figure 7
code/02_household_regression/     Table 2 and Figure 4
    cleaning/ variables/ merging/ construction stage
code/03_calibration/              Tables 3 and 4, Figures 5 and 6
data/public/                      income aggregates included in the archive
data/local_only/                  restricted inputs, omitted from the archive
outputs/                          tables, figures, and diagnostics
provenance/                       original-file map
scripts/                          run and archive commands
tests/                            identity and missing-input checks
```

Details of access are in `DATA_AVAILABILITY.md`. The verification record is `REPLICATION_STATUS.md`. Original filenames are in `provenance/SOURCE_PROVENANCE.md`.
