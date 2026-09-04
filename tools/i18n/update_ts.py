from __future__ import annotations

import argparse
import shutil
import subprocess
import sys
from pathlib import Path


def _root() -> Path:
    return Path(__file__).resolve().parents[2]


def _collect_sources(root: Path) -> list[str]:
    globs = [
        "modules/pmg_qt/**/*.py",
        "modules/pymol/Qt/**/*.py",
        "modules/pymol/_gui.py",
        "modules/pymol/plugins/**/*_qt.py",
        "modules/pymol/plugins/**/managergui_qt.py",
        "modules/pymol/plugins/__init__.py",
        "modules/pmg_qt/forms/**/*.ui",
        "data/startup/apbs_gui/*.ui",
    ]
    files: list[Path] = []
    for g in globs:
        files.extend(root.glob(g))
    files = [p for p in files if p.is_file()]
    return [str(p) for p in sorted(set(files))]


def main(argv: list[str]) -> int:
    parser = argparse.ArgumentParser(description="Extract translatable strings")
    parser.add_argument(
        "--lang",
        default="zh_CN",
        help="target language code (default: zh_CN)",
    )
    args = parser.parse_args(argv)

    root = _root()
    out_dir = root / "data" / "pmg_qt" / "i18n"
    out_dir.mkdir(parents=True, exist_ok=True)
    ts_file = out_dir / f"pymol_{args.lang}.ts"

    lupdate = shutil.which("pyside6-lupdate") or shutil.which("lupdate")
    if not lupdate:
        sys.stderr.write("missing pyside6-lupdate (or lupdate) on PATH\n")
        return 2

    sources = _collect_sources(root)
    if not sources:
        sys.stderr.write("no sources found\n")
        return 3

    cmd = [
        lupdate,
        # _tr(context, text, ...) - canonical Qt translate call
        "-tr-function-alias",
        "_tr+=QCoreApplication.translate",
        # tr(text) -> single-arg form, context resolved from class (QObject subclass)
        "-tr-function-alias",
        "tr+=QCoreApplication.translate",
        # i18n.tr(context, text) - explicit pymol.Qt.i18n namespace
        "-tr-function-alias",
        "i18n.tr+=QCoreApplication.translate",
        # _mtr(text) - menu-specific wrapper, context hardcoded to "Menu"
        "-tr-function-alias",
        "_mtr+=QCoreApplication.translate",
        *sources,
        "-ts",
        str(ts_file),
    ]
    p = subprocess.run(cmd, cwd=str(root))
    return p.returncode


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
