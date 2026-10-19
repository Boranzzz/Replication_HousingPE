"""Reproduce every result that belongs in this package.

Runs calibration, then Regression 1, then Regression 2 from prepared inputs.
A missing restricted input is incomplete and does not stop the other stages.
This command does not rebuild the CFPS analysis file and does not draw
Figures 1–3.
"""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from run_calibration import STEPS as CALIBRATION
from run_regression1 import STEPS as REGRESSION1
from run_regression2 import STEPS as REGRESSION2
from run_steps import run_steps


if __name__ == "__main__":
    run_steps([*CALIBRATION, *REGRESSION1, *REGRESSION2], "run_all_log.json")
