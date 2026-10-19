"""Run package scripts and record which steps reproduced."""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

PACKAGE = Path(__file__).resolve().parents[1]


def run_steps(steps: list[tuple[str, Path]], log_name: str) -> list[dict]:
    log = []
    for name, script in steps:
        completed = subprocess.run([sys.executable, str(script)], cwd=PACKAGE, check=False)
        if completed.returncode == 0:
            status = "reproduced"
            print(f"REPRODUCED  {name}")
        elif completed.returncode == 2:
            status = "incomplete"
            print(f"INCOMPLETE  {name}")
        else:
            status = "failed"
            print(f"FAILED      {name} (exit {completed.returncode})")
        log.append(
            {
                "step": name,
                "script": str(script.relative_to(PACKAGE)),
                "status": status,
                "exit_code": completed.returncode,
            }
        )
    out = PACKAGE / "outputs" / "diagnostics" / log_name
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(log, indent=2) + "\n", encoding="utf-8")
    failed = [row for row in log if row["status"] == "failed"]
    if failed:
        raise SystemExit(1)
    return log
