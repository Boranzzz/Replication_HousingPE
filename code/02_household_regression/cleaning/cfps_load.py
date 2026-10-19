"""Load raw CFPS modules and return standardized per-wave DataFrames.

Every loader reads only the columns it needs, renames them to standardized
names, and converts CFPS sentinel codes to missing. No variable construction
happens here — that belongs to src/variables/.
"""

from __future__ import annotations

import pandas as pd

from cleaning.cfps_config import MISSING_CODES, RAW_CFPS, RESP_CHILD_SLOTS, WAVES


def _read(year: int, filename: str, columns: list[str]) -> pd.DataFrame:
    """Read selected columns from one raw .dta file."""
    path = RAW_CFPS / str(year) / filename
    df = pd.read_stata(path, columns=columns, convert_categoricals=False)
    return df


def _clean_missing(s: pd.Series) -> pd.Series:
    """Replace CFPS sentinel codes with NA."""
    return s.mask(s.isin(MISSING_CODES))


def load_famecon(year: int) -> pd.DataFrame:
    """Household-level economics: one row per household.

    Returns columns:
    fid, fid10, resp_pid, own_raw, familysize, inc_pc,
    urban, provcd, countyid, weight
    """
    cfg = WAVES[year]
    cols = [
        cfg["fid"], "fid10", cfg["own_raw"], cfg["familysize"],
        cfg["inc_pc"], cfg["urban"], cfg["provcd"], cfg["countyid"],
        cfg["weight"],
    ]
    if cfg["resp_pid"]:
        cols.append(cfg["resp_pid"])
    df = _read(year, cfg["famecon_file"], cols)

    rename = {
        cfg["fid"]: "fid",
        cfg["own_raw"]: "own_raw",
        cfg["familysize"]: "familysize",
        cfg["inc_pc"]: "inc_pc",
        cfg["urban"]: "urban",
        cfg["provcd"]: "provcd",
        cfg["countyid"]: "countyid",
        cfg["weight"]: "weight",
    }
    if cfg["resp_pid"]:
        rename[cfg["resp_pid"]] = "resp_pid"
    df = df.rename(columns=rename)

    # 2012: financial-respondent pid lives in a separate file
    if cfg["resp_pid_file"]:
        pid_map = pd.read_stata(
            RAW_CFPS / str(year) / cfg["resp_pid_file"],
            convert_categoricals=False,
        ).rename(columns={cfg["fid"]: "fid", "pid": "resp_pid"})
        pid_map = pid_map.drop_duplicates("fid")
        df = df.merge(pid_map, on="fid", how="left")

    for col in ["own_raw", "familysize", "inc_pc", "urban", "resp_pid"]:
        df[col] = _clean_missing(df[col])
    # 地理码: 负值一律视为缺失
    for col in ["provcd", "countyid"]:
        df[col] = df[col].mask(df[col] < 0)

    assert not df["fid"].duplicated().any(), f"{year} famecon: fid not unique"
    df["year"] = year
    return df


def load_person(year: int) -> pd.DataFrame:
    """Individual-level file (adult/person): one row per person.

    Returns columns:
    pid, fid, age, gender, eduy, hukou_status, hukou_loc, hukou_changed
    """
    cfg = WAVES[year]
    cols = ["pid", cfg["fid"], cfg["age"], cfg["gender"], cfg["eduy"],
            cfg["hukou_status"], cfg["hukou_loc"]]
    if cfg["hukou_changed"]:
        cols.append(cfg["hukou_changed"])
    df = _read(year, cfg["person_file"], cols)

    rename = {
        cfg["fid"]: "fid",
        cfg["age"]: "age",
        cfg["gender"]: "gender",
        cfg["eduy"]: "eduy",
        cfg["hukou_status"]: "hukou_status",
        cfg["hukou_loc"]: "hukou_loc",
    }
    if cfg["hukou_changed"]:
        rename[cfg["hukou_changed"]] = "hukou_changed"
    df = df.rename(columns=rename)
    if "hukou_changed" not in df.columns:
        df["hukou_changed"] = pd.NA

    for col in ["age", "gender", "eduy", "hukou_status", "hukou_loc",
                "hukou_changed"]:
        df[col] = _clean_missing(df[col])
    # 79 = 非中国国籍等特殊码
    df["hukou_status"] = df["hukou_status"].mask(df["hukou_status"] == 79)
    # hukou_loc 有效取值 1-8, 其余视为缺失
    df["hukou_loc"] = df["hukou_loc"].mask(~df["hukou_loc"].isin(range(1, 9)))

    df = df.drop_duplicates(["fid", "pid"])
    df["year"] = year
    return df


def load_crossyearid_migrant(year: int) -> pd.DataFrame:
    """CFPS official migrant flag from crossyearid (2012-2016 only).

    The 2016 crossyearid file contains migrant10/12/14/16 for all prior
    waves. The 2014 crossyearid file does NOT include migrant variables.
    Returns: pid, migrant_cy (0/1).
    """
    cfg = WAVES[year]
    col = cfg.get("migrant_cy")
    if not col:
        return pd.DataFrame(columns=["pid", "migrant_cy"])

    path = RAW_CFPS / "2016" / "cfps2016crossyearid.dta"
    df = pd.read_stata(path, columns=["pid", col], convert_categoricals=False)
    df = df.rename(columns={col: "migrant_cy"})
    df["migrant_cy"] = _clean_missing(df["migrant_cy"])
    df["migrant_cy"] = df["migrant_cy"].astype("Int64")
    return df.drop_duplicates("pid")


def _resp_pid_map(year: int) -> pd.DataFrame:
    """Map household id -> financial respondent pid for one wave."""
    cfg = WAVES[year]
    fid_col = cfg["fid"]
    if cfg["resp_pid"]:
        df = _read(year, cfg["famecon_file"], [fid_col, cfg["resp_pid"]])
        return df.rename(columns={fid_col: "fid", cfg["resp_pid"]: "resp_pid"})
    pid_map = pd.read_stata(
        RAW_CFPS / str(year) / cfg["resp_pid_file"],
        convert_categoricals=False,
    ).rename(columns={fid_col: "fid", "pid": "resp_pid"})
    return pid_map.drop_duplicates("fid")


def load_resp_children(year: int) -> pd.DataFrame:
    """Birth years of the financial respondent's children (famconf tb1y_a_c*).

    CFPS famconf stores up to ten children on the respondent's own roster row.
    Returns long format: fid, birth_year (one row per non-missing child slot).
    """
    cfg = WAVES[year]
    fid_col = cfg["fid"]
    cols = ["pid", fid_col, *RESP_CHILD_SLOTS]
    famconf = _read(year, cfg["famconf_file"], cols).rename(columns={fid_col: "fid"})
    resp = _resp_pid_map(year)
    merged = resp.merge(famconf, left_on=["fid", "resp_pid"], right_on=["fid", "pid"], how="left")

    long = merged[["fid", *RESP_CHILD_SLOTS]].melt(
        id_vars="fid", var_name="child_slot", value_name="birth_year"
    )
    long["birth_year"] = _clean_missing(long["birth_year"])
    long = long.dropna(subset=["birth_year"])
    return long[["fid", "birth_year"]].reset_index(drop=True)


def load_roster(year: int) -> pd.DataFrame:
    """Family roster (famconf): one row per household member.

    Returns columns: fid, pid, member_age, marriage
    """
    cfg = WAVES[year]
    cols = ["pid", cfg["fid"], cfg["roster_birthy"], cfg["marriage"]]
    if cfg["roster_age"]:
        cols.append(cfg["roster_age"])
    df = _read(year, cfg["famconf_file"], cols)
    df = df.rename(columns={cfg["fid"]: "fid", cfg["marriage"]: "marriage"})

    birthy = _clean_missing(df[cfg["roster_birthy"]])
    if cfg["roster_age"]:
        age = _clean_missing(df[cfg["roster_age"]])
        df["member_age"] = age.fillna(year - birthy)
    else:
        df["member_age"] = year - birthy
    df["member_age"] = df["member_age"].mask(
        (df["member_age"] < 0) | (df["member_age"] > 120)
    )
    df["marriage"] = _clean_missing(df["marriage"]).mask(df["marriage"] == 0)

    df = df[["fid", "pid", "member_age", "marriage"]].drop_duplicates(["fid", "pid"])
    df["year"] = year
    return df
