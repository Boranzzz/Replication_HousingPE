"""Solve the partial-equilibrium housing valuation and its two decompositions.

The script uses the provisional calibration. It does not estimate parameters,
does not impose q < z_L(w_u - A_r), and does not solve for a market price.

    python housing_valuation/solve_housing_valuation.py
"""

from __future__ import annotations

import math
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[2]
OUT_TABLES = ROOT / "outputs" / "tables"
W_U = 1.0
A_R = 0.386020
SIGMA = 0.729509
PI = 0.5
RHO_GRID = (0.65, 0.94, 1.241)
Q_BASELINE = (0.12, 0.129, 0.209, 0.21)
Q_ROBUST = (0.076, 0.218, 0.252, 0.265, 0.443)
RHO_CENTRAL = 0.94
Q_CENTRAL = 0.129


def productivity_states(sigma: float = SIGMA, pi: float = PI) -> tuple[float, float, float]:
    """Equal-probability-ready two-point support with E[z]=1 and sd(ln z)=sigma."""
    gap = sigma / math.sqrt(pi * (1.0 - pi))
    z_low = 1.0 / (pi + (1.0 - pi) * math.exp(gap))
    z_high = math.exp(gap) * z_low
    return z_low, z_high, gap


def rho_min(y_low: float, y_high: float, pi: float = PI) -> float:
    return 1.0 / (pi / y_low + (1.0 - pi) / y_high)


def marginal(y_low: float, y_high: float, bequest: float, rho: float, pi: float = PI) -> float:
    return -1.0 + rho * (pi / (y_low + bequest) + (1.0 - pi) / (y_high + bequest))


def optimal_bequest(y_low: float, y_high: float, rho: float, pi: float = PI) -> tuple[float, bool, float]:
    """Return (b, interior, first-order residual at the reported b).

    A corner at zero is used whenever the derivative there is not strictly positive.
    """
    if y_low <= 0 or y_high <= 0:
        raise ValueError("State resources must be positive at a zero bequest")
    slope = marginal(y_low, y_high, 0.0, rho, pi)
    if slope <= 0.0:
        return 0.0, False, slope
    total = y_low + y_high
    product = y_low * y_high
    weighted = pi * y_high + (1.0 - pi) * y_low
    linear = total - rho
    constant = product - rho * weighted
    discriminant = linear * linear - 4.0 * constant
    if discriminant < 0:
        raise RuntimeError("Interior first-order condition has no real root")
    roots = (
        (-linear + math.sqrt(discriminant)) / 2.0,
        (-linear - math.sqrt(discriminant)) / 2.0,
    )
    candidates = []
    for bequest in roots:
        if bequest <= 0:
            continue
        residual = marginal(y_low, y_high, bequest, rho, pi)
        if abs(residual) < 1e-9:
            candidates.append(bequest)
    if len(candidates) != 1:
        raise RuntimeError(f"Expected one positive root, found {candidates}")
    bequest = candidates[0]
    return bequest, True, marginal(y_low, y_high, bequest, rho, pi)


def optimized_value(y_low: float, y_high: float, rho: float, pi: float = PI) -> tuple[float, float, bool]:
    bequest, interior, _residual = optimal_bequest(y_low, y_high, rho, pi)
    value = -bequest + rho * (
        pi * math.log(y_low + bequest) + (1.0 - pi) * math.log(y_high + bequest)
    )
    return value, bequest, interior


def evaluate_case(
    q: float,
    rho: float,
    z_low: float,
    z_high: float,
    pi: float = PI,
    a_r: float = A_R,
) -> dict:
    y1_low = z_low * W_U
    y1_high = z_high * W_U
    y0_low = z_low * a_r
    y0_high = z_high * W_U - q
    if y0_high <= 0:
        raise ValueError("High-state urban earnings do not cover rent")
    value_house, b1, interior_b1 = optimized_value(y1_low, y1_high, rho, pi)
    value_restricted, b0, interior_b0 = optimized_value(y0_low, y0_high, rho, pi)
    reservation = value_house - value_restricted
    bequest_gap = b0 - b1
    low_component = rho * pi * math.log((y1_low + b1) / (y0_low + b0))
    high_component = rho * (1.0 - pi) * math.log((y1_high + b1) / (y0_high + b0))
    y_free_low = max(z_low * a_r, z_low * W_U - q)
    value_free, b_free, interior_free = optimized_value(y_free_low, y0_high, rho, pi)
    reservation_free = value_house - value_free
    institutional = reservation - reservation_free
    q_crit = z_low * (W_U - a_r)
    q_high = z_high * (W_U - a_r)
    return {
        "q": q,
        "rho": rho,
        "pi": pi,
        "a_r": a_r,
        "z_low": z_low,
        "z_high": z_high,
        "q_crit": q_crit,
        "q_high": q_high,
        "b1": b1,
        "b0": b0,
        "b_free": b_free,
        "interior_b1": interior_b1,
        "interior_b0": interior_b0,
        "interior_free": interior_free,
        "B": bequest_gap,
        "H": low_component,
        "S": high_component,
        "P_star": reservation,
        "P_components": bequest_gap + low_component + high_component,
        "component_gap": reservation - (bequest_gap + low_component + high_component),
        "share_B": bequest_gap / reservation,
        "share_H": low_component / reservation,
        "share_S": high_component / reservation,
        "y_free_low": y_free_low,
        "P_free": reservation_free,
        "I": institutional,
        "I_over_P": institutional / reservation,
        "reservation_reduction": institutional / reservation,
        "below_high_state_bound": q < q_high,
    }


def verification_flags(row: pd.Series) -> dict:
    interior = bool(row.interior_b0 and row.interior_b1)
    q_crit = float(row.q_crit)
    flags = {
        "identity_holds": abs(row.component_gap) < 1e-10,
        "shares_sum_to_one": abs(row.share_B + row.share_H + row.share_S - 1.0) < 1e-10,
        "interior": interior,
    }
    if not interior:
        flags["region_check"] = "corner"
        return flags
    if row.q < q_crit - 1e-12:
        flags["region_check"] = "below"
        flags["region_ok"] = (
            row.q < row.B < q_crit
            and row.H > 0
            and row.S < 0
            and row.I > 0
            and abs(row.P_free - row.q) < 1e-10
        )
    elif abs(row.q - q_crit) <= 1e-12:
        flags["region_check"] = "threshold"
        flags["region_ok"] = abs(row.H) < 1e-10 and abs(row.S) < 1e-10
    else:
        flags["region_check"] = "above"
        flags["region_ok"] = (
            q_crit < row.B < row.q
            and row.H < 0
            and row.S > 0
            and abs(row.I) < 1e-10
        )
    return flags


def main() -> None:
    z_low, z_high, gap = productivity_states()
    mean_z = PI * z_low + (1.0 - PI) * z_high
    var_log = PI * (1.0 - PI) * gap ** 2
    if abs(mean_z - 1.0) > 1e-12 or abs(math.sqrt(var_log) - SIGMA) > 1e-12:
        raise AssertionError("Productivity states do not match the requested moments")

    rows = []
    for rho in RHO_GRID:
        for q in Q_BASELINE:
            row = evaluate_case(q, rho, z_low, z_high)
            row["block"] = "baseline_grid"
            rows.append(row)
    for q in Q_ROBUST:
        row = evaluate_case(q, RHO_CENTRAL, z_low, z_high)
        row["block"] = "housing_arrangement"
        rows.append(row)
    q_crit = z_low * (W_U - A_R)
    threshold = evaluate_case(q_crit, RHO_CENTRAL, z_low, z_high)
    threshold["block"] = "exact_threshold"
    rows.append(threshold)

    results = pd.DataFrame(rows)
    checks = pd.DataFrame([verification_flags(row) for row in results.itertuples(index=False)])
    results = pd.concat([results, checks], axis=1)
    if not results["identity_holds"].all() or not results["shares_sum_to_one"].all():
        raise AssertionError("Valuation identity failed")
    if not results["below_high_state_bound"].all():
        raise AssertionError("A rent meets or exceeds the high-state urban surplus")
    if not results.loc[results.interior, "region_ok"].all():
        failed = results.loc[results.interior & ~results.region_ok, ["block", "q", "rho", "region_check"]]
        raise AssertionError(f"Region checks failed:\n{failed}")

    OUT_TABLES.mkdir(parents=True, exist_ok=True)
    results.to_csv(OUT_TABLES / "table04_valuation_results.csv", index=False)
    summary = {
        "z_low": z_low,
        "z_high": z_high,
        "log_gap": gap,
        "mean_z": mean_z,
        "sd_log_z": math.sqrt(var_log),
        "q_crit": q_crit,
        "q_high": z_high * (W_U - A_R),
        "A_r": A_R,
        "w_u": W_U,
        "pi": PI,
        "sigma": SIGMA,
    }
    pd.Series(summary).to_csv(OUT_TABLES / "table03_calibration_parameters.csv", header=["value"])
    show = results.loc[
        results.block.eq("baseline_grid") & results.q.eq(Q_CENTRAL),
        ["rho", "b1", "b0", "B", "H", "S", "P_star", "P_free", "I", "I_over_P"],
    ]
    print(pd.Series(summary).to_string())
    print(show.to_string(index=False))
    print("All identity and region checks passed.")


if __name__ == "__main__":
    main()
