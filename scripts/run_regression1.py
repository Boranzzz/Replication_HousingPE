"""Reproduce Regression 1 from the prepared city-year sample.

Does not rebuild the CREPRICE panel and does not read CFPS microdata.
"""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from run_steps import PACKAGE, run_steps

STEPS = [
    ("city_regressions", PACKAGE / "code/01_city_regression/estimate_city_regressions.py"),
    ("city_loo_figure", PACKAGE / "code/01_city_regression/plot_loo_city_trends.py"),
]


if __name__ == "__main__":
    run_steps(STEPS, "run_regression1_log.json")
