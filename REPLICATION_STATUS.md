# Replication status

Verified with Anaconda Python 3.12.7, pandas 2.2.2, numpy 1.26.4, statsmodels 0.14.6, patsy 0.5.6, scipy 1.17.1, matplotlib 3.9.2, and openpyxl 3.1.5.

The command was `python scripts/run_all.py` from the package directory. Regression 1 read `data/local_only/city/R1_estimation_sample_2014_2019.xlsx`. Regression 2 read `data/local_only/household/cfps_mechanism.csv`. Neither file is in the shareable archive. A run without them leaves calibration runnable and marks the regression steps incomplete.

Figures 1–3 are not part of this package.

## Reproduced

| Result | Check |
| --- | --- |
| Table 1, city trends | 85 cities, 506 city-years, 2014–2019. Interaction −0.306175 (SE 0.067840), R² 0.798232. Prints as −0.3062 (0.068). |
| City trends with province effects | −0.332582 (SE 0.119481), R² 0.893666. |
| City trends with demeaned controls | −0.314011 (SE 0.068143), R² 0.800450. |
| Appendix Table 5, TWFE | −0.059757 (SE 0.258842). With controls, −0.023817 (SE 0.222230). |
| TWFE, controls, and city trends | −0.504156. Full-rank city-clustered SE 0.193172, conventional p 0.009057, R² 0.964378. Singular design SE 0.193469. Prints as −0.5042 (0.193). |
| Wild cluster bootstrap | Seed 20261019, 9,999 Rademacher draws. Coefficient p 0.1023. t p 0.1179. |
| Appendix Figure 7 | 85 leave-one-city-out estimates, all negative, from −0.564691 (Xuzhou) to −0.353577 (Beijing). |
| Table 2 | Interactions 0.125554 (0.062633), N = 2,724, 36 cities; 0.128366 (0.065304), N = 2,403, 27 cities; 0.125596 (0.051633), N = 1,998, 22 cities; 0.133505 (0.046013), N = 1,998; 0.083851 (0.052830), N = 1,998. |
| Figure 4 | Joint interactions 0.126838, 0.124173, 0.002159, 0.111328, and 0.059755. Rounded to four decimals: 0.1268, 0.1242, 0.0022, 0.1113, 0.0598. |
| Tables 3 and 4 | At q = 0.129 and rho = 0.94, P* = 0.206481599874, I = 0.077481599874, and I/P* = 0.375247. |
| Alternative rent | At q = 0.209, P* = 0.225970541135, I = 0.016970541135, and I/P* = 0.075101. |
| Identities | P* − (B + H + S) and P* − (P_free* + I) are within 1e-16 at both rental costs. |
| Altruism grid | At rho = 0.65, 0.94, and 1.241, P* is 0.211978, 0.206482, and 0.202221. |
| Figures 5 and 6 | P* is 0.187932 at q = 0.05 and 0.289471 at q = 0.45. The institutional premium is 0.055652, 0.077482, and 0.093522 at pi = 0.2, 0.5, and 0.8. |

The household construction command was also run against the local CFPS files. The rebuilt analysis file has the same 6,855 household-year keys as the prepared file, and every compared numeric column has a maximum absolute gap of 0. The prepared file was not replaced.

## Rounding

The solver's stored baseline reservation value is 0.206481599873735, which differs from 0.206481599874 by 2.6e-13. The institutional premium differs from 0.077481599874 by the same amount. The alternative-rent reservation value, 0.225970541134735, differs from 0.225970541135 by 2.6e-13. P_free* at q = 0.129 is stored as 0.12899999999999995 and equals 0.129 at printed precision. The bootstrap records the full-rank coefficient as −0.504156391270, while the OLS table records −0.504156391339. Both print as −0.5042, and the analytic standard error prints as 0.193 in both places.

No sample filter, formula, or parameter was changed to close these gaps.

## Not rerun inside this package

The 506-row city sample was not rebuilt from the CREPRICE city extracts. The county crosswalk was used as an input and was not reconstructed. The rental-cost values q = 0.129 and q = 0.209 are calibration inputs.
