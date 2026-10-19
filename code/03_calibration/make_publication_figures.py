"""Publication figures for the one-period reservation-value sensitivities.

Does not change the household problem or estimate parameters.

    python housing_valuation/make_publication_figures.py
"""

from __future__ import annotations

import json
import re
import sys
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from matplotlib import font_manager
from matplotlib.lines import Line2D
from matplotlib.patches import Patch

ROOT = Path(__file__).resolve().parent
PROJECT = ROOT.parents[1]
sys.path.insert(0, str(ROOT))

import solve_housing_valuation as model  # noqa: E402

OUT = PROJECT / "outputs" / "figures"
ARCHIVE = ROOT / "archived_checks"
TNR_PATH = Path("/System/Library/Fonts/Supplemental/Times New Roman.ttf")
TNR_FAMILY = (
    TNR_PATH,
    TNR_PATH.with_name("Times New Roman Bold.ttf"),
    TNR_PATH.with_name("Times New Roman Italic.ttf"),
    TNR_PATH.with_name("Times New Roman Bold Italic.ttf"),
)

NAVY = "#1B4F72"
CLAY = "#8C4E3A"
BAND = "#E4E4E4"
REFERENCE = "#4F4F4F"
INK = "#222222"

Q_MIN = 0.05
Q_MAX = 0.45
Q_EMPIRICAL_LOW = 0.12
Q_EMPIRICAL_HIGH = 0.21
PI_MIN = 0.2
PI_MAX = 0.8


def register_times() -> str:
    """Register the installed Times New Roman files and refuse any substitute."""
    if not TNR_PATH.is_file():
        raise FileNotFoundError(f"Times New Roman is not at {TNR_PATH}")
    for path in TNR_FAMILY:
        if not path.is_file():
            raise FileNotFoundError(f"Required Times face is missing: {path}")
        font_manager.fontManager.addfont(str(path))
    name = font_manager.FontProperties(fname=str(TNR_PATH)).get_name()
    if name != "Times New Roman":
        raise RuntimeError(f"Font file reported {name!r} rather than Times New Roman")
    resolved = Path(
        font_manager.findfont(
            font_manager.FontProperties(family="Times New Roman"),
            fallback_to_default=False,
        )
    )
    if "Times New Roman" not in resolved.name:
        raise RuntimeError(f"Matplotlib resolved Times New Roman to {resolved}")
    return str(resolved)


def use_journal_style() -> None:
    plt.rcParams.update(
        {
            "font.family": "Times New Roman",
            "font.size": 10,
            "axes.labelsize": 11,
            "axes.labelcolor": INK,
            "axes.edgecolor": INK,
            "axes.linewidth": 0.6,
            "axes.titlesize": 11,
            "xtick.labelsize": 9,
            "ytick.labelsize": 9,
            "xtick.color": INK,
            "ytick.color": INK,
            "legend.fontsize": 9,
            "text.color": INK,
            "mathtext.fontset": "stix",
            "pdf.fonttype": 42,
            "ps.fonttype": 42,
            "axes.unicode_minus": False,
            "figure.facecolor": "white",
            "axes.facecolor": "white",
            "savefig.facecolor": "white",
            "savefig.bbox": "tight",
            "savefig.pad_inches": 0.04,
        }
    )


def polish(ax: plt.Axes) -> None:
    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)
    ax.tick_params(axis="both", which="major", direction="out", length=3.2, width=0.6, pad=2)
    for spine in ("left", "bottom"):
        ax.spines[spine].set_linewidth(0.6)
        ax.spines[spine].set_color(INK)


def city_rural_income() -> dict:
    """Quartiles of rural/urban income across the 51 matched strict cities."""
    cities = pd.read_csv(PROJECT / "data" / "public" / "income_gap" / "income_gap_city_2018.csv")
    sample = cities.loc[
        cities["high_strict"].eq(1)
        & cities["match_status"].eq("matched_exact_province_city")
        & cities["urban_income"].gt(0)
        & cities["rural_income"].gt(0)
    ].copy()
    if len(sample) != 51:
        raise AssertionError(f"Expected 51 strict cities, found {len(sample)}")
    ratio = sample["urban_income"].to_numpy(dtype=float) / sample["rural_income"].to_numpy(dtype=float)
    if (sample["income_ratio"].to_numpy(dtype=float) - ratio).max() > 1e-8:
        raise AssertionError("Stored income ratios do not match urban/rural income")
    rural_share = sample["rural_income"].to_numpy(dtype=float) / sample["urban_income"].to_numpy(dtype=float)
    summary = pd.read_csv(PROJECT / "data" / "public" / "income_gap" / "income_gap_summary.csv").set_index("moment")
    published = {
        "r_min": float(summary.loc["r_min", "income_or_wage_ratio"]),
        "r_p25": float(summary.loc["r_p25", "income_or_wage_ratio"]),
        "r_p50": float(summary.loc["r_p50", "income_or_wage_ratio"]),
        "r_p75": float(summary.loc["r_p75", "income_or_wage_ratio"]),
        "r_max": float(summary.loc["r_max", "income_or_wage_ratio"]),
    }
    recomputed = {
        "r_min": float(np.min(ratio)),
        "r_p25": float(np.quantile(ratio, 0.25, method="linear")),
        "r_p50": float(np.quantile(ratio, 0.50, method="linear")),
        "r_p75": float(np.quantile(ratio, 0.75, method="linear")),
        "r_max": float(np.max(ratio)),
    }
    for key, value in published.items():
        if abs(recomputed[key] - value) > 1e-10:
            raise AssertionError(f"{key} changed relative to income_gap_summary.csv")
    quantiles = np.quantile(rural_share, [0.0, 0.25, 0.5, 0.75, 1.0], method="linear")
    # Endpoints and the odd-sample median commute with the reciprocal. The
    # interpolated quartiles do not, so the band uses quantiles of A_r itself.
    complements = 1.0 / np.array(
        [published["r_max"], published["r_p75"], published["r_p50"], published["r_p25"], published["r_min"]]
    )
    if np.max(np.abs(quantiles[[0, 2, 4]] - complements[[0, 2, 4]])) > 1e-10:
        raise AssertionError("Endpoint or median rural income does not match the published ratios")
    return {
        "n_cities": int(len(sample)),
        "a_r_min": float(quantiles[0]),
        "a_r_p25": float(quantiles[1]),
        "a_r_p50": float(quantiles[2]),
        "a_r_p75": float(quantiles[3]),
        "a_r_max": float(quantiles[4]),
        "ratio_p25": published["r_p25"],
        "ratio_p75": published["r_p75"],
        "a_r_from_ratio_p75": float(complements[1]),
        "a_r_from_ratio_p25": float(complements[3]),
    }


def evaluate_grid(q, rho, z_low, z_high, pi, a_r) -> pd.DataFrame:
    q_values = np.atleast_1d(np.asarray(q, dtype=float))
    pi_values = np.atleast_1d(np.asarray(pi, dtype=float))
    a_values = np.atleast_1d(np.asarray(a_r, dtype=float))
    varying = [len(q_values) > 1, len(pi_values) > 1, len(a_values) > 1]
    if sum(varying) > 1:
        raise ValueError("Only one dimension is varied in a plotted schedule")
    n = max(len(q_values), len(pi_values), len(a_values))
    if len(q_values) == 1:
        q_values = np.repeat(q_values, n)
    if len(pi_values) == 1:
        pi_values = np.repeat(pi_values, n)
    if len(a_values) == 1:
        a_values = np.repeat(a_values, n)
    rows = [
        model.evaluate_case(float(one_q), rho, z_low, z_high, pi=float(one_pi), a_r=float(one_a))
        for one_q, one_pi, one_a in zip(q_values, pi_values, a_values, strict=True)
    ]
    frame = pd.DataFrame(rows)
    gap = (frame["P_star"] - frame["P_free"] - frame["I"]).abs()
    if gap.max() > 1e-10:
        raise AssertionError("P* is not equal to P_free* + I on a plotted grid")
    if (frame["P_star"] - frame["P_components"]).abs().max() > 1e-10:
        raise AssertionError("Component decomposition failed on a plotted grid")
    if frame["I"].min() < -1e-10:
        raise AssertionError("An institutional premium is negative")
    if not np.allclose(frame["z_low"], z_low) or not np.allclose(frame["z_high"], z_high):
        raise AssertionError("Productivity states were rematched")
    return frame


def rental_schedule(z_low: float, z_high: float, q_crit: float) -> pd.DataFrame:
    grid = np.linspace(Q_MIN, Q_MAX, 801)
    grid = np.unique(np.concatenate([grid, [q_crit, model.Q_CENTRAL, Q_EMPIRICAL_LOW, Q_EMPIRICAL_HIGH]]))
    frame = evaluate_grid(grid, model.RHO_CENTRAL, z_low, z_high, model.PI, model.A_R)
    below = frame["q"] < q_crit - 1e-12
    above = frame["q"] > q_crit + 1e-12
    if (frame.loc[below, "P_free"] - frame.loc[below, "q"]).abs().max() > 1e-9:
        raise AssertionError("P_free* is not equal to q below the threshold")
    if (frame.loc[above, "P_free"] - frame.loc[above, "P_star"]).abs().max() > 1e-9:
        raise AssertionError("P_free* and P* separate above the threshold")
    if frame.loc[above, "I"].abs().max() > 1e-9:
        raise AssertionError("Institutional premium does not vanish above the threshold")
    if not frame["interior_b1"].all() or not frame["interior_b0"].all():
        raise AssertionError("A rental-cost point is a bequest corner at the central altruism")
    saved = pd.read_csv(ARCHIVE / "sensitivity_q.csv")
    for target in (0.076, 0.12, 0.129, 0.209, 0.21, 0.218, 0.252, 0.265, 0.443):
        fresh = frame.iloc[(frame["q"] - target).abs().argmin()]
        if abs(fresh["q"] - target) > 1e-12:
            continue
        previous = saved.iloc[(saved["q"] - target).abs().argmin()]
        if abs(previous["P_star"] - fresh["P_star"]) > 1e-9 or abs(previous["I"] - fresh["I"]) > 1e-9:
            raise AssertionError(f"Rental schedule moved at q={target}")
    return frame.sort_values("q").reset_index(drop=True)


def probability_schedule(z_low: float, z_high: float) -> pd.DataFrame:
    grid = np.linspace(PI_MIN, PI_MAX, 601)
    frame = evaluate_grid(model.Q_CENTRAL, model.RHO_CENTRAL, z_low, z_high, grid, model.A_R)
    saved = pd.read_csv(ARCHIVE / "sensitivity_pi.csv")
    saved = saved.loc[saved["exercise"].eq("pi_fixed_support")]
    for record in saved.itertuples(index=False):
        fresh = frame.iloc[(frame["pi"] - record.pi).abs().argmin()]
        if abs(fresh["I"] - record.I) > 1e-9 or abs(fresh["P_star"] - record.P_star) > 1e-9:
            raise AssertionError(f"Fixed-support premium moved at pi={record.pi}")
        if abs(fresh["q_crit"] - record.q_crit) > 1e-12:
            raise AssertionError("Binding threshold moved in the fixed-support exercise")
    return frame


def rural_schedule(z_low: float, z_high: float, cities: dict) -> pd.DataFrame:
    grid = np.linspace(cities["a_r_min"], cities["a_r_max"], 601)
    grid = np.unique(np.concatenate([grid, [model.A_R, cities["a_r_p25"], cities["a_r_p75"]]]))
    frame = evaluate_grid(model.Q_CENTRAL, model.RHO_CENTRAL, z_low, z_high, model.PI, grid)
    saved = pd.read_csv(ARCHIVE / "sensitivity_a_r.csv")
    for record in saved.itertuples(index=False):
        fresh = model.evaluate_case(
            model.Q_CENTRAL, model.RHO_CENTRAL, z_low, z_high, pi=model.PI, a_r=float(record.a_r)
        )
        if abs(fresh["I"] - record.I) > 1e-9 or abs(fresh["z_low"] - z_low) > 1e-12:
            raise AssertionError(f"Rural-income premium moved at A_r={record.a_r}")
        if abs(fresh["z_high"] - z_high) > 1e-12:
            raise AssertionError("Changing A_r rematched the productivity states")
    return frame.sort_values("a_r").reset_index(drop=True)


def embedded_fonts(path: Path) -> list[str]:
    raw = path.read_bytes()
    found = re.findall(rb"/BaseFont\s*/([A-Za-z0-9+_-]+)", raw)
    names = sorted({item.decode("ascii").split("+")[-1] for item in found})
    banned = ("DejaVu", "Liberation", "Helvetica", "Arial", "Nimbus", "FreeSans", "FreeSerif")
    if any(any(token in name for token in banned) for name in names):
        raise RuntimeError(f"{path.name} embedded a substitute font: {names}")
    if not any("TimesNewRoman" in name for name in names):
        raise RuntimeError(f"{path.name} did not embed Times New Roman: {names}")
    if not any(name.startswith("STIX") for name in names):
        raise RuntimeError(f"{path.name} did not embed STIX math: {names}")
    return names


def save(fig: plt.Figure, stem: str) -> dict:
    png = OUT / f"{stem}.png"
    pdf = OUT / f"{stem}.pdf"
    fig.savefig(png, dpi=600)
    fig.savefig(pdf)
    plt.close(fig)
    return {"png": png.name, "pdf": pdf.name, "fonts": embedded_fonts(pdf)}


def figure_rental(schedule: pd.DataFrame, q_crit: float) -> plt.Figure:
    fig, ax = plt.subplots(figsize=(6.45, 3.85))
    ax.axvspan(
        Q_EMPIRICAL_LOW,
        Q_EMPIRICAL_HIGH,
        color=BAND,
        linewidth=0,
        zorder=0,
    )
    ax.fill_between(
        schedule["q"],
        schedule["P_free"],
        schedule["P_star"],
        where=schedule["P_star"] - schedule["P_free"] > 1e-10,
        interpolate=True,
        color=NAVY,
        alpha=0.16,
        linewidth=0,
        zorder=1,
    )
    ax.plot(schedule["q"], schedule["P_star"], color=NAVY, linewidth=1.35, solid_capstyle="round", zorder=3)
    ax.plot(
        schedule["q"],
        schedule["P_free"],
        color=CLAY,
        linewidth=1.25,
        linestyle=(0, (4.2, 2.1)),
        dash_capstyle="round",
        zorder=4,
    )
    ax.axvline(q_crit, color=REFERENCE, linewidth=0.7, linestyle=(0, (2.4, 2.0)), zorder=2)
    ax.annotate(
        r"$q^{\mathrm{crit}}$",
        xy=(q_crit, 1.0),
        xycoords=("data", "axes fraction"),
        xytext=(5, -4),
        textcoords="offset points",
        ha="left",
        va="top",
        fontsize=9,
        color=INK,
    )
    ax.set_xlim(Q_MIN, Q_MAX)
    ax.set_ylim(0.0, 0.36)
    ax.set_xticks([0.05, 0.15, 0.25, 0.35, 0.45])
    ax.set_yticks([0.0, 0.1, 0.2, 0.3])
    ax.set_xlabel(r"Normalized annual rental cost, $q$")
    ax.set_ylabel("One-period reservation value")
    handles = [
        Line2D([0], [0], color=NAVY, linewidth=1.35, label=r"$P^{*}$"),
        Line2D([0], [0], color=CLAY, linewidth=1.25, linestyle=(0, (4.2, 2.1)), label=r"$P_{\mathrm{free}}^{*}$"),
        Patch(facecolor=NAVY, alpha=0.16, edgecolor="none", label=r"$\mathcal{I}$"),
        Patch(facecolor=BAND, edgecolor="none", label="Empirical range"),
    ]
    legend = ax.legend(
        handles=handles,
        loc="upper left",
        frameon=False,
        handlelength=1.7,
        handletextpad=0.45,
        borderaxespad=0.2,
        labelspacing=0.25,
    )
    legend.set_zorder(5)
    polish(ax)
    fig.set_layout_engine("constrained")
    return fig


def figure_institutional(probability: pd.DataFrame, rural: pd.DataFrame, cities: dict) -> plt.Figure:
    fig, axes = plt.subplots(1, 2, figsize=(6.5, 3.22), sharey=True)
    upper = 0.15
    axes[0].plot(probability["pi"], probability["I"], color=NAVY, linewidth=1.35, solid_capstyle="round")
    axes[0].axvline(model.PI, color=REFERENCE, linewidth=0.7, linestyle=(0, (2.4, 2.0)), zorder=0)
    axes[0].set_xlim(0.18, 0.82)
    axes[0].set_xticks([0.2, 0.3, 0.4, 0.5, 0.6, 0.7, 0.8])
    axes[0].set_xlabel(r"Low-productivity probability, $\pi$")
    axes[0].set_ylabel(r"Institutional-access premium, $\mathcal{I}$")
    axes[0].set_title("(a)", loc="left", pad=3, color=INK)
    axes[0].legend(
        handles=[
            Line2D(
                [0],
                [0],
                color=REFERENCE,
                linewidth=0.7,
                linestyle=(0, (2.4, 2.0)),
                label=r"Baseline $\pi=0.5$",
            )
        ],
        loc="upper right",
        frameon=False,
        handlelength=1.6,
        handletextpad=0.45,
        borderaxespad=0.15,
    )

    axes[1].axvspan(cities["a_r_p25"], cities["a_r_p75"], color=BAND, linewidth=0, zorder=0)
    axes[1].plot(rural["a_r"], rural["I"], color=NAVY, linewidth=1.35, solid_capstyle="round", zorder=2)
    axes[1].axvline(model.A_R, color=REFERENCE, linewidth=0.7, linestyle=(0, (2.4, 2.0)), zorder=1)
    pad = 0.012
    axes[1].set_xlim(cities["a_r_min"] - pad, cities["a_r_max"] + pad)
    axes[1].set_xticks([0.30, 0.40, 0.50, 0.60])
    axes[1].set_xlabel(r"Rural income, $A_r$")
    axes[1].set_title("(b)", loc="left", pad=3, color=INK)
    handles = [
        Patch(facecolor=BAND, edgecolor="none", label="Interquartile range"),
        Line2D(
            [0],
            [0],
            color=REFERENCE,
            linewidth=0.7,
            linestyle=(0, (2.4, 2.0)),
            label=r"Baseline $A_r=0.386$",
        ),
    ]
    axes[1].legend(
        handles=handles,
        loc="lower right",
        bbox_to_anchor=(1.0, 1.012),
        ncol=2,
        frameon=False,
        handlelength=1.45,
        handletextpad=0.4,
        columnspacing=0.9,
        borderaxespad=0.0,
    )
    for ax in axes:
        ax.set_ylim(0.0, upper)
        ax.set_yticks([0.0, 0.05, 0.10, 0.15])
        polish(ax)
    fig.set_layout_engine("constrained")
    return fig


def housed_corner_probability(z_low: float, z_high: float) -> float:
    """Probability at which the housed bequest switches from a corner to an interior."""
    target = 1.0 / model.RHO_CENTRAL
    weight = (target - 1.0 / z_high) / (1.0 / z_low - 1.0 / z_high)
    return float(weight)


def main() -> None:
    resolved_font = register_times()
    use_journal_style()
    OUT.mkdir(parents=True, exist_ok=True)

    z_low, z_high, gap = model.productivity_states()
    q_crit = z_low * (model.W_U - model.A_R)
    cities = city_rural_income()
    rents = rental_schedule(z_low, z_high, q_crit)
    probability = probability_schedule(z_low, z_high)
    rural = rural_schedule(z_low, z_high, cities)
    corner = housed_corner_probability(z_low, z_high)
    checks = {
        "font_file": resolved_font,
        "font_family": "Times New Roman",
        "mathtext_fontset": "stix",
        "w_u": model.W_U,
        "a_r": model.A_R,
        "rho": model.RHO_CENTRAL,
        "pi": model.PI,
        "sigma_ln_z": model.SIGMA,
        "z_low": z_low,
        "z_high": z_high,
        "log_gap": gap,
        "q_central": model.Q_CENTRAL,
        "q_crit": q_crit,
        "q_axis": [Q_MIN, Q_MAX],
        "q_empirical_band": [Q_EMPIRICAL_LOW, Q_EMPIRICAL_HIGH],
        "pi_axis_curve": [PI_MIN, PI_MAX],
        "cities": cities,
        "housed_bequest_corner_pi": corner,
        "I_at_pi_0.2": float(probability.loc[(probability["pi"] - 0.2).abs().idxmin(), "I"]),
        "I_at_pi_0.5": float(probability.loc[(probability["pi"] - 0.5).abs().idxmin(), "I"]),
        "I_at_pi_0.8": float(probability.loc[(probability["pi"] - 0.8).abs().idxmin(), "I"]),
        "I_at_a_r_min": float(rural.iloc[0]["I"]),
        "I_at_a_r_max": float(rural.iloc[-1]["I"]),
        "P_star_at_q_min": float(rents.iloc[0]["P_star"]),
        "P_free_at_q_min": float(rents.iloc[0]["P_free"]),
        "P_star_at_q_max": float(rents.iloc[-1]["P_star"]),
        "max_abs_identity_gap_q": float((rents["P_star"] - rents["P_free"] - rents["I"]).abs().max()),
        "min_I_q": float(rents["I"].min()),
        "min_I_pi": float(probability["I"].min()),
        "min_I_ar": float(rural["I"].min()),
    }
    rent_fig = figure_rental(rents, q_crit)
    inst_fig = figure_institutional(probability, rural, cities)
    checks["figure_q_fonts"] = save(rent_fig, "fig05_rental_cost_sensitivity")
    checks["figure_institutional_fonts"] = save(inst_fig, "fig06_institutional_access_premium")
    (OUT / "publication_figure_checks.json").write_text(json.dumps(checks, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(checks, indent=2))


if __name__ == "__main__":
    main()
