"""Run every i18n gate in one go and fail if any of them leaks.

    python tools/i18n/run_gates.py [--lang zh_CN]

Each gate answers a different question, and history shows why one is not
enough: status.py reported 100% while seven strings were unreachable,
audit_coverage reported 0 findings while 308 .ui strings were marked
notr="true" and painted English, and both were silent about console output.
"""
from __future__ import annotations

import argparse
import subprocess
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]

GATES = [
    ('catalogue completeness', 'status.py'),
    ('console glossary (printf/whitespace safe)', 'check_console_glossary.py'),
    ('AST coverage: unwrapped/uncatalogued/ui/console', 'audit_coverage.py'),
    ('forms painted Chinese in real widgets', 'sweep_forms.py'),
    ('runtime lookups through QTranslator', 'test_translations.py'),
]


def main(argv) -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument('--lang', default='zh_CN')
    args = ap.parse_args(argv)
    sys.stdout.reconfigure(encoding='utf-8', errors='replace')

    failed = []
    for title, script in GATES:
        cmd = [sys.executable, str(HERE / script)]
        # status.py and test_translations.py take the language as argv[1];
        # the others default to zh_CN and take --lang.
        if script in ('status.py', 'test_translations.py'):
            cmd.append(args.lang)
        elif script == 'audit_coverage.py':
            cmd.append(f'--lang={args.lang}')
        p = subprocess.run(cmd, cwd=str(ROOT), capture_output=True, text=True,
                           encoding='utf-8', errors='replace')
        ok = p.returncode == 0
        tail = [l for l in (p.stdout or '').splitlines() if l.strip()]
        print(f'[{"PASS" if ok else "FAIL"}] {title}')
        for line in tail[-2:]:
            print(f'       {line}')
        if not ok:
            failed.append(title)
            for line in (p.stdout or '').splitlines():
                if ' | ' in line or line.startswith('  '):
                    print(f'       {line}')
            if p.stderr.strip():
                print(f'       stderr: {p.stderr.strip()[:400]}')
    print(f'\n{len(GATES) - len(failed)}/{len(GATES)} gates passed')
    for f in failed:
        print(f'  FAILED: {f}')
    return 1 if failed else 0


if __name__ == '__main__':
    raise SystemExit(main(sys.argv[1:]))
