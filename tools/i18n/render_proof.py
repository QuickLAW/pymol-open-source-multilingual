"""Render real forms with the zh_CN catalogues and save PNGs as proof.

A catalogue can be 100% "finished" and still paint nothing: lrelease only
checks the .ts it was given, and a context or a whitespace difference makes a
translation unreachable. This drives the same path PyMOL uses -- QUiLoader
plus an installed QTranslator -- and puts pixels on disk, so both the
translated and the untranslated case are observable.

    python tools/i18n/render_proof.py [--lang zh_CN] [--outdir .scratch/proof]
"""
from __future__ import annotations

import argparse
import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]


def main(argv):
    ap = argparse.ArgumentParser()
    ap.add_argument('--lang', default='zh_CN')
    ap.add_argument('--outdir', default=str(ROOT / '.scratch' / 'proof'))
    args = ap.parse_args(argv)

    os.environ['PYMOL_LANG'] = args.lang
    sys.stdout.reconfigure(encoding='utf-8', errors='replace')

    from PySide6 import QtCore, QtGui, QtWidgets
    from PySide6.QtUiTools import QUiLoader
    from PySide6.QtCore import QFile, QIODevice

    app = QtWidgets.QApplication.instance() or QtWidgets.QApplication([])

    refs = []
    tdir = ROOT / 'data' / 'pmg_qt' / 'i18n' / args.lang
    for qm in sorted(tdir.glob('*.qm')):
        t = QtCore.QTranslator()
        if t.load(str(qm)):
            app.installTranslator(t)
            refs.append(t)
    print(f'{len(refs)} translators installed from {tdir}')

    tr = QtCore.QCoreApplication.translate
    forms = [
        (ROOT / 'modules/pmg_qt/forms/props.ui', 'PropertiesDialog'),
        (ROOT / 'modules/pmg_qt/forms/pluginmanager.ui', 'Form'),
        (ROOT / 'modules/pmg_qt/forms/render.ui', 'Form'),
        (ROOT / 'modules/pmg_qt/forms/save_molecule.ui', 'Form'),
        (ROOT / 'data/startup/apbs_gui/apbs.ui', 'Form'),
    ]

    outdir = Path(args.outdir)
    outdir.mkdir(parents=True, exist_ok=True)
    loader = QUiLoader()
    painted = 0
    for path, ctx in forms:
        if not path.is_file():
            continue
        f = QFile(str(path))
        if not f.open(QIODevice.ReadOnly):
            print(f'  cannot open {path.name}')
            continue
        w = loader.load(f, None)
        f.close()
        if w is None:
            print(f'  loader returned None for {path.name}')
            continue
        w.resize(w.sizeHint().expandedTo(QtCore.QSize(560, 420)))
        w.show()
        app.processEvents()
        pix = w.grab()
        png = outdir / f'{path.stem}.png'
        pix.save(str(png))
        # Collect the labels that actually ended up on the widget, which is
        # the only thing that proves the lookup happened.
        texts = [x.text() for x in w.findChildren(QtWidgets.QLabel)
                 if x.text()][:6]
        buttons = [x.text() for x in w.findChildren(QtWidgets.QPushButton)
                   if x.text()][:4]
        han = sum(any('一' <= c <= '鿿' for c in t) for t in texts + buttons)
        painted += bool(han)
        print(f'\n{path.name} -> {png.name}  {pix.width()}x{pix.height()} '
              f'{han} chinese label(s)')
        for t in texts + buttons:
            print(f'    {t!r}')
        w.deleteLater()

    # A menu built the way pymol_qt_gui builds it: labels come from _mtr().
    bar = QtWidgets.QMenuBar()
    for label in ['File', 'Edit', 'Build', 'Display', 'Setting', 'Wizard',
                  'Help', 'Language']:
        bar.addMenu(tr('Menu', label) if label != 'Language'
                    else tr('PyMOLQtGUI', label))
    bar.show()
    app.processEvents()
    pix = bar.grab()
    menupng = outdir / 'menubar.png'
    pix.save(str(menupng))
    titles = [a.text() for a in bar.actions()]
    print(f'\nmenubar -> {menupng.name}: {titles}')
    print(f'\n{painted}/{len(forms)} forms painted Chinese text')
    return 0 if painted else 1


if __name__ == '__main__':
    raise SystemExit(main(sys.argv[1:]))
