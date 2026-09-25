"""List string-literal-taking calls that the audit has not classified.

audit_coverage only reports leaks at call sites it knows are user-visible, so
an unrecognised setter is invisible forever -- that is exactly how
QMessageBox.warning(parent, "Title", "Body") slipped past the old scanner.
This enumerates every call that receives a prose string and is *not* already a
known sink, a known-benign property, or inside a translate call, so the sink
list cannot silently rot as the GUI code grows.

    python tools/i18n/enumerate_sinks.py            # unclassified, by method
    python tools/i18n/enumerate_sinks.py --show-known
"""
from __future__ import annotations

import argparse
import ast
import sys
from collections import Counter, defaultdict
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
sys.stdout.reconfigure(encoding='utf-8', errors='replace')

import audit_coverage as ac

# Calls that take a string but never render it: object names for stylesheet
# selectors, settings keys the user types back in, file/URL paths, signals.
BENIGN_CALLS = {
    'setObjectName', 'setProperty', 'objectName', 'setStyleSheet', 'style',
    'setAccessibleName', 'setAccessibleDescription', 'setFactoryId',
    'setBindingContext', 'setContextMenuPolicy', 'setFilePattern',
    'setNameFilter', 'addNameFilter', 'setDirectory', 'setFileName',
    'setDefaultSuffix', 'setFormat', 'setMimeTypeFilter', 'setFilter',
    'findChild', 'findChildren', 'inherits', 'registerHandler', 'deregisterHandler',
    'connect', 'disconnect', 'emit', 'slot', 'Signal', 'Slot', 'pyqtSignal',
    'getattr', 'setattr', 'hasattr', 'delattr', 'dict', 'get', 'set', 'pop',
    'startswith', 'endswith', 'split', 'join', 'replace', 'format', 'strip',
    'lstrip', 'rstrip', 'encode', 'decode', 'addCallback', 'removeCallback',
    'open', 'write', 'remove', 'mkdir', 'path', 'join', 'exists', 'isfile',
    'isdir', 'expanduser', 'abspath', 'realpath', 'dirname', 'basename',
    'splitext', 'normpath', 'walk', 'glob', 'iglob', 'copy', 'copyfile',
    'which', 'run', 'Popen', 'check_output', 'call', 'getenv', 'environ',
    'setenv', 'addStep', 'setName', 'setKey', 'setValue', 'setTag',
    'setIdentifier', 'setPluginName', 'setPrefix', 'setSuffix',
    'setSettingName', 'setCallback', 'setUserRole', 'setDataRole',
    'setStartAction', 'setStopAction', 'setHelpTopic', 'setHelp',
    'setWhatsThis',  # handled as a sink below; kept out only if unused
}
BENIGN_CALLS.discard('setWhatsThis')

# Prefixes that mean "this is a Qt/PyMOL setter on some object we do not model".
IGNORE_PREFIXES = ('cmd.', '_self.', 'self.cmd.')


def main(argv):
    ap = argparse.ArgumentParser()
    ap.add_argument('--show-known', action='store_true',
                    help='also count the already-classified sinks')
    args = ap.parse_args(argv)

    files = set()
    for g in ac.SOURCE_GLOBS:
        files.update(ac.ROOT.glob(g))

    unknown = Counter()
    samples = defaultdict(list)
    known = Counter()

    for path in sorted(p for p in files if p.is_file()):
        rel = path.relative_to(ac.ROOT).as_posix()
        try:
            tree = ast.parse(path.read_text(encoding='utf-8', errors='replace'))
        except SyntaxError:
            continue

        class V(ast.NodeVisitor):
            def __init__(self):
                self.in_tr = 0

            def visit_Call(self, n):
                is_tr, _ = ac._is_tr_call(n)
                name = ac._func_name(n.func)
                short = name.split('.')[-1]
                if is_tr:
                    self.in_tr += 1
                    self.generic_visit(n)
                    self.in_tr -= 1
                    return
                prose = [a.value for a in n.args
                         if isinstance(a, ast.Constant)
                         and isinstance(a.value, str) and ac._prose(a.value)]
                if prose and self.in_tr == 0:
                    if short in ac.SINK_METHODS or any(
                            p in ac.SINK_CLASSES for p in name.split('.')):
                        known[short] += len(prose)
                    elif (short not in BENIGN_CALLS
                          and short not in ac.USER_RAISES
                          and not name.startswith(IGNORE_PREFIXES)
                          and short not in ('ctr', 'print', 'print_msg')):
                        unknown[short] += len(prose)
                        if len(samples[short]) < 3:
                            samples[short].append(
                                (rel, n.lineno, prose[0][:64]))
                self.generic_visit(n)

        V().visit(tree)

    if args.show_known:
        print('--- already classified (covered by the audit) ---')
        for k, v in known.most_common():
            print(f'  {v:5d}  {k}')
        print()

    if not unknown:
        print('OK: every prose string literal reaches a known sink or a '
              'translate call')
        return 0

    print(f'--- {len(unknown)} UNCLASSIFIED method(s) taking prose strings ---')
    for k, v in unknown.most_common():
        print(f'  {v:5d}  {k}')
        for rel, ln, s in samples[k]:
            print(f'          {rel}:{ln}  {s!r}')
    print('\nClassify each: add to SINK_METHODS (user-visible), '
          'BENIGN_CALLS (never rendered), or wrap the call site in _tr().')
    return 1


if __name__ == '__main__':
    raise SystemExit(main(sys.argv[1:]))
