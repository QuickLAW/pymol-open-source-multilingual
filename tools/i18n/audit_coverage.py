"""AST-based i18n coverage audit.

Unlike the regex scanner, this walks the syntax tree so that a literal is
judged by whether it really sits inside a translate call, at any argument
position and any nesting depth. It answers three separate questions:

  unwrapped  user-visible literal passed straight to a Qt sink
  uncataloged literal correctly wrapped in _tr() but absent from the .ts files
  fake        catalog entry that is unfinished or identical to the source

Exit code is non-zero when any of the three is non-empty, so CI cannot pass
while strings are leaking.
"""
from __future__ import annotations

import argparse
import ast
import glob
import os
import re
import sys
import xml.etree.ElementTree as ET
from collections import defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]

SOURCE_GLOBS = [
    'modules/pmg_qt/**/*.py',
    'modules/pymol/**/*.py',
    'data/startup/**/*.py',
]

# Qt APIs whose string arguments end up on screen.
SINK_METHODS = {
    'setText', 'setWindowTitle', 'setToolTip', 'setStatusTip',
    'setPlaceholderText', 'setWhatsThis', 'setTitle', 'setLabelText',
    'setInformativeText', 'setDetailedText', 'setPlainText', 'setHtml',
    'setDescription', 'setSummary', 'setLabel', 'setTabText',
    'setButtonText', 'setHeader', 'setHeaderLabels', 'setWindowTitlePrefix',
    'insertItem', 'addItem', 'addItems', 'setMessage', 'addAction',
    'setFilter', 'setNameFilter', 'setWindowTitleSuffix',
}
SINK_CLASSES = {
    'QMessageBox', 'QInputDialog', 'QErrorMessage', 'QMimeData',
    'QTreeWidgetItem', 'QListWidgetItem', 'QTableWidgetItem',
    'QTableView', 'QGroupBox', 'QPushButton', 'QLabel', 'QCheckBox',
    'QRadioButton', 'QTabWidget', 'QMenu', 'QAction', 'QToolButton',
}
IGNORE_METHODS = {
    'setObjectName', 'setProperty', 'setStyleSheet', 'setGeometry',
    'setSizeHint', 'setAccessibleName', 'setAccessibleDescription',
}

# Functions that resolve a translation at runtime.
TR_FUNCS = {'_tr', 'tr', 'i18n.tr', 'translate', '_mtr', 'ctr'}
MENU_CONTEXT = 'Menu'
# pymol.console_i18n.ctr() has one argument and a fixed context.
CONSOLE_CONTEXT = 'Console'

# Console/output-window writers. Text here is shown to the user in the
# PyMOL output window, so it belongs in a translation audit.
CONSOLE_FUNCS = {
    'print', 'print_msg', 'print_user', 'PRINTFB', 'sys.stdout.write',
    'stdout.write',
}

_UI_PROPS = {
    'windowTitle', 'title', 'text', 'label', 'toolTip', 'whatsThis',
    'statusTip', 'placeholderText', 'toolButtonText', 'html', 'plainText',
    'caption',
}

# Entries that stay English on purpose: file-format and product names, and
# template placeholders substituted into an already-translated sentence.
# Anything listed here is exempt from the "identity means untranslated"
# test, so the gate stays meaningful instead of drowning in true negatives.
APPROVED_IDENTITY = {
    ('Builder', 'DNA'), ('Builder', 'RNA'),
    ('Dialog', 'partial=1'),
    ('Form', '--ff=AMBER'), ('Form', '360p'), ('Form', '480p'),
    ('Form', '720p'), ('Form', 'prepwizard (SCHRODINGER)'),
    ('Form', '{loadtime}'), ('Form', '{name}'), ('Form', '{name}_{state}'),
    ('Form', '{pluginname}'), ('Form', '{version}'),
    ('Menu', 'COLLADA...'), ('Menu', 'GLTF...'), ('Menu', 'MPEG...'),
    ('Menu', 'PNG...'), ('Menu', 'POV-Ray...'), ('Menu', 'STL...'),
    ('Menu', 'VRML 2...'),
    ('PyMOLQtGUI', 'PyMOL (%s)'),
}

# A literal that is obviously not prose: no letters, a bare format spec,
# a Qt stylesheet/colour name, a filename/URL, or a command-line fragment.
BENIGN_EXACT = {
    '', ' ', '\n', '\t', '|', '-', '--', ':', ',', ';', '*', '#', '%s', '%d',
    '%g', '%f', '%r', '%.1f', '%.2f', '%.3f', '%02d', '%s %s', '...', '>>>',
    'PyMOL>', 'None', 'True', 'False', 'utf-8', 'rb', 'wb', 'r', 'w', 'a',
    'png', 'pdb', 'cif', 'xml', 'json', 'py', 'qt', 'Qt', 'all', 'none',
}
BENIGN_RE = [
    re.compile(r'^[%{][.0-9]*[sdfgeixxo]\}?[:\s]*$'),        # '%s' / '{}'
    re.compile(r'^https?://'),
    re.compile(r'^file://'),
    re.compile(r'^[\w./+\\-]+\.(png|jpg|pdb|cif|mol|pse|py|ui|xml|json|csv|gz|zip)$'),
    re.compile(r'^[A-Za-z_][A-Za-z0-9_]*$'),                   # a single identifier
    re.compile(r'^[#%\*\-\+=_ \d.:,;xX|/\\]+$'),               # separators
    re.compile(r'^[a-z]+_[a-z0-9_ ,|*+-]*$'),                  # snake_case key lists
]


def _benign(text: str) -> bool:
    if text in BENIGN_EXACT:
        return True
    if not any(c.isalpha() for c in text):
        return True
    if len(text.strip()) <= 1:
        return True
    return any(r.match(text) for r in BENIGN_RE)


def _ui_reportable(text: str) -> bool:
    """Widget text is user-visible whatever its length, so the prose test used
    for console output must not apply: 'Width', 'Reset' and 'Save...' are real
    labels and were silently hidden by it once before.
    """
    t = text.strip()
    if not t:
        return False
    if t in {'...', '…', '|', '-', ':', 'x', 'X', 'A', 'B'}:
        return False
    if BENIGN_RE[0].match(t):          # bare format spec: %s / {}
        return False
    if re.fullmatch(r'\{[a-z_]+\}', t):  # template placeholder
        return False
    return any(c.isalpha() for c in t)



_PROSE_RE = re.compile(r'\b([A-Za-z]{2,}\s+){2,}[A-Za-z]{2,}')


def _prose(text: str) -> bool:
    """True when a console string reads as an English sentence, not a dump.

    PyMOL prints a lot of coordinate tables, atom counts and CGO code; only
    sentence-shaped output is worth putting in a catalog.
    """
    if _benign(text):
        return False
    t = text.strip()
    if len(t) < 12 or not t[0].isalpha():
        return False
    return bool(_PROSE_RE.search(t))


def _func_name(node: ast.expr) -> str:
    if isinstance(node, ast.Name):
        return node.id
    if isinstance(node, ast.Attribute):
        base = _func_name(node.value)
        return f'{base}.{node.attr}' if base else node.attr
    return ''


def _is_tr_call(node: ast.AST) -> tuple[bool, str | None]:
    """(is_translate_call, context_or_None). None context means unresolved."""
    if not isinstance(node, ast.Call):
        return False, None
    name = _func_name(node.func)
    short = name.split('.')[-1]
    if name not in TR_FUNCS and short not in TR_FUNCS:
        return False, None
    if name == '_mtr':
        return True, MENU_CONTEXT
    if name == 'ctr':
        return True, CONSOLE_CONTEXT
    if short in ('_tr', 'tr', 'translate') and node.args:
        a0 = node.args[0]
        if isinstance(a0, ast.Constant) and isinstance(a0.value, str):
            # _tr('Ctx', 'text'); a 1-arg self.tr('text') keeps its class context
            if len(node.args) >= 2:
                return True, a0.value
            return True, None
    return True, None


class Walk(ast.NodeVisitor):
    def __init__(self, path: Path):
        self.path = path
        self.in_tr = 0
        self.class_name = ''
        self.unwrapped = []   # (line, sink, text)
        self.wrapped = []     # (line, context_or_None, text)
        self.console = []     # (line, func, text)
        self.consts = {}      # module-level str constants, by name

    def collect_consts(self, tree: ast.Module):
        """Map module-level NAME -> its string value.

        pymol --help prints a module constant, so ctr(helptext1) carries no
        literal at the call site and a literal-only scan cannot see the
        largest block of user-facing text in the program.
        """
        for st in tree.body:
            if isinstance(st, ast.Assign):
                if not isinstance(st.value, ast.Constant) or not isinstance(
                        st.value.value, str):
                    continue
                for tgt in st.targets:
                    if isinstance(tgt, ast.Name):
                        self.consts[tgt.id] = st.value.value

    def _text_of(self, node):
        if isinstance(node, ast.Constant) and isinstance(node.value, str):
            return node.value
        if isinstance(node, ast.Name) and node.id in self.consts:
            return self.consts[node.id]
        return None

    def visit_ClassDef(self, node):
        outer, self.class_name = self.class_name, node.name
        self.generic_visit(node)
        self.class_name = outer

    def visit_Call(self, node):
        is_tr, ctx = _is_tr_call(node)
        name = _func_name(node.func)
        short = name.split('.')[-1]

        if is_tr:
            # Record the catalogued string, then look inside for anything
            # that escaped (a second positional literal is often user text).
            args = node.args
            if name in ('_mtr', 'ctr'):
                ctx = MENU_CONTEXT if name == '_mtr' else CONSOLE_CONTEXT
                for a in args:
                    t = self._text_of(a)
                    if t is not None:
                        self.wrapped.append((node.lineno, ctx, t))
            elif len(args) >= 2:
                a0, a1 = args[0], args[1]
                if (isinstance(a0, ast.Constant) and isinstance(a0.value, str)):
                    t = self._text_of(a1)
                    if t is not None:
                        self.wrapped.append((node.lineno, a0.value, t))
            self.in_tr += 1
            for child in ast.iter_child_nodes(node):
                self.visit(child)
            self.in_tr -= 1
            return

        is_sink = (short in SINK_METHODS and short not in IGNORE_METHODS)
        if isinstance(node.func, ast.Attribute) and node.func.attr in IGNORE_METHODS:
            is_sink = False
        # QMessageBox.warning(parent, "Title", "Body") and friends: the class
        # name can sit anywhere in the dotted path and the literals are never
        # the first argument, so a prefix-only test silently misses every one.
        parts = name.split('.')
        if any(p in SINK_CLASSES for p in parts):
            is_sink = True

        if is_sink:
            for a in ast.iter_child_nodes(node):
                if isinstance(a, ast.Constant) and isinstance(a.value, str):
                    if not _benign(a.value):
                        self.unwrapped.append((node.lineno, short, a.value))

        # Console text lands in the GUI output window, so it is as
        # user-visible as a menu label -- but nothing audited it before.
        # print(..., file=f) writes generated source or data to disk, not to
        # the user, and localising it would corrupt the emitted file.
        to_file = any(k.arg == 'file' for k in node.keywords)
        if short in CONSOLE_FUNCS and not is_tr and not to_file:
            for a in ast.iter_child_nodes(node):
                lit = None
                if isinstance(a, ast.Constant) and isinstance(a.value, str):
                    lit = a
                elif (isinstance(a, ast.BinOp) and isinstance(a.op, ast.Mod)
                      and isinstance(a.left, ast.Constant)
                      and isinstance(a.left.value, str)):
                    # "Error: no such %s" % name -- still user-visible prose
                    lit = a.left
                if lit is not None and _prose(lit.value):
                    self.console.append((node.lineno, name, lit.value))
        # A bare literal that is itself a translated-value comparison, e.g.
        # `if text == 'x'`, is handled by the sink test above; nothing to do.
        self.generic_visit(node)


def scan_sources():
    unwrapped, console = [], []
    wrapped = defaultdict(set)
    files = set()
    for g in SOURCE_GLOBS:
        files.update(ROOT.glob(g))
    for path in sorted(p for p in files if p.is_file()):
        try:
            tree = ast.parse(path.read_text(encoding='utf-8', errors='replace'))
        except SyntaxError as e:
            print(f'  !! cannot parse {path}: {e}', file=sys.stderr)
            continue
        w = Walk(path)
        w.collect_consts(tree)
        w.visit(tree)
        rel = path.relative_to(ROOT).as_posix()
        for line, sink, text in w.unwrapped:
            unwrapped.append((rel, line, sink, text))
        for line, func, text in w.console:
            console.append((rel, line, func, text))
        for line, ctx, text in w.wrapped:
            wrapped[(ctx, text)].add(f'{rel}:{line}')
    # Position 1 must stay `wrapped`: generate_ts.py indexes it.
    return unwrapped, wrapped, console


def load_catalog(lang: str):
    """{(context, source): (translation, type_attr)} from every .ts for lang."""
    cat = {}
    for f in sorted(glob.glob(str(ROOT / 'data' / 'pmg_qt' / 'i18n' / lang / '*.ts'))):
        try:
            root = ET.parse(f).getroot()
        except ET.ParseError as e:
            print(f'  !! cannot parse {f}: {e}', file=sys.stderr)
            continue
        for ctx_el in root.findall('context'):
            cname = ctx_el.findtext('name', '')
            for msg in ctx_el.findall('message'):
                src = msg.findtext('source', '')
                tel = msg.find('translation')
                tr = (tel.text or '') if tel is not None else ''
                ttype = tel.get('type', '') if tel is not None else 'unfinished'
                cat[(cname, src)] = (tr, ttype)
    return cat


def scan_ui():
    out = []
    for path in sorted(ROOT.rglob('*.ui')):
        if 'build' in path.parts or '.venv' in path.parts:
            continue
        try:
            root = ET.parse(path).getroot()
        except ET.ParseError:
            continue
        cls = (root.findtext('class') or '').strip() or path.stem
        for prop in root.iter('property'):
            if prop.get('name') not in _UI_PROPS:
                continue
            s = prop.find('string')
            if s is None:
                continue
            # notr="true" is Designer's flag; uic/QUiLoader then emit the text
            # with no translate() call, so a catalogue entry can never reach it.
            if s.get('translatable', 'true') == 'false' or s.get('notr') == 'true':
                continue
            text = s.text or ''
            if _ui_reportable(text):
                out.append((cls, text, path.relative_to(ROOT).as_posix()))
    return out


def main(argv):
    if hasattr(sys.stdout, 'reconfigure'):
        # Windows consoles default to a legacy code page that cannot encode
        # the Chinese strings this audit prints.
        sys.stdout.reconfigure(encoding='utf-8', errors='replace')
    ap = argparse.ArgumentParser()
    ap.add_argument('--lang', default='zh_CN')
    ap.add_argument('--verbose', action='store_true', help='list every finding')
    ap.add_argument('--no-console', action='store_true',
                    help='exclude console-output findings from the failure count')
    args = ap.parse_args(argv)

    cat = load_catalog(args.lang)
    unwrapped, wrapped, console = scan_sources()
    ui = scan_ui()

    uncataloged = []
    for (ctx, text), where in sorted(wrapped.items()):
        if ctx is None:
            ctx = '?'
        if (ctx, text) not in cat:
            uncataloged.append((ctx, text, sorted(where)[0]))

    fake = []
    for (ctx, src), (tr, ttype) in sorted(cat.items()):
        if not src.strip():
            continue
        if ttype in ('unfinished', 'obsolete', 'vanishing'):
            fake.append((ctx, src, ttype))
        elif tr.strip() == src.strip() and not _benign(src):
            if (ctx, src) in APPROVED_IDENTITY:
                continue
            fake.append((ctx, src, 'identity'))

    # .ui strings must exist in the catalog under the form's own context,
    # which is the class name recorded by uic/QUiLoader.
    ui_missing = [(cls, text, f) for cls, text, f in ui if (cls, text) not in cat]

    print(f'=== i18n coverage audit ({args.lang}) ===')
    print(f'catalog entries      : {len(cat)}')
    print(f'wrapped literals     : {len(wrapped)}')
    print(f'.ui translatable     : {len(ui)}')
    print()
    # Console text is covered once the exact sentence exists in the catalog
    # under any context; a context-per-module split would double-count the
    # same message printed from several places.
    catalog_sources = {src for (_ctx, src) in cat}
    seen = set()
    console_leaks = []
    for rel, line, func, text in sorted(console):
        if text in catalog_sources or text in seen:
            continue
        seen.add(text)
        console_leaks.append((rel, line, func, text))

    groups = [
        ('UNWRAPPED (never translated)', unwrapped),
        ('WRAPPED BUT NOT IN CATALOG', uncataloged),
        ('FAKE / UNFINISHED CATALOG ENTRY', fake),
        ('UI STRING NOT IN CATALOG', ui_missing),
        ('CONSOLE OUTPUT NOT IN CATALOG', [] if args.no_console else console_leaks),
    ]
    print(f'console prose candidates: {len(console_leaks)} '
          f'(suppressed by --no-console)' if args.no_console
          else f'console prose candidates: {len(console_leaks)}')
    print()
    bad = 0
    for title, rows in groups:
        bad += len(rows)
        print(f'--- {title}: {len(rows)}')
        if rows and (args.verbose or len(rows) <= 200):
            for r in rows:
                print('    ' + ' | '.join(str(x)[:90] for x in r))
        print()
    print(f'TOTAL FINDINGS: {bad}')
    return 1 if bad else 0


if __name__ == '__main__':
    raise SystemExit(main(sys.argv[1:]))
