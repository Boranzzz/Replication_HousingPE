# Final replication report

The package reproduces the city regression, the CFPS household regression, and the partial-equilibrium valuation. It does not reproduce Figures 1–3.

A reversible copy of the package as it stood before this consolidation is `Replication_Package_backup_20261019`, next to the package. Original research directories were not modified.

## Directory structure

```text
Replication_Package/
  README.md
  DATA_AVAILABILITY.md
  REPLICATION_STATUS.md
  FINAL_REPLICATION_REPORT.md
  requirements.txt
  replication_paths.py
  scripts/
    run_all.py
    run_regression1.py
    run_regression2.py
    run_calibration.py
    rebuild_household_inputs.py
    make_archive.py
  code/
    01_city_regression/
    02_household_regression/
      cleaning/ variables/ merging/
    03_calibration/
  data/
    public/income_gap/
    local_only/          omitted from the ZIP
  outputs/tables/ outputs/figures/ outputs/diagnostics/
  tests/
  provenance/
```

The verified estimation modules stayed in place and were renumbered. Household construction code was added under `cleaning/`, `variables/`, and `merging/` rather than copied into a second estimator.

## Sources consolidated

- City estimation from the existing `code/02_city_regression/` scripts, themselves checked against `Regression1_TWFE_Audit`.
- Household estimation from the existing package copies of the HousingProject regression, figure, table, and clustered-OLS modules.
- Household construction from `HousingProject/src/clean/`, `src/variables/cfps_mechanism.py`, and `src/merge/`. Only the output locations were redirected.
- Calibration from the existing `code/04_calibration/` solver, figure script, and rental-cost comparison, which came from `housing_valuation/`.

## Files excluded from the shareable archive

- `data/local_only/`, including the CREPRICE city workbooks, `strict.xlsx`, `cfps_mechanism.csv`, the county crosswalk, and the rebuilt household files.
- Official CFPS `.dta` files, which were never copied into the package.
- Figure 1–3 scripts, the expectations workbook, and `fig01` and `fig03` outputs. Those files remain in the backup.
- `__pycache__`, `.pyc`, and `.DS_Store`.
- The pre-consolidation backup.

`scripts/make_archive.py` applies that exclusion list and refuses to archive a Python file containing an author-specific absolute path.

## Numerical verification

Regression 1, from the 506-row sample: city-trend interaction −0.306175 (SE 0.067840), province specification −0.332582 (0.119481), demeaned controls −0.314011 (0.068143). TWFE −0.059757 (0.258842) and −0.023817 (0.222230). Full-rank trends −0.504156 (0.193172), R² 0.964378, 85 cities. Wild-cluster p-values 0.1023 and 0.1179 at seed 20261019 with 9,999 draws. Leave-one-city-out ranges from −0.564691 to −0.353577, and all 85 estimates are negative.

Regression 2, from the prepared file: the five interactions are 0.125554, 0.128366, 0.125596, 0.133505, and 0.083851, with sample sizes 2,724, 2,403, 1,998, 1,998, and 1,998 and city counts 36, 27, 22, 22, and 22. Figure 4 is 0.126838, 0.124173, 0.002159, 0.111328, and 0.059755, which round to the four-decimal targets 0.1268, 0.1242, 0.0022, 0.1113, and 0.0598.

Calibration: baseline P* = 0.206481599874, I = 0.077481599874, share 37.5 percent. Alternative q = 0.209 gives P* = 0.225970541135, I = 0.016970541135, share 7.5 percent. Both valuation identities hold. The last stored digit of P* and I differs from those twelve-decimal targets by 2.6e-13. The bootstrap coefficient and the OLS table coefficient differ in the eleventh digit and both print as −0.5042.

The raw-data rebuild of the household file matched all 6,855 keys and all compared numeric fields exactly. That rebuilt file was not substituted for the prepared file.

## How each result can be reproduced

- Tables 3 and 4, Figures 5 and 6, the altruism grid, and the q = 0.129 versus q = 0.209 comparison are fully reproducible from the distributed code and the public income file.
- Table 1, Appendix Table 5, the wild cluster bootstrap, and Figure 7 are reproducible with the local 506-row city sample. This package does not rebuild that sample from the CREPRICE extracts.
- Table 2 and Figure 4 are reproducible from the prepared `cfps_mechanism.csv`.
- That prepared file was also rebuilt here from local CFPS `.dta` files, `strict.xlsx`, and the existing county crosswalk. The crosswalk itself has no generating script, so the household file is not reproducible from the survey modules alone.

## Unresolved dependencies

- `countyid_baseline162.dta` is an undocumented input to the hukou merge.
- The city estimation sample is a prepared merge. The cleaning notebook that interpolates migration and urbanization overwrites its source and is intentionally not included.
- q = 0.129 and q = 0.209 are supplied parameters. They are not remeasured from a rental extract in this package.
- Figures 5, 6, and 7 look for Times New Roman at the standard macOS font path. The numerical tables do not need that font.

## Redistribution

CFPS person and household records, `cfps_mechanism.csv`, CREPRICE-derived city workbooks, `strict.xlsx`, and the county crosswalk stay on the local machine. The public income aggregates, coefficient tables, figures, and calibration schedules are in the archive. A cleaned CFPS file is still restricted.

## ZIP validation

`Replication_Package.zip` is written by `scripts/make_archive.py`. The audited archive contains the package code, documentation, public income file, permitted outputs, and tests. It contains no `data/local_only` entry, no `.dta` file, no CREPRICE workbook, and no `fig01` or `fig03` output. The only filename containing the text `cfps_mechanism` is the variable-construction module `variables/cfps_mechanism.py`, which holds definitions rather than observations.

The archive was extracted to a temporary directory. Unit tests passed. `scripts/run_calibration.py` reproduced Tables 3 and 4, Figures 5 and 6, and the rental-cost comparison. The city regression, both household estimation scripts, and the household rebuild each exited with status 2 and an `INCOMPLETE` message naming the missing local file. The leave-one-city-out figure still ran from the saved coefficient file. No Python member contains an author home-directory path. The archive was not uploaded.
