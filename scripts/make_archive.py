"""Build the shareable ZIP with an explicit exclusion list.

Restricted inputs, Figure 1–3 materials, caches, and backups are omitted.
The archive is written next to the package and is not uploaded.
"""

from __future__ import annotations

import sys
import zipfile
from pathlib import Path

PACKAGE = Path(__file__).resolve().parents[1]
DEST = PACKAGE.parent / "Replication_Package.zip"

EXCLUDED_DIR_NAMES = {
    "__pycache__",
    ".ipynb_checkpoints",
    "local_only",
    "backup",
    "backups",
}
EXCLUDED_SUFFIXES = {".pyc", ".pyo", ".dta"}
EXCLUDED_NAMES = {
    ".DS_Store",
    "exp.xlsx",
    "cfps_mechanism.csv",
    "cfps_mechanism_rebuilt.csv",
    "cfps_household_panel.csv",
    "strict.xlsx",
    "R1Full_Rent.xlsx",
    "R1Full_Rent_2014_2019.xlsx",
    "R1_estimation_sample_2014_2019.xlsx",
    "R1Full_Rent_monthly.xlsx",
    "R1Full_monthly.xlsx",
}
EXCLUDED_NAME_PREFIXES = ("fig01_", "fig03_")


def excluded(path: Path) -> str | None:
    relative = path.relative_to(PACKAGE)
    parts = set(relative.parts)
    if parts.intersection(EXCLUDED_DIR_NAMES):
        return "restricted or cache directory"
    if path.name in EXCLUDED_NAMES or path.suffix in EXCLUDED_SUFFIXES:
        return "restricted or cache file"
    if path.name.startswith(EXCLUDED_NAME_PREFIXES):
        return "Figure 1 or Figure 3 output"
    if "01_descriptive_figures" in relative.parts:
        return "Figure 1–3 code"
    if relative.parts[:2] == ("data", "raw"):
        return "raw descriptive inputs"
    return None


def python_has_machine_path(path: Path) -> bool:
    text = path.read_text(encoding="utf-8", errors="replace")
    return ("/Users/" + "boran/") in text


def main() -> None:
    offenders = [
        path.relative_to(PACKAGE).as_posix()
        for path in PACKAGE.rglob("*.py")
        if python_has_machine_path(path) and excluded(path) is None
    ]
    if offenders:
        print("Refusing to archive. Executable Python still contains a machine-specific path:")
        for name in offenders:
            print(name)
        raise SystemExit(1)

    if DEST.exists():
        DEST.unlink()
    included = []
    with zipfile.ZipFile(DEST, "w", compression=zipfile.ZIP_DEFLATED) as archive:
        for path in sorted(PACKAGE.rglob("*")):
            if not path.is_file():
                continue
            reason = excluded(path)
            if reason is not None:
                continue
            if path.is_symlink():
                print(f"Refusing to archive symlink {path}")
                raise SystemExit(1)
            archive.write(path, Path("Replication_Package") / path.relative_to(PACKAGE))
            included.append(path.relative_to(PACKAGE).as_posix())
    print(f"Wrote {DEST} with {len(included)} files")
    for name in included:
        print(name)


if __name__ == "__main__":
    main()
