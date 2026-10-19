"""CFPS Part 2 Regression 2: intergenerational insurance (strong-mechanism design).

Main equation (LPM):
  OwnHouse = b1*M + b2*Child + b3*(M x Child) + X + CityFE + YearFE

Sample:
  - Urban CFPS households, 2014/2016/2018
  - Financial respondent age in [25, 50]
  - Optional high-Strict city subsample (aligned with Part 1)
  - Child windows: preschool_age (0-5), child_0_15, school_age (6-15)

Outputs (under output/reg2/):
  - cfps_reg2_column_results.csv
  - cfps_reg2_cell_counts.csv
  - summaries JSON
"""

from __future__ import annotations

import json
import math
import sys
from dataclasses import dataclass
from pathlib import Path

import numpy as np
import pandas as pd

PACKAGE = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(PACKAGE))
sys.path.insert(0, str(Path(__file__).resolve().parent))

from ols_cluster import (  # noqa: E402
    SHANGHAI_CITY_CODE,
    one_way_cluster_cov,
    to_float_frame,
    two_sided_p_from_t,
    two_way_cluster_cov,
    year_dummies,
)
from replication_paths import mechanism_csv  # noqa: E402

OUT_DIR = PACKAGE / "outputs" / "tables" / "household"

AGE_MIN = 25
AGE_MAX = 50
CHILD_VARS = ("preschool_age", "child_0_15", "school_age")
CHILD_LABELS = {
    "preschool_age": "PreschoolAge (0--5)",
    "child_0_15": "ChildAges 0--15",
    "school_age": "SchoolAge (6--15)",
}
DEMO_CONTROLS = ["age", "gender", "eduy", "mar"]
FULL_CONTROLS = ["age", "gender", "eduy", "mar", "hukou_status", "familysize", "log_inc_pc"]


@dataclass(frozen=True)
class ColumnSpec:
    col_id: str
    label: str
    panel: str  # main | appendix
    strict_share: float | None  # None = all cities; else top share e.g. 0.60
    child_var: str
    controls: str  # none | demo | full
    drop_shanghai: bool = False


# Main table columns (1)-(5) + appendix A1 stepwise / A2 thresholds / A3 no Shanghai
MAIN_SPECS = [
    ColumnSpec("1", "All cities", "main", None, "preschool_age", "full"),
    ColumnSpec("2", "Top 75\\% Strict", "main", 0.75, "preschool_age", "full"),
    ColumnSpec("3", "Top 60\\% Strict", "main", 0.60, "preschool_age", "full"),
    ColumnSpec("4", "Top 60\\% Strict", "main", 0.60, "child_0_15", "full"),
    ColumnSpec("5", "Top 60\\% Strict", "main", 0.60, "school_age", "full"),
]

APPENDIX_SPECS = [
    # A1: stepwise controls on main sample (top 60% strict, preschool)
    ColumnSpec("A1a", "FE only", "appendix_A1", 0.60, "preschool_age", "none"),
    ColumnSpec("A1b", "+ demographics", "appendix_A1", 0.60, "preschool_age", "demo"),
    ColumnSpec("A1c", "+ hukou", "appendix_A1", 0.60, "preschool_age", "demo_hukou"),
    ColumnSpec("A1d", "+ all controls", "appendix_A1", 0.60, "preschool_age", "full"),
    # A2: threshold sensitivity
    ColumnSpec("A2a", "Top 75\\% Strict", "appendix_A2", 0.75, "preschool_age", "full"),
    ColumnSpec("A2b", "Top 67\\% Strict", "appendix_A2", 0.67, "preschool_age", "full"),
    ColumnSpec("A2c", "Top 60\\% Strict", "appendix_A2", 0.60, "preschool_age", "full"),
    ColumnSpec("A2d", "Top 50\\% Strict", "appendix_A2", 0.50, "preschool_age", "full"),
    # A3: drop Shanghai
    ColumnSpec("A3a", "Top 60\\% Strict", "appendix_A3", 0.60, "preschool_age", "full", False),
    ColumnSpec("A3b", "Top 60\\% Strict, drop Shanghai", "appendix_A3", 0.60, "preschool_age", "full", True),
    ColumnSpec("A3c", "Top 75\\% Strict, drop Shanghai", "appendix_A3", 0.75, "preschool_age", "full", True),
]


def _add_log_inc(df: pd.DataFrame) -> pd.DataFrame:
    out = df.copy()
    out["log_inc_pc"] = np.nan
    pos = out["inc_pc"].notna() & (out["inc_pc"] > 0)
    out.loc[pos, "log_inc_pc"] = np.log(out.loc[pos, "inc_pc"].astype(float))
    return out


def filter_sample(
    df: pd.DataFrame,
    *,
    strict_share: float | None,
    drop_shanghai: bool,
    age_min: int = AGE_MIN,
    age_max: int = AGE_MAX,
) -> tuple[pd.DataFrame, float | None]:
    """Age window + optional top-Strict city filter."""
    out = df.copy()
    out = out[out["age"].between(age_min, age_max)].copy()
    threshold = None
    if strict_share is not None:
        city_vals = out.groupby("city_code")["strict"].mean()
        # top share of cities by mean Strict within the age-restricted sample's cities
        # Use full-data city means for stable ranking
        city_vals_full = df.groupby("city_code")["strict"].mean()
        threshold = float(city_vals_full.quantile(1.0 - strict_share))
        keep = city_vals_full[city_vals_full >= threshold].index
        out = out[out["city_code"].isin(keep)].copy()
    if drop_shanghai:
        out = out[out["city_code"] != SHANGHAI_CITY_CODE].copy()
    return out, threshold


def _control_terms(controls: str) -> list[str]:
    if controls == "none":
        return []
    if controls == "demo":
        return list(DEMO_CONTROLS)
    if controls == "demo_hukou":
        return DEMO_CONTROLS + ["hukou_status"]
    if controls == "full":
        return list(FULL_CONTROLS)
    raise ValueError(f"Unknown controls mode: {controls}")


def build_design(
    df: pd.DataFrame,
    *,
    child_var: str,
    controls: str,
) -> tuple[pd.Series, pd.DataFrame, list[str]]:
    if child_var not in CHILD_VARS:
        raise ValueError(f"Unsupported child_var: {child_var}")

    d = _add_log_inc(df)
    d[child_var] = d[child_var].astype("Int64")
    d["migrant_x_child"] = d["migrant"] * d[child_var]

    core = ["migrant", child_var, "migrant_x_child"]
    ctrl = _control_terms(controls)
    y = d["own_house"].astype(float)
    blocks = [
        pd.get_dummies(d["city_code"], prefix="city", dtype=float),
        to_float_frame(d, core + ctrl),
        year_dummies(d, drop_first=False).astype(float),
    ]
    X = pd.concat(blocks, axis=1)
    return y, X, core


def estimate_column(df: pd.DataFrame, spec: ColumnSpec) -> dict:
    sample, threshold = filter_sample(
        df,
        strict_share=spec.strict_share,
        drop_shanghai=spec.drop_shanghai,
    )
    y, X, core = build_design(sample, child_var=spec.child_var, controls=spec.controls)

    mask = y.notna().values
    for c in X.columns:
        mask &= X[c].notna().values
    d_cc = sample.loc[mask].copy()
    y_cc = y.loc[mask]
    X_cc = X.loc[mask].copy()

    beta, *_ = np.linalg.lstsq(X_cc.to_numpy(dtype=float), y_cc.to_numpy(dtype=float), rcond=None)
    params = pd.Series(beta, index=X_cc.columns, dtype=float)
    resid = y_cc.to_numpy(dtype=float) - X_cc.to_numpy(dtype=float) @ beta

    vc_city = one_way_cluster_cov(X_cc, pd.Series(resid, index=X_cc.index), d_cc["city_code"])
    se_city = pd.Series(np.sqrt(np.diag(vc_city)), index=X_cc.columns, dtype=float)
    vc_2w = two_way_cluster_cov(
        X_cc,
        pd.Series(resid, index=X_cc.index),
        d_cc["city_code"],
        d_cc["fid10"],
    )
    se_2w = pd.Series(np.sqrt(np.diag(vc_2w)), index=X_cc.columns, dtype=float)

    def _pack(term: str) -> dict:
        coef = float(params[term])
        se = float(se_city[term])
        p = float(two_sided_p_from_t(coef / se)) if se > 0 else float("nan")
        se2 = float(se_2w[term])
        p2 = float(two_sided_p_from_t(coef / se2)) if se2 > 0 else float("nan")
        return {
            "term": term,
            "coef": coef,
            "se_city": se,
            "p_city": p,
            "se_two_way": se2,
            "p_two_way": p2,
        }

    n_mxp = int(((d_cc["migrant"] == 1) & (d_cc[spec.child_var] == 1)).sum())
    row = {
        "col_id": spec.col_id,
        "panel": spec.panel,
        "label": spec.label,
        "strict_share": spec.strict_share,
        "strict_cutoff": threshold,
        "child_var": spec.child_var,
        "controls": spec.controls,
        "drop_shanghai": spec.drop_shanghai,
        "nobs": int(len(d_cc)),
        "n_cities": int(d_cc["city_code"].nunique()),
        "n_households": int(d_cc["fid10"].nunique()),
        "n_migrant": int((d_cc["migrant"] == 1).sum()),
        "n_mxp_cell": n_mxp,
        "years": ",".join(str(int(y)) for y in sorted(d_cc["year"].dropna().unique())),
    }
    for term in core:
        packed = _pack(term)
        prefix = {
            "migrant": "m",
            spec.child_var: "child",
            "migrant_x_child": "mxp",
        }[term]
        row[f"{prefix}_coef"] = packed["coef"]
        row[f"{prefix}_se"] = packed["se_city"]
        row[f"{prefix}_p"] = packed["p_city"]
        row[f"{prefix}_se_2w"] = packed["se_two_way"]
        row[f"{prefix}_p_2w"] = packed["p_two_way"]
    return row


def cell_counts(df: pd.DataFrame, spec: ColumnSpec) -> pd.DataFrame:
    sample, _ = filter_sample(
        df,
        strict_share=spec.strict_share,
        drop_shanghai=spec.drop_shanghai,
    )
    sample = _add_log_inc(sample)
    # complete-case aligned with full-controls columns when controls=full
    need = ["own_house", "migrant", spec.child_var, "age", "gender", "eduy", "mar"]
    if spec.controls in {"demo_hukou", "full"}:
        need.append("hukou_status")
    if spec.controls == "full":
        need += ["familysize", "log_inc_pc"]
    cc = sample.dropna(subset=need).copy()
    g = (
        cc.groupby(["migrant", spec.child_var], dropna=False)
        .agg(n=("own_house", "size"), own_rate=("own_house", "mean"))
        .reset_index()
    )
    g["col_id"] = spec.col_id
    g["child_var"] = spec.child_var
    return g


def run_all(df: pd.DataFrame) -> tuple[pd.DataFrame, pd.DataFrame]:
    specs = MAIN_SPECS + APPENDIX_SPECS
    rows = [estimate_column(df, s) for s in specs]
    results = pd.DataFrame(rows)
    cells = pd.concat([cell_counts(df, s) for s in MAIN_SPECS], ignore_index=True)
    return results, cells


def main() -> None:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    data_path = mechanism_csv()
    if not data_path.is_file():
        print(
            "INCOMPLETE: household regression requires the CFPS analysis file "
            f"cfps_mechanism.csv. Looked for {data_path}. "
            "Place the authorized file there, set CFPS_MECHANISM_CSV, "
            "or set REPLICATION_LOCAL_DATA to the directory that contains "
            "household/cfps_mechanism.csv. "
            "The file is restricted microdata and is not in the shareable archive."
        )
        raise SystemExit(2)
    df = pd.read_csv(data_path)
    results, cells = run_all(df)

    results_path = OUT_DIR / "cfps_reg2_column_results.csv"
    cells_path = OUT_DIR / "cfps_reg2_cell_counts.csv"
    results.to_csv(results_path, index=False, encoding="utf-8-sig")
    cells.to_csv(cells_path, index=False, encoding="utf-8-sig")

    summary = {
        "age_window": [AGE_MIN, AGE_MAX],
        "restrict_measure": "strict = h*(1+h2)",
        "main_column": "3 (Top 60% Strict, PreschoolAge, full controls)",
        "n_columns": len(results),
        "main_nobs": int(results.loc[results["col_id"] == "3", "nobs"].iloc[0]),
        "main_mxp_cell": int(results.loc[results["col_id"] == "3", "n_mxp_cell"].iloc[0]),
        "outputs": [str(results_path), str(cells_path)],
    }
    (OUT_DIR / "cfps_reg2_summary.json").write_text(
        json.dumps(summary, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )

    # concise console preview
    preview = results[results["panel"] == "main"][
        ["col_id", "label", "child_var", "nobs", "n_cities", "n_mxp_cell", "mxp_coef", "mxp_se", "mxp_p"]
    ]
    print(preview.to_string(index=False))
    print(f"\nWrote {results_path}")
    print(f"Wrote {cells_path}")


if __name__ == "__main__":
    main()
