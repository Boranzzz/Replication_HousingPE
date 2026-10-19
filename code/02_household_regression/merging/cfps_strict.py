"""Merge city-level hukou strictness into the CFPS household panel.

Inputs:
    data/interim/cfps_household_panel.csv
    data/interim/cfps_geo/countyid_baseline162.dta
    data/raw/city/strict.xlsx

Outputs:
    data/interim/cfps_city_crosswalk.csv
    data/final/cfps_mechanism.csv
    output/cfps_strict_match_quality.md

Only exact survey-year matches are used. The Strict workbook covers 2014-2019,
so the final CFPS sample contains the 2014, 2016, and 2018 waves. Cities absent
from Strict are dropped, as authorized by the research design.
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

from cleaning.cfps_config import INTERIM, OUTPUT
from replication_paths import county_crosswalk, strict_workbook

PANEL_PATH = INTERIM / "cfps_household_panel.csv"
COUNTY_MAP_PATH = county_crosswalk()
STRICT_PATH = strict_workbook()
CROSSWALK_PATH = INTERIM / "cfps_city_crosswalk.csv"
FINAL_PATH = INTERIM / "cfps_mechanism_rebuilt.csv"
REPORT_PATH = OUTPUT / "cfps_strict_match_quality.md"

# Historical names found in the third-party county crosswalk.
CITY_ALIASES = {
    "襄樊": "襄阳",
}

SUFFIXES = (
    "哈尼族彝族自治州",
    "苗族侗族自治州",
    "布依族苗族自治州",
    "彝族自治州",
    "藏族自治州",
    "回族自治州",
    "自治州",
    "地区",
    "盟",
    "市",
)


def normalize_place(value: object) -> str:
    """Normalize Chinese province/city names for exact matching."""
    text = str(value).strip()
    for suffix in SUFFIXES:
        if text.endswith(suffix):
            text = text[: -len(suffix)]
            break
    return CITY_ALIASES.get(text, text)


def load_crosswalk() -> pd.DataFrame:
    """Build unique CFPS countyid -> prefecture city crosswalk."""
    crosswalk = pd.read_stata(COUNTY_MAP_PATH, convert_categoricals=False)
    crosswalk["province_key"] = crosswalk["provname"].map(normalize_place)
    crosswalk["city_key"] = crosswalk["cityname"].map(normalize_place)
    crosswalk = crosswalk.rename(
        columns={
            "code": "county_code",
            "city": "city_code",
            "provname": "province_name",
            "cityname": "city_name",
            "countyname": "county_name",
        }
    )
    keep = [
        "countyid",
        "county_code",
        "city_code",
        "province_name",
        "city_name",
        "county_name",
        "province_key",
        "city_key",
    ]
    crosswalk = crosswalk[keep]
    assert not crosswalk["countyid"].duplicated().any()
    return crosswalk


def load_strict() -> pd.DataFrame:
    """Read and validate the city-year Strict workbook."""
    strict = pd.read_excel(STRICT_PATH)
    required = {"province", "city", "year", "strict", "h", "h2"}
    missing = required.difference(strict.columns)
    if missing:
        raise ValueError(f"Strict workbook missing columns: {sorted(missing)}")
    if strict.duplicated(["province", "city", "year"]).any():
        raise ValueError("Strict workbook has duplicate province-city-year rows")
    strict["province_key"] = strict["province"].map(normalize_place)
    strict["city_key"] = strict["city"].map(normalize_place)
    return strict


def build_final() -> tuple[pd.DataFrame, pd.DataFrame]:
    """Merge, filter to exact-year matched urban core sample, and save."""
    panel = pd.read_csv(PANEL_PATH)
    crosswalk = load_crosswalk()
    strict = load_strict()

    merged = panel.merge(
        crosswalk,
        on="countyid",
        how="left",
        validate="many_to_one",
        indicator="county_merge",
    )
    merged = merged.merge(
        strict[["province_key", "city_key", "year", "h", "h2", "strict"]],
        on=["province_key", "city_key", "year"],
        how="left",
        validate="many_to_one",
        indicator="strict_merge",
    )

    # Regression sample: urban, exact-year Strict match, and all three core
    # mechanism variables observed. Control-variable missingness is retained
    # and handled transparently by each regression specification.
    final = merged[
        (merged["urban"] == 1)
        & merged["strict"].notna()
        & merged[["own_house", "migrant", "school_age"]].notna().all(axis=1)
    ].copy()

    final["city_year_id"] = (
        final["city_code"].astype("Int64").astype("string")
        + "_"
        + final["year"].astype("string")
    )
    final = final.drop(columns=["county_merge", "strict_merge"])
    assert not final.duplicated(["year", "fid"]).any()

    CROSSWALK_PATH.parent.mkdir(parents=True, exist_ok=True)
    crosswalk.to_csv(CROSSWALK_PATH, index=False, encoding="utf-8-sig")
    FINAL_PATH.parent.mkdir(parents=True, exist_ok=True)
    final.to_csv(FINAL_PATH, index=False, encoding="utf-8-sig")
    return merged, final


def make_report(merged: pd.DataFrame, final: pd.DataFrame) -> str:
    """Create a transparent matching and sample-loss report."""
    lines = [
        "# CFPS × Strict 匹配质量报告",
        "",
        "## 匹配规则",
        "",
        "- `countyid` → 基线 162 区县映射 → 地级市",
        "- 省份名 + 城市名 + **同年** 与 `strict.xlsx` 匹配",
        "- Strict 仅覆盖 2014–2019，所以 CFPS 仅保留 2014/2016/2018",
        "- 城市限制变量：`h`=总体落户难度，`h2`=购房分项指数，`strict`=综合指数",
        "- 按要求删除 Strict 中不存在的城市",
        "- 主样本限 `urban==1`，且 own_house/migrant/school_age 非缺失",
        "",
        "## 分年匹配",
        "",
        "| 年份 | CFPS 户数 | countyid→city | Strict 同年匹配 | 最终城镇核心样本 |",
        "|------|----------:|--------------:|----------------:|-----------------:|",
    ]
    for year, group in merged.groupby("year"):
        final_n = int((final["year"] == year).sum())
        lines.append(
            f"| {year} | {len(group):,} "
            f"| {group['city_code'].notna().sum():,} "
            f"| {group['strict'].notna().sum():,} "
            f"| {final_n:,} |"
        )

    lines += [
        "",
        "## 最终样本",
        "",
        f"- Household-years: **{len(final):,}**",
        f"- 家庭数 (`fid10`): **{final['fid10'].nunique():,}**",
        f"- 城市数: **{final['city_code'].nunique():,}**",
        f"- 年份: **{', '.join(map(str, sorted(final['year'].unique())))}**",
        f"- Strict 范围: **{final['strict'].min():.3f} – {final['strict'].max():.3f}**",
        "",
        "## 核心交互单元格",
        "",
        "| migrant | school_age | N | own_house 均值 |",
        "|---------:|-----------:|--:|---------------:|",
    ]
    cells = (
        final.groupby(["migrant", "school_age"])["own_house"]
        .agg(["count", "mean"])
        .reset_index()
    )
    for row in cells.itertuples(index=False):
        lines.append(
            f"| {int(row.migrant)} | {int(row.school_age)} "
            f"| {int(row.count):,} | {row.mean:.3f} |"
        )

    lines += [
        "",
        "## 限制",
        "",
        "- 当前 countyid crosswalk 仅覆盖 CFPS 基线 162 区县；后续新增迁移目的地可能被删掉",
        "- Strict 只有 2014–2019，不能无假设地外推到 2012、2020、2022",
        f"- 最终只有 {final['city_code'].nunique()} 个城市，城市聚类标准误需谨慎解释",
        (
            "- 其中只有 "
            f"{int((final.assign(ms=(final['migrant'] == 1) & (final['school_age'] == 1)).groupby('city_code')['ms'].sum() > 0).sum())} "
            "个城市出现 migrant×school_age 观测"
        ),
        f"- 上海占最终样本 {((final['city_code'] == 310000).mean()):.1%}，需做剔除上海稳健性检验",
    ]
    return "\n".join(lines)


def main() -> None:
    merged, final = build_final()
    REPORT_PATH.parent.mkdir(parents=True, exist_ok=True)
    REPORT_PATH.write_text(make_report(merged, final), encoding="utf-8")
    print(f"crosswalk -> {CROSSWALK_PATH}")
    print(f"final: {len(final):,} rows x {len(final.columns)} cols -> {FINAL_PATH}")
    print(f"report -> {REPORT_PATH}")


if __name__ == "__main__":
    main()
