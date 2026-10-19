"""CFPS Reg2 mechanism check: child-age gradient.

Joint LPM with all five age-bin indicators and their interactions with
migrant status, on the preferred Top 60% Strict sample. Tests the
pre-enrollment timing prediction of Section 2.3 (school entry at age 6).

Outputs under output/reg2/:
  - cfps_reg2_age_gradient.csv
  - fig_reg2_age_gradient.pdf / .png   (main-text figure)
  - cfps_reg2_mechanism_appendix.tex   (full estimates)
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd

PROJECT_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(Path(__file__).resolve().parent))

from estimate_homeownership import (  # noqa: E402
    AGE_MAX,
    AGE_MIN,
    FULL_CONTROLS,
    _add_log_inc,
    filter_sample,
)
from cfps_reg2_age_gradient import plot_age_gradient  # noqa: E402
from ols_cluster import (  # noqa: E402
    one_way_cluster_cov,
    to_float_frame,
    two_sided_p_from_t,
    year_dummies,
)

from estimate_homeownership import mechanism_csv

OUT_DIR = PROJECT_ROOT / "outputs" / "tables" / "household"
FIG_DIR = PROJECT_ROOT / "outputs" / "figures"

AGE_BINS = ["child_0_2", "child_3_5", "child_6_8", "child_9_11", "child_12_15"]
AGE_BIN_LABELS = {
    "child_0_2": "Ages 0--2",
    "child_3_5": "Ages 3--5",
    "child_6_8": "Ages 6--8",
    "child_9_11": "Ages 9--11",
    "child_12_15": "Ages 12--15",
}
def _stars(p: float) -> str:
    if pd.isna(p):
        return ""
    if p < 0.01:
        return "***"
    if p < 0.05:
        return "**"
    if p < 0.1:
        return "*"
    return ""


def _ols_cluster(y: pd.Series, X: pd.DataFrame, clusters: pd.Series) -> dict:
    mask = y.notna().values
    for c in X.columns:
        mask &= X[c].notna().values
    Xc, yc, g = X.loc[mask], y.loc[mask], clusters.loc[mask]
    beta, *_ = np.linalg.lstsq(Xc.to_numpy(dtype=float), yc.to_numpy(dtype=float), rcond=None)
    params = pd.Series(beta, index=Xc.columns, dtype=float)
    resid = yc.to_numpy(dtype=float) - Xc.to_numpy(dtype=float) @ beta
    vc = one_way_cluster_cov(Xc, pd.Series(resid, index=Xc.index), g)
    se = pd.Series(np.sqrt(np.diag(vc)), index=Xc.columns, dtype=float)
    return {"params": params, "se": se, "nobs": int(len(Xc)), "n_cities": int(g.nunique()), "index": Xc.index}


def estimate_age_gradient(df: pd.DataFrame, *, strict_share: float = 0.60) -> pd.DataFrame:
    """Joint regression: Own = M + sum bins + sum M x bins + X + CityFE + YearFE."""
    sample, cut = filter_sample(df, strict_share=strict_share, drop_shanghai=False)
    d = _add_log_inc(sample)
    for b in AGE_BINS:
        d[f"m_x_{b}"] = d["migrant"] * d[b]

    core = ["migrant", *AGE_BINS, *[f"m_x_{b}" for b in AGE_BINS]]
    y = d["own_house"].astype(float)
    X = pd.concat(
        [
            pd.get_dummies(d["city_code"], prefix="city", dtype=float),
            to_float_frame(d, core + FULL_CONTROLS),
            year_dummies(d, drop_first=False).astype(float),
        ],
        axis=1,
    )
    fit = _ols_cluster(y, X, d["city_code"])
    rows = []
    for b in AGE_BINS:
        term = f"m_x_{b}"
        coef = float(fit["params"][term])
        se = float(fit["se"][term])
        p = float(two_sided_p_from_t(coef / se)) if se > 0 else float("nan")
        n_cell = int(((d.loc[fit["index"], "migrant"] == 1) & (d.loc[fit["index"], b] == 1)).sum())
        rows.append(
            {
                "bin": b,
                "label": AGE_BIN_LABELS[b],
                "coef": coef,
                "se": se,
                "p": p,
                "ci_lo": coef - 1.96 * se,
                "ci_hi": coef + 1.96 * se,
                "n_mx_cell": n_cell,
                "nobs": fit["nobs"],
                "n_cities": fit["n_cities"],
                "strict_share": strict_share,
                "strict_cutoff": cut,
            }
        )
    return pd.DataFrame(rows)


def latex_appendix(age_df: pd.DataFrame) -> str:
    lines = [
        r"\begin{table}[htbp]",
        r"\centering",
        r"\caption{Appendix: Full Child-Age Gradient Estimates}",
        r"\label{tab:cfps_reg2_mechanism_app}",
        r"\begin{threeparttable}",
        r"\begin{tabular}{lcccc}",
        r"\toprule",
        r"Age bin & Coefficient & SE & $p$-value & $M\times$bin cell $N$ \\",
        r"\midrule",
    ]
    for r in age_df.itertuples():
        lines.append(
            f"{r.label} & {r.coef:.3f}{_stars(r.p)} & {r.se:.3f} & {r.p:.3f} & {int(r.n_mx_cell)} \\\\"
        )
    lines += [
        r"\midrule",
        rf"Observations & \multicolumn{{4}}{{c}}{{{int(age_df.nobs.iloc[0]):,}}} \\",
        rf"Cities & \multicolumn{{4}}{{c}}{{{int(age_df.n_cities.iloc[0])}}} \\",
        r"\bottomrule",
        r"\end{tabular}",
        r"\begin{tablenotes}[flushleft]",
        r"\footnotesize",
        r"\item \textit{Notes:} Same sample construction as Table~\ref{tab:cfps_reg2_main} (Top 60\% Strict cities, respondents aged 25--50, full controls, city and year fixed effects). All five age-bin indicators and their interactions with migrant status enter jointly; the table reports the interaction coefficients plotted in Figure~\ref{fig:cfps_reg2_age_gradient}. City-clustered standard errors. $^{*}p<0.10$, $^{**}p<0.05$, $^{***}p<0.01$.",
        r"\end{tablenotes}",
        r"\end{threeparttable}",
        r"\end{table}",
        "",
    ]
    return "\n".join(lines)


def main() -> None:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    FIG_DIR.mkdir(parents=True, exist_ok=True)
    data_path = mechanism_csv()
    if not data_path.is_file():
        print(
            "INCOMPLETE: age-gradient regression requires cfps_mechanism.csv at "
            f"{data_path}, or CFPS_MECHANISM_CSV. Restricted microdata is not in the shareable archive."
        )
        raise SystemExit(2)
    df = pd.read_csv(data_path)
    missing = [c for c in AGE_BINS if c not in df.columns]
    if missing:
        raise SystemExit(
            f"Missing age-bin columns {missing}. The analysis file must be the "
            "HousingProject cfps_mechanism.csv built by the original household panel "
            "and Strict merge. This package does not rebuild CFPS microdata."
        )

    age_df = estimate_age_gradient(df, strict_share=0.60)
    age_df.to_csv(OUT_DIR / "cfps_reg2_age_gradient.csv", index=False, encoding="utf-8-sig")

    plot_age_gradient(age_df, FIG_DIR / "fig04_child_age_interaction")
    (OUT_DIR / "cfps_reg2_mechanism_appendix.tex").write_text(
        latex_appendix(age_df), encoding="utf-8"
    )

    summary = {
        "age_gradient": age_df.to_dict(orient="records"),
        "peak_bin": age_df.loc[age_df["coef"].idxmax(), "label"],
    }
    (OUT_DIR / "cfps_reg2_mechanism_summary.json").write_text(
        json.dumps(summary, ensure_ascii=False, indent=2), encoding="utf-8"
    )

    print(age_df[["label", "coef", "se", "p", "n_mx_cell"]].to_string(index=False))
    print(f"\nWrote figure + appendix table under {OUT_DIR}")


if __name__ == "__main__":
    main()
