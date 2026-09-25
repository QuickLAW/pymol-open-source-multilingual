# -*- mode: python ; coding: utf-8 -*-
"""PyInstaller spec for a self-contained PyMOL build.

Two knobs, both from the environment, so one file serves both deliverables:
  PYMOL_ONEFILE=1  single portable exe   (else: onedir / multi-file)
  PYMOL_CONSOLE=1  keep the console window for diagnostics
"""

import os

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(SPEC)))
DEPS_BIN = r"C:\Users\yewil\Desktop\pymol\_deps\prefix\bin"

ONEFILE = os.environ.get("PYMOL_ONEFILE") == "1"
CONSOLE = os.environ.get("PYMOL_CONSOLE") == "1"

# data/ subdirs that only add weight: bundled examples, the legacy Tk frontend
# we do not ship, OpenVR assets (built without --openvr), and the CJK font --
# that one is compiled into _cmd as layer1/FontTTF3.h, so shipping the .otf too
# would just double it.
DATA_SKIP = {"demo", "tut", "pmg_tk", "openvr", "fonts"}


def data_tree():
    out = []
    base = os.path.join(ROOT, "data")
    for entry in sorted(os.listdir(base)):
        if entry in DATA_SKIP:
            continue
        src = os.path.join(base, entry)
        if os.path.isdir(src):
            out.append((src, os.path.join("data", entry)))
        else:
            out.append((src, "data"))
    return out


binaries = []
for dll in ("glew32.dll", "freetype.dll", "libpng16.dll", "zlib.dll"):
    p = os.path.join(DEPS_BIN, dll)
    if os.path.isfile(p):
        binaries.append((p, "."))
    else:
        warn = f"missing dependency DLL: {p}"
        print("WARNING:", warn)

def local_submodules(*pkgs):
    """Enumerate submodules by walking modules/, without importing them.

    collect_submodules() has to import each package, which here means loading
    _cmd.pyd inside PyInstaller's spec process -- and it silently returns []
    when that fails. Several of these packages also import optional
    dependencies we do not ship (chempy.fast wants Numeric), so an import-based
    scan would drop real modules that are fine at runtime because they are only
    imported on demand.
    """
    base = os.path.join(ROOT, "modules")
    found = []
    for pkg in pkgs:
        pkgdir = os.path.join(base, pkg.replace("/", os.sep))
        for dirpath, _dirnames, filenames in os.walk(pkgdir):
            if "__pycache__" in dirpath:
                continue
            for fn in filenames:
                if not fn.endswith(".py"):
                    continue
                rel = os.path.relpath(os.path.join(dirpath, fn), base)
                mod = rel[:-3].replace(os.sep, ".")
                if mod.endswith(".__init__"):
                    mod = mod[: -len(".__init__")]
                found.append(mod)
    return sorted(set(found))


hiddenimports = local_submodules("pymol", "pymol2", "pmg_qt", "chempy")
hiddenimports += ["pymol._cmd", "pmg_qt.pymol_qt_gui", "pymol.Qt.i18n"]

# Fail loudly rather than ship a bundle that dies at startup on a missing
# module: these are all reached only through dynamic imports.
missing = [
    m
    for m in (
        "pymol.povray",
        "pymol.helping",
        "pymol.Qt.i18n",
        "pmg_qt.pymol_qt_gui",
        "chempy.mmtf.io",
    )
    if m not in hiddenimports
]
if len(hiddenimports) < 100 or missing:
    raise SystemExit(
        f"module collection broken: {len(hiddenimports)} found, missing {missing}"
    )
print(f"collected {len(hiddenimports)} submodules")

datas = data_tree()


def prune(entries, label):
    """Drop Qt payload we provably do not load, and report every hit.

    The PySide6 hook pulls in the whole Qt runtime; these are the parts PyMOL's
    Qt frontend never touches. Printed so the reduction stays auditable rather
    than becoming a mystery delta between builds.
    """
    drop_dirs = (
        "PySide6/qml/",            # QML/Quick, both excluded above
        "PySide6/plugins/canvaseshare/",
        "PySide6/plugins/multimedia/",
        "PySide6/plugins/networkinformation/",
        "PySide6/plugins/platforminputcontexts/",
        "PySide6/plugins/printsupport/",
        "PySide6/plugins/scenepositioners/",
        "PySide6/plugins/sqldrivers/",
        "PySide6/plugins/tls/",
        "PySide6/plugins/webview/",
        "PySide6/translations/",   # bulk of it, minus the keep_prefixes below
    )
    keep_prefixes = (
        # Qt's own strings for the shipped locales: without these the standard
        # dialog buttons (OK/Cancel) fall back to English.
        "PySide6/translations/qtbase_zh",
    )
    drop_files = (
        "PySide6/opengl32sw.dll",  # llvmpipe fallback; PyMOL needs real GL anyway
        "PySide6/Qt6Pdf.dll",
        "PySide6/Qt6Charts.dll",
        "PySide6/Qt6Quick.dll",
        "PySide6/Qt6Qml.dll",
        "PySide6/Qt6Sql.dll",
        "PySide6/Qt6Test.dll",
        "PySide6/Qt6WebEngineCore.dll",
    )
    kept, dropped = [], []
    for e in entries:
        dest = e[0].replace("\\", "/")
        if dest.startswith(keep_prefixes):
            kept.append(e)
        elif dest.startswith(drop_dirs) or dest in drop_files:
            dropped.append(dest)
        else:
            kept.append(e)
    print(f"prune[{label}]: dropped {len(dropped)} entries")
    for d in sorted(set(dropped)):
        print("   -", d)
    return kept

a = Analysis(
    [os.path.join(ROOT, "build_tools", "entry.py")],
    pathex=[os.path.join(ROOT, "modules")],
    binaries=binaries,
    datas=datas,
    hiddenimports=hiddenimports,
    hookspath=[],
    runtime_hooks=[],
    excludes=[
        "tkinter",
        "turtle",
        "unittest",
        "pydoc_data",
        "matplotlib",
        "scipy",
        "pandas",
        "IPython",
        "pytest",
        # Qt modules PyMOL never imports
        "PySide6.QtQml",
        "PySide6.QtQuick",
        "PySide6.QtQuickWidgets",
        "PySide6.QtWebEngineCore",
        "PySide6.QtWebEngineWidgets",
        "PySide6.QtWebChannel",
        "PySide6.QtWebSockets",
        "PySide6.QtMultimedia",
        "PySide6.QtMultimediaWidgets",
        "PySide6.Qt3DCore",
        "PySide6.Qt3DRender",
        "PySide6.QtCharts",
        "PySide6.QtDataVis",
        "PySide6.QtDesigner",
        "PySide6.QtPdf",
        "PySide6.QtPositioning",
        "PySide6.QtRemoteObjects",
        "PySide6.QtSerialPort",
        "PySide6.QtSql",
        "PySide6.QtTest",
        "PySide6.QtTextToSpeech",
        "PySide6.QtXml",
    ],
    noarchive=False,
)

a.binaries = prune(a.binaries, "binaries")
a.datas = prune(a.datas, "datas")

pyz = PYZ(a.pure)

if ONEFILE:
    exe = EXE(
        pyz,
        a.scripts,
        a.binaries,
        a.datas,
        [],
        name="PyMOL",
        debug=False,
        strip=False,
        upx=False,
        console=CONSOLE,
        icon=None,
    )
else:
    exe = EXE(
        pyz,
        a.scripts,
        [],
        exclude_binaries=True,
        name="PyMOL",
        debug=False,
        strip=False,
        upx=False,
        console=CONSOLE,
        icon=None,
    )
    COLLECT(
        exe,
        a.binaries,
        a.datas,
        strip=False,
        upx=False,
        name="PyMOL",
    )
