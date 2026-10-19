"""Build the CFPS 2012-2022 household-year panel for the Part-2 regression.

Pipeline (per docs/cfps_regression_spec.md):

  famecon (one row per household)
    + financial respondent's person-level traits (migrant, controls)
    + famconf roster aggregate (school_age, marriage)
  -> household-year panel, unique on (year, fid)

Run from project root:
    python -m src.merge.cfps_household_panel
"""

from __future__ import annotations

import sys
from pathlib import Path

import pandas as pd

_PACKAGE = Path(__file__).resolve().parents[3]
_CODE = Path(__file__).resolve().parents[1]
for _path in (_PACKAGE, _CODE):
    if str(_path) not in sys.path:
        sys.path.insert(0, str(_path))

from cleaning.cfps_config import INTERIM, OUTPUT, WAVES
from cleaning.cfps_load import (
    load_crossyearid_migrant,
    load_famecon,
    load_person,
    load_resp_children,
    load_roster,
)
from variables.cfps_mechanism import (
    backfill_hukou_loc,
    build_migrant,
    build_migrant_from_crossyearid,
    build_own_house,
    build_resp_child_flags,
    build_school_age,
)

PANEL_PATH = INTERIM / "cfps_household_panel.csv"
REPORT_PATH = OUTPUT / "pipeline" / "cfps_panel_quality.md"

CHILD_BIN_COLS = ["child_0_2", "child_3_5", "child_6_8", "child_9_11", "child_12_15"]


def build_person_long() -> pd.DataFrame:
    """Stack person files across waves and backfill skipped hukou answers."""
    frames = [load_person(year) for year in WAVES]
    long = pd.concat(frames, ignore_index=True)
    return backfill_hukou_loc(long)


def build_wave(year: int, person_long: pd.DataFrame) -> pd.DataFrame:
    """Assemble one household-year cross-section."""
    fam = load_famecon(year)
    roster = load_roster(year)

    fam["own_house"] = build_own_house(fam["own_raw"])
    children = load_resp_children(year)
    child_flags = build_resp_child_flags(children, year, fam["fid"])
    fam = fam.merge(child_flags, on="fid", how="left")
    for col in ["school_age", "preschool_age", "child_0_15", *CHILD_BIN_COLS]:
        fam[col] = fam[col].fillna(0).astype("Int64")
    # Legacy broad definition for comparison / diagnostics.
    fam = fam.merge(build_school_age(roster), on="fid", how="left")

    # Financial respondent's individual traits (incl. filled hukou location)
    person = person_long[person_long["year"] == year]
    person = person[["pid", "age", "gender", "eduy", "hukou_status",
                     "hukou_loc_filled"]].rename(columns={"pid": "resp_pid"})
    fam = fam.merge(person, on="resp_pid", how="left")

    # Main definition (all years): hukou location relative to current
    # residence (qa302/pa302, categories 4+ = outside county), with
    # cross-wave backfill for the 2016+ skip pattern.
    #
    # NOTE: crossyearid migrantYY is NOT hukou-based. Its label is
    # "人户分离或区县及以上搬迁"; in 2012, 68% of migrantYY=1 respondents
    # report LOCAL hukou in qa302. It is kept only as a reference column.
    fam["migrant"] = build_migrant(fam["hukou_loc_filled"], year)

    cy = load_crossyearid_migrant(year)
    if len(cy):
        fam = fam.merge(cy, left_on="resp_pid", right_on="pid", how="left")
        fam["migrant_moved"] = build_migrant_from_crossyearid(fam["migrant_cy"])
        fam = fam.drop(columns=["pid", "migrant_cy"], errors="ignore")
    else:
        fam["migrant_moved"] = pd.NA

    # Respondent's marriage from the roster row
    marriage = roster[["fid", "pid", "marriage"]].rename(
        columns={"pid": "resp_pid"}
    )
    fam = fam.merge(marriage, on=["fid", "resp_pid"], how="left")
    fam["mar"] = fam["marriage"].isin([2, 3]).astype("Int64").where(
        fam["marriage"].notna()
    )

    keep = ["year", "fid", "fid10", "resp_pid", "provcd", "countyid", "urban",
            "own_house", "migrant", "migrant_moved",
            "school_age", "preschool_age", "child_0_15", *CHILD_BIN_COLS,
            "school_age_any",
            "age", "gender", "eduy", "hukou_status", "mar",
            "familysize", "inc_pc", "weight"]
    out = fam[keep]
    assert not out.duplicated(["year", "fid"]).any(), f"{year}: fid not unique"
    return out


def quality_report(panel: pd.DataFrame) -> str:
    """Markdown data-quality summary by wave."""
    lines = [
        "# CFPS 家庭面板质量报告",
        "",
        f"文件: `{PANEL_PATH.relative_to(_PACKAGE)}`",
        "",
        f"总观测: {len(panel):,} household-years, "
        f"跨期家庭 (fid10): {panel['fid10'].nunique():,}",
        "",
        "## 分年概览",
        "",
        "| 年份 | 户数 | own_house 缺失 | own 率 | migrant 缺失 | mig 率 "
        "| school_age 率 | preschool 率 | child_0_15 率 | 城镇占比 | resp 匹配率 |",
        "|------|------|---------------|--------|--------------|--------"
        "|--------------|-------------|-------------|----------|-------------|",
    ]
    for year, g in panel.groupby("year"):
        n = len(g)
        own_miss = g["own_house"].isna().mean()
        mig_miss = g["migrant"].isna().mean()
        resp_match = g["age"].notna().mean()
        lines.append(
            f"| {year} | {n:,} "
            f"| {own_miss:.1%} | {g['own_house'].mean():.3f} "
            f"| {mig_miss:.1%} | {g['migrant'].mean():.3f} "
            f"| {g['school_age'].mean():.3f} "
            f"| {g['preschool_age'].mean():.3f} "
            f"| {g['child_0_15'].mean():.3f} "
            f"| {g['urban'].mean():.3f} | {resp_match:.1%} |"
        )

    lines += [
        "",
        "## 完整回归样本（own/migrant/school_age 全非缺失, urban=1）",
        "",
        "| 年份 | N | migrant=1 且 school_age=1 |",
        "|------|---|---------------------------|",
    ]
    core = panel.dropna(subset=["own_house", "migrant", "school_age"])
    core = core[core["urban"] == 1]
    for year, g in core.groupby("year"):
        both = ((g["migrant"] == 1) & (g["school_age"] == 1)).sum()
        lines.append(f"| {year} | {len(g):,} | {both:,} |")
    lines += [
        "",
        f"合计: {len(core):,} household-years "
        f"（migrant×school_age 单元格 {((core['migrant'] == 1) & (core['school_age'] == 1)).sum():,}）",
        "",
        "## 提示",
        "",
        "- migrant（主口径，全部年份）: qa302/pa302 户口不在本县 + 跨期回填",
        "- migrant_moved（对照）: crossyearid 人户分离/搬迁标记，非户口口径",
        "- school_age / preschool_age / child_0_15 基于财务回答者子女 (tb1y_a_c*)",
        "- school_age_any 为旧口径：同住任一成员 6-15 岁",
        "- 主键唯一性已断言: (year, fid) 无重复",
    ]
    return "\n".join(lines)


def main() -> None:
    person_long = build_person_long()
    waves = [build_wave(year, person_long) for year in WAVES]
    panel = pd.concat(waves, ignore_index=True)

    PANEL_PATH.parent.mkdir(parents=True, exist_ok=True)
    panel.to_csv(PANEL_PATH, index=False, encoding="utf-8-sig")
    print(f"panel: {panel.shape[0]:,} rows x {panel.shape[1]} cols -> {PANEL_PATH}")

    REPORT_PATH.parent.mkdir(parents=True, exist_ok=True)
    REPORT_PATH.write_text(quality_report(panel), encoding="utf-8")
    print(f"report -> {REPORT_PATH}")


if __name__ == "__main__":
    main()
