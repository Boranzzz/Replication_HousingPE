"""Compare the baseline CFPS contract rent with the CREPRICE asking rent.

Calls the existing valuation solver. Does not rewrite Table 3 or Table 4.
"""

from __future__ import annotations

from pathlib import Path

import pandas as pd

import solve_housing_valuation as model

PACKAGE = Path(__file__).resolve().parents[2]
TABLE4 = PACKAGE / "outputs" / "tables" / "table04_valuation_results.csv"
OUT_CSV = PACKAGE / "outputs" / "tables" / "rental_cost_q129_vs_q209.csv"
OUT_MD = PACKAGE / "outputs" / "tables" / "rental_cost_q129_vs_q209.md"

CASES = (
    ("cfps_contract_rent", 0.129),
    ("creprice_asking_rent", 0.209),
)


def main() -> None:
    z_low, z_high, _gap = model.productivity_states()
    archived = pd.read_csv(TABLE4)
    rows = []
    for label, q in CASES:
        fresh = model.evaluate_case(q, model.RHO_CENTRAL, z_low, z_high)
        stored = archived.loc[
            archived["block"].eq("baseline_grid")
            & archived["rho"].eq(model.RHO_CENTRAL)
            & (archived["q"] - q).abs().lt(1e-12)
        ]
        if len(stored) != 1:
            raise RuntimeError(f"Table 4 does not contain one central row at q={q}")
        stored = stored.iloc[0]
        for field in ("b1", "b0", "B", "H", "S", "P_star", "P_free", "I", "I_over_P"):
            if abs(float(fresh[field]) - float(stored[field])) > 1e-12:
                raise AssertionError(f"{label} {field} differs from Table 4")
        identity_components = fresh["P_star"] - (fresh["B"] + fresh["H"] + fresh["S"])
        identity_premium = fresh["P_star"] - (fresh["P_free"] + fresh["I"])
        if abs(identity_components) > 1e-12 or abs(identity_premium) > 1e-12:
            raise AssertionError(f"Valuation identity failed at q={q}")
        rows.append(
            {
                "scenario": label,
                "q": fresh["q"],
                "rho": fresh["rho"],
                "pi": fresh["pi"],
                "a_r": fresh["a_r"],
                "w_u": model.W_U,
                "z_low": fresh["z_low"],
                "z_high": fresh["z_high"],
                "b_star_1": fresh["b1"],
                "b_star_0": fresh["b0"],
                "interior_b1": fresh["interior_b1"],
                "interior_b0": fresh["interior_b0"],
                "B": fresh["B"],
                "H": fresh["H"],
                "S": fresh["S"],
                "P_star": fresh["P_star"],
                "P_free": fresh["P_free"],
                "I": fresh["I"],
                "I_over_P": fresh["I_over_P"],
                "q_crit": fresh["q_crit"],
                "q_below_q_crit": fresh["q"] < fresh["q_crit"],
                "identity_BHS": identity_components,
                "identity_free_plus_I": identity_premium,
            }
        )
    comparison = pd.DataFrame(rows)
    comparison.to_csv(OUT_CSV, index=False)
    OUT_MD.write_text(report(comparison), encoding="utf-8")
    print(comparison.to_string(index=False))
    print(f"Wrote {OUT_CSV}")
    print(f"Wrote {OUT_MD}")


def report(comparison: pd.DataFrame) -> str:
    baseline = comparison.iloc[0]
    asking = comparison.iloc[1]
    lines = [
        "# Rental-cost comparison at the baseline calibration",
        "",
        "Both rows use the existing solver at the central parameters",
        f"`rho={model.RHO_CENTRAL}`, `pi={model.PI}`, `A_r={model.A_R}`, `w_u={model.W_U}`,",
        f"`z_L={baseline['z_low']}`, and `z_H={baseline['z_high']}`.",
        "Bequests are re-optimized for each rent. Both solutions are interior.",
        "The CFPS contract-rent row matches the central row of `table04_valuation_results.csv`.",
        "The asking-rent row matches the same file's `q=0.209` row at `rho=0.94`.",
        "",
        "| Object | CFPS contract rent | CREPRICE asking rent |",
        "| --- | ---: | ---: |",
        f"| q | {baseline['q']:.6f} | {asking['q']:.6f} |",
        f"| b*(1) | {baseline['b_star_1']:.6f} | {asking['b_star_1']:.6f} |",
        f"| b*(0) | {baseline['b_star_0']:.6f} | {asking['b_star_0']:.6f} |",
        f"| B | {baseline['B']:.6f} | {asking['B']:.6f} |",
        f"| H | {baseline['H']:.6f} | {asking['H']:.6f} |",
        f"| S | {baseline['S']:.6f} | {asking['S']:.6f} |",
        f"| P* | {baseline['P_star']:.6f} | {asking['P_star']:.6f} |",
        f"| P*_free | {baseline['P_free']:.6f} | {asking['P_free']:.6f} |",
        f"| I | {baseline['I']:.6f} | {asking['I']:.6f} |",
        f"| I/P* | {baseline['I_over_P']:.6f} | {asking['I_over_P']:.6f} |",
        f"| q < z_L(w_u-A_r) | {bool(baseline['q_below_q_crit'])} | {bool(asking['q_below_q_crit'])} |",
        "",
        f"The threshold is `z_L(w_u-A_r)={baseline['q_crit']:.12f}`.",
        "For both rents, `P* - (B+H+S)` and `P* - (P*_free+I)` are below `1e-12`.",
        "",
        "Full precision is in `rental_cost_q129_vs_q209.csv`.",
        "",
    ]
    return "\n".join(lines)


if __name__ == "__main__":
    main()
