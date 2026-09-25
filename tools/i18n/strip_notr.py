"""Un-mark user-visible .ui strings that Designer exported as notr="true".

``<string notr="true">`` is Qt Designer's "not translatable" flag: uic and
QUiLoader then emit the text *without* a translate() call, so no catalogue
entry can ever reach the widget. 308 strings were marked this way, including
every label in props.ui and most of apbs.ui, which is why the forms looked
fully translated to the audit yet painted English.

Only the properties whose value is shown to the user are un-marked. styleSheet
(QSS) and suffix (unit symbols like %, cm, px) keep their notr flag.
"""
from __future__ import annotations

import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]

VISIBLE = ('text', 'toolTip', 'title', 'windowTitle', 'placeholderText',
           'statusTip', 'whatsThis', 'toolButtonText', 'label', 'caption',
           'plainText')

# QTabWidget page titles are <attribute name="title">, not <property>, so
# matching only <property> left every tab label marked notr and untranslated.
PROP = re.compile(
    r'<(property|attribute) name="(' + '|'.join(VISIBLE) + r')"[^>]*>(.*?)</\1>',
    re.DOTALL)
NOTR = re.compile(r'(<string)\s+notr="true"(\s*>)')
# An empty or whitespace-only string has nothing to translate.
BLANK = re.compile(r'<string>\s*</string>')


def main() -> int:
    total_files = total_strings = 0
    for path in sorted(ROOT.rglob('*.ui')):
        if '.venv' in path.parts or 'build' in path.parts:
            continue
        src = path.read_text(encoding='utf-8')
        changed = 0

        def repl(m):
            nonlocal changed
            tag, name, body = m.group(1), m.group(2), m.group(3)
            whole = m.group(0)
            prefix = whole[:whole.index('>') + 1]
            new, n = NOTR.subn(r'\1\2', body)
            if n:
                changed += n
            return prefix + new + f'</{tag}>'

        out = PROP.sub(repl, src)
        total_strings += changed
        if changed:
            path.write_text(out, encoding='utf-8', newline='')
            total_files += 1
            print(f'{path.relative_to(ROOT).as_posix()}: {changed} string(s)')
    print(f'\n{total_strings} string(s) made translatable in {total_files} file(s)')
    return 0


if __name__ == '__main__':
    sys.stdout.reconfigure(encoding='utf-8')
    raise SystemExit(main())
