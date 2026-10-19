"""Checks that do not require restricted microdata."""

from __future__ import annotations

import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

PACKAGE = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PACKAGE))
sys.path.insert(0, str(PACKAGE / "code" / "03_calibration"))

import solve_housing_valuation as model  # noqa: E402


class CalibrationIdentities(unittest.TestCase):
    def test_baseline_and_alternative_rent(self) -> None:
        z_low, z_high, _gap = model.productivity_states()
        baseline = model.evaluate_case(0.129, model.RHO_CENTRAL, z_low, z_high)
        alternative = model.evaluate_case(0.209, model.RHO_CENTRAL, z_low, z_high)
        self.assertAlmostEqual(baseline["P_star"], 0.206481599874, places=12)
        self.assertAlmostEqual(baseline["I"], 0.077481599874, places=12)
        self.assertAlmostEqual(baseline["I_over_P"], 0.375246994992, places=9)
        self.assertAlmostEqual(alternative["P_star"], 0.225970541135, places=12)
        self.assertAlmostEqual(alternative["I"], 0.016970541135, places=12)
        self.assertAlmostEqual(alternative["I_over_P"], 0.075100679272, places=9)
        for row in (baseline, alternative):
            self.assertAlmostEqual(row["P_star"], row["B"] + row["H"] + row["S"], places=12)
            self.assertAlmostEqual(row["P_star"], row["P_free"] + row["I"], places=12)


class MissingRestrictedInputs(unittest.TestCase):
    def test_city_and_household_scripts_exit_with_a_message(self) -> None:
        with tempfile.TemporaryDirectory() as empty:
            env = os.environ.copy()
            env["REPLICATION_LOCAL_DATA"] = empty
            env.pop("CFPS_MECHANISM_CSV", None)
            env.pop("CFPS_RAW_DIR", None)
            scripts = [
                PACKAGE / "code/01_city_regression/estimate_city_regressions.py",
                PACKAGE / "code/02_household_regression/estimate_homeownership.py",
                PACKAGE / "code/02_household_regression/estimate_age_gradient.py",
                PACKAGE / "scripts/rebuild_household_inputs.py",
            ]
            for script in scripts:
                completed = subprocess.run(
                    [sys.executable, str(script)],
                    cwd=PACKAGE,
                    env=env,
                    capture_output=True,
                    text=True,
                    check=False,
                )
                self.assertEqual(completed.returncode, 2, script.name + completed.stderr)
                self.assertIn("INCOMPLETE", completed.stdout, script.name)


class PortableSources(unittest.TestCase):
    def test_executable_python_has_no_author_path(self) -> None:
        offenders = []
        for path in PACKAGE.rglob("*.py"):
            if "local_only" in path.parts or "__pycache__" in path.parts:
                continue
            if ("/Users/" + "boran/") in path.read_text(encoding="utf-8", errors="replace"):
                offenders.append(str(path))
        self.assertEqual(offenders, [])


if __name__ == "__main__":
    unittest.main()
