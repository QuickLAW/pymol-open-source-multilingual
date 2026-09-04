"""Minimal verification: load .qm files and print actual translated values.

IMPORTANT: Keep references to QTranslator objects, otherwise Python's GC
will destroy them and remove them from the translator chain.
"""
import os
os.environ['PYMOL_LANG'] = 'zh_CN'
from PySide6 import QtCore
from pathlib import Path

app = QtCore.QCoreApplication([])
tdir = (Path(__file__).resolve().parents[2]
        / 'data' / 'pmg_qt' / 'i18n' / 'zh_CN')

# Keep references! Otherwise QTranslator objects get GC'd and removed from
# the translator chain.
translators = []
for qm in sorted(tdir.glob('*.qm')):
    t = QtCore.QTranslator()
    if t.load(str(qm)):
        app.installTranslator(t)
        translators.append(t)  # KEEP REFERENCE
print(f'Loaded: {len(translators)} translators')

samples = [
    ('PyMOLQtGUI', 'About PyMOL'),
    ('PyMOLQtGUI', 'Reset'),
    ('PyMOLQtGUI', 'Zoom'),
    ('Builder', 'Builder'),
    ('Builder', 'Protein'),
    ('ScenePanel', 'Add Scene'),
    ('ShortcutMenu', 'Keyboard Shortcut Menu'),
    ('TextEditor', 'Text Editor'),
    ('PropertiesDialog', 'Settings'),
    ('Volume', 'Volume Color Map Editor'),
    ('AdvancedSettings', 'Filter'),
    ('FileDialogs', 'Error'),
    ('PluginManager', 'Plugin Information'),
    ('PluginInstallation', 'Success'),
    ('PluginRepository', 'Downloading'),
    ('Form', 'Plugin Manager'),
    ('Form', 'Cancel'),
    ('Form', 'Save Molecule'),
    ('Form', 'APBS Electrostatics'),
    ('Dialog', 'Shortcut Help'),
    ('Dialog', 'Create Shortcut'),
    ('Dialog', 'Load Session'),
    ('Menu', 'Edit'),
]

print()
print('Direct QCoreApplication.translate() results:')
ok = 0
for ctx, s in samples:
    trans = QtCore.QCoreApplication.translate(ctx, s)
    expected_zh = {
        'PyMOLQtGUI': {'About PyMOL':'关于 PyMOL','Reset':'重置','Zoom':'缩放'},
        'Builder': {'Builder':'构建器','Protein':'蛋白质'},
        'ScenePanel': {'Add Scene':'添加场景'},
        'ShortcutMenu': {'Keyboard Shortcut Menu':'键盘快捷键菜单'},
        'TextEditor': {'Text Editor':'文本编辑器'},
        'PropertiesDialog': {'Settings':'设置'},
        'Volume': {'Volume Color Map Editor':'体积颜色映射编辑器'},
        'AdvancedSettings': {'Filter':'筛选'},
        'FileDialogs': {'Error':'错误'},
        'PluginManager': {'Plugin Information':'插件信息'},
        'PluginInstallation': {'Success':'成功'},
        'PluginRepository': {'Downloading':'正在下载'},
        'Form': {'Plugin Manager':'插件管理器','Cancel':'取消','Save Molecule':'保存分子','APBS Electrostatics':'APBS 静电学'},
        'Dialog': {'Shortcut Help':'快捷键帮助','Create Shortcut':'创建快捷键','Load Session':'加载会话'},
        'Menu': {'Edit':'编辑'},
    }
    expected = expected_zh.get(ctx, {}).get(s, '')
    match = '✓' if trans == expected else ('?' if trans == s else 'X')
    if trans == expected:
        ok += 1
    print(f'  {match} [{ctx:18s}] {s!r:42s} -> {trans!r}')

print(f'\n{ok}/{len(samples)} translations verified')
