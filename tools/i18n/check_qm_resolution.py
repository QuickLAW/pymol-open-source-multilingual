"""Assert every finished catalogue entry actually resolves through QTranslator.

The catalogue-completeness and AST-coverage gates both compare .ts against
source text. Neither can see the last step: lrelease may drop or alter an entry,
a context may not be the one the widget asks under, whitespace may differ
between the .ts and the compiled form. This loads the compiled .qm exactly the
way pymol.Qt.i18n.install() does and asks each finished entry for its
translation, so an entry that exists but can never be reached is a failure.
"""
from __future__ import annotations

import argparse
import glob
import os
import sys
import xml.etree.ElementTree as ET
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
sys.stdout.reconfigure(encoding='utf-8', errors='replace')

import audit_coverage as ac


def main(argv) -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument('--lang', default=os.environ.get('PYMOL_LANG', 'zh_CN'))
    ap.add_argument('--limit', type=int, default=25)
    args = ap.parse_args(argv)

    from PySide6 import QtCore, QtWidgets
    app = QtWidgets.QApplication.instance() or QtWidgets.QApplication([])

    root = ac.ROOT
    loc = root / 'data' / 'pmg_qt' / 'i18n' / args.lang
    refs = []
    for qm in sorted(loc.glob('*.qm')):
        t = QtCore.QTranslator()
        if t.load(str(qm)):
            app.installTranslator(t)
            refs.append(t)
    if not refs:
        print(f'no .qm loaded for {args.lang}')
        return 1

    # Qt's own catalogue, like i18n.install() arranges, so standard button
    # text is not reported as dead.
    li = QtCore.QLibraryInfo
    qt = QtCore.QTranslator()
    if qt.load(f'qtbase_{args.lang}.qm', li.path(li.LibraryPath.TranslationsPath)):
        app.installTranslator(qt)
        refs.append(qt)

    T = QtCore.QCoreApplication.translate
    total = 0
    dead = []
    for ts in sorted(loc.glob('*.ts')):
        name = ts.name
        for ctx in ET.parse(ts).getroot().findall('context'):
            cname = ctx.findtext('name', '')
            for msg in ctx.findall('message'):
                src = msg.findtext('source') or ''
                tel = msg.find('translation')
                tr = (tel.text or '') if tel is not None else ''
                if not tr.strip():
                    continue        # unfinished: nothing to resolve
                if not src.strip():
                    continue
                total += 1
                got = T(cname, src)
                if got == src and tr.strip() != src.strip():
                    dead.append((name, cname, src))

    print(f'{len(refs)} translators; {total} finished entries checked')
    for name, cname, src in dead[:args.limit]:
        print(f'  DEAD  {name} [{cname}] {src[:70]!r}')
    if len(dead) > args.limit:
        print(f'  ... {len(dead) - args.limit} more')
    print(f'\n{total - len(dead)}/{total} entries resolve at runtime')
    return 1 if dead else 0


if __name__ == '__main__':
    raise SystemExit(main(sys.argv[1:]))
