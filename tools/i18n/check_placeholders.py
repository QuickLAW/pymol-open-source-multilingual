"""Fail when a translation cannot be substituted into like its source.

Nearly every gate so far asks whether a string is *translated*. None of them
asked whether the translated string still works when the program does
``_tr(...) % args`` or ``.format(...)`` -- a missing or reordered %s there is
not a cosmetic defect, it raises TypeError/ValueError at the moment a user
triggers the message.

Only the 241 console strings had that check (in check_console_glossary). This
covers the whole catalogue:

  * printf specifiers, compared as an ordered list because ``%`` with a tuple
    is positional -- reordering them for Chinese word order swaps values;
  * ``{}`` / ``{name}`` format fields;
  * Qt positional ``%1``..``%9`` arguments;
  * HTML/XML tags, since these strings go through QLabel's rich text and a
    dropped </a> leaves the label visibly broken;
  * the ``&`` accelerator count, so a menu item cannot lose its mnemonic.

    python tools/i18n/check_placeholders.py [--lang zh_CN]
"""
from __future__ import annotations

import argparse
import glob
import os
import re
import sys
import xml.etree.ElementTree as ET
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]

PRINTF = re.compile(r'%(?:\d+\$)?[-+ #0]*[\d.]*[sdifgeExXocr%]')
BRACE = re.compile(r'\{[a-zA-Z_0-9]*\}')
QTPos = re.compile(r'%(\d)')
TAG = re.compile(r'</?[a-zA-Z][^>]*/?>')
MNEM = re.compile(r'&([A-Za-z1-9])')
ENTITY = re.compile(r'&[a-zA-Z]+;|&#\d+;')


def mnemonics(text: str) -> list[str]:
    """Qt accelerators, with HTML entities removed first.

    Without that, &quot; reads as a mnemonic on 'q' and every rich-text label
    reports a false mismatch.
    """
    return MNEM.findall(ENTITY.sub('', text))


def printf(text: str) -> list[str]:
    return [s for s in PRINTF.findall(text) if s != '%%']


def main(argv) -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument('--lang', default=os.environ.get('PYMOL_LANG', 'zh_CN'))
    args = ap.parse_args(argv)
    sys.stdout.reconfigure(encoding='utf-8', errors='replace')

    loc = ROOT / 'data' / 'pmg_qt' / 'i18n' / args.lang
    total = 0
    problems = []
    for ts in sorted(loc.glob('*.ts')):
        for msg in ET.parse(ts).getroot().iter('message'):
            src = msg.findtext('source') or ''
            tel = msg.find('translation')
            tr = (tel.text or '') if tel is not None else ''
            if not src.strip() or not tr.strip():
                continue
            total += 1
            name = ts.name
            if printf(src) != printf(tr):
                problems.append((name, 'printf', src, tr,
                                 f'{printf(src)} -> {printf(tr)}'))
            elif sorted(BRACE.findall(src)) != sorted(BRACE.findall(tr)):
                problems.append((name, 'format-field', src, tr,
                                 f'{sorted(BRACE.findall(src))} -> '
                                 f'{sorted(BRACE.findall(tr))}'))
            elif sorted(QTPos.findall(src)) != sorted(QTPos.findall(tr)):
                problems.append((name, 'qt-positional', src, tr, ''))
            elif sorted(TAG.findall(src)) != sorted(TAG.findall(tr)):
                # <TAB> is a key name, not markup, but it is picked up by the
                # tag regex; compare it as a case-insensitive multiset so the
                # real signal is not buried under it.
                a = sorted(t.lower() for t in TAG.findall(src))
                b = sorted(t.lower() for t in TAG.findall(tr))
                if a != b:
                    problems.append((name, 'html-tag', src, tr,
                                     f'{sorted(TAG.findall(src))} -> '
                                     f'{sorted(TAG.findall(tr))}'))
            elif len(mnemonics(src)) != len(mnemonics(tr)):
                problems.append((name, 'mnemonic', src, tr,
                                 f'{mnemonics(src)} -> {mnemonics(tr)}'))

    print(f'{total} translated pairs checked for substitution safety')
    for name, kind, src, tr, detail in problems[:25]:
        print(f'  {name} [{kind}] {detail}')
        print(f'      EN {src[:78]!r}')
        print(f'      ZH {tr[:78]!r}')
    if len(problems) > 25:
        print(f'  ... {len(problems) - 25} more')
    if not problems:
        print('OK: every translation accepts the same arguments as its source')
    return 1 if problems else 0


if __name__ == '__main__':
    raise SystemExit(main(sys.argv[1:]))
