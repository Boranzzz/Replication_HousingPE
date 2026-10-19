# Provenance

The consolidated code was copied from the research files below. Those originals were not moved or edited. A pre-consolidation copy of this package is stored beside it as `Replication_Package_backup_20261019`.

## City regression

The estimation code is the verified script that was already in this package. It implements the specifications checked in `Regression1_TWFE_Audit`.

| File | SHA-256 | Role |
| --- | --- | --- |
| `R1Full_Rent.xlsx` | `cc5dca8ecd7e23c5fadb9b83c1ef7ad9b927482d87c9103a6ce448bb1c7bacc3` | Rent, price, migration, population, income, urbanization. 2,620 city-years. |
| `R1Full_Rent_2014_2019.xlsx` | `578f94150bb9f1f298b6bf984858b9b349f84c9874cabffb07e78ab20fd394f6` | Keys, hukou index, and province. 506 city-years. |
| `R1_estimation_sample_2014_2019.xlsx` | `125e5643c648886387177575f49e436ae83e1837466f173ca608ca97ca902ef1` | Merged sample read by `code/01_city_regression/`. |

The script rebuilds `ln(rent/price)`, `strict * mig`, `trend = year - 2014`, and the within-city demeaned income and population terms in memory. The original cleaning notebook interpolates migration and urbanization and overwrites its input. It is not part of this package.

## Household regression

Estimation scripts in `code/02_household_regression/` are the verified copies of:

- `HousingProject/src/regressions/cfps_reg2_insurance.py`
- `HousingProject/src/regressions/cfps_reg2_mechanism.py`
- `HousingProject/src/figures/cfps_reg2_age_gradient.py`
- `HousingProject/src/tables/cfps_reg2_latex.py`
- `HousingProject/src/utils/ols_cluster.py`

The construction stage copies, with output paths redirected into this package:

- `HousingProject/src/clean/cfps_config.py`
- `HousingProject/src/clean/cfps_load.py`
- `HousingProject/src/variables/cfps_mechanism.py`
- `HousingProject/src/merge/cfps_household_panel.py`
- `HousingProject/src/merge/cfps_strict.py`

The chain is:

1. Official CFPS `.dta` files for 2012, 2014, 2016, 2018, 2020, and 2022.
2. `cleaning/cfps_load.py` reads the named columns and replaces sentinel missing codes.
3. `variables/cfps_mechanism.py` builds homeownership, migrant status, and the child-age indicators.
4. `merging/cfps_household_panel.py` writes the household panel.
5. `merging/cfps_strict.py` attaches the county crosswalk and the same-year hukou index, keeps urban households with nonmissing ownership, migrant status, and school-age status, and writes the analysis CSV.
6. `estimate_homeownership.py` and `estimate_age_gradient.py` produce Table 2 and Figure 4.

The prepared analysis file used for estimation is the existing `HousingProject/data/final/cfps_mechanism.csv`. The rebuild writes `cfps_mechanism_rebuilt.csv` and does not replace that file. On the verification machine the rebuilt and prepared files have the same 6,855 keys and a maximum absolute numeric gap of 0.

`countyid_baseline162.dta` is an input to step 5. No script in `HousingProject/src/` or in this package creates it.

Variable definitions, the age window 25–50, the top-share city filters, city and year fixed effects, and city-clustered standard errors are unchanged.

## Calibration

The solver and figure script come from `housing_valuation/solve_housing_valuation.py` and `housing_valuation/make_publication_figures.py`. Baseline parameters are constants in the solver. They are calibration targets, not coefficients estimated by the regression scripts.

| Quantity | Role |
| --- | --- |
| `w_u = 1`, `A_r = 0.386020`, `sigma = 0.729509`, `pi = 0.5` | Calibrated or normalized inputs |
| `rho` in `{0.65, 0.94, 1.241}` | Altruism sensitivity, with `0.94` as the baseline |
| `q = 0.129` and `q = 0.209` | Rental-cost scenarios supplied to the model |
| `P*`, `B`, `H`, `S`, `P_free*`, `I` | Quantities solved from those inputs |

The identities are `P* = B + H + S` and `P* = P_free* + I`. The rural-income band reads `data/public/income_gap/`. The older general-equilibrium code under `HousingProject/calibration` is a different model and is not used.

## Not included

Figures 1–3 and their plotting scripts were in the pre-consolidation package. They are in the backup and are not part of this package. The expectations workbook used for Figure 3 is likewise omitted.
