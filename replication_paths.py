"""Project-relative paths for the replication package.

Executable scripts use this module instead of machine-specific directories.
Restricted inputs are read from ``REPLICATION_LOCAL_DATA`` when that variable
is set, and otherwise from ``data/local_only`` inside the package.
"""

from __future__ import annotations

import os
from pathlib import Path


def package_root() -> Path:
    return Path(__file__).resolve().parent


def local_root() -> Path:
    env = os.environ.get("REPLICATION_LOCAL_DATA")
    if env:
        return Path(env).expanduser().resolve()
    return package_root() / "data" / "local_only"


def city_sample() -> Path:
    return local_root() / "city" / "R1_estimation_sample_2014_2019.xlsx"


def mechanism_csv() -> Path:
    env = os.environ.get("CFPS_MECHANISM_CSV")
    if env:
        return Path(env).expanduser().resolve()
    return local_root() / "household" / "cfps_mechanism.csv"


def cfps_raw_dir() -> Path:
    env = os.environ.get("CFPS_RAW_DIR")
    if env:
        return Path(env).expanduser().resolve()
    return local_root() / "cfps"


def strict_workbook() -> Path:
    return local_root() / "city" / "strict.xlsx"


def county_crosswalk() -> Path:
    return local_root() / "cfps_geo" / "countyid_baseline162.dta"


def household_rebuild_dir() -> Path:
    return local_root() / "household" / "rebuild"


def public_income_dir() -> Path:
    return package_root() / "data" / "public" / "income_gap"
