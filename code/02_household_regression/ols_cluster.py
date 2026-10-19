"""Numpy-only OLS helpers with cluster-robust covariance.

Used by Part 2 Regression 2. Avoids heavy dependencies (statsmodels/linearmodels)
that may fail in some environments.
"""

from __future__ import annotations

import math

import numpy as np
import pandas as pd

SHANGHAI_CITY_CODE = 310000


def normal_cdf(z: float) -> float:
    return 0.5 * (1.0 + math.erf(z / (2.0**0.5)))


def two_sided_p_from_t(t: float) -> float:
    return 2.0 * (1.0 - normal_cdf(abs(t)))


def one_way_cluster_cov(
    X: pd.DataFrame, resid: pd.Series, clusters: pd.Series
) -> pd.DataFrame:
    """Cluster-robust covariance (one-way) via the score 'meat' formula."""
    keep = clusters.notna().values
    Xc = X.loc[keep]
    ec = resid.loc[keep]
    g = clusters.loc[keep]

    X_mat = Xc.to_numpy(dtype=float, copy=False)
    e_vec = ec.to_numpy(dtype=float, copy=False)
    k = X_mat.shape[1]
    xtx_inv = np.linalg.pinv(X_mat.T @ X_mat)

    meat = np.zeros((k, k), dtype=float)
    for grp in pd.unique(g):
        mask = (g == grp).values
        sg = X_mat[mask, :].T @ e_vec[mask]
        meat += np.outer(sg, sg)

    vcov = xtx_inv @ meat @ xtx_inv
    return pd.DataFrame(vcov, index=X.columns, columns=X.columns)


def two_way_cluster_cov(
    X: pd.DataFrame,
    resid: pd.Series,
    clusters1: pd.Series,
    clusters2: pd.Series,
) -> pd.DataFrame:
    """Two-way cluster covariance: V1 + V2 - V_{1∩2}."""
    inter = clusters1.astype("string") + "___" + clusters2.astype("string")
    return (
        one_way_cluster_cov(X, resid, clusters1)
        + one_way_cluster_cov(X, resid, clusters2)
        - one_way_cluster_cov(X, resid, inter)
    )


def year_dummies(df: pd.DataFrame, *, drop_first: bool) -> pd.DataFrame:
    years = sorted(pd.unique(df["year"].dropna()))
    if len(years) < 2:
        return pd.DataFrame(index=df.index)
    dummies = pd.get_dummies(df["year"], prefix="year", dtype=float)
    if drop_first:
        dummies = dummies[[f"year_{yy}" for yy in years[1:]]]
    return dummies


def to_float_frame(df: pd.DataFrame, cols: list[str]) -> pd.DataFrame:
    out = pd.DataFrame(index=df.index)
    for c in cols:
        out[c] = pd.to_numeric(df[c], errors="coerce").astype(float)
    return out
