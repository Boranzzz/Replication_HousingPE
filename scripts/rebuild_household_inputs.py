"""Rebuild the CFPS household file from authorized raw inputs.

Writes only under this package. Does not run the HousingProject scripts in
place and does not replace data/local_only/household/cfps_mechanism.csv.
A rebuilt file is saved separately and compared with the prepared file.
"""

from __future__ import annotations

import sys
from pathlib import Path

import pandas as pd

PACKAGE = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PACKAGE))
CODE = PACKAGE / "code" / "02_household_regression"
sys.path.insert(0, str(CODE))

from replication_paths import (  # noqa: E402
    cfps_raw_dir,
    county_crosswalk,
    household_rebuild_dir,
    mechanism_csv,
    strict_workbook,
)


def _missing_inputs() -> list[str]:
    notes = []
    raw = cfps_raw_dir()
    if not raw.is_dir():
        notes.append(
            "Official CFPS .dta files were not found at "
            f"{raw}. Set CFPS_RAW_DIR to the folder that contains the wave "
            "subdirectories, or place them in REPLICATION_LOCAL_DATA/cfps. "
            "Those files are restricted and are not in the shareable archive."
        )
    strict = strict_workbook()
    if not strict.is_file():
        notes.append(
            "The hukou workbook strict.xlsx was not found at "
            f"{strict}. Place it in REPLICATION_LOCAL_DATA/city/ or "
            "data/local_only/city/. It is not in the shareable archive."
        )
    crosswalk = county_crosswalk()
    if not crosswalk.is_file():
        notes.append(
            "The county crosswalk countyid_baseline162.dta was not found at "
            f"{crosswalk}. Place it in REPLICATION_LOCAL_DATA/cfps_geo/. "
            "No script in this package builds that crosswalk."
        )
    return notes


def _compare(rebuilt: Path, prepared: Path) -> None:
    out_dir = PACKAGE / "outputs" / "diagnostics" / "cfps_rebuild"
    out_dir.mkdir(parents=True, exist_ok=True)
    report = out_dir / "rebuild_comparison.csv"
    if not prepared.is_file():
        pd.DataFrame(
            [{"check": "prepared_file", "status": "absent", "detail": str(prepared)}]
        ).to_csv(report, index=False)
        print(f"Rebuilt file written. Prepared analysis file was not available for comparison: {prepared}")
        return
    left = pd.read_csv(rebuilt)
    right = pd.read_csv(prepared)
    keys = ["year", "fid"]
    for frame in (left, right):
        frame["year"] = pd.to_numeric(frame["year"], errors="coerce").astype("int64")
        frame["fid"] = frame["fid"].astype(str).str.replace(r"\.0$", "", regex=True)
    left_keys = left[keys].astype(str).agg("|".join, axis=1)
    right_keys = right[keys].astype(str).agg("|".join, axis=1)
    shared_cols = sorted(set(left.columns).intersection(right.columns) - set(keys))
    numeric = [
        col
        for col in shared_cols
        if pd.api.types.is_numeric_dtype(left[col]) and pd.api.types.is_numeric_dtype(right[col])
    ]
    merged = left[keys + numeric].merge(
        right[keys + numeric],
        on=keys,
        how="outer",
        suffixes=("_rebuilt", "_prepared"),
        indicator=True,
    )
    rows = [
        {"check": "rows_rebuilt", "status": "info", "detail": len(left)},
        {"check": "rows_prepared", "status": "info", "detail": len(right)},
        {
            "check": "key_overlap",
            "status": "match" if set(left_keys) == set(right_keys) else "differ",
            "detail": int((merged["_merge"] == "both").sum()),
        },
    ]
    both = merged[merged["_merge"].eq("both")]
    max_gap = 0.0
    for col in numeric:
        gap = (both[f"{col}_rebuilt"] - both[f"{col}_prepared"]).abs()
        gap = gap[gap.notna()]
        value = float(gap.max()) if len(gap) else 0.0
        max_gap = max(max_gap, value)
        rows.append(
            {
                "check": f"max_abs_{col}",
                "status": "match" if value <= 1e-8 else "differ",
                "detail": value,
            }
        )
    status = "match" if max_gap <= 1e-8 and set(left_keys) == set(right_keys) else "differ"
    rows.append({"check": "overall", "status": status, "detail": max_gap})
    pd.DataFrame(rows).to_csv(report, index=False)
    print(f"Comparison status: {status}. Largest numeric gap: {max_gap}")
    print(f"Wrote {report}")
    print("The prepared analysis file was not replaced.")


def main() -> None:
    notes = _missing_inputs()
    if notes:
        print("INCOMPLETE: the CFPS analysis file cannot be rebuilt from raw inputs.")
        for note in notes:
            print(note)
        raise SystemExit(2)

    from merging import cfps_household_panel, cfps_strict

    cfps_household_panel.main()
    cfps_strict.main()
    rebuilt = household_rebuild_dir() / "cfps_mechanism_rebuilt.csv"
    _compare(rebuilt, mechanism_csv())


if __name__ == "__main__":
    main()
