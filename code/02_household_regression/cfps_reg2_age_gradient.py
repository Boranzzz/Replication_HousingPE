"""Publication figure for the CFPS child-age-gradient mechanism check."""

from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

AGE_BIN_TICKS = ["0–2", "3–5", "6–8", "9–11", "12–15"]
N_PRE_BINS = 2
PAPER_RED = "#A93226"
PAPER_TEAL = "#17817B"
GRID_GRAY = "0.88"
SPINE_GRAY = "0.35"


def _apply_paper_style() -> None:
    plt.rcParams.update(
        {
            "font.family": "serif",
            "font.serif": ["Times New Roman", "Times", "STIXGeneral"],
            "mathtext.fontset": "stix",
            "axes.labelsize": 10,
            "axes.titlesize": 10,
            "xtick.labelsize": 9,
            "ytick.labelsize": 9,
            "axes.linewidth": 0.7,
            "xtick.major.width": 0.7,
            "ytick.major.width": 0.7,
        }
    )


def plot_age_gradient(age_df: pd.DataFrame, out_stem: Path) -> None:
    """Plot joint interaction estimates and 95% confidence intervals."""
    _apply_paper_style()
    fig, ax = plt.subplots(figsize=(5.8, 3.5))

    n = len(age_df)
    x = np.arange(n)
    split = N_PRE_BINS - 0.5
    ax.axhline(0, color="0.45", lw=0.8, ls="--", zorder=1)
    ax.axvspan(-0.5, split, color=PAPER_TEAL, alpha=0.07, zorder=0)
    ax.axvline(split, color=PAPER_TEAL, lw=0.8, ls=":", alpha=0.6, zorder=1)

    ax.text(
        (-0.5 + split) / 2,
        0.955,
        "before school entry",
        transform=ax.get_xaxis_transform(),
        ha="center",
        va="top",
        fontsize=8.5,
        style="italic",
        color=PAPER_TEAL,
    )
    ax.text(
        (split + n - 0.5) / 2,
        0.955,
        "after school entry",
        transform=ax.get_xaxis_transform(),
        ha="center",
        va="top",
        fontsize=8.5,
        style="italic",
        color="0.45",
    )

    ax.errorbar(
        x,
        age_df["coef"],
        yerr=1.96 * age_df["se"],
        fmt="o",
        color=PAPER_RED,
        ecolor=PAPER_RED,
        elinewidth=1.1,
        capsize=3.5,
        capthick=1.1,
        markersize=5.5,
        markerfacecolor=PAPER_RED,
        markeredgecolor="white",
        markeredgewidth=0.6,
        zorder=3,
    )
    ax.plot(x, age_df["coef"], color=PAPER_RED, lw=0.9, alpha=0.35, zorder=2)

    ax.set_xticks(x)
    ax.set_xticklabels(AGE_BIN_TICKS)
    ax.set_xlabel("Child age (years)")
    ax.set_ylabel(r"Coefficient on $M \times$ child-age bin")
    ax.set_xlim(-0.5, n - 0.5)
    lo = float((age_df["coef"] - 1.96 * age_df["se"]).min())
    hi = float((age_df["coef"] + 1.96 * age_df["se"]).max())
    pad = 0.12 * (hi - lo)
    ax.set_ylim(lo - pad, hi + 2.4 * pad)

    ax.yaxis.grid(True, color=GRID_GRAY, lw=0.6, zorder=0)
    ax.set_axisbelow(True)
    for side in ("top", "right"):
        ax.spines[side].set_visible(False)
    for side in ("left", "bottom"):
        ax.spines[side].set_color(SPINE_GRAY)
    ax.tick_params(colors=SPINE_GRAY, labelcolor="black")

    fig.tight_layout()
    fig.savefig(out_stem.with_suffix(".pdf"), bbox_inches="tight")
    fig.savefig(out_stem.with_suffix(".png"), dpi=300, bbox_inches="tight")
    plt.close(fig)
