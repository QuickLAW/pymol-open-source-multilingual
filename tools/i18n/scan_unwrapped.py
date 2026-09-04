"""Scan for user-visible Qt calls with literal string args not wrapped in _tr().

Reports strings that would show up untranslated in the GUI. Temporary
noise (format templates, macOS hacks, numeric formats) must be
reviewed manually.
""".
import re
import glob

pat = re.compile(
    r"(?:QMessageBox[.\w]*\(|\.setText\(|\.setWindowTitle\(|"
    r"\.setToolTip\(|\.setStatusTip\(|\.setPlaceholderText\(|"
    r"\.setTitle\(|\.addItem\(|\.setMessage\(|\.addAction\()"
)
tr_pat = re.compile(r"_tr\s*\(")
lit_pat = re.compile(r"""\s*(f?['"](?:[^'"\\]|\\.)*['"])""")

files = []
files += glob.glob('modules/pmg_qt/**/*.py', recursive=True)
files += glob.glob('modules/pymol/Qt/**/*.py', recursive=True)
files += glob.glob('modules/pymol/plugins/**/*.py', recursive=True)
files += glob.glob('data/startup/**/*.py', recursive=True)

total = 0
for f in sorted(files):
    src = open(f, encoding='utf-8', errors='replace').read()
    for m in pat.finditer(src):
        tail = src[m.end():m.end() + 200]
        lm = lit_pat.match(tail)
        if not lm:
            continue
        s = lm.group(1)
        if len(s) <= 3:
            continue
        pre = src[max(0, m.start() - 80):m.start()]
        if tr_pat.search(pre):
            continue
        ln = src[:m.start()].count('\n') + 1
        total += 1
        print(f"{f}:{ln}: {s[:70]!r}")
print(f"=== {total} potentially unwrapped user-visible literals ===")
