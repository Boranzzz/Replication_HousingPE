"""Reproduce Tables 3 and 4, Figures 5 and 6, and the alternative-rent comparison.

These steps use the public income aggregates and the coded calibration.
They do not read CFPS or CREPRICE microdata.
"""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from run_steps import PACKAGE, run_steps

STEPS = [
    ("calibration_tables", PACKAGE / "code/03_calibration/solve_housing_valuation.py"),
    ("calibration_figures", PACKAGE / "code/03_calibration/make_publication_figures.py"),
    ("rental_cost_comparison", PACKAGE / "code/03_calibration/compare_rental_cost.py"),
]


if __name__ == "__main__":
    run_steps(STEPS, "run_calibration_log.json")
