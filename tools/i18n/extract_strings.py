"""
Extract translatable strings from Python source files.

Scans for _tr('Context', 'text') and _mtr('text') calls and groups
strings by context. Outputs a JSON-like summary that can be used to
generate or update .ts files manually.
"""
from __future__ import annotations

import re
import sys
from pathlib import Path


# Match _tr('Context', 'text') or _tr("Context", "text")
# Handles single, double, and triple-quoted strings, with possible
# string concatenation like 'foo' 'bar'.
_TR_CALL_RE = re.compile(
    r"_tr\s*\(\s*"
    r"(['\"])(?P<context>[^'\"]+)\1\s*,\s*"
    r"(?P<text>(?:'''[\s\S]*?'''|\"\"\"[\s\S]*?\"\"\"|'(?:[^'\\]|\\.)*'|\"(?:[^\"\\]|\\.)*\"))"
    r"(?:\s*\)?\s*%)?",
    re.MULTILINE,
)

# Match _mtr('text')
_MTR_CALL_RE = re.compile(
    r"_mtr\s*\(\s*"
    r"(?P<text>(?:'''[\s\S]*?'''|\"\"\"[\s\S]*?\"\"\"|'(?:[^'\\]|\\.)*'|\"(?:[^\"\\]|\\.)*\"))",
    re.MULTILINE,
)


def _unescape(s: str) -> str:
    """Decode Python string escapes for display."""
    try:
        return bytes(s, 'utf-8').decode('unicode_escape')
    except Exception:
        return s


def _strip_quotes(s: str) -> str:
    s = s.strip()
    if not s:
        return s
    if s[0] in '"\'':
        q = s[0]
        # triple-quoted
        if s.startswith(q * 3):
            return s[3:-3]
        return s[1:-1]
    return s


def scan_file(path: Path) -> dict[str, set[str]]:
    """Return {context: set(source_text)} from one file."""
    content = path.read_text(encoding='utf-8', errors='replace')
    out: dict[str, set[str]] = {}

    for m in _TR_CALL_RE.finditer(content):
        ctx = m.group('context')
        raw = m.group('text')
        text = _unescape(_strip_quotes(raw))
        if text:
            out.setdefault(ctx, set()).add(text)

    # _mtr implies context "Menu"
    menu_texts = out.setdefault('Menu', set())
    for m in _MTR_CALL_RE.finditer(content):
        raw = m.group('text')
        text = _unescape(_strip_quotes(raw))
        if text:
            menu_texts.add(text)

    return out


def main() -> int:
    root = Path(__file__).resolve().parents[2]
    sources = []
    for pattern in [
        "modules/pmg_qt/**/*.py",
        "modules/pymol/Qt/**/*.py",
        "modules/pymol/_gui.py",
        "modules/pymol/plugins/**/*.py",
        "modules/pmg_qt/forms/**/*.ui",
    ]:
        sources.extend(root.glob(pattern))
    sources = sorted(set(p for p in sources if p.is_file()))

    contexts: dict[str, dict[str, list[str]]] = {}
    for path in sources:
        for ctx, texts in scan_file(path).items():
            rel = path.relative_to(root).as_posix()
            contexts.setdefault(ctx, {})
            for text in sorted(texts):
                contexts[ctx].setdefault(text, []).append(rel)

    for ctx in sorted(contexts):
        print(f"\n=== Context: {ctx} ({len(contexts[ctx])} strings) ===")
        for text in sorted(contexts[ctx]):
            files = contexts[ctx][text]
            print(f"  [{','.join(files)}]")
            print(f"    {text!r}")

    print(f"\nTotal: {sum(len(v) for v in contexts.values())} strings "
          f"in {len(contexts)} contexts")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
