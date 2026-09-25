"""Find prose strings sitting in module-level data tables.

Every other gate looks at a translate *call*: it asks whether the literal that
reaches _tr()/ctr()/setText() is catalogued. Text that lives in a module-level
list, tuple or dict never reaches such a call at the point of definition -- it
is looked up later and handed to a widget or the output window as data. The
viewport labels in pymol/Qt/i18n.py and the --help blocks were both this shape,
so the class is real and otherwise unmeasured.

This lists the candidate tables so each can be made translatable or marked
intentionally-English (setting names, keywords and file formats belong to the
latter group: the user has to type them).

    python tools/i18n/scan_data_tables.py [--show-ignored]
"""
from __future__ import annotations

import argparse
import ast
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
sys.stdout.reconfigure(encoding='utf-8', errors='replace')

import audit_coverage as ac

# Tables whose contents are identifiers the user types, not prose to read.
IGNORED_TABLES = {
    # setting names / keywords / file extensions
    ('modules/pymol/setting.py', 'name_dict'),
    ('modules/pymol/parsing/Lexer.py', 'c_tokens'),
}

# Tables that ARE user-visible text, mapped to the context they are translated
# under and a function pulling the display strings out of the literal. Every
# value they yield must be finished in the catalogue -- no call-site gate can
# see this pairing, because the lookup happens later.
def _tuple_field(i):
    def get(node):
        out = []
        for v in node.values if isinstance(node, ast.Dict) else []:
            if isinstance(v, (ast.Tuple, ast.List)) and len(v.elts) > i:
                e = v.elts[i]
                if isinstance(e, ast.Constant) and isinstance(e.value, str) \
                        and e.value.strip():
                    out.append(e.value)
        return out
    return get


TRANSLATABLE_TABLES = {
    # shortcut_dict_ref[key] = (command, description, user_command); the
    # description is the editor's third column
    ('modules/pymol/shortcut_dict.py', 'shortcut_dict_ref'):
        ('ShortcutMenu', _tuple_field(1)),
}

CONTAINERS = (ast.List, ast.Tuple, ast.Set)


def prose_strings(node):
    """All prose string constants anywhere inside a literal container."""
    out = []
    for c in ast.walk(node):
        if isinstance(c, ast.Constant) and isinstance(c.value, str):
            if ac._prose(c.value):
                out.append(c.value)
    return out


def registered_tables():
    """[(relpath, varname, context, [display strings])] for TRANSLATABLE_TABLES."""
    out = []
    for rel, var in TRANSLATABLE_TABLES:
        path = ac.ROOT / rel
        if not path.is_file():
            continue
        tree = ast.parse(path.read_text(encoding='utf-8', errors='replace'))
        ctx, extract = TRANSLATABLE_TABLES[(rel, var)]
        for st in tree.body:
            if (isinstance(st, ast.Assign)
                    and any(isinstance(t, ast.Name) and t.id == var
                            for t in st.targets)):
                out.append((rel, var, ctx, extract(st.value)))
    return out


def main(argv):
    ap = argparse.ArgumentParser()
    ap.add_argument('--show-ignored', action='store_true')
    ap.add_argument('--lang', default='zh_CN')
    args = ap.parse_args(argv)

    catalog = ac.load_catalog(args.lang)

    registered = {(rel, var): (ctx, values)
                  for rel, var, ctx, values in registered_tables()}
    missing = []
    for (rel, var), (ctx, values) in sorted(registered.items()):
        uncat = [v for v in values if (ctx, v) not in catalog]
        print(f'  {rel} {var} -> context {ctx!r}: '
              f'{len(values) - len(uncat)}/{len(values)} catalogued')
        for v in uncat:
            missing.append((ctx, v, f'{rel}:{var}'))

    files = set()
    for g in ac.SOURCE_GLOBS:
        files.update(ac.ROOT.glob(g))

    hits = []
    for path in sorted(p for p in files if p.is_file()):
        rel = path.relative_to(ac.ROOT).as_posix()
        if rel in ac.LEGACY_TK_MODULES:
            continue
        try:
            tree = ast.parse(path.read_text(encoding='utf-8', errors='replace'))
        except SyntaxError:
            continue
        for st in tree.body:                      # module level only
            if not isinstance(st, ast.Assign):
                continue
            names = [t.id for t in st.targets if isinstance(t, ast.Name)]
            if not names:
                continue
            key = (rel, names[0])
            if key in registered:
                continue

            if isinstance(st.value, CONTAINERS):
                values = prose_strings(st.value)
            elif isinstance(st.value, ast.Dict):
                # keys are usually identifiers; the values are the labels
                values = []
                for v in st.value.values:
                    values.extend(prose_strings(v))
            else:
                continue
            if not values:
                continue
            ignored = key in IGNORED_TABLES
            if ignored and not args.show_ignored:
                continue
            hits.append((rel, st.lineno, names[0], len(values), values[:3],
                         ignored))

    for ctx, v, where in missing:
        print(f'  UNTRANSLATED [{ctx}] {v!r}  ({where})')
    if hits:
        print(f'\n{len(hits)} unregistered table(s) holding prose strings:')
        for rel, ln, name, n, sample, ignored in hits:
            tag = 'ignored' if ignored else 'REVIEW'
            print(f'  [{tag}] {rel}:{ln} {name} ({n} prose strings)')
            for s in sample:
                print(f'            {s[:72]!r}')
        print('\nRegister it in TRANSLATABLE_TABLES (and translate at render '
              'time) or IGNORED_TABLES with a reason.')
    if not missing and not hits:
        print('OK: every data-table string is catalogued or classified')
    return 1 if (missing or hits) else 0


if __name__ == '__main__':
    raise SystemExit(main(sys.argv[1:]))
