"""Guard the console glossary against the three ways it can silently break.

A mistranslated console string is worse than an untranslated one: these
messages go through Python's ``%`` operator, so reordering or dropping a
specifier swaps or crashes values at runtime, and dropping the leading
spaces misaligns indented output. Nothing else in the pipeline would notice.

Checks every string the AST says is wrapped in ctr():
  * it has a glossary entry            (coverage)
  * no entry is orphaned               (typos in a key are otherwise invisible)
  * %s/%d/%.3f specifiers match in ORDER
  * leading/trailing whitespace matches
"""
from __future__ import annotations

import ast
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
sys.stdout.reconfigure(encoding='utf-8', errors='replace')

import audit_coverage as ac
from translations_console_zh import CONSOLE_ZH
from translations_blocks_zh import BLOCK_ZH_BY_SOURCE

SPEC = re.compile(r'%(?:\d+\$)?[-+ #0]*[\d.]*[sdifgeExXcr%]')


def specs(text: str) -> list[str]:
    return [s for s in SPEC.findall(text) if s != '%%']


def block_entries() -> dict[str, str]:
    """Resolve the by-variable-name glossary into source -> Chinese.

    Only blocks that the AST says are actually used as Console text are
    folded in, so a stale entry still shows up as an unused key.
    """
    out = {}
    for rel, mapping in BLOCK_ZH_BY_SOURCE.items():
        tree = ast.parse((ac.ROOT / rel).read_text(encoding='utf-8'))
        consts = {}
        for st in tree.body:
            if (isinstance(st, ast.Assign)
                    and isinstance(st.value, ast.Constant)
                    and isinstance(st.value.value, str)):
                for tgt in st.targets:
                    if isinstance(tgt, ast.Name):
                        consts[tgt.id] = st.value.value
        for var, zh in mapping.items():
            if var in consts:
                out[consts[var]] = zh
    return out


def main() -> int:
    _, wrapped, _ = ac.scan_sources()
    runtime = {t for (c, t) in wrapped if c == 'Console'}

    entries = dict(CONSOLE_ZH)
    entries.update({k: v for k, v in block_entries().items() if k in runtime})

    errors = []

    missing = sorted(runtime - set(entries))
    for t in missing:
        errors.append(f'NO TRANSLATION: {t[:120]!r}')

    orphan = sorted(set(entries) - runtime)
    for t in orphan:
        errors.append(f'UNUSED KEY (typo?): {t[:120]!r}')

    for t in sorted(runtime & set(entries)):
        z = entries[t]
        if specs(t) != specs(z):
            errors.append(
                f'SPECIFIER MISMATCH {specs(t)} -> {specs(z)} for {t!r}')
        if len(t) - len(t.lstrip(' ')) != len(z) - len(z.lstrip(' ')):
            errors.append(f'LEADING SPACES CHANGED for {t!r}')
        if len(t) - len(t.rstrip(' ')) != len(z) - len(z.rstrip(' ')):
            errors.append(f'TRAILING SPACES CHANGED for {t!r}')
        if not z.strip():
            errors.append(f'EMPTY TRANSLATION for {t!r}')

    print(f'{len(runtime)} console strings at runtime, '
          f'{len(entries)} glossary entries')
    for e in errors:
        print('  ' + e)
    print(f'{"FAIL" if errors else "OK"}: {len(errors)} problem(s)')
    return 1 if errors else 0


if __name__ == '__main__':
    raise SystemExit(main())
