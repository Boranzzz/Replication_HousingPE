"""CFPS wave-level configuration.

Each wave maps the raw official variable names to standardized names used in
the pipeline. Verified against Stata variable labels in the official CFPS files.

Path constants are the only intentional change from HousingProject/src/clean/cfps_config.py.
Outputs stay inside this package. Raw CFPS files are read from CFPS_RAW_DIR or
from REPLICATION_LOCAL_DATA/cfps. They are not bundled with the package.
"""

import sys
from pathlib import Path

_PACKAGE = Path(__file__).resolve().parents[3]
if str(_PACKAGE) not in sys.path:
    sys.path.insert(0, str(_PACKAGE))

from replication_paths import cfps_raw_dir, household_rebuild_dir, package_root

RAW_CFPS = cfps_raw_dir()
INTERIM = household_rebuild_dir()
OUTPUT = package_root() / "outputs" / "diagnostics" / "cfps_rebuild"

# CFPS sentinel codes that mean "missing" for (almost) every variable.
MISSING_CODES = {-10, -9, -8, -7, -2, -1}

# Main analysis waves. 2010 is excluded from the main sample because the
# housing-ownership question (fq1/fq2) does not exist in that wave.
WAVES = {
    2012: {
        "person_file": "cfps2012adult.dta",
        "famecon_file": "cfps2012famecon.dta",
        "famconf_file": "cfps2012famconf.dta",
        "fid": "fid12",
        # famecon: household-level
        "own_raw": "fq1",           # 现住房归谁所有
        "familysize": "familysize",
        "inc_pc": "fincome1_per",
        "urban": "urban12",
        "provcd": "provcd",
        "countyid": "countyid",
        "weight": "fswt_natcs12",
        "resp_pid": None,           # famecon has no resp pid; use cfps2012pid.dta
        "resp_pid_file": "cfps2012pid.dta",
        # person: individual-level
        "age": "cfps2012_age",
        "gender": "cfps2012_gender_best",
        "eduy": "eduy2012",
        "hukou_status": "qa301",    # 农业/非农
        "hukou_loc": "qa302",       # 现在户口所在地（相对现居地）
        "hukou_changed": None,      # 2012 直接询问, 无跳题 flag
        # 户口所在地类别 → migrant 判定
        "loc_local": {1, 2, 3},
        "loc_migrant": {4, 5},
        # famconf roster
        "roster_age": "tb1b_a_p",
        "roster_birthy": "tb1y_a_p",
        "marriage": "tb3_a12_p",
        "migrant_cy": "migrant12",   # from cfps2016crossyearid.dta
    },
    2014: {
        "person_file": "cfps2014adult.dta",
        "famecon_file": "cfps2014famecon.dta",
        "famconf_file": "cfps2014famconf.dta",
        "fid": "fid14",
        "own_raw": "fq2",
        "familysize": "familysize",
        "inc_pc": "fincome1_per",
        "urban": "urban14",
        "provcd": "provcd14",
        "countyid": "countyid14",
        "weight": "fswt_natcs14",
        "resp_pid": "fresp1pid",
        "resp_pid_file": None,
        "age": "cfps2014_age",
        "gender": "cfps_gender",
        "eduy": "cfps2014eduy",
        "hukou_status": "qa301",
        "hukou_loc": "qa302",
        "hukou_changed": None,
        "loc_local": {1, 2, 3},
        "loc_migrant": {4, 5, 6},   # 6=境外
        "roster_age": None,
        "roster_birthy": "tb1y_a_p",
        "marriage": "tb3_a14_p",
        "migrant_cy": "migrant14",
    },
    2016: {
        "person_file": "cfps2016adult.dta",
        "famecon_file": "cfps2016famecon.dta",
        "famconf_file": "cfps2016famconf.dta",
        "fid": "fid16",
        "own_raw": "fq2",
        "familysize": "familysize16",
        "inc_pc": "fincome1_per",
        "urban": "urban16",
        "provcd": "provcd16",
        "countyid": "countyid16",
        "weight": "fswt_natcs16",
        "resp_pid": "resp1pid",
        "resp_pid_file": None,
        "age": "cfps_age",
        "gender": "cfps_gender",
        "eduy": "cfps2016eduy",
        "hukou_status": "pa301",
        "hukou_loc": "pa302",
        "hukou_changed": "pa3020",  # 0=未变化(跳题), 1=变化
        "loc_local": {1, 2, 3},
        "loc_migrant": {4, 5, 6},
        "roster_age": None,
        "roster_birthy": "tb1y_a_p",
        "marriage": "tb3_a16_p",
        "migrant_cy": "migrant16",
    },
    2018: {
        "person_file": "cfps2018person.dta",
        "famecon_file": "cfps2018famecon.dta",
        "famconf_file": "cfps2018famconf.dta",
        "fid": "fid18",
        "own_raw": "fq2",
        "familysize": "familysize18",
        "inc_pc": "fincome1_per",
        "urban": "urban18",
        "provcd": "provcd18",
        "countyid": "countyid18",
        "weight": "fswt_natcs18n",
        "resp_pid": "resp1pid",
        "resp_pid_file": None,
        "age": "age",
        "gender": "gender",
        "eduy": "cfps2018eduy",
        "hukou_status": "qa301",
        "hukou_loc": "qa302",
        "hukou_changed": "qa3020",
        "loc_local": {1, 2, 3},
        "loc_migrant": {4, 5, 6, 7},  # 2018+ 量表: 4市/区其他县 5省内其他市 6其他省 7境外
        "roster_age": None,
        "roster_birthy": "tb1y_a_p",
        "marriage": "tb3_a18_p",
    },
    2020: {
        "person_file": "cfps2020person.dta",
        "famecon_file": "cfps2020famecon.dta",
        "famconf_file": "cfps2020famconf.dta",
        "fid": "fid20",
        "own_raw": "fq2",
        "familysize": "familysize20",
        "inc_pc": "fincome1_per",
        "urban": "urban20",
        "provcd": "provcd20",
        "countyid": "countyid20",
        "weight": "fswt_natcs20n",
        "resp_pid": "resp1pid",
        "resp_pid_file": None,
        "age": "age",
        "gender": "gender",
        "eduy": "cfps2020eduy",
        "hukou_status": "qa301",
        "hukou_loc": "qa302",
        "hukou_changed": "qa3020",
        "loc_local": {1, 2, 3},
        "loc_migrant": {4, 5, 6, 7},
        "roster_age": None,
        "roster_birthy": "tb1y_a_p",
        "marriage": "tb3_a20_p",
    },
    2022: {
        "person_file": "cfps2022person.dta",
        "famecon_file": "cfps2022famecon.dta",
        "famconf_file": "cfps2022famconf.dta",
        "fid": "fid22",
        "own_raw": "fq2",
        "familysize": "familysize22",
        "inc_pc": "fincome1_per",
        "urban": "urban22",
        "provcd": "provcd22",
        "countyid": "countyid22",
        "weight": "fswt_natcs22n",
        "resp_pid": "resp1pid",
        "resp_pid_file": None,
        "age": "age",
        "gender": "gender",
        "eduy": "cfps2022eduy",
        "hukou_status": "qa301",
        "hukou_loc": "qa302",
        "hukou_changed": "qa3020",
        "loc_local": {1, 2, 3},
        "loc_migrant": {4, 5, 6, 7},
        "roster_age": None,
        "roster_birthy": "tb1y_a_p",
        "marriage": "tb3_a22_p",
    },
}

# School-age windows (inclusive), per docs/cfps_regression_spec.md
SCHOOL_AGE_MIN = 6
SCHOOL_AGE_MAX = 15
PRESCHOOL_AGE_MIN = 0
PRESCHOOL_AGE_MAX = 5
CHILD_0_15_MIN = 0
CHILD_0_15_MAX = 15
# Mechanism age bins (inclusive): school entry at age 6 splits 3-5 vs 6-8
CHILD_AGE_BINS = (
    ("child_0_2", 0, 2),
    ("child_3_5", 3, 5),
    ("child_6_8", 6, 8),
    ("child_9_11", 9, 11),
    ("child_12_15", 12, 15),
)
RESP_CHILD_SLOTS = tuple(f"tb1y_a_c{i}" for i in range(1, 11))
