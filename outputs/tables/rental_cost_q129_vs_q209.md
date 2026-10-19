# Rental-cost comparison at the baseline calibration

Both rows use the existing solver at the central parameters
`rho=0.94`, `pi=0.5`, `A_r=0.38602`, `w_u=1.0`,
`z_L=0.37723513100698913`, and `z_H=1.6227648689930108`.
Bequests are re-optimized for each rent. Both solutions are interior.
The CFPS contract-rent row matches the central row of `table04_valuation_results.csv`.
The asking-rent row matches the same file's `q=0.209` row at `rho=0.94`.

| Object | CFPS contract rent | CREPRICE asking rent |
| --- | ---: | ---: |
| q | 0.129000 | 0.209000 |
| b*(1) | 0.250215 | 0.250215 |
| b*(0) | 0.472058 | 0.479578 |
| B | 0.221842 | 0.229362 |
| H | 0.007378 | 0.001690 |
| S | -0.022739 | -0.005082 |
| P* | 0.206482 | 0.225971 |
| P*_free | 0.129000 | 0.209000 |
| I | 0.077482 | 0.016971 |
| I/P* | 0.375247 | 0.075101 |
| q < z_L(w_u-A_r) | True | True |

The threshold is `z_L(w_u-A_r)=0.231614825736`.
For both rents, `P* - (B+H+S)` and `P* - (P*_free+I)` are below `1e-12`.

Full precision is in `rental_cost_q129_vs_q209.csv`.
