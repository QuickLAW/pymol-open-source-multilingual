"""Load every .ui form the way PyMOL does and report labels still in English.

The catalogue-based audit can say "all .ui strings are catalogued" while the
widgets still paint English, because a catalogue entry is only reachable if
uic/QUiLoader actually issued a translate() call. This asks the widgets
themselves, which is the only end-to-end answer for the forms layer.
"""
from __future__ import annotations

import glob
import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
sys.stdout.reconfigure(encoding='utf-8', errors='replace')

os.environ.setdefault('PYMOL_LANG', 'zh_CN')

from PySide6 import QtCore, QtWidgets
from PySide6.QtCore import QFile, QIODevice
from PySide6.QtUiTools import QUiLoader

import audit_coverage as ac

TEXT_WIDGETS = (QtWidgets.QLabel, QtWidgets.QPushButton, QtWidgets.QCheckBox,
                QtWidgets.QRadioButton, QtWidgets.QGroupBox,
                QtWidgets.QToolButton)


# Things that must stay English because the user has to type them or because
# they are unit/product names. Listed rather than inferred, so adding one is
# a deliberate decision that shows up in review.
NON_TRANSLATABLE = {
    'sele',                 # PyMOL selection keyword
    'load_traj...',         # command name
    'DPI', 'cm', 'px', '%',  # units
    '720p', '480p', '360p',
    'MPEG-4(&4)', 'MPEG-1(&1)', 'MPEG-2(&2)',
    'apbs', 'pdb2pqr', 'prepwizard (SCHRODINGER)', 'ffmpeg',
    'GIF(&I)', 'mpeg_encode', 'protein_assign_charges_and_radii',
    'apbs_map', 'apbs_ramp',
}


def han(s: str) -> bool:
    """Chinese text, or a Latin label the catalogue already localised by
    giving it fullwidth punctuation ('PDB ID：')."""
    return any('一' <= c <= '鿿' for c in s) or '：' in s or '（' in s


def main() -> int:
    import argparse
    ap = argparse.ArgumentParser()
    ap.add_argument('--lang', default=os.environ.get('PYMOL_LANG', 'zh_CN'))
    args = ap.parse_args()
    lang = args.lang

    app = QtWidgets.QApplication.instance() or QtWidgets.QApplication([])
    refs = []
    root = ac.ROOT
    for qm in sorted((root / 'data' / 'pmg_qt' / 'i18n' / lang).glob('*.qm')):
        t = QtCore.QTranslator()
        if t.load(str(qm)):
            app.installTranslator(t)
            refs.append(t)
    print(f'{len(refs)} translators installed for {lang}')

    # Qt's own catalogue supplies standard button text (OK/Cancel/Apply),
    # exactly as pymol.Qt.i18n.install() arranges at startup. Without it the
    # sweep would report those as leaks and they are not.
    li = QtCore.QLibraryInfo
    qtp = li.path(li.LibraryPath.TranslationsPath)
    qt = QtCore.QTranslator()
    if qt.load(f'qtbase_{lang}.qm', qtp):
        app.installTranslator(qt)
        refs.append(qt)
        print('qtbase_%s.qm installed (standard buttons)' % lang)
    else:
        print('WARNING: qtbase_%s.qm not found -- standard buttons stay English'
              % lang)

    loader = QUiLoader()
    forms = sorted(glob.glob(str(root / 'modules/pmg_qt/forms/*.ui')))
    forms += sorted(glob.glob(str(root / 'data/startup/**/*.ui'),
                              recursive=True))
    total = 0
    failed = 0
    for path in forms:
        f = QFile(path.replace('\\', '/'))
        if not f.open(QIODevice.ReadOnly):
            print(f'{Path(path).name:24s} cannot open')
            failed += 1
            continue
        w = loader.load(f, None)
        f.close()
        if w is None:
            print(f'{Path(path).name:24s} LOADER FAILED')
            failed += 1
            continue
        texts = []
        for cls in TEXT_WIDGETS:
            for x in w.findChildren(cls):
                # QGroupBox spells its caption title(), not text()
                t = x.title() if isinstance(x, QtWidgets.QGroupBox) else x.text()
                if t:
                    texts.append(t)
        for x in w.findChildren(QtWidgets.QComboBox):
            for i in range(x.count()):
                if x.itemText(i):
                    texts.append(x.itemText(i))
        for x in w.findChildren(QtWidgets.QLineEdit):
            if x.placeholderText():
                texts.append(x.placeholderText())
        for x in w.findChildren(QtWidgets.QTabWidget):
            for i in range(x.count()):
                if x.tabText(i):
                    texts.append(x.tabText(i))
        for x in w.findChildren(QtWidgets.QTableWidget):
            for i in range(x.columnCount()):
                h = x.horizontalHeaderItem(i)
                if h and h.text():
                    texts.append(h.text())
        if w.windowTitle():
            texts.append(w.windowTitle())
        eng = [t for t in texts
               if ac._ui_reportable(t) and not han(t)
               and t.strip() not in NON_TRANSLATABLE]
        total += len(eng)
        flag = '  ' if eng else 'OK'
        print(f'{flag} {Path(path).name:24s} visible={len(texts):3d} '
              f'english={len(eng):2d}  {eng[:5]}')
    print(f'\n{total} English label(s) left in {len(forms)} forms, '
          f'{failed} load failure(s)')
    return 1 if total or failed else 0


if __name__ == '__main__':
    raise SystemExit(main())
