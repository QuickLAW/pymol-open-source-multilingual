"""Fail when one English term is rendered several different ways.

Coverage gates only prove a string *has* a translation, not that it agrees with
the rest of the catalogue. A terminology sweep found two real defects that every
coverage number was happy about:

  * "Movie" appeared as 电影, 影片 and 动画 in three different parts of the UI --
    including the top-level menu against its own dialogs;
  * "Cycle bond valence" was 循环切换键级 in the menu and 循环切换键价 in the
    Builder tooltip describing the same command.

Each term lists the renderings that are acceptable, which covers the legitimate
compounds (双键/单键/键角 are correct chemistry, and forcing 化学键 into them
would be worse than the status quo). Anything else is a finding.

    python tools/i18n/check_terminology.py [--lang zh_CN] [--list]
"""
from __future__ import annotations

import argparse
import os
import re
import sys
import xml.etree.ElementTree as ET
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
sys.stdout.reconfigure(encoding='utf-8', errors='replace')

ROOT = Path(__file__).resolve().parents[2]

# term -> (accepted renderings, terms that must win instead)
# The "wins" list stops a shorter word firing inside a longer, correct one.
TERMS = {
    'movie':        ['动画'],
    'frame':        ['帧', '循环播放'],   # the menu item is 'Loop Frames'
    'scene':        ['场景'],
    'selection':    ['选择', '反选'],   # 'invert selection'
    'object':       ['对象'],
    'state':        ['状态'],
    'residue':      ['残基'],
    'chain':        ['链'],
    'atom':         ['原子'],
    'molecule':     ['分子'],
    'plugin':       ['插件'],
    'wizard':       ['向导'],
    'surface':      ['表面', '曲面'],
    'volume':       ['体积'],
    'density':      ['密度'],
    'symmetry':     ['对称'],
    'ligand':       ['配体'],
    'hydrogen':     ['氢'],
    'charge':       ['电荷'],
    'valence':      ['键级', '化合价'],   # bond valence vs chemical valence
    'model':        ['模型'],
    'mask':         ['掩码'],
    'distance':     ['距离'],
    'angle':        ['角'],
    'color':        ['颜色', '色彩'],
    'bond':         ['化学键', '键'],
    'setting':      ['设置', '设定'],
}

# Sources where the English word is part of a literal name, a command, or an
# HTML block, so no Chinese term can appear. Matched against the source.
SKIP_SOURCE = re.compile(
    r'<!DOCTYPE|<html|href=|state=0|surface > |A > |CONECT|'
    r'\bset \b|default_|_\(|\[Ctrl|PyMOL>')


def accepted_for(lang):
    """The term map, re-spelled for a traditional locale.

    zh_TW is derived from zh_CN, so its renderings are the same words in
    traditional orthography; comparing them against simplified strings would
    report every entry as inconsistent.
    """
    if lang == 'zh_CN':
        return TERMS
    try:
        from opencc import OpenCC
        cc = OpenCC('s2twp')
    except ImportError:
        return TERMS
    return {t: [cc.convert(a) for a in v] for t, v in TERMS.items()}


def main(argv) -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument('--lang', default=os.environ.get('PYMOL_LANG', 'zh_CN'))
    ap.add_argument('--list', action='store_true', help='show every finding')
    args = ap.parse_args(argv)

    loc = ROOT / 'data' / 'pmg_qt' / 'i18n' / args.lang
    terms = accepted_for(args.lang)
    pairs = []
    for ts in sorted(loc.glob('*.ts')):
        for msg in ET.parse(ts).getroot().iter('message'):
            src = msg.findtext('source') or ''
            tel = msg.find('translation')
            tr = (tel.text or '') if tel is not None else ''
            if src.strip() and tr.strip() and tr.strip() != src.strip():
                pairs.append((ts.name, src, tr))

    findings = []
    for name, src, tr in pairs:
        if SKIP_SOURCE.search(src):
            continue
        for term, accepted in terms.items():
            if not re.search(r'\b' + term + r's?\b', src, re.I):
                continue
            if any(a in tr for a in accepted):
                break
            findings.append((term, accepted, name, src, tr))
            break

    by_term = {}
    for term, accepted, name, src, tr in findings:
        by_term.setdefault(term, []).append((name, src, tr))

    print(f'{len(pairs)} translated pairs checked against {len(terms)} terms')
    for term, rows in sorted(by_term.items()):
        print(f'  {term}: {len(rows)} (expects one of {"、".join(terms[term])})')
        if args.list:
            for name, src, tr in rows:
                print(f'      {name}  {src[:58]!r}')
                print(f'             {tr[:58]!r}')
    if not findings:
        print('OK: terminology consistent')
    return 1 if findings else 0


if __name__ == '__main__':
    raise SystemExit(main(sys.argv[1:]))
