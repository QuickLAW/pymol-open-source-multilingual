"""Diagnose translator conflict when all .qm files are loaded."""
import os
import sys

# Force output to stderr to bypass any stdout buffering issues
def log(msg):
    sys.stderr.write(str(msg) + '\n')
    sys.stderr.flush()

os.environ['PYMOL_LANG'] = 'zh_CN'
try:
    from PySide6 import QtCore
except Exception as e:
    log(f'Import failed: {e}')
    sys.exit(1)

from pathlib import Path

app = QtCore.QCoreApplication([])
tdir = Path(r'd:\Codes\GitHub\pymol-open-source-multilingual\data\pmg_qt\i18n\zh_CN')

translators = []
log('Loading .qm files one by one:')
for qm in sorted(tdir.glob('*.qm')):
    try:
        t = QtCore.QTranslator()
        loaded = t.load(str(qm))
        if loaded:
            app.installTranslator(t)
            translators.append((qm.name, t))
            r = QtCore.QCoreApplication.translate('PyMOLQtGUI', 'About PyMOL')
            state = 'OK' if r == '关于 PyMOL' else ('BROKEN' if r == 'About PyMOL' else '?')
            log(f'  +{qm.name:30s} -> About PyMOL = {r!r:20s} ({state})')
    except Exception as e:
        log(f'  ERROR loading {qm.name}: {e}')

log('')
log('Removing in reverse order:')
for name, t in reversed(translators):
    app.removeTranslator(t)
    r = QtCore.QCoreApplication.translate('PyMOLQtGUI', 'About PyMOL')
    state = 'OK' if r == '关于 PyMOL' else ('BROKEN' if r == 'About PyMOL' else '?')
    log(f'  -{name:30s} -> About PyMOL = {r!r:20s} ({state})')
    if state == 'OK':
        log(f'  >>> CULPRIT: {name}')
        break
