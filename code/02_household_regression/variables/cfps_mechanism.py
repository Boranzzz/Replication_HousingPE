"""Construct Part-2 mechanism variables from standardized CFPS inputs.

Definitions follow docs/cfps_regression_spec.md:

- own_house:   fq1 (2012) / fq2 (2014+) in {1, 2}  -> 1;  in {3..7, 77} -> 0
- migrant:     hukou location relative to current residence, with
               cross-wave backfill when the skip flag says "unchanged"
- school_age:  financial respondent's own child aged 6-15 (famconf tb1y_a_c*)
- preschool_age: respondent's child aged 0-5 (pre-enrollment insurance window)
- child_0_15: respondent's child aged 0-15 (combined window)
"""

from __future__ import annotations

import pandas as pd

from cleaning.cfps_config import (
    CHILD_0_15_MAX,
    CHILD_0_15_MIN,
    CHILD_AGE_BINS,
    PRESCHOOL_AGE_MAX,
    PRESCHOOL_AGE_MIN,
    RESP_CHILD_SLOTS,
    SCHOOL_AGE_MAX,
    SCHOOL_AGE_MIN,
    WAVES,
)

OWN_YES = {1, 2}          # 家庭成员拥有完全/部分产权
OWN_NO = {3, 4, 5, 6, 7, 77}


def build_own_house(own_raw: pd.Series) -> pd.Series:
    """0/1 homeownership of the current dwelling."""
    out = pd.Series(pd.NA, index=own_raw.index, dtype="Int64")
    out[own_raw.isin(OWN_YES)] = 1
    out[own_raw.isin(OWN_NO)] = 0
    return out


def backfill_hukou_loc(person_long: pd.DataFrame) -> pd.DataFrame:
    """Fill skipped hukou-location answers from the previous wave.

    CFPS 2016+ only re-asks qa302/pa302 when the hukou address changed
    (qa3020/pa3020 == 1). When the flag is 0 and the current answer is
    missing, we carry forward the person's last observed answer.

    Input: person-level long table with pid, year, hukou_loc, hukou_changed.
    Output: same table with extra column hukou_loc_filled.
    """
    df = person_long.sort_values(["pid", "year"]).copy()
    last_seen = df.groupby("pid")["hukou_loc"].ffill()
    carry_ok = df["hukou_loc"].notna() | (df["hukou_changed"] == 0)
    df["hukou_loc_filled"] = last_seen.where(carry_ok)
    return df


def build_migrant(hukou_loc: pd.Series, year: int) -> pd.Series:
    """0/1 migrant status from the (filled) hukou-location category.

    Used for 2018-2022 where crossyearid migrant flags are unavailable.
    """
    cfg = WAVES[year]
    out = pd.Series(pd.NA, index=hukou_loc.index, dtype="Int64")
    out[hukou_loc.isin(cfg["loc_local"])] = 0
    out[hukou_loc.isin(cfg["loc_migrant"])] = 1
    return out


def build_migrant_from_crossyearid(migrant_cy: pd.Series) -> pd.Series:
    """0/1 migrant from CFPS crossyearid official flag (2012-2016)."""
    return migrant_cy.astype("Int64")


def build_school_age(roster: pd.DataFrame) -> pd.DataFrame:
    """Legacy flag: any co-resident member aged 6-15 in the famconf roster."""
    in_window = roster["member_age"].between(SCHOOL_AGE_MIN, SCHOOL_AGE_MAX)
    flag = in_window.groupby(roster["fid"]).max().astype("Int64")
    return flag.rename("school_age_any").reset_index()


def _household_child_flag(
    children: pd.DataFrame,
    year: int,
    age_min: int,
    age_max: int,
    out_name: str,
) -> pd.Series:
    """Aggregate child-level ages to a 0/1 household flag."""
    ages = year - children["birth_year"]
    ages = ages.mask((ages < 0) | (ages > 120))
    in_window = ages.between(age_min, age_max)
    flag = in_window.groupby(children["fid"]).max()
    # Households with no valid child birth years -> 0 (no child in window).
    all_fids = children["fid"].drop_duplicates()
    flag = flag.reindex(all_fids, fill_value=False).astype("Int64")
    return flag.rename(out_name)


def build_resp_child_flags(
    children: pd.DataFrame, year: int, fids: pd.Series
) -> pd.DataFrame:
    """Household flags from the financial respondent's children (tb1y_a_c*)."""
    base = pd.DataFrame({"fid": pd.unique(fids)})
    windows = [
        ("school_age", SCHOOL_AGE_MIN, SCHOOL_AGE_MAX),
        ("preschool_age", PRESCHOOL_AGE_MIN, PRESCHOOL_AGE_MAX),
        ("child_0_15", CHILD_0_15_MIN, CHILD_0_15_MAX),
        *CHILD_AGE_BINS,
    ]
    for col, lo, hi in windows:
        flag = _household_child_flag(children, year, lo, hi, col)
        base = base.merge(flag.reset_index(), on="fid", how="left")
        base[col] = base[col].fillna(0).astype("Int64")
    return base
