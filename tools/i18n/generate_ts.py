"""
Generate or update .ts (Qt Translation Source) files for PyMOL.

This script:
- Generates new .ts files for contexts that don't yet have one
- Updates existing .ts files by merging in any new source strings
  (existing translations are preserved; new strings get the provided
  translation)

Translations are encoded inline as a dict: {context: {source: translation}}.
Strings without an inline translation are added with <translation type="unfinished"/>
so a human can fill them in later.

Usage:
    python tools/i18n/generate_ts.py
    python tools/i18n/generate_ts.py --lang zh_CN
"""
from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path
from xml.etree import ElementTree as ET


# ---------------------------------------------------------------------------
# Translation table (English -> Chinese)
# Only zh_CN is provided here. Add new languages by extending this dict.
# ---------------------------------------------------------------------------
TRANSLATIONS: dict[str, dict[str, str]] = {
    "zh_CN": {
        # ---- AdvancedSettings ----
        "Filter": "筛选",
        "PyMOL Advanced Settings": "PyMOL 高级设置",

        # ---- Builder ----
        "\n\n": "\n\n",
        "Alpha Helix": "α 螺旋",
        "Beta Sheet (Anti-Parallel)": "β 折叠（反平行）",
        "Beta Sheet (Parallel)": "β 折叠（平行）",
        "Build %s residue": "构建 %s 残基",
        "Builder": "构建器",
        'Building "Undo" is disabled for the following objects:': '以下对象未启用 "撤销" 功能：',
        "Chemical": "化学",
        "Confirm": "确认",
        "DNA": "DNA",
        "Enable for objects?": "为这些对象启用？",
        "Error: can only clean one object at a time": "错误：一次只能清理一个对象",
        "Error: cannot sculpt more than one object at a time": "错误：一次只能雕刻一个对象",
        "Hint: Also check out ": "提示：也可以查看 ",
        "Nucleic Acid": "核酸",
        "Protein": "蛋白质",
        "RNA": "RNA",
        "Really delete everything?": "确定要删除所有内容吗？",
        "Secondary Structure:": "二级结构：",
        "Select a single atom on the residue and press remove again": "请在残基上选择单个原子，然后再次按下移除",

        # ---- FileDialogs ----
        "Encoder '%s' is not installed.": "未安装编码器 '%s'。",
        "Error": "错误",
        "Load as structures?": "加载为结构？",
        "Load sequences as extended structures instead?": "改为以扩展结构方式加载序列？",
        "Need 4 letter PDB code": "需要 4 字符的 PDB 代码",
        "No alignment objects loaded": "未加载比对对象",
        "No map objects loaded": "未加载电子密度图对象",
        'No alignment objects loaded\n\nHint: create alignment objects with "align" and\n"super" using the "object=..." argument.':
            "未加载比对对象\n\n提示：使用 \"align\" 和 \"super\" 命令的 \"object=...\" 参数创建比对对象。",
        "Save ": "保存 ",
        "Save As...": "另存为...",
        "Save Molecule As...": "保存分子为...",
        "To load a trajectory, you first need to load a molecular object":
            "要加载轨迹，请先加载一个分子对象",
        "Warning": "警告",
        "_get_assemblies failed": "_get_assemblies 失败",
        "_get_chains failed": "_get_chains 失败",

        # ---- Menu (additional) ----
        "Edit": "编辑",
        # Labels in _gui.py get_menudata() tuples (item[1]) that the literal
        # _tr/_mtr regex cannot see; routed to their menu file via MENU_SPLIT.
        "Camera": "相机",
        "Default (Atomic)": "默认（按原子）",
        "Gray": "灰色",
        "Ignore .pymolrc and plugins (-k)": "忽略 .pymolrc 和插件 (-k)",
        "Light Gray": "浅灰色",
        "Reps": "表示方式",
        "Reps + Color": "表示方式 + 颜色",
        "Sphere": "球体",
        "Stick": "棍状",
        "1 Cycle per Update": "每次更新 1 次循环",
        # Mouse mode names (controlling.py mode_name_dict values, rendered
        # via _mtr in the viewport status line and Mouse menu)
        "2-Btn. Selecting": "双键选择模式",
        "3-Button Maestro": "三键 Maestro 模式",

        # ---- Qt utils (modules/pymol/Qt/utils.py font context menu) ----
        "Select Font...": "选择字体...",
        "Select Font": "选择字体",

        # ---- PluginInstallation ----
        " Warning: Version parsing failed for": " 警告：版本解析失败：",
        "and/or": "和/或",
        "A newer version (%s) of this plugin is already installed. Install anyway?":
            "已安装此插件的更新版本 (%s)。仍然安装？",
        "An older version (%s) of this plugin is already installed. Install version %s now?":
            "已安装此插件的旧版本 (%s)。现在安装版本 %s 吗？",
        "Citation Required": "需要引用",
        "Could not create user plugin directory": "无法创建用户插件目录",
        'Directory "%s" already exists, overwrite?': "目录 \"%s\" 已存在，是否覆盖？",
        'File "%s" already exists, overwrite?': "文件 \"%s\" 已存在，是否覆盖？",
        "In which directory should the plugin be installed?": "插件应安装到哪个目录？",
        "Info": "信息",
        "Installation aborted": "安装已中止",
        "Installation cancelled": "安装已取消",
        'Plugin "%s" has been installed but initialization failed.': "插件 \"%s\" 已安装，但初始化失败。",
        'Plugin "%s" has been installed.': "插件 \"%s\" 已安装。",
        "Plugin already installed. Reinstall?": "插件已安装。重新安装？",
        "Select plugin directory": "选择插件目录",
        "Success": "成功",
        "This plugin requires citation. Show information now?": "此插件需要引用。立即显示信息？",
        'Unable to install plugin "{}".\n{}': "无法安装插件 \"{}\"。\n{}",
        "Unable to write to the plugin directory.\n": "无法写入插件目录。\n",

        # ---- PluginManager ----
        " Error: set_startup_path failed": " 错误：set_startup_path 失败",
        ' Plugin "%s" loaded in %.2f seconds': " 插件 \"%s\" 在 %.2f 秒内加载完成",
        " Plugin settings saved!": " 插件设置已保存！",
        " Plugin-Error: Cannot write Plugins resource file to": " 插件错误：无法将插件资源文件写入",
        " Scanning for modules took %.4f seconds": " 扫描模块耗时 %.4f 秒",
        " info: plugin already loaded": " 信息：插件已加载",
        " warning: multiple plugins named": " 警告：多个插件同名",
        "Add plugin directory": "添加插件目录",
        "Add repository": "添加仓库",
        'Could not delete files for plugin "%s".': "无法删除插件 \"%s\" 的文件。",
        "Could not get plugin info": "无法获取插件信息",
        "Could not install plugin ": "无法安装插件 ",
        'Do you really want to uninstall plugin "%s"': "确定要卸载插件 \"%s\" 吗",
        "Enter repository URL": "输入仓库 URL",
        "Fetching Plugin failed.\n": "获取插件失败。\n",
        "Filename": "文件名",
        "Network download has been disabled, sorry!": "抱歉，网络下载已被禁用！",
        "No documentation available.": "暂无文档。",
        "Not loaded": "未加载",
        "Please install XQuartz (https://www.xquartz.org/)": "请安装 XQuartz (https://www.xquartz.org/)",
        'Plugin "%s" successfully removed. Please restart PyMOL.': "插件 \"%s\" 已成功移除。请重启 PyMOL。",
        "Plugin '%s' only available with PyQt GUI.": "插件 '%s' 仅在 PyQt 图形界面下可用。",
        "Plugin Information": "插件信息",
        "PyMOL will now download executable code from the internet! Proceed?":
            "PyMOL 即将从互联网下载可执行代码！是否继续？",
        "Python Module Name": "Python 模块名",
        "Took %.3f seconds to load": "加载耗时 %.3f 秒",
        "Unable to initialize plugin '%s' (%s).": "无法初始化插件 '%s' (%s)。",
        "WARNING: Plugin not Python 3.x compatible: ": "警告：插件不兼容 Python 3.x：",
        "commands": "命令",
        "Name": "名称",

        # ---- PluginRepository ----
        "Downloading": "正在下载",
        'File "%s" exists, will not redownload': "文件 \"%s\" 已存在，将不会重新下载",
        "Warning: %d chunks found, only saving first": "警告：发现 %d 个数据块，仅保存第一个",
        "Warning: Infobox filename found, but download failed": "警告：找到 Infobox 文件名，但下载失败",

        # ---- PropertiesDialog ----
        "Atom-Level": "原子级",
        "Atom-State-Level": "原子-状态级",
        "Identifiers": "标识符",
        "Object-Level": "对象级",
        "Object-State-Level": "对象-状态级",
        "Properties (built-in)": "属性（内置）",
        "Settings": "设置",
        "State Matrix": "状态矩阵",
        "TTT Matrix": "TTT 矩阵",
        "Title": "标题",

        # ---- PyMOLQtGUI ----
        " Image copied to clipboard": " 图像已复制到剪贴板",
        " get_view: matrix copied to clipboard.": " get_view：矩阵已复制到剪贴板。",
        "<": "<",
        ">": ">",
        ">|": ">|",
        "Abort": "中止",
        "About PyMOL": "关于 PyMOL",
        "All rights reserved.\n": "保留所有权利。\n",
        "Builder": "构建器",
        "Change Working Directory": "更改工作目录",
        "Command Input Area\n\nGet the list of commands by hitting <TAB>\n\nGet the list of arguments for one command with a question mark:\nPyMOL> color ?\n\nRead the online help for a command with \"help\":\nPyMOL> help color\n\nGet autocompletion for many arguments by hitting <TAB>\nPyMOL> color ye<TAB>    (will autocomplete \"yellow\")\n":
            "命令输入区\n\n按 <Tab> 键获取命令列表\n\n使用问号获取某个命令的参数列表：\nPyMOL> color ?\n\n使用 \"help\" 阅读命令的在线帮助：\nPyMOL> help color\n\n按 <Tab> 键获取许多参数的自动补全：\nPyMOL> color ye<Tab>    （将自动补全为 \"yellow\"）\n",
        "Could not read PyMOL stylesheet.": "无法读取 PyMOL 样式表。",
        "Deselect": "反选",
        "Draw/Ray": "渲染",
        "External GUI": "外部界面",
        "For more information:": "更多信息：",
        "Get View": "获取视图",
        "Initialize Plugin System": "初始化插件系统",
        "Legacy Plugins": "传统插件",
        "License information:": "许可证信息：",
        "MClear": "清空动画缓存",
        "Open Logfile...": "打开日志文件...",
        "Open file": "打开文件",
        "Open-Source Build": "开源版本",
        "Orient": "取向",
        "Play": "播放",
        "Properties": "属性",
        "PyMOL": "PyMOL",
        "PyMOL (%s)": "PyMOL (%s)",
        "PyMOL>": "PyMOL>",
        "Rebuild": "重建",
        "Reset": "重置",
        "Rock": "摇摆",
        "Save Session As...": "会话另存为...",
        "Stop": "停止",
        "The PyMOL Molecular Graphics System\n": "PyMOL 分子图形系统\n",
        "Toggle dockable": "切换可停靠",
        "Unpick": "取消选择",
        "Version %s": "版本 %s",
        "Visible": "可见",
        "Zoom": "缩放",
        "no prior image": "无先前图像",
        "|<": "|<",

        # ---- ScenePanel ----
        "Add Scene": "添加场景",
        "Blank scene names are not allowed": "不允许空白场景名",
        "Delete Scene": "删除场景",
        "Double click selected thumbnail to \nload into Workspace.":
            "双击选中的缩略图\n以加载到工作区。",
        "Item not found": "未找到项目",
        "Name": "名称",
        "Scene Panel": "场景面板",
        "Scene Preview": "场景预览",
        "Scene names with spaces are not supported": "不支持带空格的场景名",
        "Update Scene": "更新场景",

        # ---- ShortcutMenu ----
        " has been deleted and will be removed from the table": " 已被删除，将从表中移除",
        "Add a key binding that does not currently appear on the table":
            "添加当前未在表中显示的键绑定",
        "Command (click to edit)": "命令（点击编辑）",
        "Create New": "新建",
        "Delete Selected": "删除选中",
        "Deleted": "已删除",
        "Description": "描述",
        "Failed to change key binding": "更改键绑定失败",
        "Key": "键",
        "Keyboard Shortcut Menu": "键盘快捷键菜单",
        "Refresh the table to reflect any external changes":
            "刷新表格以反映外部更改",
        "Reset All": "全部重置",
        "Reset Selected": "重置选中",
        "Restore all key bindings to their default values and remove any that have been created":
            "将所有键绑定恢复为默认值，并移除已创建的绑定",
        "Restore selected key bindings to their default values":
            "将选中的键绑定恢复为默认值",
        "Save": "保存",
        "Save the current key bindings to be loaded automatically when opening PyMOL":
            "保存当前键绑定，以便打开 PyMOL 时自动加载",
        "This key does not have a default value.": "此键没有默认值。",
        "Unbind selected key bindings and remove any that have been created":
            "解绑选中的键绑定，并移除已创建的绑定",
        "user defined": "用户自定义",

        # ---- TextEditor ----
        "Active pymolrc files:": "当前 pymolrc 文件：",
        "Create new pymolrc?": "创建新的 pymolrc？",
        "File": "文件",
        "Filename of new pymolrc": "新 pymolrc 的文件名",
        "Open": "打开",
        "Open file": "打开文件",
        "PML": "PML",
        "Plain Text": "纯文本",
        "Python": "Python",
        "Save": "保存",
        "Save As...": "另存为...",
        "Save as ...": "另存为 ...",
        "Save changes?": "保存修改？",
        "Save?": "保存？",
        "Select pymolrc file": "选择 pymolrc 文件",
        "Syntax": "语法",
        "Text Editor": "文本编辑器",

        # ---- Volume ----
        "Get colors as script": "获取颜色为脚本",
        "Help": "帮助",
        "Maximum Alpha Value": "最大 Alpha 值",
        "Maximum Data Value": "最大数据值",
        "Minimum Data Value": "最小数据值",
        "Paste into a .pml or .py script or your pymolrc file and use this\n":
            "粘贴到 .pml 或 .py 脚本，或您的 pymolrc 文件中，并使用此\n",
        "Reset Data Range": "重置数据范围",
        "Update volume colors in real-time": "实时更新体积颜色",
        "Volume Color Map Editor": "体积颜色映射编辑器",
        "VOLUME PANEL HELP\n\n--------------------------------------------------\nCanvas Mouse Actions (no Point under Cursor)\n\n  L-Click            Add point\n  CTRL+L-Click       Add 3 points (isosurface)\n\n  CTRL+R-Drag        Zoom in\n\n--------------------------------------------------\nMouse Actions with Point under Cursor\n\n  L-Click            Edit point color\n  R-Click            Edit point value\n  SHIFT+R-Click      Edit point opacity\n  CTRL+L-Click       Edit color of 3 points\n\n  M-Click            Remove Point\n  SHIFT+L-Click      Remove Point\n  CTRL+M-Click       Remove 3 points\n  CTRL+SHIFT+L-Click Remove 3 points\n\n  L-Drag             Move point\n  CTRL+L-Drag        Move 3 points (horizontal only)\n  R-Drag             Move point along one axis only\n\n--------------------------------------------------\nL = Left mouse button\nM = Middle mouse button\nR = Right mouse button\n\n--------------------------------------------------\nSee also the \"volume_color\" command for getting and\nsetting volume colors on the command line.\n":
            "体积面板帮助\n\n--------------------------------------------------\n画布鼠标操作（光标下无控制点）\n\n  左键单击           添加控制点\n  Ctrl+左键          添加 3 个控制点（等值面）\n\n  Ctrl+右键拖动     放大\n\n--------------------------------------------------\n光标下有控制点时的鼠标操作\n\n  左键单击           编辑控制点颜色\n  右键单击           编辑控制点数值\n  Shift+右键         编辑控制点不透明度\n  Ctrl+左键          编辑 3 个控制点的颜色\n\n  中键单击           移除控制点\n  Shift+左键         移除控制点\n  Ctrl+中键          移除 3 个控制点\n  Ctrl+Shift+左键   移除 3 个控制点\n\n  左键拖动           移动控制点\n  Ctrl+左键拖动     移动 3 个控制点（仅水平方向）\n  右键拖动           仅沿一个轴移动控制点\n\n--------------------------------------------------\nL = 鼠标左键\nM = 鼠标中键\nR = 鼠标右键\n\n--------------------------------------------------\n另请参阅 \"volume_color\" 命令，可在命令行\n获取和设置体积颜色。\n",

        # ---- Existing PluginManager strings (already in pluginmanager.ts, preserved) ----
        # These are listed for safety; existing translations are kept.

        # ---- APBS plugin (data/startup/apbs_gui) ----
        "Continue?": "继续？",
        " emmitted warnings, do you want to continue?": " 报告了警告，是否继续？",
        "Abort": "中止",
        "Run": "运行",
        "Finished": "完成",
        "Finished with Success. Close the APBS dialog?": "已成功完成。关闭 APBS 对话框？",
        "Error": "错误",
        "Warning": "警告",
        'Warning: File "%s" does not exist': '警告：文件 "%s" 不存在',
        "Selection is invalid": "选择无效",
        "No preparation necessary, selection has charges and radii": "无需准备，选择已具有电荷和半径",
        "Selection needs preparation (partial_charge: %s, elec_radius: %s)":
            "选择需要准备（partial_charge: %s, elec_radius: %s）",
        "YES": "是",
        "no": "否",

        # ---- Lighting Settings plugin (data/startup/lightingsettings_gui) ----
        "Lighting Settings": "光照设置",
        "Presets:": "预设：",
        "Default": "默认",
        "Metal": "金属",
        "Plastic": "塑料",
        "Rubber": "橡胶",
        "X-Ray": "X 射线",
        "Diffuse Reflection": "漫反射",
        "Direct Light from Front": "正面直射光",
        "Free placeable directed Lights": "可自由放置的定向光",
        "Specular Reflection": "镜面反射",
        "Ambient Occlusion (Surface only)": "环境光遮蔽（仅表面）",
        "Ray trace only": "仅光线追踪",
        "direct (+reflect)": "直射（+反射）",
        "specular_intensity (=specular)": "镜面强度（=specular）",
    },
}


# Context -> file basename (without language suffix)
CONTEXT_FILES = {
    "PyMOLQtGUI": "pymolqtgui",
    "Menu": "menu_misc",  # "Menu" is split across menu_*.ts; new strings go to menu_misc
    "PluginManager": "pluginmanager",
    "AdvancedSettings": "advanced_settings",
    "Builder": "builder",
    "FileDialogs": "file_dialogs",
    "PluginInstallation": "plugin_installation",
    "PluginRepository": "plugin_repository",
    "PropertiesDialog": "properties_dialog",
    "ScenePanel": "scene_panel",
    "ShortcutMenu": "shortcut_menu",
    "TextEditor": "text_editor",
    "Volume": "volume",
    "APBS": "apbs",
    "LightingSettings": "lighting_settings",
    "QtUtils": "qt_utils",
    # UI form classes (used as Qt translation contexts for .ui files)
    "Form": "forms",
    "Dialog": "dialogs",
}


# ---------------------------------------------------------------------------
# UI translations (for .ui form files)
# Keyed by context (class name from .ui <class> element).
# ---------------------------------------------------------------------------
UI_TRANSLATIONS: dict[str, dict[str, dict[str, str]]] = {
    "zh_CN": {
        "Dialog": {
            "&Discard current session": "放弃当前会话(&D)",
            "&Merge with current session (partial load)": "与当前会话合并（部分加载）(&M)",
            "Add New": "新建",
            "All currently &loaded objects will be deleted.": "所有当前加载的对象都将被删除(&L)。",
            "Amplitudes": "振幅",
            "Are you sure you want to change this existing key binding?":
                "确定要更改此现有的键绑定吗？",
            "Automatically rename duplicate objects": "自动重命名重复对象",
            "Cancel": "取消",
            "Column Labels": "列标签",
            "Command:": "命令：",
            "Confirm": "确认",
            "Confirm Changing Existing Binding": "确认更改现有绑定",
            "Create Shortcut": "创建快捷键",
            "Creating New Shortcuts": "创建新快捷键",
            "Dialog": "对话框",
            "Don't show this again": "不再显示",
            "Each session will have i&ts own window.": "每个会话将拥有自己的窗口(&T)。",
            "Help": "帮助",
            "High": "高",
            "Key:": "键：",
            "Load Session": "加载会话",
            "Low": "低",
            "Map Options": "电子密度图选项",
            "New Map Name Prefix": "新电子密度图名前缀",
            "Open &in new PyMOL Window": "在新 PyMOL 窗口中打开(&I)",
            "Phases": "相位",
            "Press Key": "按键",
            "Reflection File Import": "反射数据文件导入",
            "Resolution": "分辨率",
            "Shortcut Help": "快捷键帮助",
            "Show All": "显示全部",
            "Show Basic": "显示基础",
            "The current PyMOL window has a session in progress. How do you want to proceed?":
                "当前 PyMOL 窗口有进行中的会话。您希望如何继续？",
            "Type Command": "输入命令",
            "Weights": "权重",
            "Will not restore &global settings, selections, scenes or movies from the session.":
                "将不从会话中恢复全局设置、选择、场景或影片(&G)。",
            "auto_rename_duplicate_objects (global setting)":
                "auto_rename_duplicate_objects（全局设置）",
            "partial=1": "partial=1",
            '<!DOCTYPE HTML PUBLIC "-//W3C//DTD HTML 4.0//EN" "http://www.w3.org/TR/REC-html40/strict.dtd">\n<html><head><meta name="qrichtext" content="1" /><style type="text/css">\np, li { white-space: pre-wrap; }\n</style></head><body style=" font-family:\'Sans Serif\'; font-size:9pt; font-weight:400; font-style:normal;">\n<p style=" margin-top:0px; margin-bottom:0px; margin-left:0px; margin-right:0px; -qt-block-indent:0; text-indent:0px;"><span style=" font-weight:600;">Creating New Shortcuts</span></p>\n<p style="-qt-paragraph-type:empty; margin-top:0px; margin-bottom:0px; margin-left:0px; margin-right:0px; -qt-block-indent:0; text-indent:0px;"></p>\n<p style=" margin-top:0px; margin-bottom:0px; margin-left:0px; margin-right:0px; -qt-block-indent:0; text-indent:0px;">Shortcuts can be added with the <span style=" font-style:italic;">Create Shortcut</span> dialog.</p>\n<p style="-qt-paragraph-type:empty; margin-top:0px; margin-bottom:0px; margin-left:0px; margin-right:0px; -qt-block-indent:0; text-indent:0px;"></p>\n<p style=" margin-top:0px; margin-bottom:0px; margin-left:0px; margin-right:0px; -qt-block-indent:0; text-indent:0px;">Add a <span style=" font-style:italic;">Key</span> by pressing the key (or key combination) and then enter a <span style=" font-style:italic;">Command</span> that should be executed.</p></body></html>':
                '<!DOCTYPE HTML PUBLIC "-//W3C//DTD HTML 4.0//EN" "http://www.w3.org/TR/REC-html40/strict.dtd">\n<html><head><meta name="qrichtext" content="1" /><style type="text/css">\np, li { white-space: pre-wrap; }\n</style></head><body style=" font-family:\'Sans Serif\'; font-size:9pt; font-weight:400; font-style:normal;">\n<p style=" margin-top:0px; margin-bottom:0px; margin-left:0px; margin-right:0px; -qt-block-indent:0; text-indent:0px;"><span style=" font-weight:600;">创建新快捷键</span></p>\n<p style="-qt-paragraph-type:empty; margin-top:0px; margin-bottom:0px; margin-left:0px; margin-right:0px; -qt-block-indent:0; text-indent:0px;"></p>\n<p style=" margin-top:0px; margin-bottom:0px; margin-left:0px; margin-right:0px; -qt-block-indent:0; text-indent:0px;">可以通过<span style=" font-style:italic;">创建快捷键</span>对话框添加快捷键。</p>\n<p style="-qt-paragraph-type:empty; margin-top:0px; margin-bottom:0px; margin-left:0px; margin-right:0px; -qt-block-indent:0; text-indent:0px;"></p>\n<p style=" margin-top:0px; margin-bottom:0px; margin-left:0px; margin-right:0px; -qt-block-indent:0; text-indent:0px;">按下键（或组合键）即可添加<span style=" font-style:italic;">键</span>，然后输入要执行的<span style=" font-style:italic;">命令</span>。</p></body></html>',
        },
        "Form": {
            # Window titles
            "APBS Electrostatics": "APBS 静电学",
            "Colors": "颜色",
            "Get PDB File": "获取 PDB 文件",
            "Load Alignment": "加载比对",
            "Maestro File Import": "Maestro 文件导入",
            "Map Import": "电子密度图导入",
            "Movie Export": "影片导出",
            "Plugin Manager": "插件管理器",
            "Properties Inspector": "属性检查器",
            "Save Molecule": "保存分子",
            "Save PNG image": "保存 PNG 图像",
            "Trajectory Import": "轨迹导入",
            "Form": "窗体",

            # Group / section titles
            "Column Labels": "列标签",
            "Frames": "帧",
            "Install from PyMOLWiki or any URL": "从 PyMOLWiki 或任意 URL 安装",
            "Install from Repository": "从仓库安装",
            "Install from local file": "从本地文件安装",
            "Map Object": "电子密度图对象",
            "Memory Optimization": "内存优化",
            "Movie Format": "影片格式",
            "Objects and Files": "对象和文件",
            "PDB Structure Options": "PDB 结构选项",
            "Plugin override search path": "插件覆盖搜索路径",
            "Preferences": "首选项",
            "Program Locations": "程序位置",
            "Rendering": "渲染",
            "Representation": "表示方式",
            "Target Object": "目标对象",
            "This will run the following command": "将运行以下命令",
            "Resolution": "分辨率",

            # Button labels
            "&Draw (fast)": "绘制（快速）(&D)",
            "&Quality": "质量(&Q)",
            "Add...": "添加...",
            "Add new directory ...": "添加新目录...",
            "Apply": "应用",
            "Browse...": "浏览...",
            "Calculate Map with APBS": "用 APBS 计算电子密度图",
            "Cancel": "取消",
            "Choose file...": "选择文件...",
            "Copy Image to Clipboard": "复制图像到剪贴板",
            "Don't delete temporary files": "不删除临时文件",
            "Don't group new objects": "不分组新对象",
            "Download": "下载",
            "Draw (fast)": "绘制（快速）",
            "E&ncoder": "编码器(&N)",
            "Fetch": "获取",
            "G&IF": "GIF(&I)",
            "Ignore warnings": "忽略警告",
            "Info": "信息",
            "Install": "安装",
            "Interval": "间隔",
            "Load": "加载",
            "Load on startup": "启动时加载",
            "Lock aspect ratio": "锁定宽高比",
            "MOV (Quic&kTime)": "MOV（QuickTime）(&K)",
            "MPEG &1": "MPEG-1(&1)",
            "MPEG &4": "MPEG-4(&4)",
            "Move down": "下移",
            "Move up": "上移",
            "Multiple entries": "多个条目",
            "OK": "确定",
            "Options >>": "选项 >>",
            "PNG &Images": "PNG 图像(&I)",
            "Prepare Molecule": "准备分子",
            "Ra&y (slow)": "光线追踪（慢）(&Y)",
            "Ray (slow)": "光线追踪（慢）",
            "Refresh": "刷新",
            "Register APBS Use": "注册 APBS 使用",
            "Remove": "移除",
            "Reset": "重置",
            "Run": "运行",
            "S&tate": "状态(&T)",
            "Save Image to File": "保存图像到文件",
            "Save Movie as ...": "保存影片为...",
            "Save PNG image as ...": "保存 PNG 图像为...",
            "Save...": "保存...",
            "Se&lection": "选择(&L)",
            "Start": "开始",
            "Stop": "停止",
            "Uninstall": "卸载",
            "Wid&th": "宽度(&T)",
            "< Back": "< 上一步",
            "Next >": "下一步 >",
            "b&uffer": "缓冲(&U)",

            # Field labels
            "Assembly (optional):": "组装（可选）：",
            "Atom:": "原子：",
            "Blue": "蓝色",
            "Chain name (optional):": "链名称（可选）：",
            "Common:": "通用：",
            "DPI": "DPI",
            "Focus Selection (optional):": "聚焦选择（可选）：",
            "Green": "绿色",
            "Grid Spacing:": "网格间距：",
            "Hei&ght": "高度(&G)",
            "Height": "高度",
            "Key": "键",
            "Map:": "电子密度图：",
            "Method:": "方法：",
            "Molecular Object:": "分子对象：",
            "Name": "名称",
            "Object": "对象",
            "Object:": "对象：",
            "Output Map Object:": "输出电子密度图对象：",
            "Output Molecule Object:": "输出分子对象：",
            "Output Ramp:": "输出渐变：",
            "PDB ID:": "PDB ID：",
            "PDB Structure": "PDB 结构",
            "Range: +/-": "范围：+/-",
            "Red": "红色",
            "Selection has ...": "选择有...",
            "Selection:": "选择：",
            "Settings": "设置",
            "State": "状态",
            "State:": "状态：",
            "Units": "单位",
            "URL:": "URL：",
            "Value": "值",
            "Width": "宽度",
            "at": "在",
            "center": "居中",
            "convert": "转换",
            "level": "等级",
            "polymer": "聚合物",
            "loaded": "已加载",
            "all": "全部",
            "startup": "启动",
            "startup all": "全部启动",
            "startup none": "不启动",

            # Checkboxes / radio
            "2FoFc Map": "2FoFc 电子密度图",
            "Append if state=0": "若 state=0 则追加",
            "FoFc Map": "FoFc 电子密度图",
            "Original atom order (according to \"rank\")":
                "原始原子顺序（按 \"rank\"）",
            "Retain atom ids": "保留原子 ID",
            "Write CONECT records for all bonds": "为所有键写入 CONECT 记录",
            "Write HEADER for every object": "为每个对象写入 HEADER",
            "Write multiple bonds as duplicate CONECT records":
                "将多重键写为重复的 CONECT 记录",
            "Write objects or states to ...": "将对象或状态写入...",
            "Write segment identifier (segi) column":
                "写入分段标识符（segi）列",
            "as one multi-state object (discrete states)":
                "作为一个多状态对象（离散状态）",
            "as one multi-state object (trajectory)":
                "作为一个多状态对象（轨迹）",
            "as separate objects": "作为独立对象",
            "automatic handling": "自动处理",
            "capture current display": "捕获当前显示",
            "defer_builds_mode=3 (don't keep geometry for other states in memory)":
                "defer_builds_mode=3（不在内存中保留其他状态的几何信息）",
            "draw antialiased OpenGL image": "绘制抗锯齿 OpenGL 图像",
            "enabled": "已启用",
            "fetch ...": "获取...",
            "load ...": "加载...",
            "load_traj ...": "load_traj...",
            "normalize (mean=0 stdev=1)": "归一化（均值=0 标准差=1）",
            "o&ne file per object-state": "每个对象-状态一个文件(&N)",
            "one file per ob&ject": "每个对象一个文件(&J)",
            "one single f&ile": "单个文件(&I)",
            "ray trace with opaque background": "使用不透明背景光线追踪",
            "ray trace with transparent background": "使用透明背景光线追踪",
            "se&lection": "选择(&L)",
            "transparent background (\"Ray\" only)":
                "透明背景（仅 \"Ray\"）",
            "use CA-pseudocharge and radius=3.0":
                "使用 CA 伪电荷和半径=3.0",
            "use CB-pseudocharge and vdw": "使用 CB 伪电荷和 vdw",
            "use formal_charge and vdw": "使用 formal_charge 和 vdw",
            "use vdw": "使用 vdw",
            "volume": "体积",
            "isomesh": "等值线",
            "isosurface": "等值面",
            "carve": "雕刻",
            "cm": "厘米",
            "inch": "英寸",

            # Description / paragraph labels
            "Coarse grained charge model for CA-only models: place a pseudo charge on the C-alpha atoms.":
                "仅 CA 模型的粗粒化电荷模型：在 C-alpha 原子上放置伪电荷。",
            "Coarse grained charge model for proteins with \"stub\" side chains: place a pseudo charge on the C-alpha atoms.":
                "带 \"残桩\" 侧链蛋白质的粗粒化电荷模型：在 C-alpha 原子上放置伪电荷。",
            "Coarse grained charge model: use formal charges (-1/0/1) and PyMOL's vdw radii.":
                "粗粒化电荷模型：使用形式电荷（-1/0/1）和 PyMOL 的 vdw 半径。",
            "Molecular Surface Visualization": "分子表面可视化",
            "Other Visualizations": "其他可视化",
            "Projects the electrostatic potential onto the molecular surface":
                "将静电势投影到分子表面上",
            "After the map has been calculated, create additional visualizations using the controls below.":
                "计算电子密度图后，使用下方控件创建其他可视化。",
            "New in PyMOL 2.0: To render a sized antialiased image, use the Draw/Ray panel (from menu: File > Save Image As > PNG).":
                "PyMOL 2.0 新功能：要渲染指定尺寸的抗锯齿图像，请使用 Draw/Ray 面板（菜单：文件 > 将图像另存为 > PNG）。",
            "For RNA, use residue names RA, RC, RG, RU":
                "对于 RNA，使用残基名称 RA、RC、RG、RU",
            "Field lines with \"A > gradient > default\"":
                "使用 \"A > gradient > default\" 的场线",
            "Isosurface with \"A > surface > level +/-1.0\"":
                "使用 \"A > surface > level +/-1.0\" 的等值面",
            "Slice with \"A > slice > default\"":
                "使用 \"A > slice > default\" 的切片",
            "Solvent Accessible Surface": "溶剂可及表面",
            "Solvent Excluded Surface (Connolly surface)":
                "溶剂排除表面（Connolly 表面）",
            "Volume with \"A > volume > esp\"":
                "使用 \"A > volume > esp\" 的体积",
            "Paste a link to a script or plugin, or a PyMOLWiki url which then will be downloaded.":
                "粘贴脚本或插件的链接，或 PyMOLWiki URL，随后将被下载。",
            "PyMOL restart required in order to find plugins in modified plugin search path":
                "需要重启 PyMOL 才能在修改后的插件搜索路径中找到插件",
            "Documentation: <a href=\"https://apbs.readthedocs.io/en/latest/using/input/elec.html#flags-and-keywords\">APBS documentation</a>":
                "文档：<a href=\"https://apbs.readthedocs.io/en/latest/using/input/elec.html#flags-and-keywords\">APBS 文档</a>",
            "Use settings to match cartoon/ribbon color and ballstick style":
                "使用设置以匹配 cartoon/ribbon 颜色和球棍样式",
            "Normalization does NOT take the unit cell into account. PyMOL normalizes across all stored map points.":
                "归一化不考虑单位晶胞。PyMOL 对所有存储的电子密度图点进行归一化。",
            "<html><head/><body><p>Note: Downloading will save the files in the directory of the first selected object and load them.</p></body></html>":
                "<html><head/><body><p>注意：下载将把文件保存到第一个选中对象的目录中并加载它们。</p></body></html>",

            # Tooltips
            "\"movie_quality\" setting, the lower the lossier":
                "\"movie_quality\" 设置，越低越有损",
            "\"pdb2pqr\" adds hydrogens and missing sidechain atoms, assigns partial charges and radii.":
                "\"pdb2pqr\" 添加氢原子和缺失的侧链原子，分配部分电荷和半径。",
            "\"prepwizard\" adds hydrogens and missing sidechain atoms, and assigns partial charges and radii. Schrödinger only.":
                "\"prepwizard\" 添加氢原子和缺失的侧链原子，并分配部分电荷和半径。仅限 Schrödinger。",
            "\"protein_assign_charges_and_radii\" REMOVES incomplete or modified residues, and assigns partial charges and radii.":
                "\"protein_assign_charges_and_radii\" 会移除不完整或修改过的残基，并分配部分电荷和半径。",
            "4 letter PDB code": "4 字符 PDB 代码",
            "Additional command line options for prepwizard, for example \"-r 2.0\" or \"-fixmissing\"":
                "prepwizard 的额外命令行选项，例如 \"-r 2.0\" 或 \"-fixmissing\"",
            "Angstrom": "埃",
            "Animated GIF": "动画 GIF",
            "Common Video Resolutions": "常用视频分辨率",
            "Dots per Inch": "每英寸点数",
            "Export a series of numbered PNG files": "导出一系列编号的 PNG 文件",
            "For same topology with different conformations, choose \"trajectory\". For independent coordinates, choose \"objects\".":
                "对于相同拓扑但不同构象的情况，选择 \"轨迹\"。对于独立坐标，选择 \"对象\"。",
            "Grid spacing not guaranteed, will increase grid spacing if grid doesn't fit into given box":
                "不保证网格间距，若网格不适合给定盒子将增大网格间距",
            "Load entire trajectory if stop &lt; 1":
                "若 stop &lt; 1 则加载整个轨迹",
            "Render each movie frame with ray tracing.\nMay take a long time, but produces higher quality results.":
                "使用光线追踪渲染每个影片帧。\n可能耗时较长，但能产生更高质量的结果。",
            "Use current viewport size": "使用当前视口尺寸",
            "Use fast on-screen rendering": "使用快速屏幕渲染",
            "Use high-quality ray-tracing.\nSupports optimal multi-layer\ntransparency, shadows, etc.":
                "使用高质量光线追踪。\n支持最佳的多层\n透明度、阴影等。",
            "contour level (\"sigma\" or \"rmsd\" if data is normalized)":
                "等值线级别（数据归一化时为 \"sigma\" 或 \"rmsd\"）",
            "for periodic systems (x-ray) display the data acound the given atom selection (symmetry related)":
                "对于周期性系统（X 射线），显示围绕给定原子选择（对称相关）的数据",
            "ignore_pdb_segi": "ignore_pdb_segi",
            "limit the expensive fine grid calculation to a region of interest, e.g. a binding site":
                "将昂贵的精细网格计算限制在感兴趣的区域，例如结合位点",
            "margin around the selection (in Angstrom)": "选择周围的边距（以埃为单位）",
            "only show density which is within the carve-radius of any atom":
                "仅显示在任意原子 carve-radius 内的密度",
            "pdb_conect_all": "pdb_conect_all",
            "pdb_conect_nodup": "pdb_conect_nodup",
            "pdb_retain_ids": "pdb_retain_ids",
            "Placeholders:\n{name} - object name\n{state} - state number\n{title} - state title\n{segi} - segment identifier":
                "占位符：\n{name} - 对象名\n{state} - 状态编号\n{title} - 状态标题\n{segi} - 分段标识符",
            "retain_order": "retain_order",
            "space delimited list of property names, or * for all":
                "以空格分隔的属性名列表，或 * 表示全部",
            "uncheck if the selected molecule already has partial charges and radii (\"elec_radius\" setting)":
                "如果所选分子已有部分电荷和半径（\"elec_radius\" 设置），请取消勾选",
            "use \"multisave\" command": "使用 \"multisave\" 命令",
            "video height in pixels": "视频高度（以像素为单位）",
            "video width in pixels": "视频宽度（以像素为单位）",
            "antialiased on-screen rendering": "抗锯齿屏幕渲染",

            # Placeholders
            "Filter": "筛选",
            "Object name (optional)": "对象名（可选）",
            "apbs_map": "apbs_map",
            "apbs_ramp": "apbs_ramp",
            "extra command line options": "额外命令行选项",
            "object name": "对象名",
            "prepared": "已准备",

            # Stand-alone terms
            "Atom properties": "原子属性",
            "Object properties": "对象属性",
            "PyMOL Object": "PyMOL 对象",
            "Object/group name": "对象/组名",

            # Program names and technical tokens (passthrough)
            "apbs": "apbs",
            "ffmpeg": "ffmpeg",
            "mpeg_encode": "mpeg_encode",
            "pdb2pqr": "pdb2pqr",
            "prepwizard (SCHRODINGER)": "prepwizard (SCHRODINGER)",
            "protein_assign_charges_and_radii": "protein_assign_charges_and_radii",
            "sele": "sele",

            # Placeholder tokens for templates (passthrough)
            "{loadtime}": "{loadtime}",
            "{name}": "{name}",
            "{name}_{state}": "{name}_{state}",
            "{pluginname}": "{pluginname}",
            "{version}": "{version}",

            # Value list / numeric items
            "*": "*",
            "- or -": "- 或 -",
            "--ff=AMBER": "--ff=AMBER",
            "-1 (current)": "-1（当前）",
            "...": "...",
            "0 (all states)": "0（所有状态）",
            "150": "150",
            "300": "300",
            "360p": "360p",
            "480p": "480p",
            "720p": "720p",
            "90": "90",
            "command line options:": "命令行选项：",

            # Additional misc labels
            "Use existing \"partial_charge\", use vdw as \"elec_radius\"":
                "使用现有 \"partial_charge\"，使用 vdw 作为 \"elec_radius\"",
            "Load existing \"apbs.in\" file:": "加载现有 \"apbs.in\" 文件：",

            # Full-length tooltip/description variants (some .ui files have
            # longer versions than the variants above)
            "\"pdb2pqr\" adds hydrogens and missing sidechain atoms, assigns partial charges and radii. REMOVES ligands and modified residues.":
                "\"pdb2pqr\" 添加氢原子和缺失的侧链原子，分配部分电荷和半径。会移除配体和修改过的残基。",
            "\"prepwizard\" adds hydrogens and missing sidechain atoms, and assigns partial charges. Can handle ligands and modified residues. PyMOL's vdw radii will be used. Requires Schrodinger Suite.":
                "\"prepwizard\" 添加氢原子和缺失的侧链原子，并分配部分电荷。可处理配体和修改过的残基。将使用 PyMOL 的 vdw 半径。需要 Schrödinger Suite。",
            "\"protein_assign_charges_and_radii\" REMOVES incomplete or modified residues, adds missing C-terminus, and assigns AMBER99 partial charges and radii":
                "\"protein_assign_charges_and_radii\" 会移除不完整或修改过的残基，添加缺失的 C 末端，并分配 AMBER99 部分电荷和半径",
            "Additional command line options for prepwizard, for example \"-r 2.0\" or \"-fix\"":
                "prepwizard 的额外命令行选项，例如 \"-r 2.0\" 或 \"-fix\"",
            "After the map has been calculated, create additional visualizations using the \"Action\" items in the object menu panel:":
                "计算电子密度图后，使用对象菜单面板中的 \"操作\" 项创建其他可视化：",
            "Coarse grained charge model for CA-only models: place a pseudo charge on the CA atom of GLU, ASP, ARG and LYS and set a radius of 3.0 for all atoms":
                "仅 CA 模型的粗粒化电荷模型：在 GLU、ASP、ARG 和 LYS 的 CA 原子上放置伪电荷，并将所有原子的半径设置为 3.0",
            "Coarse grained charge model for proteins with \"stub\" side chains: place a pseudo charge on the CB atom of GLU, ASP, ARG and LYS":
                "带 \"残桩\" 侧链蛋白质的粗粒化电荷模型：在 GLU、ASP、ARG 和 LYS 的 CB 原子上放置伪电荷",
            "Coarse grained charge model: use formal charges (-1/0/1) and PyMOL's vdw radii. Note that missing sidechains of charged residues (e.g. GLU) will not contribute any charge!":
                "粗粒化电荷模型：使用形式电荷（-1/0/1）和 PyMOL 的 vdw 半径。注意：带电残基（如 GLU）缺失的侧链将不贡献任何电荷！",
            "Documentation: <a href=\"https://apbs.readthedocs.io/en/latest/using/input/elec/\">apbs.readthedocs.io</a>":
                "文档：<a href=\"https://apbs.readthedocs.io/en/latest/using/input/elec/\">apbs.readthedocs.io</a>",
            "For same topology with different conformations, choose \"trajectory\". For independent molecules, like a set of different ligands, choose \"separate objects\" or \"discrete states\".":
                "对于相同拓扑但不同构象的情况，选择 \"轨迹\"。对于独立分子（如一组不同的配体），选择 \"独立对象\" 或 \"离散状态\"。",
            "Grid spacing not guaranteed, will increase grid spacing if grid doesn't fit into memory":
                "不保证网格间距，若网格不适合内存将增大网格间距",
            "New in PyMOL 2.0: To render a sized antialiased image, use the Draw/Ray panel in the upper right.":
                "PyMOL 2.0 新功能：要渲染指定尺寸的抗锯齿图像，请使用右上角的 Draw/Ray 面板。",
            "Normalization does NOT take the unit cell into account. PyMOL normalizes across the data extent present in the map file, which may not be aligned with the unit cell. (This is different from Coot)":
                "归一化不考虑单位晶胞。PyMOL 对电子密度图文件中存在的数据范围进行归一化，该范围可能与单位晶胞不对齐。（与 Coot 不同）",
            "Paste a link to a script or plugin, or a PyMOLWiki url which then will be downloaded and scanned for scripts that extend the PyMOL API":
                "粘贴脚本或插件的链接，或 PyMOLWiki URL，随后将被下载并扫描以查找扩展 PyMOL API 的脚本",
            "Placeholders:\n{name} - object name\n{state} - state number\n{title} - state title\n{num} - running number":
                "占位符：\n{name} - 对象名\n{state} - 状态编号\n{title} - 状态标题\n{num} - 运行编号",
            "Prompt for every file": "为每个文件提示",
            "Render each movie frame with ray tracing.\nMay take a long time, but produces the\nbest quality.":
                "使用光线追踪渲染每个影片帧。\n可能耗时较长，但能产生\n最佳质量。",
            "Use high-quality ray-tracing.\nSupports optimal multi-layer\ntransparency, shadows, and\nalpha-channel background.":
                "使用高质量光线追踪。\n支持最佳的多层\n透明度、阴影和\nAlpha 通道背景。",
            "for periodic systems (x-ray) display the data acound the given atom selection (box shaped, unless \"carve\" is checked)":
                "对于周期性系统（X 射线），显示围绕给定原子选择的数据（盒形，除非勾选 \"carve\"）",
            "limit the expensive fine grid calculation to a region of interest, e.g. a binding pocket":
                "将昂贵的精细网格计算限制在感兴趣的区域，例如结合口袋",
            "uncheck if the selected molecule already has partial charges and radii (\"elec_radius\" property) assigned, e.g. if you have loaded a PQR file":
                "如果所选分子已分配部分电荷和半径（\"elec_radius\" 属性），例如已加载 PQR 文件，请取消勾选",
            "<html><head/><body><p>Note: Downloading will save the files in the directory defined by the &quot;<a href=\"http://pymolwiki.org/index.php/Fetch_Path\"><span style=\" text-decoration: underline; color:#0057ae;\">fetch_path</span></a>&quot; setting.</p></body></html>":
                "<html><head/><body><p>注意：下载将把文件保存到 <a href=\"http://pymolwiki.org/index.php/Fetch_Path\"><span style=\" text-decoration: underline; color:#0057ae;\">fetch_path</span></a> 设置所定义的目录中。</p></body></html>",

            # Long HTML help blocks in plugin manager / shortcut help
            '<!DOCTYPE HTML PUBLIC "-//W3C//DTD HTML 4.0//EN" "http://www.w3.org/TR/REC-html40/strict.dtd">\n<html><head><meta name="qrichtext" content="1" /><style type="text/css">\np, li { white-space: pre-wrap; }\n</style></head><body style=" font-family:\'Ubuntu\'; font-size:9pt; font-weight:400; font-style:normal;">\n<p style=" margin-top:12px; margin-bottom:12px; margin-left:0px; margin-right:0px; -qt-block-indent:0; text-indent:0px;">Plugins are external modules which extend PyMOL\'s capabilities.</p>\n<p style=" margin-top:12px; margin-bottom:12px; margin-left:0px; margin-right:0px; -qt-block-indent:0; text-indent:0px;">Plugins can provide new commands and/or add menu items to the &quot;Plugin&quot; menu.</p>\n<p style=" margin-top:12px; margin-bottom:12px; margin-left:0px; margin-right:0px; -qt-block-indent:0; text-indent:0px;">For technical details, visit</p>\n<ul style="margin-top: 0px; margin-bottom: 0px; margin-left: 0px; margin-right: 0px; -qt-list-indent: 1;"><li style=" margin-top:12px; margin-bottom:0px; margin-left:0px; margin-right:0px; -qt-block-indent:0; text-indent:0px;"><a href="http://pymolwiki.org/index.php/PluginArchitecture"><span style=" text-decoration: underline; color:#0057ae;">http://pymolwiki.org/index.php/PluginArchitecture</span></a></li>\n<li style=" margin-top:0px; margin-bottom:12px; margin-left:0px; margin-right:0px; -qt-block-indent:0; text-indent:0px;"><a href="http://pymolwiki.org/index.php/Script_Tutorial"><span style=" text-decoration: underline; color:#0057ae;">http://pymolwiki.org/index.php/Script_Tutorial</span></a></li></ul>\n<p style=" margin-top:12px; margin-bottom:12px; margin-left:0px; margin-right:0px; -qt-block-indent:0; text-indent:0px;"><br /></p></body></html>':
                '<!DOCTYPE HTML PUBLIC "-//W3C//DTD HTML 4.0//EN" "http://www.w3.org/TR/REC-html40/strict.dtd">\n<html><head><meta name="qrichtext" content="1" /><style type="text/css">\np, li { white-space: pre-wrap; }\n</style></head><body style=" font-family:\'Ubuntu\'; font-size:9pt; font-weight:400; font-style:normal;">\n<p style=" margin-top:12px; margin-bottom:12px; margin-left:0px; margin-right:0px; -qt-block-indent:0; text-indent:0px;">插件是扩展 PyMOL 功能的外部模块。</p>\n<p style=" margin-top:12px; margin-bottom:12px; margin-left:0px; margin-right:0px; -qt-block-indent:0; text-indent:0px;">插件可以提供新命令和/或在 \"插件\" 菜单中添加菜单项。</p>\n<p style=" margin-top:12px; margin-bottom:12px; margin-left:0px; margin-right:0px; -qt-block-indent:0; text-indent:0px;">技术详情请访问</p>\n<ul style="margin-top: 0px; margin-bottom: 0px; margin-left: 0px; margin-right: 0px; -qt-list-indent: 1;"><li style=" margin-top:12px; margin-bottom:0px; margin-left:0px; margin-right:0px; -qt-block-indent:0; text-indent:0px;"><a href="http://pymolwiki.org/index.php/PluginArchitecture"><span style=" text-decoration: underline; color:#0057ae;">http://pymolwiki.org/index.php/PluginArchitecture</span></a></li>\n<li style=" margin-top:0px; margin-bottom:12px; margin-left:0px; margin-right:0px; -qt-block-indent:0; text-indent:0px;"><a href="http://pymolwiki.org/index.php/Script_Tutorial"><span style=" text-decoration: underline; color:#0057ae;">http://pymolwiki.org/index.php/Script_Tutorial</span></a></li></ul>\n<p style=" margin-top:12px; margin-bottom:12px; margin-left:0px; margin-right:0px; -qt-block-indent:0; text-indent:0px;"><br /></p></body></html>',
        },
        # Dialog-context additions
        "__dialog_extras__": {},
    },
}


# Append Dialog-context extras (longer variants) to the Dialog dict above.
# We use a separate dict and merge to avoid duplicating keys in source code.
_DIALOG_EXTRAS = {
    "Will not restore &global settings, selections, scenes or movies from the session file":
        "将不会从会话文件中恢复全局设置、选择、场景或影片(&G)。",
    '<!DOCTYPE HTML PUBLIC "-//W3C//DTD HTML 4.0//EN" "http://www.w3.org/TR/REC-html40/strict.dtd">\n<html><head><meta name="qrichtext" content="1" /><style type="text/css">\np, li { white-space: pre-wrap; }\n</style></head><body style=" font-family:\'.AppleSystemUIFont\'; font-size:13pt; font-weight:400; font-style:normal;">\n<p style=" margin-top:0px; margin-bottom:0px; margin-left:0px; margin-right:0px; -qt-block-indent:0; text-indent:0px;">General Tips:</p>\n<p style=" margin-top:0px; margin-bottom:0px; margin-left:0px; margin-right:0px; -qt-block-indent:0; text-indent:0px;">   - Check the menu first before assigning.</p>\n<p style=" margin-top:0px; margin-bottom:0px; margin-left:0px; margin-right:0px; -qt-block-indent:0; text-indent:0px;">   - CTRL-S, CTRL-E, CTRL-O, and CTRL-M are reserved and cannot be bound</p>\n<p style=" margin-top:0px; margin-bottom:0px; margin-left:0px; margin-right:0px; -qt-block-indent:0; text-indent:0px;">   - Not all commands shown on the table are available to be assigned to other keys at this time. </p>\n<p style="-qt-paragraph-type:empty; margin-top:0px; margin-bottom:0px; margin-left:0px; margin-right:0px; -qt-block-indent:0; text-indent:0px;"><br /></p>\n<p style=" margin-top:0px; margin-bottom:0px; margin-left:0px; margin-right:0px; -qt-block-indent:0; text-indent:0px;">Available Keys for Assignment:</p>\n<p style=" margin-top:0px; margin-bottom:0px; margin-left:0px; margin-right:0px; -qt-block-indent:0; text-indent:0px;">    - F1 to F12</p>\n<p style=" margin-top:0px; margin-bottom:0px; margin-left:0px; margin-right:0px; -qt-block-indent:0; text-indent:0px;">    - left, right, pgup, pgdn, home, insert</p>\n<p style=" margin-top:0px; margin-bottom:0px; margin-left:0px; margin-right:0px; -qt-block-indent:0; text-indent:0px;">    - CTRL-A to CTRL-Z</p>\n<p style=" margin-top:0px; margin-bottom:0px; margin-left:0px; margin-right:0px; -qt-block-indent:0; text-indent:0px;">    - ALT-0 to ALT-9, ALT-A to ALT-Z</p>\n<p style="-qt-paragraph-type:empty; margin-top:0px; margin-bottom:0px; margin-left:0px; margin-right:0px; -qt-block-indent:0; text-indent:0px;"><br /></p>\n<p style=" margin-top:0px; margin-bottom:0px; margin-left:0px; margin-right:0px; -qt-block-indent:0; text-indent:0px;">Available Commands for Assignment:</p>\n<p style=" margin-top:0px; margin-bottom:0px; margin-left:0px; margin-right:0px; -qt-block-indent:0; text-indent:0px;">    - Type help into command bar</p>\n<p style=" margin-top:0px; margin-bottom:0px; margin-left:0px; margin-right:0px; -qt-block-indent:0; text-indent:0px;">    - Assign new commands with extend</p>\n<p style=" margin-top:0px; margin-bottom:0px; margin-left:0px; margin-right:0px; -qt-block-indent:0; text-indent:0px;">    - Multiple python commands can be run together by seperating with \';\'</p></body></html>':
        '<!DOCTYPE HTML PUBLIC "-//W3C//DTD HTML 4.0//EN" "http://www.w3.org/TR/REC-html40/strict.dtd">\n<html><head><meta name="qrichtext" content="1" /><style type="text/css">\np, li { white-space: pre-wrap; }\n</style></head><body style=" font-family:\'.AppleSystemUIFont\'; font-size:13pt; font-weight:400; font-style:normal;">\n<p style=" margin-top:0px; margin-bottom:0px; margin-left:0px; margin-right:0px; -qt-block-indent:0; text-indent:0px;">通用提示：</p>\n<p style=" margin-top:0px; margin-bottom:0px; margin-left:0px; margin-right:0px; -qt-block-indent:0; text-indent:0px;">   - 在分配之前请先检查菜单。</p>\n<p style=" margin-top:0px; margin-bottom:0px; margin-left:0px; margin-right:0px; -qt-block-indent:0; text-indent:0px;">   - CTRL-S、CTRL-E、CTRL-O 和 CTRL-M 已保留，无法绑定</p>\n<p style=" margin-top:0px; margin-bottom:0px; margin-left:0px; margin-right:0px; -qt-block-indent:0; text-indent:0px;">   - 并非所有显示在表中的命令此时都可分配给其他键。 </p>\n<p style="-qt-paragraph-type:empty; margin-top:0px; margin-bottom:0px; margin-left:0px; margin-right:0px; -qt-block-indent:0; text-indent:0px;"><br /></p>\n<p style=" margin-top:0px; margin-bottom:0px; margin-left:0px; margin-right:0px; -qt-block-indent:0; text-indent:0px;">可分配的键：</p>\n<p style=" margin-top:0px; margin-bottom:0px; margin-left:0px; margin-right:0px; -qt-block-indent:0; text-indent:0px;">    - F1 到 F12</p>\n<p style=" margin-top:0px; margin-bottom:0px; margin-left:0px; margin-right:0px; -qt-block-indent:0; text-indent:0px;">    - left、right、pgup、pgdn、home、insert</p>\n<p style=" margin-top:0px; margin-bottom:0px; margin-left:0px; margin-right:0px; -qt-block-indent:0; text-indent:0px;">    - CTRL-A 到 CTRL-Z</p>\n<p style=" margin-top:0px; margin-bottom:0px; margin-left:0px; margin-right:0px; -qt-block-indent:0; text-indent:0px;">    - ALT-0 到 ALT-9，ALT-A 到 ALT-Z</p>\n<p style="-qt-paragraph-type:empty; margin-top:0px; margin-bottom:0px; margin-left:0px; margin-right:0px; -qt-block-indent:0; text-indent:0px;"><br /></p>\n<p style=" margin-top:0px; margin-bottom:0px; margin-left:0px; margin-right:0px; -qt-block-indent:0; text-indent:0px;">可分配的命令：</p>\n<p style=" margin-top:0px; margin-bottom:0px; margin-left:0px; margin-right:0px; -qt-block-indent:0; text-indent:0px;">    - 在命令栏中输入 help</p>\n<p style=" margin-top:0px; margin-bottom:0px; margin-left:0px; margin-right:0px; -qt-block-indent:0; text-indent:0px;">    - 使用 extend 分配新命令</p>\n<p style=" margin-top:0px; margin-bottom:0px; margin-left:0px; margin-right:0px; -qt-block-indent:0; text-indent:0px;">    - 多个 Python 命令可以通过 \';\' 分隔一起运行</p></body></html>',
}

# Merge the extras into the zh_CN Dialog dict
for _k, _v in _DIALOG_EXTRAS.items():
    UI_TRANSLATIONS["zh_CN"]["Dialog"][_k] = _v
del _DIALOG_EXTRAS
# Remove placeholder key
UI_TRANSLATIONS["zh_CN"].pop("__dialog_extras__", None)


# Strings that belong to the "Menu" context but should be split into
# specific menu_*.ts files (based on which top-level menu they belong to).
# For new menu strings, we put them into menu_misc.ts as a fallback.
MENU_SPLIT = {
    "Edit": "menu_edit",
    # _gui.py labels (see TRANSLATIONS above) -> top-level menu file
    "Ignore .pymolrc and plugins (-k)": "menu_file",
    "1 Cycle per Update": "menu_build",
    "Light Gray": "menu_setting",
    "Gray": "menu_setting",
    "Default (Atomic)": "menu_setting",
    "Sphere": "menu_setting",
    "Stick": "menu_setting",
    "Camera": "menu_scene",
    "Reps": "menu_scene",
    "Reps + Color": "menu_scene",
    # controlling.py mode_name_dict values
    "2-Btn. Selecting": "menu_mouse",
    "3-Button Maestro": "menu_mouse",
}


# Strings passed to _tr() via variables (not matched by the literal regex).
# Manually listed per context so they land in the .ts files.
_SUPPLEMENTAL_STRINGS: dict[str, list[str]] = {
    "LightingSettings": [
        "Default", "Metal", "Plastic", "Rubber", "X-Ray",
        "Diffuse Reflection", "Direct Light from Front",
        "Free placeable directed Lights", "Specular Reflection",
        "Ambient Occlusion (Surface only)", "Ray trace only",
        "direct (+reflect)", "specular_intensity (=specular)",
    ],
    "APBS": ["YES", "no"],
    # Menu labels defined as tuple items in _gui.py get_menudata(); the
    # literal _tr/_mtr regex cannot match them, so list them here. Each is
    # routed to its top-level menu file via MENU_SPLIT.
    "Menu": [
        "Camera", "Default (Atomic)", "Gray", "Light Gray",
        "Reps", "Reps + Color", "Sphere", "Stick",
        "1 Cycle per Update", "Ignore .pymolrc and plugins (-k)",
        # controlling.py mode_name_dict values
        "2-Btn. Selecting", "3-Button Maestro",
    ],
}


def _root() -> Path:
    return Path(__file__).resolve().parents[2]


def _collect_sources(root: Path) -> list[Path]:
    globs = [
        "modules/pmg_qt/**/*.py",
        "modules/pymol/Qt/**/*.py",
        "modules/pymol/_gui.py",
        "modules/pymol/plugins/**/*.py",
        "data/startup/**/*.py",
    ]
    files: list[Path] = []
    for g in globs:
        files.extend(root.glob(g))
    return sorted(set(p for p in files if p.is_file()))


# Match _tr('Context', 'text') - returns (context, text) pairs
_TR_CALL_RE = re.compile(
    r"_tr\s*\(\s*"
    r"(['\"])(?P<context>[^'\"]+)\1\s*,\s*"
    r"(?P<text>(?:'''[\s\S]*?'''|\"\"\"[\s\S]*?\"\"\"|'(?:[^'\\]|\\.)*'|\"(?:[^\"\\]|\\.)*\"))"
    r"(?:\s*\)?\s*%)?",
    re.MULTILINE,
)

# Match _mtr('text') - context is "Menu"
_MTR_CALL_RE = re.compile(
    r"_mtr\s*\(\s*"
    r"(?P<text>(?:'''[\s\S]*?'''|\"\"\"[\s\S]*?\"\"\"|'(?:[^'\\]|\\.)*'|\"(?:[^\"\\]|\\.)*\"))",
    re.MULTILINE,
)


def _strip_quotes(s: str) -> str:
    s = s.strip()
    if not s:
        return s
    if s[0] in '"\'':
        q = s[0]
        if s.startswith(q * 3):
            return s[3:-3]
        return s[1:-1]
    return s


def _unescape(s: str) -> str:
    try:
        return bytes(s, 'utf-8').decode('unicode_escape')
    except Exception:
        return s


def extract_strings(root: Path) -> dict[str, set[str]]:
    sources = _collect_sources(root)
    contexts: dict[str, set[str]] = {}
    for path in sources:
        content = path.read_text(encoding='utf-8', errors='replace')
        for m in _TR_CALL_RE.finditer(content):
            ctx = m.group('context')
            text = _unescape(_strip_quotes(m.group('text')))
            if text:
                contexts.setdefault(ctx, set()).add(text)
        for m in _MTR_CALL_RE.finditer(content):
            text = _unescape(_strip_quotes(m.group('text')))
            if text:
                contexts.setdefault('Menu', set()).add(text)
    return contexts


# ---------------------------------------------------------------------------
# .ui form file extraction
# ---------------------------------------------------------------------------
# Properties whose <string> child is user-visible text.
_UI_TRANSLATABLE_PROPS = {
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
}


def _collect_ui_files(root: Path) -> list[Path]:
    files: list[Path] = []
    forms_dir = root / 'modules' / 'pmg_qt' / 'forms'
    if forms_dir.exists():
        files.extend(forms_dir.glob('*.ui'))
    apbs_dir = root / 'data' / 'startup' / 'apbs_gui'
    if apbs_dir.exists():
        files.extend(apbs_dir.glob('*.ui'))
    # any other .ui files in the project (excluding build/install dirs)
    for p in root.rglob('*.ui'):
        if 'build' in p.parts or 'install' in p.parts:
            continue
        if p not in files:
            files.append(p)
    return sorted(set(files))


def _parse_ui(path: Path) -> tuple[str, list[str]]:
    """Parse a .ui file and return (class_name, [translatable_strings, ...])."""
    try:
        tree = ET.parse(path)
    except ET.ParseError:
        return ('', [])
    root = tree.getroot()

    # The <class>...</class> element is the form's class name, used by
    # Qt's QUiLoader as the translation context.
    class_el = root.find('class')
    class_name = (class_el.text or '').strip() if class_el is not None else ''
    if not class_name:
        widget_el = root.find('widget')
        if widget_el is not None:
            class_name = widget_el.get('name', '')
        if not class_name:
            class_name = path.stem

    strings: list[str] = []

    def _extract_from(container):
        for prop in container.iter('property'):
            pname = prop.get('name', '')
            if pname not in _UI_TRANSLATABLE_PROPS:
                continue
            s = prop.find('string')
            if s is None:
                continue
            if s.get('translatable', 'true') == 'false':
                continue
            text = s.text or ''
            if text and text.strip():
                strings.append(text)

    _extract_from(root)
    return class_name, strings


def extract_ui_strings(root: Path) -> dict[str, set[str]]:
    """Extract translatable strings from .ui files.
    Returns {class_name: set_of_strings}.
    """
    contexts: dict[str, set[str]] = {}
    for path in _collect_ui_files(root):
        class_name, strings = _parse_ui(path)
        if not class_name:
            continue
        contexts.setdefault(class_name, set()).update(strings)
    return contexts


def parse_ts(path: Path) -> dict[str, dict[str, str]]:
    """Parse a .ts file. Returns {context: {source: translation_or_None}}.

    translation_or_None is None if the message has type="unfinished" or
    is empty.
    """
    if not path.exists():
        return {}
    try:
        tree = ET.parse(path)
    except ET.ParseError as e:
        print(f"  WARN: failed to parse {path}: {e}", file=sys.stderr)
        return {}

    root_el = tree.getroot()
    out: dict[str, dict[str, str]] = {}
    for ctx in root_el.findall('context'):
        name = ctx.findtext('name', '')
        if not name:
            continue
        msgs = out.setdefault(name, {})
        for msg in ctx.findall('message'):
            source = msg.findtext('source', '')
            if not source:
                continue
            trans_el = msg.find('translation')
            if trans_el is None:
                msgs[source] = ''
                continue
            ttype = trans_el.get('type', '')
            if ttype in ('unfinished', 'obsolete'):
                msgs[source] = ''  # treat as untranslated
            else:
                msgs[source] = trans_el.text or ''
    return out


def build_ts_xml(context: str, translations: dict[str, str]) -> str:
    """Build .ts XML for a single context."""
    lines = []
    lines.append('<?xml version="1.0" encoding="utf-8"?>')
    lines.append('<!DOCTYPE TS>')
    lines.append(f'<TS version="2.1" language="{_LANG}">')
    lines.append('  <context>')
    lines.append(f'    <name>{_xml_escape(context)}</name>')
    for source in sorted(translations):
        trans = translations[source]
        lines.append('    <message>')
        lines.append(f'      <source>{_xml_escape(source)}</source>')
        if trans:
            lines.append(f'      <translation>{_xml_escape(trans)}</translation>')
        else:
            lines.append('      <translation type="unfinished"></translation>')
        lines.append('    </message>')
    lines.append('    </context>')
    lines.append('</TS>')
    return '\n'.join(lines) + '\n'


def _xml_escape(s: str) -> str:
    return (s.replace('&', '&amp;')
             .replace('<', '&lt;')
             .replace('>', '&gt;'))


def merge_and_write(
    ts_path: Path,
    context: str,
    source_strings: set[str],
    translations: dict[str, str],
) -> tuple[int, int]:
    """Merge source_strings into ts_path for the given context.

    Returns (num_total, num_new) where num_new is the count of newly
    added strings (previously missing or unfinished).
    """
    existing = parse_ts(ts_path)
    existing_translations = existing.get(context, {})

    merged: dict[str, str] = {}
    new_count = 0
    for source in source_strings:
        if source in existing_translations and existing_translations[source]:
            merged[source] = existing_translations[source]
        else:
            # Use translation table if available, else empty (unfinished)
            trans = translations.get(source, '')
            if not trans:
                # try fuzzy match: source with normalized whitespace
                trans = translations.get(source.strip(), '')
            if trans:
                new_count += 1
            merged[source] = trans

    # Also preserve existing translations that are NOT in source_strings
    # (they may have been removed from source but we keep them as obsolete)
    for source, trans in existing_translations.items():
        if source not in merged and trans:
            merged[source] = trans

    xml = build_ts_xml(context, merged)
    ts_path.parent.mkdir(parents=True, exist_ok=True)
    ts_path.write_text(xml, encoding='utf-8')
    return len(merged), new_count


_LANG = 'zh_CN'


def main(argv: list[str]) -> int:
    global _LANG
    parser = argparse.ArgumentParser(description="Generate/update .ts files")
    parser.add_argument("--lang", default="zh_CN", help="target language code")
    args = parser.parse_args(argv)
    _LANG = args.lang
    translations = TRANSLATIONS.get(_LANG, {})
    # Merge in UI translations (per-context dict)
    ui_translations = UI_TRANSLATIONS.get(_LANG, {})

    root = _root()
    out_dir = root / "data" / "pmg_qt" / "i18n" / _LANG
    out_dir.mkdir(parents=True, exist_ok=True)

    contexts = extract_strings(root)
    # Merge in strings passed via variables (see _SUPPLEMENTAL_STRINGS)
    for ctx, strings in _SUPPLEMENTAL_STRINGS.items():
        contexts.setdefault(ctx, set()).update(strings)
    # Merge in .ui strings
    ui_contexts = extract_ui_strings(root)
    ui_total = 0
    for ctx, strings in ui_contexts.items():
        contexts.setdefault(ctx, set()).update(strings)
        ui_total += len(strings)
    print(f"Extracted {sum(len(v) for v in contexts.values())} strings "
          f"in {len(contexts)} contexts ({ui_total} from .ui files)")

    total_new = 0
    for context, strings in sorted(contexts.items()):
        # Pick translation table: UI_TRANSLATIONS for Form/Dialog, else TRANSLATIONS
        trans_table = ui_translations.get(context) if context in ("Form", "Dialog") else None
        if trans_table is None:
            trans_table = translations

        # Decide which file to write to
        if context == "Menu":
            # Menu strings are split across menu_*.ts. Each menu string
            # is supposed to go to a specific file (e.g. 'File' -> menu_file.ts).
            # For simplicity, group all menu strings into per-menu files
            # based on MENU_SPLIT, with fallback to menu_misc.ts.
            menu_by_file: dict[str, set[str]] = {}
            for s in strings:
                fname = MENU_SPLIT.get(s, 'menu_misc')
                menu_by_file.setdefault(fname, set()).add(s)
            for fname, s_set in menu_by_file.items():
                ts_path = out_dir / f"{fname}.ts"
                total, new = merge_and_write(
                    ts_path, "Menu", s_set, trans_table)
                print(f"  {fname}.ts ({context}): {total} strings ({new} new)")
                total_new += new
        else:
            fname = CONTEXT_FILES.get(context)
            if fname is None:
                # Unknown context: write to <context_lower>.ts
                fname = context.lower()
            ts_path = out_dir / f"{fname}.ts"
            total, new = merge_and_write(
                ts_path, context, strings, trans_table)
            print(f"  {fname}.ts ({context}): {total} strings ({new} new)")
            total_new += new

    print(f"\nDone. {total_new} new translations added.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
