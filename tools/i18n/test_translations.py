"""
Runtime verification: load all .qm files for a given language and test
that key strings translate correctly.
"""
from __future__ import annotations

import os
import sys
from pathlib import Path


def main(argv: list[str]) -> int:
    lang = 'zh_CN'
    if len(argv) > 1:
        lang = argv[1]

    # Find translations dir
    root = Path(__file__).resolve().parents[2]
    tdir = root / 'data' / 'pmg_qt' / 'i18n' / lang
    if not tdir.is_dir():
        print(f'No translations dir: {tdir}')
        return 1

    # Set env so i18n.py picks zh_CN
    os.environ['PYMOL_LANG'] = lang

    # Import Qt
    try:
        from PySide6 import QtCore
    except ImportError:
        print('PySide6 not available')
        return 2

    app = QtCore.QCoreApplication([])

    # Load all .qm files in the language directory
    loaded = 0
    translators = []
    for qm in sorted(tdir.glob('*.qm')):
        t = QtCore.QTranslator()
        if t.load(str(qm)):
            app.installTranslator(t)
            translators.append(t)
            loaded += 1
    print(f'Loaded {loaded} .qm translators from {tdir}')

    # Test translations from various contexts
    tests = [
        ('PyMOLQtGUI', 'About PyMOL', '关于 PyMOL'),
        ('PyMOLQtGUI', 'Reset', '重置'),
        ('PyMOLQtGUI', 'Zoom', '缩放'),
        ('Builder', 'Alpha Helix', 'α 螺旋'),
        ('Builder', 'Protein', '蛋白质'),
        ('ScenePanel', 'Add Scene', '添加场景'),
        ('ShortcutMenu', 'Keyboard Shortcut Menu', '键盘快捷键菜单'),
        ('TextEditor', 'Text Editor', '文本编辑器'),
        ('PropertiesDialog', 'Settings', '设置'),
        ('Volume', 'Help', '帮助'),
        ('AdvancedSettings', 'Filter', '筛选'),
        ('FileDialogs', 'Error', '错误'),
        ('PluginManager', 'Plugin Information', '插件信息'),
        ('PluginInstallation', 'Success', '成功'),
        ('PluginRepository', 'Downloading', '正在下载'),
        # UI form contexts
        ('Form', 'Plugin Manager', '插件管理器'),
        ('Form', 'Cancel', '取消'),
        ('Form', 'Apply', '应用'),
        ('Form', 'Save Molecule', '保存分子'),
        ('Form', 'APBS Electrostatics', 'APBS 静电学'),
        ('Dialog', 'Shortcut Help', '快捷键帮助'),
        ('Dialog', 'Create Shortcut', '创建快捷键'),
        ('Dialog', 'Show All', '显示全部'),
        ('Dialog', 'Load Session', '加载会话'),
        ('Menu', 'Edit', '编辑'),
    ]

    print('\n=== Translation Tests ===')
    passed = 0
    failed = 0
    for ctx, source, expected in tests:
        actual = QtCore.QCoreApplication.translate(ctx, source)
        ok = (actual == expected)
        mark = 'OK' if ok else 'FAIL'
        if ok:
            passed += 1
        else:
            failed += 1
        print(f'  [{mark}] {ctx}.{source!r}')
        if not ok:
            print(f'        expected: {expected!r}')
            print(f'        actual:   {actual!r}')

    print(f'\n{passed}/{passed+failed} translations OK')
    return 0 if failed == 0 else 3


if __name__ == '__main__':
    raise SystemExit(main(sys.argv[1:]))
