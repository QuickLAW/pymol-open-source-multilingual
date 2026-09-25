"""Regenerate data/fonts/NotoSansSC-PyMOL.otf from a full Noto Sans CJK SC font.

Coverage target is GBK + Big5 (cp950), enumerated through Python's own codecs,
so both shipped locales (zh_CN and zh_TW) can render user-typed text -- residue
names, labels, selections -- not just strings this fork already translates.
That is essentially the whole set Noto Sans SC actually contains, so there is no
meaningfully larger tier to chase.

Layout tables and hinting are dropped: PyMOL draws plain runs with no shaping
requests, and the Latin glyphs users see come from DejaVu via the fallback in
Text.cpp, so this font's Latin metrics and hinting do not affect the UI. That
trade takes the subset from 10.65 MiB to ~4.8 MiB at identical coverage.

    python tools/i18n/make_font_subset.py --src /path/NotoSansCJKsc-Regular.otf
    python tools/i18n/gen_fontttf3.py            # re-embed into layer1/FontTTF3.h
"""

import argparse
import os
import sys

from fontTools import subset

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.dirname(os.path.dirname(HERE))
OUT = os.path.join(REPO, "data", "fonts", "NotoSansSC-PyMOL.otf")

# Codepoint ranges the UI needs regardless of locale: Latin, general
# punctuation, fullwidth forms, CJK punctuation.
BASE = (
    range(0x20, 0x180),
    range(0x2000, 0x2100),
    range(0x3000, 0x3030),
    range(0xFF00, 0xFFF0),
)


def codec_chars(encoding):
    """Every codepoint reachable as a 2-byte sequence of `encoding`."""
    chars = set()
    for hi in range(0x81, 0xFF):
        for lo in range(0x40, 0xFF):
            if lo == 0x7F:
                continue
            try:
                chars.update(bytes([hi, lo]).decode(encoding))
            except (UnicodeDecodeError, LookupError):
                continue
    return {ord(c) for c in chars if ord(c) > 127}


def catalogue_chars():
    """Non-ASCII characters this fork's catalogues can actually emit."""
    import glob
    import re

    out = set()
    for path in glob.glob(os.path.join(REPO, "data/pmg_qt/i18n/zh_*/*.ts")):
        text = open(path, encoding="utf-8").read()
        for m in re.finditer(r"<translation[^>]*>(.*?)</translation>", text, re.S):
            s = re.sub(r"&[a-z]+;|&#\d+;", "", m.group(1))
            out.update(ord(c) for c in s if ord(c) > 127)
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--src", required=True, help="path to NotoSansCJKsc-Regular.otf")
    ap.add_argument("--profile", default="full",
                    choices=["full", "nolayout", "nohint", "lean"],
                    help="how aggressively to strip tables; see the size notes above")
    args = ap.parse_args()

    cps = set()
    for r in BASE:
        cps.update(r)
    cps |= codec_chars("gbk")
    cps |= codec_chars("cp950")
    our_own = catalogue_chars()
    cps |= our_own
    cps.discard(0xFFFD)

    opts = subset.Options()
    opts.name_IDs = ["family", "version", "license", "license-url", "copyright"]
    opts.drop_tables += ["DSIG"]
    opts.notdef_outline = True
    if args.profile in ("nolayout", "lean"):
        opts.layout_features = []
    if args.profile in ("nohint", "lean"):
        opts.hinting = False

    font = subset.load_font(args.src, opts)
    before = len(font.getBestCmap())
    sub = subset.Subsetter(options=opts)
    sub.populate(unicodes=sorted(cps))
    sub.subset(font)

    os.makedirs(os.path.dirname(OUT), exist_ok=True)
    subset.save_font(font, OUT, opts)

    got = font.getBestCmap()
    print(f"source glyphs: {before}")
    print(f"requested cps: {len(cps)} (our own catalogues contribute {len(our_own)})")
    print(f"subset glyphs: {len(got)}")
    print(f"size: {os.path.getsize(OUT) / 1048576:.2f} MiB -> {OUT}")

    # Positive controls: a character from each locale plus one that only the
    # catalogue path could have pulled in.
    missing = [hex(c) for c in (0x4E2D, 0x663E, 0x7F6E, 0x908A, 0x7D22) if c not in got]
    if missing:
        print(f"FAILED positive controls: {missing}")
        return 1
    if 0x41 in got:
        print("note: Latin present but served by DejaVu via the fallback")
    print("controls OK")
    return 0


if __name__ == "__main__":
    sys.exit(main())
