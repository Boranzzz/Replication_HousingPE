"""City-level Regression 1 and the TWFE robustness columns.

Reads the reconstructed 2014-2019 city-year sample. Does not modify that file.
Formulas, clustering, the full-rank trend normalization, the leave-one-city-out
design, and the wild cluster bootstrap match the verified audit:

- Table 1 is fit on all 506 rows. trend = year - 2014.
- Column 3 demeans lnPOP and lnINC within city. urb stays in levels.
- TWFE controls enter in levels. Province fixed effects are not added
  alongside city fixed effects.
- The trend-adjusted interaction is reported from the full-rank design that
  drops the Beijing city trend. Leave-one-city-out drops the 2019 year dummy
  instead, so the omitted column does not disappear when a city is excluded.
- The wild cluster bootstrap is null-imposed, Rademacher, 9,999 draws, seed
  20261019. It does not replace the analytic clustered standard error.
"""

from __future__ import annotations

import json
import warnings
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import numpy as np
import pandas as pd
import patsy
import statsmodels.api as sm
from numpy.linalg import inv, matrix_rank
from scipy import stats

import sys

PACKAGE = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(PACKAGE))
from replication_paths import city_sample  # noqa: E402

TABLES = PACKAGE / "outputs" / "tables"
DIAG = PACKAGE / "outputs" / "diagnostics"
SEED = 20261019
BOOT_REPS = 9999

TABLE1 = {
    "col1_city_trends": "ln_rent_price_ratio ~ strict_mig + mig + C(city):trend",
    "col2_province_fe": "ln_rent_price_ratio ~ strict_mig + mig + C(province) + C(city):trend",
    "col3_controls": (
        "ln_rent_price_ratio ~ strict_mig + mig + lnPOP_demean + lnINC_demean + urb + C(city):trend"
    ),
}
TWFE_BASE = "ln_rent_price_ratio ~ mig + strict + strict_mig + C(city) + C(year)"
TWFE_CONTROLS = TWFE_BASE + " + lnPOP + lnINC + urb"
TWFE_TRENDS = TWFE_CONTROLS + " + C(city):trend"

PUBLISHED = {
    "col1_city_trends": (-0.3062, 0.068, 0.798),
    "col2_province_fe": (-0.3326, 0.119, 0.894),
    "col3_controls": (-0.3140, 0.068, 0.800),
}


def load() -> pd.DataFrame:
    sample_path = city_sample()
    if not sample_path.is_file():
        print(
            "INCOMPLETE: city regression requires "
            f"{sample_path.name} at {sample_path}. "
            "Set REPLICATION_LOCAL_DATA to the directory that contains "
            "city/R1_estimation_sample_2014_2019.xlsx, or place that file under "
            "data/local_only/city/. The workbook contains CREPRICE-derived rent "
            "and price and is not in the shareable archive."
        )
        raise SystemExit(2)
    df = pd.read_excel(sample_path, sheet_name="sample")
    df = df.sort_values(["city", "year"]).reset_index(drop=True)
    df["ln_rent_price_ratio"] = np.log(df["rent"] / df["price"])
    df["strict_mig"] = df["strict"] * df["mig"]
    df["trend"] = df["year"] - int(df["year"].min())
    df["lnPOP_demean"] = df["lnPOP"] - df.groupby("city")["lnPOP"].transform("mean")
    df["lnINC_demean"] = df["lnINC"] - df.groupby("city")["lnINC"].transform("mean")
    if len(df) != 506 or df["city"].nunique() != 85:
        raise RuntimeError(f"expected 506 rows and 85 cities, found {len(df)} and {df['city'].nunique()}")
    if int(df["year"].min()) != 2014 or int(df["year"].max()) != 2019:
        raise RuntimeError("expected years 2014-2019")
    return df


def design(df: pd.DataFrame, formula: str) -> tuple[pd.Series, pd.DataFrame]:
    y, x = patsy.dmatrices(formula, df, return_type="dataframe")
    if len(y) != len(df):
        raise RuntimeError("design dropped rows")
    return y.iloc[:, 0], x


def fit_cluster(y: pd.Series, x: pd.DataFrame, groups: np.ndarray):
    with warnings.catch_warnings(record=True) as caught:
        warnings.simplefilter("always")
        result = sm.OLS(y.to_numpy(), x.to_numpy()).fit(
            cov_type="cluster",
            cov_kwds={"groups": groups, "use_correction": True},
        )
    result.model.data.xnames = list(x.columns)
    return result


def interaction_row(result, columns: list[str], name: str, n_cities: int) -> dict:
    j = columns.index("strict_mig")
    beta = float(result.params[j])
    se = float(result.bse[j])
    return {
        "specification": name,
        "beta_interaction": beta,
        "se_city_cluster": se,
        "p_normal": float(result.pvalues[j]),
        "r_squared": float(result.rsquared),
        "nobs": int(result.nobs),
        "n_cities": n_cities,
        "rank": int(result.df_model + result.k_constant),
        "n_columns": len(columns),
    }


def cluster_se_vector(x: np.ndarray, y: np.ndarray, groups: np.ndarray) -> tuple[np.ndarray, np.ndarray]:
    beta = inv(x.T @ x) @ (x.T @ y)
    resid = y - x @ beta
    codes, _ = pd.factorize(groups, sort=False)
    g_count = int(codes.max()) + 1
    meat = np.zeros((x.shape[1], x.shape[1]))
    for g in range(g_count):
        idx = codes == g
        score = x[idx].T @ resid[idx]
        meat += np.outer(score, score)
    xtx_inv = inv(x.T @ x)
    n, k = x.shape
    scale = (g_count / (g_count - 1.0)) * ((n - 1.0) / (n - k))
    cov = scale * (xtx_inv @ meat @ xtx_inv)
    se = np.sqrt(np.clip(np.diag(cov), 0, None))
    return beta, se


def loo(x: pd.DataFrame, y: np.ndarray, cities: np.ndarray) -> pd.DataFrame:
    """Full-rank leave-one-city-out. Drops the 2019 year dummy on each subsample."""
    names = list(x.columns)
    x_np = x.to_numpy()
    rows = []
    for city in pd.unique(cities):
        mask = cities != city
        sub = x_np[mask]
        sub_names = names[:]
        keep = np.abs(sub).sum(axis=0) > 1e-10
        sub = sub[:, keep]
        sub_names = [name for name, flag in zip(sub_names, keep) if flag]
        drop_col = "C(year)[T.2019]"
        j_drop = sub_names.index(drop_col)
        sub = np.delete(sub, j_drop, axis=1)
        del sub_names[j_drop]
        beta, se = cluster_se_vector(sub, y[mask], cities[mask])
        idx = sub_names.index("strict_mig")
        z = beta[idx] / se[idx]
        rows.append(
            {
                "excluded_city": city,
                "n": int(mask.sum()),
                "n_cities": int(pd.unique(cities[mask]).size),
                "beta3": float(beta[idx]),
                "se": float(se[idx]),
                "p_normal": float(2 * stats.norm.sf(abs(z))),
                "rank": int(matrix_rank(sub)),
                "n_columns": int(sub.shape[1]),
            }
        )
    return pd.DataFrame(rows)


def wild_cluster_bootstrap(x: np.ndarray, y: np.ndarray, groups: np.ndarray, column: int) -> dict:
    rng = np.random.default_rng(SEED)
    keep = [i for i in range(x.shape[1]) if i != column]
    xr = x[:, keep]
    br = inv(xr.T @ xr) @ (xr.T @ y)
    fitted = xr @ br
    restricted_resid = y - fitted
    beta_hat, se_hat = cluster_se_vector(x, y, groups)
    t_hat = float(beta_hat[column] / se_hat[column])
    xtx_inv = inv(x.T @ x)
    bread_col = xtx_inv[:, column]
    v = x @ bread_col
    codes, _ = pd.factorize(groups, sort=False)
    g_count = int(codes.max()) + 1
    n, k = x.shape
    scale = (g_count / (g_count - 1.0)) * ((n - 1.0) / (n - k))
    slices = [np.flatnonzero(codes == g) for g in range(g_count)]
    weights = rng.choice(np.array([-1.0, 1.0]), size=(BOOT_REPS, g_count))
    beta_star = np.empty(BOOT_REPS)
    t_star = np.empty(BOOT_REPS)
    for b in range(BOOT_REPS):
        w = np.empty(n)
        for g, idx in enumerate(slices):
            w[idx] = weights[b, g]
        y_star = fitted + w * restricted_resid
        beta = xtx_inv @ (x.T @ y_star)
        u = y_star - x @ beta
        acc = 0.0
        vu = v * u
        for idx in slices:
            acc += float(vu[idx].sum()) ** 2
        se = np.sqrt(scale * acc)
        beta_star[b] = beta[column]
        t_star[b] = beta[column] / se if se > 0 else np.nan

    def p_value(draws: np.ndarray, observed: float) -> float:
        finite = draws[np.isfinite(draws)]
        return float((1 + np.sum(np.abs(finite) >= abs(observed))) / (BOOT_REPS + 1))

    return {
        "seed": SEED,
        "reps": BOOT_REPS,
        "weights": "Rademacher {-1, +1}",
        "null": "restricted model drops strict_mig",
        "beta_hat": float(beta_hat[column]),
        "se_analytic": float(se_hat[column]),
        "p_analytic_normal": float(2 * stats.norm.sf(abs(t_hat))),
        "p_bootstrap_coefficient": p_value(beta_star, beta_hat[column]),
        "p_bootstrap_t": p_value(t_star, t_hat),
    }


def main() -> None:
    TABLES.mkdir(parents=True, exist_ok=True)
    DIAG.mkdir(parents=True, exist_ok=True)
    df = load()
    groups = df["city"].to_numpy()
    rows = []
    for name, formula in TABLE1.items():
        y, x = design(df, formula)
        result = fit_cluster(y, x, groups)
        row = interaction_row(result, list(x.columns), name, int(df["city"].nunique()))
        published_b, published_se, published_r2 = PUBLISHED[name]
        row["matches_published_precision"] = (
            abs(row["beta_interaction"] - published_b) < 5e-5
            and abs(row["se_city_cluster"] - published_se) < 5e-4
            and abs(row["r_squared"] - published_r2) < 5e-4
        )
        rows.append(row)

    y1, x1 = design(df, TWFE_BASE)
    rows.append(interaction_row(fit_cluster(y1, x1, groups), list(x1.columns), "twfe", 85))
    y2, x2 = design(df, TWFE_CONTROLS)
    rows.append(interaction_row(fit_cluster(y2, x2, groups), list(x2.columns), "twfe_controls", 85))

    y3, x3 = design(df, TWFE_TRENDS)
    singular = fit_cluster(y3, x3, groups)
    rows.append(interaction_row(singular, list(x3.columns), "twfe_controls_trends_singular", 85))

    x_full = x3.drop(columns=["C(city)[北京]:trend"])
    full = fit_cluster(y3, x_full, groups)
    rows.append(interaction_row(full, list(x_full.columns), "twfe_controls_trends_full_rank", 85))

    table = pd.DataFrame(rows)
    table.to_csv(TABLES / "table01_city_regressions.csv", index=False)

    loo_frame = loo(x3, y3.to_numpy(), groups)
    loo_frame.to_csv(DIAG / "loo_trend_fullrank.csv", index=False)

    j = list(x_full.columns).index("strict_mig")
    boot = wild_cluster_bootstrap(x_full.to_numpy(), y3.to_numpy(), groups, j)
    (DIAG / "wild_cluster_bootstrap.json").write_text(json.dumps(boot, indent=2) + "\n")

    full_beta = float(table.loc[table.specification.eq("twfe_controls_trends_full_rank"), "beta_interaction"].iloc[0])
    check = {
        "nobs": 506,
        "cities": 85,
        "years": "2014-2019",
        "table1_col1": rows[0]["beta_interaction"],
        "twfe_controls": rows[4]["beta_interaction"],
        "trend_full_rank": full_beta,
        "trend_se": rows[6]["se_city_cluster"],
        "trend_p": rows[6]["p_normal"],
        "loo_min": float(loo_frame.beta3.min()),
        "loo_max": float(loo_frame.beta3.max()),
        "loo_all_negative": bool((loo_frame.beta3 < 0).all()),
        "bootstrap_p_coefficient": boot["p_bootstrap_coefficient"],
        "bootstrap_p_t": boot["p_bootstrap_t"],
    }
    (DIAG / "city_regression_checks.json").write_text(json.dumps(check, indent=2) + "\n")
    print(table[["specification", "beta_interaction", "se_city_cluster", "p_normal", "r_squared", "nobs"]].to_string(index=False))
    print(json.dumps(boot, indent=2))


if __name__ == "__main__":
    main()
