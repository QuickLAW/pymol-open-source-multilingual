"""Wrap output-window messages in ctr() so they can be localised.

Console text is user-visible but nothing below the Qt layer could translate
it, so the strings were simply invisible to the i18n pipeline. This rewrites
the call sites in place and prints the deduplicated list of source strings
that then need a zh_CN entry.

It only touches a literal when the literal is the whole argument, or the left
side of a ``"...%s..." % args`` binary -- wrapping the constant keeps the
format specifiers applied to the translated text, which is what Qt's own
``arg()``/printf workflow does too.

    python tools/i18n/wrap_console.py            # report
    python tools/i18n/wrap_console.py --apply    # rewrite
"""
from __future__ import annotations

import argparse
import ast
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
sys.stdout.reconfigure(encoding='utf-8', errors='replace')

import audit_coverage as ac

ROOT = ac.ROOT
IMPORT_LINE = 'from pymol.console_i18n import ctr'
SKIP = {'modules/pymol/console_i18n.py', 'tools/i18n'}


def _targets(tree: ast.Module, src: str):
    """Yield (span_start, span_end, literal_source, text) to rewrite."""
    out = []

    class V(ast.NodeVisitor):
        def __init__(self):
            self.in_tr = 0

        def visit_Call(self, node):
            is_tr, _ = ac._is_tr_call(node)
            name = ac._func_name(node.func)
            short = name.split('.')[-1]
            if short in ('ctr',) or is_tr:
                self.in_tr += 1
                self.generic_visit(node)
                self.in_tr -= 1
                return
            if short in ac.CONSOLE_FUNCS and not any(
                    k.arg == 'file' for k in node.keywords):
                # print(..., file=f) emits generated source/data, not UI text
                for a in node.args:
                    lit = None
                    if isinstance(a, ast.Constant) and isinstance(a.value, str):
                        lit = a
                    elif (isinstance(a, ast.BinOp) and isinstance(a.op, ast.Mod)
                          and isinstance(a.left, ast.Constant)
                          and isinstance(a.left.value, str)):
                        lit = a.left
                    if lit is None or not ac._prose(lit.value):
                        continue
                    seg = ast.get_source_segment(src, lit)
                    if seg is None:
                        continue
                    out.append((lit.lineno, lit.col_offset, lit.end_lineno,
                                lit.end_col_offset, seg, lit.value))
            self.generic_visit(node)

    V().visit(tree)
    return out


def _insert_import(lines, tree, nl='\n'):
    """Add the shim import after the module's leading import block."""
    last = 0
    start = 0
    body = list(tree.body)
    if (body and isinstance(body[0], ast.Expr)
            and isinstance(body[0].value, ast.Constant)
            and isinstance(body[0].value.value, str)):
        start = body[0].end_lineno  # keep the docstring first
    seen = False
    for st in body[start:]:
        if isinstance(st, (ast.Import, ast.ImportFrom)):
            # try/except import blocks are still sequential top-level nodes
            last = max(last, st.end_lineno)
            seen = True
        elif seen and isinstance(st, ast.Try):
            break
        elif seen:
            break
    at = last or start
    # Never land inside a leading copyright banner: those files have no
    # top-level imports before it, so `at` would otherwise be 0.
    while at < len(lines) and (
            lines[at].lstrip().startswith('#') or not lines[at].strip()):
        at += 1
    # The newline matters: an element without one joins the following line
    # when the list is re-joined, gluing the import onto the next statement.
    lines.insert(at, IMPORT_LINE + nl)
    return lines


def main(argv):
    ap = argparse.ArgumentParser()
    ap.add_argument('--apply', action='store_true')
    args = ap.parse_args(argv)

    files = set()
    for g in ac.SOURCE_GLOBS:
        files.update(ROOT.glob(g))
    collected = {}
    touched = 0

    for path in sorted(p for p in files if p.is_file()):
        rel = path.relative_to(ROOT).as_posix()
        if any(s in rel for s in SKIP):
            continue
        src = path.read_text(encoding='utf-8', errors='replace')
        try:
            tree = ast.parse(src)
        except SyntaxError:
            continue
        tg = _targets(tree, src)
        if not tg:
            continue
        if IMPORT_LINE in src:
            # already wrapped; the literals are what matters now
            for _ in tg:
                collected.setdefault(_[5], rel)
            continue
        for _ in tg:
            collected.setdefault(_[5], rel)
        touched += 1
        if not args.apply:
            continue

        # Rewrite backwards so earlier Spans keep their offsets.
        lines = src.splitlines(keepends=True)
        nl = '\r\n' if '\r\n' in src else '\n'

        def offset(lineno, col):
            off = 0
            for i in range(lineno - 1):
                off += len(lines[i])
            return off + col

        flat = ''.join(lines)
        for lineno, col, elineno, ecol, seg, text in sorted(
                tg, key=lambda t: (t[0], t[1]), reverse=True):
            s = offset(lineno, col)
            e = offset(elineno, ecol)
            flat = flat[:s] + f'ctr({seg})' + flat[e:]
        lines = flat.splitlines(keepends=True)
        lines = _insert_import(lines, ast.parse(flat), nl)
        new = ''.join(lines)
        # Never write a file this tool just broke: an earlier version glued
        # the import onto the next statement and corrupted seven modules.
        try:
            ast.parse(new)
        except SyntaxError as e:
            print(f'SKIP {rel}: rewrite does not parse ({e})', file=sys.stderr)
            continue
        path.write_text(new, encoding='utf-8', newline='')

    print(f'{len(collected)} distinct console strings in {touched} files'
          + ('' if args.apply else '  (dry run)'))
    for text, rel in sorted(collected.items()):
        print(f'{rel}\t{text!r}')
    return 0


if __name__ == '__main__':
    raise SystemExit(main(sys.argv[1:]))
