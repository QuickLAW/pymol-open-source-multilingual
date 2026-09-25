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
import re

from collections import defaultdict
import ast
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
sys.stdout.reconfigure(encoding='utf-8', errors='replace')

import audit_coverage as ac

# Tables whose contents are not display text -- the user types them, or they
# are notation, or they are deliberately written in their own language.
IGNORED_TABLES = {
    ('modules/pymol/setting.py', 'name_dict'):
        'setting names are typed by the user',
    ('modules/pymol/parsing/Lexer.py', 'c_tokens'):
        'language tokens',
    ('modules/pymol/completing.py', 'aa_map_c'):
        'command argument keyword, tab-completed and typed',
    ('modules/pymol/completing.py', 'aa_v_r_c'):
        'command argument keyword, tab-completed and typed',
    ('modules/pymol/completing.py', 'aa_ali_e'):
        'command argument keyword, tab-completed and typed',
    ('modules/pymol/internal.py', 'modifier_keys'):
        'modifier key codes (SHFT/CTRL/CTSH)',
    ('modules/pymol/Qt/i18n.py', 'LANGUAGE_LABELS'):
        'each language is named in its own script on purpose',
    ('modules/pymol/wizard/box.py', 'pseudo_atoms'):
        'pseudoatom resnames, typed in selections',
    ('modules/pymol/wizard/mutagenesis.py', '_rot_type_xref'):
        'residue 3-letter codes',
    ('modules/pymol/xray.py', 'hex_to_rhom_xHM'):
        'H-M space group symbols',
    ('modules/pymol/xray.py', 'sym_base'):
        'H-M space group symbols',
    ('modules/pymol/xray.py', 'space_group_map'):
        'H-M space group symbols',
}

# Tables that ARE user-visible text, mapped to the context they are translated
# under and a function pulling the display strings out of the literal. Every
# value they yield must be finished in the catalogue -- no call-site gate can
# see this pairing, because the lookup happens later.
def _tuple_field(i):
    """Yield the i-th string of every tuple/list literal, at any nesting depth.

    The Builder's tables are a list of rows of 3-tuples, so a flat scan of the
    assignment sees only the rows and finds nothing.
    """
    def get(node):
        out = []
        for n in ast.walk(node):
            if isinstance(n, (ast.Tuple, ast.List)) and len(n.elts) > i:
                e = n.elts[i]
                if isinstance(e, ast.Constant) and isinstance(e.value, str) \
                        and e.value.strip():
                    out.append(e.value)
        return out
    return get


def _all_strings(node):
    """Every string literal with letters in it -- for line-by-line text.

    Rules and separators ('=====', '') are layout, not text to translate.
    """
    return [c.value for c in ast.walk(node)
            if isinstance(c, ast.Constant) and isinstance(c.value, str)
            and c.value.strip() and any(ch.isalpha() for ch in c.value)]


def _dict_values(node):
    """Label strings among a dict's values only.

    Walking the whole literal also yields the keys, which for
    _VIEWPORT_TEXT_SETTINGS are setting names the user types -- not text.
    """
    if not isinstance(node, ast.Dict):
        return _all_strings(node)
    out = []
    for v in node.values:
        if isinstance(v, ast.Constant) and isinstance(v.value, str) \
                and v.value.strip() and any(c.isalpha() for c in v.value):
            out.append(v.value)
    return out


TRANSLATABLE_TABLES = {
    # shortcut_dict_ref[key] = (command, description, user_command); the
    # description is the editor's third column
    ('modules/pymol/shortcut_dict.py', 'shortcut_dict_ref'):
        ('ShortcutMenu', _tuple_field(1)),
    # builder.py: (label, tooltip, command) rows shown as fragment buttons.
    # The label is an element symbol or formula and stays as written.
    ('modules/pmg_qt/builder.py', 'buttons'):
        ('Builder', _tuple_field(1)),
    ('modules/pmg_qt/builder.py', 'dna_buttons'):
        ('Builder', _tuple_field(1)),
    ('modules/pmg_qt/builder.py', 'rna_buttons'):
        ('Builder', _tuple_field(1)),
    # the security wizard prints its prompt one line at a time
    ('modules/pymol/wizard/security.py', 'prompt'):
        ('Console', _all_strings),
    # i18n.py feeds these English sources through tr('Menu', source) and pushes
    # the result into settings 798-810; registering it proves the viewport text
    # stays translated when either side changes.
    ('modules/pymol/Qt/i18n.py', '_VIEWPORT_TEXT_SETTINGS'):
        ('Menu', _dict_values),
}

CONTAINERS = (ast.List, ast.Tuple, ast.Set)


_LABEL_RE = re.compile(r'^(?!.*_)[A-Z][A-Za-z]')


def looks_like_label(text: str) -> bool:
    """A string that reads as display text rather than as a key or code.

    _prose() needs two or more words, which is right for call-site arguments
    but wrong for tables: 'Hydrogen', 'Cyclohexane' and 'Methyl' are single
    words that were exactly the leak this file was written to find. So the
    table scan uses a looser test -- a space, or a Capitalised word -- and
    skips snake_case keys, ALL_CAPS codes and dotted names.
    """
    t = text.strip()
    if len(t) < 3 or not any(c.isalpha() for c in t):
        return False
    if ' ' in t:
        return True
    return bool(_LABEL_RE.match(t))


def prose_strings(node):
    """All label-like string constants anywhere inside a literal container."""
    out = []
    for c in ast.walk(node):
        if isinstance(c, ast.Constant) and isinstance(c.value, str):
            if looks_like_label(c.value):
                out.append(c.value)
    return out


def registered_tables():
    """[(relpath, varname, context, [display strings])] for TRANSLATABLE_TABLES.

    Searches every scope: the Builder's tables are locals inside a method, and
    several share one name across the file, so a module-level-only lookup would
    miss them.
    """
    out = []
    for rel, var in TRANSLATABLE_TABLES:
        path = ac.ROOT / rel
        if not path.is_file():
            continue
        tree = ast.parse(path.read_text(encoding='utf-8', errors='replace'))
        ctx, extract = TRANSLATABLE_TABLES[(rel, var)]
        for st in ast.walk(tree):
            if not isinstance(st, ast.Assign):
                continue
            matched = any(
                (isinstance(t, ast.Name) and t.id == var)
                or (isinstance(t, ast.Attribute) and t.attr == var)
                for t in st.targets)
            if matched:
                out.append((rel, var, ctx, extract(st.value)))
    return out


def main(argv):
    ap = argparse.ArgumentParser()
    ap.add_argument('--show-ignored', action='store_true')
    ap.add_argument('--lang', default='zh_CN')
    args = ap.parse_args(argv)

    catalog = ac.load_catalog(args.lang)

    registered = defaultdict(lambda: [None, []])
    for rel, var, ctx, values in registered_tables():
        slot = registered[(rel, var)]
        slot[0] = ctx
        slot[1].extend(values)
    missing = []
    for (rel, var), (ctx, values) in sorted(registered.items()):
        values = sorted(set(values))
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
