"""Appendix figure: leave-one-city-out coefficients, TWFE + controls + city trends."""

import json
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import pandas as pd
from matplotlib import font_manager

PACKAGE = Path(__file__).resolve().parents[2]
SRC = PACKAGE / "outputs" / "diagnostics" / "loo_trend_fullrank.csv"
CHECKS = PACKAGE / "outputs" / "diagnostics" / "city_regression_checks.json"
OUT = PACKAGE / "outputs" / "figures"

ENGLISH = {
    "北京": "Beijing",
    "深圳": "Shenzhen",
    "徐州": "Xuzhou",
    "重庆": "Chongqing",
}


def main() -> None:
    regular = "/System/Library/Fonts/Supplemental/Times New Roman.ttf"
    bold = "/System/Library/Fonts/Supplemental/Times New Roman Bold.ttf"
    font_manager.fontManager.addfont(regular)
    font_manager.fontManager.addfont(bold)
    plt.rcParams.update(
        {
            "font.family": "Times New Roman",
            "font.size": 10,
            "axes.labelsize": 11,
            "axes.linewidth": 0.6,
            "xtick.labelsize": 9,
            "ytick.labelsize": 9,
            "pdf.fonttype": 42,
            "ps.fonttype": 42,
            "axes.unicode_minus": False,
        }
    )

    full = json.loads(CHECKS.read_text())["trend_full_rank"]
    frame = pd.read_csv(SRC).sort_values("beta3").reset_index(drop=True)
    frame["order"] = frame.index + 1
    if not (frame["beta3"] < 0).all():
        raise RuntimeError("expected every leave-one-city-out coefficient to be negative")

    fig, ax = plt.subplots(figsize=(6.4, 4.6))
    ax.scatter(
        frame["beta3"],
        frame["order"],
        s=16,
        c="black",
        marker="o",
        linewidths=0,
        zorder=3,
    )
    ax.axvline(full, color="black", linewidth=0.8, zorder=2, label=f"Full sample ({full:.3f})")
    ax.axvline(0, color="0.35", linewidth=0.7, linestyle=(0, (3, 2)), zorder=1, label="Zero")

    # Hand-placed so the four labels sit in the open region between the cluster and zero.
    anchors = {
        "Beijing": (-0.15, 70),
        "Shenzhen": (-0.15, 56),
        "Chongqing": (-0.15, 42),
        "Xuzhou": (-0.30, 16),
    }
    for city_cn, name in ENGLISH.items():
        row = frame.loc[frame["excluded_city"] == city_cn].iloc[0]
        text_x, text_y = anchors[name]
        ax.annotate(
            name,
            xy=(row["beta3"], row["order"]),
            xytext=(text_x, text_y),
            fontsize=10,
            color="black",
            ha="left",
            va="center",
            arrowprops={
                "arrowstyle": "-",
                "color": "black",
                "linewidth": 0.4,
                "shrinkA": 0,
                "shrinkB": 2,
            },
            zorder=4,
        )

    ax.set_xlim(-0.68, 0.08)
    ax.set_ylim(0, 90)
    ax.set_xlabel("Leave-one-city-out coefficient on migration \u00d7 strictness")
    ax.set_ylabel("Cities ordered from smallest to largest coefficient")
    ax.set_yticks([])
    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)
    ax.tick_params(axis="x", width=0.6, length=3.5)
    legend = ax.legend(
        frameon=False,
        loc="lower right",
        bbox_to_anchor=(0.98, 0.04),
        handlelength=1.6,
        borderaxespad=0.2,
    )
    for text in legend.get_texts():
        text.set_fontname("Times New Roman")

    fig.tight_layout()
    OUT.mkdir(parents=True, exist_ok=True)
    png = OUT / "loo_city_trends_only.png"
    pdf = OUT / "loo_city_trends_only.pdf"
    fig.savefig(png, dpi=600)
    fig.savefig(pdf)
    plt.close(fig)
    print(png)
    print(pdf)


if __name__ == "__main__":
    main()
