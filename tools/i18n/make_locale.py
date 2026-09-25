"""Derive a Chinese-traditional locale from the simplified one.

Adding a locale used to mean hand-copying generate_ts.py's zh_CN tables, which
is why only zh_CN existed. zh_TW is the special case where most of the work is
orthography rather than translation, so it is generated from the finished zh_CN
catalogue with OpenCC's s2twp profile -- which is phrase-aware and gets the
cases a naive character map gets wrong (然后->然後, 这里->這裡, 画面->畫面,
若干 stays 若干, 服务器->伺服器, 默认->預設, 界面->介面, 字符串->字串).

A small override table covers the choices OpenCC's general-language profile
does not make for us.

    python tools/i18n/make_locale.py --from zh_CN --to zh_TW          # write
    python tools/i18n/make_locale.py --from zh_CN --to zh_TW --check   # verify
"""
from __future__ import annotations

import argparse
import re
import subprocess
import sys
from pathlib import Path
from xml.etree import ElementTree as ET

ROOT = Path(__file__).resolve().parents[2]
I18N = ROOT / 'data' / 'pmg_qt' / 'i18n'

# Applied after conversion. Keys are the converted (traditional) text.
OVERRIDES = {
    # "Undo" reads as 復原 in TW application UI; 撤銷 is the PRC-side wording
    # that s2twp preserves because it is also correct traditional Chinese.
    '撤銷': '復原',
    # PyMOL ships a "Settings" menu; TW software UI uses 設定 for a menu of
    # options and 設置 for "install/configure", so keep them distinct.
    '高階設定': '進階設定',
}

TAG_RE = re.compile(r'<(/?)([A-Za-z_][\w.-]*)(\s[^>]*)?(/?)>')


def convert(text: str, cc) -> str:
    out = cc.convert(text)
    for k, v in OVERRIDES.items():
        out = out.replace(k, v)
    return out


def rewrite_ts(src: Path, dst: Path, cc) -> tuple[int, int]:
    """Convert every finished translation; keep English sources untouched."""
    tree = ET.parse(src)
    root = tree.getroot()
    root.set('language', dst.parent.name)
    total = changed = 0
    for msg in root.iter('message'):
        tel = msg.find('translation')
        if tel is None:
            continue
        text = tel.text or ''
        if not text.strip():
            continue
        total += 1
        new = convert(text, cc)
        if new != text:
            changed += 1
        tel.text = new
    xml = ET.tostring(root, encoding='unicode')
    dst.write_text(
        '<?xml version="1.0" encoding="utf-8"?>\n<!DOCTYPE TS>\n'
        + xml + '\n', encoding='utf-8')
    return total, changed


def main(argv) -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument('--from', dest='src', default='zh_CN')
    ap.add_argument('--to', dest='dst', default='zh_TW')
    ap.add_argument('--check', action='store_true',
                    help='report drift instead of writing')
    args = ap.parse_args(argv)
    sys.stdout.reconfigure(encoding='utf-8', errors='replace')

    from opencc import OpenCC
    cc = OpenCC('s2twp')

    src_dir = I18N / args.src
    dst_dir = I18N / args.dst
    if not src_dir.is_dir():
        print(f'no source locale: {src_dir}')
        return 2

    files = sorted(src_dir.glob('*.ts'))
    if args.check:
        if not dst_dir.is_dir():
            print(f'missing locale dir {dst_dir}')
            return 1
        drift = []
        for f in files:
            target = dst_dir / f.name
            if not target.is_file():
                drift.append(f.name)
                continue
            a = convert_text(ET.parse(f).getroot(), cc)
            b = text_of(ET.parse(target).getroot())
            if a != b:
                drift.append(f.name)
        print(f'{len(files) - len(drift)}/{len(files)} files match the '
              f'{args.src} derivation')
        for d in drift:
            print(f'  DRIFT {d}')
        return 1 if drift else 0

    dst_dir.mkdir(parents=True, exist_ok=True)
    tot = ch = 0
    for f in files:
        t, c = rewrite_ts(f, dst_dir / f.name, cc)
        tot += t
        ch += c
        print(f'  {f.name} -> {dst_dir.name}/{f.name}: {t} translated, {c} re-spelled')
    print(f'\n{tot} strings in {len(files)} files ({ch} changed by conversion)')

    lrelease = _tool('pyside6-lrelease')
    if not lrelease:
        print('pyside6-lrelease not found; run tools/i18n/compile_qm.py')
        return 0
    for ts in sorted(dst_dir.glob('*.ts')):
        subprocess.run([lrelease, str(ts), '-qm',
                        str(ts.with_suffix('.qm'))], check=True,
                       capture_output=True)
    print(f'compiled {len(list(dst_dir.glob("*.qm")))} .qm for {args.dst}')
    return 0


def text_of(root) -> list:
    return [(m.find('translation').text or '')
            for m in root.iter('message') if m.find('translation') is not None]


def convert_text(root, cc) -> list:
    out = []
    for m in root.iter('message'):
        tel = m.find('translation')
        if tel is None:
            continue
        t = tel.text or ''
        out.append(convert(t, cc) if t.strip() else t)
    return out


def _tool(name: str):
    for cand in ((ROOT / '.venv-i18n' / 'Scripts' / f'{name}.exe'),
                 (ROOT / '.venv-i18n' / 'bin' / name)):
        if cand.is_file():
            return str(cand)
    import shutil
    return shutil.which(name)


if __name__ == '__main__':
    raise SystemExit(main(sys.argv[1:]))
