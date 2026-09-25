"""Regenerate layer1/FontTTF3.h from data/fonts/NotoSansSC-PyMOL.otf.

Same shape as the FontTTF.h generator whose snippet is preserved in that file's
header comment: a header-only `static unsigned char TTF_<name>_dat[]`, included
by exactly one translation unit (Text.cpp). Chosen over build-time codegen
because setup.py keeps a duplicated copy of create_shadertext for PEP-517 build
isolation, and touching that pairing is a bigger risk than one more large
generated header.

The subset itself is produced by make_font_subset.py, which derives the
codepoint set from this fork's own translation catalogues.
"""

import os
import sys

REPO = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
FONT = os.path.join(REPO, "data", "fonts", "NotoSansSC-PyMOL.otf")
LICENSE = os.path.join(REPO, "data", "fonts", "OFL-NotoSansSC.txt")
OUT = os.path.join(REPO, "layer1", "FontTTF3.h")

BANNER = """/*
 * GENERATED FILE -- DO NOT EDIT
 * Regenerate with:
 *   python tools/i18n/gen_fontttf3.py
 *
 * Contains a subset of Noto Sans SC (SIL Open Font License 1.1) covering every
 * character this fork's zh_CN/zh_TW catalogues can emit, so the in-viewport
 * overlay text (mouse mode, selection feedback, frame counter) can render CJK.
 * The upstream bitmap font used for that text is codepoint-limited to 0-255
 * and substitutes '?' for anything above it.
 *
 * ---- License of the embedded font ----
"""


def main():
    data = open(FONT, "rb").read()
    lic = open(LICENSE, encoding="utf-8").read()

    chunks = []
    per_line = 20
    for i in range(0, len(data), per_line):
        row = data[i : i + per_line]
        chunks.append(",".join(str(b) for b in row))
    body = ",\n".join(chunks)

    text = (
        BANNER
        + "".join(
            " * " + ln.rstrip().replace("*/", "* /") + "\n"
            for ln in lic.splitlines()
        )
        + " */\n\n"
        + "static unsigned int TTF_NotoSansSC_len = %d;\n" % len(data)
        + "static unsigned char TTF_NotoSansSC_dat[] = {\n"
        + body
        + "\n};\n"
    )

    old = open(OUT, encoding="utf-8").read() if os.path.exists(OUT) else None
    if old == text:
        print(f"unchanged: {OUT}")
        return 0
    with open(OUT, "w", encoding="utf-8", newline="\n") as f:
        f.write(text)
    print(f"wrote {OUT}: {len(data)} bytes of font data")
    return 0


if __name__ == "__main__":
    sys.exit(main())
