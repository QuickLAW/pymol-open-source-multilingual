"""Keep CJK punctuation where it belongs: fullwidth only around Chinese.

Chinese typography uses （） for a parenthetical written in Chinese, but a
bracketed code fragment, format specifier, number or identifier stays
halfwidth -- （%s）, （0-14）, （-1/0/1）, （=specular）, （segi） are all wrong: they
look off next to ASCII, and a user copying the text out gets fullwidth
characters that PyMOL will not accept.

13 catalogue entries had this, so the rule lives here once and generate_ts
applies it on the way out; that way zh_CN and every derived locale agree, and
this file's --check mode fails if a future entry reintroduces it.

The rule is deliberately narrow: it only rewrites a （...） whose content holds
no CJK character. Anything with Chinese inside keeps fullwidth, and the
trailing-mnemonic form Qt needs for Chinese labels -- MOV（QuickTime）(&K) --
is untouched because its brackets already are halfwidth.
"""
from __future__ import annotations

import argparse
import glob
import re
import sys
import xml.etree.ElementTree as ET
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]

FULL = re.compile(r'（([^（）]*)）')
CJK = re.compile(r'[\u3400-\u4dbf\u4e00-\u9fff\uf900-\ufaff]')


def normalize_parens(text: str) -> str:
    """Halfwidth () when the bracketed run contains no Chinese."""
    if not text or '（' not in text:
        return text

    def fix(m):
        inner = m.group(1)
        return f'({inner})' if inner and not CJK.search(inner) else m.group(0)

    return FULL.sub(fix, text)


def offenders(text: str):
    return [m.group(0) for m in FULL.finditer(text)
            if m.group(1) and not CJK.search(m.group(1))]


def main(argv) -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument('--lang', default='zh_CN')
    args = ap.parse_args(argv)
    sys.stdout.reconfigure(encoding='utf-8', errors='replace')

    bad = []
    total = 0
    for f in sorted(glob.glob(str(ROOT / 'data' / 'pmg_qt' / 'i18n' / args.lang / '*.ts'))):
        for msg in ET.parse(f).getroot().iter('message'):
            tel = msg.find('translation')
            t = (tel.text or '') if tel is not None else ''
            if not t.strip():
                continue
            total += 1
            o = offenders(t)
            if o:
                bad.append((Path(f).name, msg.findtext('source') or '', o))

    print(f'{total} translations checked; {len(bad)} with fullwidth '
          f'brackets around non-Chinese content')
    for name, src, o in bad[:20]:
        print(f'  {name}  {src[:52]!r}  -> {o}')
    if not bad:
        print('OK: punctuation width consistent')
    return 1 if bad else 0


if __name__ == '__main__':
    raise SystemExit(main(sys.argv[1:]))
