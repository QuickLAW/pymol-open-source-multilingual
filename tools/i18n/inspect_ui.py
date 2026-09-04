"""
Inspect all .ui form files and extract user-visible strings with their
owning widget class (which becomes the Qt translation context).

Output: human-readable report of all strings grouped by class.
"""
from __future__ import annotations

import sys
from pathlib import Path
from xml.etree import ElementTree as ET


# Properties whose <string> values are user-visible
TRANSLATABLE_PROPS = {
    'windowTitle',
    'title',
    'text',
    'label',
    'toolTip',
    'whatsThis',
    'statusTip',
    'placeholderText',
    'toolButtonText',
    'html',
    'plainText',
    'caption',
    'shortcut',
}

# Attributes that hold translatable strings in <string> elements are not used
# for our purposes; we only care about the element text.


def _root() -> Path:
    return Path(__file__).resolve().parents[2]


def find_ui_files(root: Path) -> list[Path]:
    files = []
    files.extend((root / 'modules' / 'pmg_qt' / 'forms').glob('*.ui'))
    apbs_dir = root / 'data' / 'startup' / 'apbs_gui'
    if apbs_dir.exists():
        files.extend(apbs_dir.glob('*.ui'))
    # also any other .ui files
    files.extend(p for p in root.rglob('*.ui')
                 if p not in files
                 and 'build' not in p.parts
                 and 'install' not in p.parts)
    return sorted(set(files))


def parse_ui(path: Path) -> tuple[str, list[tuple[str, str]]]:
    """
    Returns (class_name, [(prop_name, string_value), ...])
    class_name comes from the root <class>...</class> element if present,
    else the root widget's name attribute.
    """
    tree = ET.parse(path)
    root = tree.getroot()

    # <class>...</class> is the form's class name used by pyside6-uic
    class_el = root.find('class')
    class_name = (class_el.text or '').strip() if class_el is not None else ''
    if not class_name:
        # fallback: root widget name
        widget_el = root.find('widget')
        if widget_el is not None:
            class_name = widget_el.get('name', '')
        if not class_name:
            class_name = path.stem

    strings: list[tuple[str, str]] = []
    # find all <property name="X"><string>Y</string></property>
    for prop in root.iter('property'):
        pname = prop.get('name', '')
        if pname not in TRANSLATABLE_PROPS:
            continue
        # string child
        s = prop.find('string')
        if s is None:
            continue
        # attribute 'translatable' defaults to "true" — only skip if "false"
        if s.get('translatable', 'true') == 'false':
            continue
        text = s.text or ''
        if text.strip():
            strings.append((pname, text))

    # Also collect <string> elements inside <item> (for list/combo widgets)
    for item in root.iter('item'):
        for prop in item.findall('property'):
            pname = prop.get('name', '')
            if pname not in TRANSLATABLE_PROPS:
                continue
            s = prop.find('string')
            if s is None:
                continue
            if s.get('translatable', 'true') == 'false':
                continue
            text = s.text or ''
            if text.strip():
                strings.append((pname, text))

    # Also collect <action><property>...</property></action> strings
    for action in root.iter('action'):
        for prop in action.findall('property'):
            pname = prop.get('name', '')
            if pname not in TRANSLATABLE_PROPS:
                continue
            s = prop.find('string')
            if s is None:
                continue
            if s.get('translatable', 'true') == 'false':
                continue
            text = s.text or ''
            if text.strip():
                strings.append((pname, text))

    return class_name, strings


def main(argv: list[str]) -> int:
    root = _root()
    ui_files = find_ui_files(root)
    if not ui_files:
        print('No .ui files found')
        return 1

    by_class: dict[str, dict[str, str]] = {}
    file_to_class: dict[str, str] = {}
    for p in ui_files:
        class_name, strings = parse_ui(p)
        file_to_class[str(p.relative_to(root))] = class_name
        mapping = by_class.setdefault(class_name, {})
        for prop, text in strings:
            # dedupe: keep first occurrence
            if text not in mapping:
                mapping[text] = prop

    print(f'=== {len(ui_files)} .ui files, {len(by_class)} unique classes ===\n')
    for path, cls in sorted(file_to_class.items()):
        print(f'  {path}  ->  class: {cls}')

    print(f'\n=== Strings by class ({sum(len(v) for v in by_class.values())} unique) ===\n')
    for class_name in sorted(by_class):
        mapping = by_class[class_name]
        print(f'--- class: {class_name} ({len(mapping)} strings) ---')
        for text, prop in sorted(mapping.items()):
            preview = text if len(text) <= 80 else text[:77] + '...'
            preview = preview.replace('\n', '\\n')
            print(f'  [{preview}] (prop: {prop})')
        print()

    return 0


if __name__ == '__main__':
    raise SystemExit(main(sys.argv[1:]))
