from __future__ import annotations

import shutil
import subprocess
import sys
from pathlib import Path


def _root() -> Path:
    return Path(__file__).resolve().parents[2]


def main(argv: list[str]) -> int:
    root = _root()
    i18n_dir = root / "data" / "pmg_qt" / "i18n"
    
    lrelease = shutil.which("pyside6-lrelease") or shutil.which("lrelease")
    if not lrelease:
        sys.stderr.write("missing pyside6-lrelease (or lrelease) on PATH\n")
        return 2

    ts_files = list(i18n_dir.rglob("*.ts"))
    if not ts_files:
        sys.stderr.write(f"no .ts files found in {i18n_dir}\n")
        return 3

    exit_code = 0
    for ts_file in ts_files:
        qm_file = ts_file.with_suffix(".qm")
        print(f"Compiling {ts_file.relative_to(root)} -> {qm_file.relative_to(root)}")
        cmd = [lrelease, str(ts_file), "-qm", str(qm_file)]
        p = subprocess.run(cmd, cwd=str(root))
        if p.returncode != 0:
            exit_code = p.returncode
            
    return exit_code


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
