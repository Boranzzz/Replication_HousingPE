"""Reproduce Table 2 and Figure 4 from the prepared CFPS analysis file.

This command does not rebuild cfps_mechanism.csv. Use
scripts/rebuild_household_inputs.py for that separate stage.
"""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from run_steps import PACKAGE, run_steps

STEPS = [
    ("household_table", PACKAGE / "code/02_household_regression/estimate_homeownership.py"),
    ("household_latex", PACKAGE / "code/02_household_regression/cfps_reg2_latex.py"),
    ("household_age_gradient", PACKAGE / "code/02_household_regression/estimate_age_gradient.py"),
]


if __name__ == "__main__":
    run_steps(STEPS, "run_regression2_log.json")
