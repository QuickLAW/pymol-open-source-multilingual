"""Frozen-app entry point for PyMOL.

PyMOL derives $PYMOL_DATA from $PYMOL_PATH at import time, and
pymol/Qt/i18n.py falls back to walking four parent directories off __file__
when PYMOL_DATA is unset. That fallback lands outside the bundle once frozen,
so PYMOL_PATH has to be pinned here before `import pymol` runs -- otherwise the
translated catalogues silently stop loading.
"""

import os
import sys


def _bundle_root():
    """Directory that holds the bundled ``data/`` and ``pymol/`` trees."""
    meipass = getattr(sys, "_MEIPASS", None)
    if meipass:
        return meipass
    # unpacked source tree: this file lives in <root>/build_tools
    return os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def main():
    root = _bundle_root()

    os.environ.setdefault("PYMOL_PATH", root)
    os.environ.setdefault("PYMOL_DATA", os.path.join(root, "data"))

    # _cmd links against glew32/freetype/libpng16. Register the payload
    # directory explicitly so loading does not depend on PATH ordering.
    for d in (root, os.path.join(root, "lib")):
        if os.path.isdir(d) and hasattr(os, "add_dll_directory"):
            try:
                os.add_dll_directory(d)
            except OSError:
                pass

    from pymol import launch

    return launch([sys.argv[0]] + sys.argv[1:])


if __name__ == "__main__":
    sys.exit(main())
