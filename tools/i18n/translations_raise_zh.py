"""zh_CN for messages PyMOL raises or prints from the command layer.

Same rules as translations_console_zh.py, and for the same reason: these go
through ``%``/``.format()``/``+ value`` before they reach the output window, so

  * leading spaces are output layout,
  * trailing spaces matter because the dynamic part is concatenated after
    them ('no such chain: ' + name),
  * placeholder order is positional and may not be rearranged.

check_console_glossary.py enforces all three.
"""

RAISE_ZH = {
    ' CEalign-Error: selection spans multiple objects, cannot create alignment object':
        ' CEalign 错误：选择跨越多个对象，无法创建比对对象',
    " Warning: no atoms for object '{}'": " 警告：对象 '{}' 中没有原子",
    ' Warning: use get_color_indices instead of get_color_tuple(mode={})':
        ' 警告：请改用 get_color_indices，不要使用 get_color_tuple(mode={})',
    ' protonate: added %d hydrogens at pH %.1f (using textbook pKa values)':
        ' protonate：已添加 %d 个氢原子，pH 为 %.1f（使用教科书 pKa 值）',
    ' protonate: added %d hydrogens at pH %.1f':
        ' protonate：已添加 %d 个氢原子，pH 为 %.1f',
    ' tdroll: defined rotations for %d frames, starting at frame %d':
        ' tdroll：已为 %d 帧定义旋转，从第 %d 帧开始',
    '%s format not supported with multisave': '%s 格式不支持 multisave',
    '%s not supported with multisave': '%s 不支持 multisave',
    'Archive must contain a single package.': '压缩包中只能包含一个插件包。',
    'Base pairing result is not returning 0 or 1': '碱基配对结果未返回 0 或 1',
    'COLLADA import not supported by this PyMOL build':
        '此 PyMOL 构建不支持 COLLADA 导入',
    "Can't map regular letters with SHFT.": '无法与 SHFT 一起映射普通字母。',
    "Can't map regular letters.": '无法映射普通字母。',
    'Command disallowed in this file': '此文件不允许该命令',
    'Double stranded bool was not provided to move_new_res':
        '未向 move_new_res 提供双链布尔值',
    'Error: no such menu: ': '错误：没有该菜单： ',
    'Error: unknown keyword mode: ': '错误：未知关键字模式： ',
    'Failed to map alignment to objects': '无法将比对映射到对象',
    'Failed to parse URL: ': '解析 URL 失败： ',
    "File doesn't look like XML": '文件看起来不是 XML',
    'File format not supported for export': '不支持导出为该文件格式',
    'Improper selection of nucleic acid.': '核酸选择无效。',
    'Improperly formatted weights name': '权重名称格式不正确',
    'Movie commands disallowed in this file': '此文件不允许动画相关命令',
    'Mutagenesis Wizard cannot be used with Movie': '突变向导不能与动画模式同时使用',
    'No <source> or <syntaxhighlight> block with cmd.extend found':
        '未找到包含 cmd.extend 的 <source> 或 <syntaxhighlight> 代码块',
    'No helix state selected': '未选择螺旋状态',
    'No objects in selection': '选择中没有对象',
    'No such assembly: "%s"': '未找到该装配体："%s"',
    'Not a valid plugin filename (%s).': '不是有效的插件文件名（%s）。',
    'PSE contains objects which cannot be unpickled (%s)':
        'PSE 含有无法反序列化的对象（%s）',
    'Python expressions disallowed in this file': '此文件不允许 Python 表达式',
    'Qt not available ({}), using GLUT/Tk interface':
        'Qt 不可用（{}），改用 GLUT/Tk 界面',
    'STL export not supported by this PyMOL build': '此 PyMOL 构建不支持 STL 导出',
    'STL import not supported by this PyMOL build': '此 PyMOL 构建不支持 STL 导入',
    "Selection must be pk1 to attach O5' phosphate":
        "必须选择 pk1 才能连接 O5' 磷酸基团",
    'Selection spans multiple object states': '选择跨越多个对象状态',
    'Something went wrong when fitting the new residue.': '拟合新残基时出现问题。',
    'Something went wrong with resv loop in extend_nuc':
        'extend_nuc 中的 resv 循环出现问题',
    "Symmetry-Error: Unrecognized space group symbol '%s'.":
        "对称性错误：无法识别的空间群符号 '%s'。",
    'Unrecognized file format': '无法识别的文件格式',
    "XML file doesn't look like a PDBML file": '该 XML 文件看起来不是 PDBML 文件',
    'ZIP file contains absolute path names': 'ZIP 文件中包含绝对路径名',
    'an object with that name already exists': '同名对象已存在',
    'apbs failed with code ': 'apbs 运行失败，返回码 ',
    'bad view argument; should be a sequence of 18 floats':
        'view 参数无效；应为 18 个浮点数组成的序列',
    'cannot find "szybki" executable, please set OE_DIR environment variable':
        '找不到 "szybki" 可执行程序，请设置 OE_DIR 环境变量',
    'color specification must be a list such as [ 1.0, 0.0, 0.0 ]':
        '颜色指定必须是一个列表，例如 [ 1.0, 0.0, 0.0 ]',
    'could not find collada2gltf': '找不到 collada2gltf',
    'double_stranded_bool is not returning True or False':
        'double_stranded_bool 未返回 True 或 False',
    'dpi > 0 required with unit "%s" (hint: set the "image_dots_per_inch" setting)':
        '单位为 "%s" 时要求 dpi > 0（提示：请设置 "image_dots_per_inch"）',
    'dx file missing': '缺少 dx 文件',
    'failed to open file "%s"': '打开文件失败："%s"',
    'filename must have .txt extension': '文件名必须使用 .txt 扩展名',
    'interpolation must be one of {}': '插值方式必须是以下之一：{}',
    "invalid connection point: must be one atom, name O3' or P":
        "连接点无效：必须是单个原子，且名称为 O3' 或 P",
    'mass is zero': '质量为零',
    'name must not contain dots (%s).': '名称中不得包含圆点（%s）。',
    'need at least 2 selection': '至少需要 2 个选择',
    'need even number of selections': '需要偶数个选择',
    'neither "ffmpeg" nor "convert" available for video encoding':
        '未找到可用于视频编码的 "ffmpeg" 或 "convert"',
    'no PDBx:atom_site nodes found in XML file': 'XML 文件中未找到 PDBx:atom_site 节点',
    'no dataset found': '未找到数据集',
    'no prior image available': '没有可用的上一帧图像',
    'no public objects': '没有公开对象',
    'no such chain: ': '没有该链： ',
    'no such plugin': '没有该插件',
    'no such script: ': '没有该脚本： ',
    "not a valid modifier key: '%s'.": "不是有效的修饰键：'%s'。",
    'pH value %s out of range (0-14)': 'pH 值 %s 超出范围（0-14）',
    'phase name missing': '缺少相位列名',
    'please provide at least 2 colors': '请至少提供 2 种颜色',
    'pmo format not supported anymore': '不再支持 pmo 格式',
    "special '%s' key not found.": "未找到特殊键 '%s'。",
    'trj magic test failed: ': 'trj 魔数校验失败： ',
    "unable to load fragment '%s'.": "无法加载片段 '%s'。",
    'unknown unit, supported units are: ': '未知单位，支持的单位有： ',
    'unsupported file type: ': '不支持的文件类型： ',
    'zipped (%s) trajectories not supported': '不支持压缩的 (%s) 轨迹文件',
    # pymol.colorprinting writes these to the output window too
    " Error-fetch: unable to load '%s'.": " 加载错误：无法加载 '%s'。",
    ' Error: Argument processing aborted due to exception (above).':
        ' 错误：由于上述异常，参数处理已中止。',
    ' Warning: Adjusting frame rate to {} fps (legal values are: {})':
        ' 警告：已将帧率调整为 {} fps（合法取值为：{}）',
    ' Warning: Cannot write to "%s"': ' 警告：无法写入 "%s"',
    ' Warning: Tuple-syntax (parentheses) for viewport is deprecated':
        ' 警告：viewport 的元组语法（括号）已被弃用',
    ' Warning: failed to fetch from %s': ' 警告：无法从 %s 获取',
    'Empty sequence for key "{}"': '键 "{}" 的序列为空',
    'PyMOL: stopped on exception.': 'PyMOL：因异常而停止。',
    'ffmpeg failed with exit status {}': 'ffmpeg 运行失败，退出状态 {}',
    # shortcut.auto_err grammar; the %s category noun is a keyword domain whose
    # choices the user must type in English, so it stays untranslated on purpose
    "Error: unknown %s: '%s'.": "错误：未知的 %s：'%s'。",
    " Choices:\n": " 可选值：\n",
    r"Error: ambiguous %s\n %s": r"错误：%s 存在歧义\n %s",
}
