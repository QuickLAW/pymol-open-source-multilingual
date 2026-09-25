"""Translate text that PyMOL writes to its output window.

The command layer lives below the Qt frontend and must keep working with no
Qt installed at all (``pymol -cq``, the C++ test suite, embedded scripts), so
every lookup here degrades to returning the English source.

Only the import is cached, never the result: a translator can be installed
after the first message is printed, and caching an early "no application yet"
answer would freeze every later message in English.
"""
from __future__ import annotations

_UNRESOLVED = object()
_QtCore: object = _UNRESOLVED

# Single context so all output-window text lands in one catalogue file.
CONTEXT = 'Console'


def _resolve():
    global _QtCore
    if _QtCore is _UNRESOLVED:
        try:
            from pymol.Qt import QtCore
            _QtCore = QtCore
        except Exception:
            # No Qt binding (headless build) -- stay English forever after.
            _QtCore = None
    return _QtCore


def ctr(text: str, context: str = CONTEXT) -> str:
    """Return *text* translated for the output window."""
    if not text:
        return text
    QtCore = _resolve()
    if QtCore is None:
        return text
    if QtCore.QCoreApplication.instance() is None:
        # Nothing could have installed a translator yet.
        return text
    try:
        out = QtCore.QCoreApplication.translate(context, text)
    except Exception:
        return text
    return out or text
