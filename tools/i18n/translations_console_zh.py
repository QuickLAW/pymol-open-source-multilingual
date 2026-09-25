"""zh_CN glossary for PyMOL's output-window ("Console") messages.

Keys are the exact literals pymol.console_i18n.ctr() passes to
QCoreApplication.translate(), which for an implicitly-concatenated literal is
the joined string. Three invariants, because these go through ``%``:

  * leading and trailing spaces are output layout -- keep them;
  * the ORDER of %s/%d/%.3f specifiers is positional, so a translation may
    not reorder them even when that reads worse in Chinese;
  * command names, setting names and identifiers stay English, since the
    user has to type them.

tools/i18n/check_console_glossary.py enforces all three.
"""

CONSOLE_ZH = {
    '       PyMOL should be able to read this, plese send the file and this mesage to ':
        '       PyMOL 本应能够读取此文件，请将文件和这条消息发送至 ',
    '       with the values for 2FoFc and FoFc, amplitude and phase names, respectively.':
        '       分别填写 2FoFc 与 FoFc 的振幅和相位列名。',
    ' Adapting to FireGL hardware.': ' 正在适配 FireGL 硬件。',
    ' Adapting to Quadro hardware.': ' 正在适配 Quadro 硬件。',
    ' Adjusting settings to improve performance for ATI cards.':
        ' 正在调整设置以提升 ATI 显卡的性能。',
    ' Altered %d MSE residues to MET': ' 已将 %d 个 MSE 残基改为 MET',
    ' Center of Mass: [%8.3f,%8.3f,%8.3f]': ' 质心：[%8.3f,%8.3f,%8.3f]',
    ' Copied %d atoms to object %s': ' 已复制 %d 个原子到对象 %s',
    ' Density-Wizard: Please pick an atom first.': ' 密度向导：请先拾取一个原子。',
    ' Detected blacklisted graphics driver.  Disabling shaders.':
        ' 检测到黑名单中的显卡驱动。正在禁用着色器。',
    ' Disabling shaders for Intel Express graphics':
        ' 正在为 Intel Express 集成显卡禁用着色器',
    ' Dragging %s atoms in object "%s".': ' 正在拖动对象 "%s" 中的 %s 个原子。',
    ' Dragging whole object "%s".': ' 正在拖动整个对象 "%s"。',
    ' Enabled multithreaded rendering.': ' 已启用多线程渲染。',
    ' Error: Map generation failed': ' 错误：密度图生成失败',
    ' Error: could not chdir to': ' 错误：无法切换工作目录到',
    ' Error: must provide an object name': ' 错误：必须提供对象名称',
    " Error: unrecognized mouse ring: '%s'": " 错误：无法识别的鼠标滚轮动作：'%s'",
    ' Error: you must first pick an atom to replace.':
        ' 错误：您必须先拾取一个要替换的原子。',
    ' Filter-Error: No matching compounds.': ' 筛选器错误：没有匹配的化合物。',
    ' Filter-Error: Please choose an object first': ' 筛选器错误：请先选择一个对象',
    " Filter-Error: Unable to write '%s'.": " 筛选器错误：无法写入 '%s'。",
    ' Filter-Error: please choose an object first': ' 筛选器错误：请先选择一个对象',
    ' Filter-Warning: attempting to write in home directory.':
        ' 筛选器警告：正尝试写入主目录。',
    ' Filter: Browsing accepted compounds.': ' 筛选器：正在浏览已接受的化合物。',
    ' Filter: Browsing all compounds.': ' 筛选器：正在浏览全部化合物。',
    ' Filter: Browsing deferred compounds.': ' 筛选器：正在浏览已暂缓的化合物。',
    ' Filter: Browsing rejected compounds.': ' 筛选器：正在浏览已拒绝的化合物。',
    ' Filter: Browsing remaining compounds': ' 筛选器：正在浏览剩余的化合物',
    ' Generating a %d residue peptide from sequence...':
        ' 正在根据序列生成含 %d 个残基的多肽...',
    ' MapGenerate-Error: Cannot import headering module.  Cannot read MTZ file or make map.':
        ' 密度图生成错误：无法导入 headering 模块，因此无法读取 MTZ 文件或生成密度图。',
    " MapGenerate-Error: Could not find file '%s'.\n Please check the filename and try again.":
        " 密度图生成错误：找不到文件 '%s'。\n 请检查文件名后重试。",
    ' Mutagenesis: no rotamers found in library.': ' 突变向导：旋转构象库中未找到旋转异构体。',
    ' Mutagenesis: object not found.': ' 突变向导：未找到对象。',
    " No key mapping and no scene or view for '%s'":
        " 没有 '%s' 的按键映射，也没有对应的场景或视图",
    " No key mapping for '%s'": " 没有 '%s' 的按键映射",
    ' OpenGL graphics engine:': ' OpenGL 图形引擎：',
    ' PyMOL-HTTPd: serving requests on http://localhost:%d':
        ' PyMOL-HTTPd：正在 http://localhost:%d 上处理请求',
    ' Report attempt may have failed.': ' 上报可能已失败。',
    " Reporting back pymol port via: '%s'": " 正在通过以下途径上报 PyMOL 端口：'%s'",
    ' Save-Error: no file written': ' 保存错误：未写入任何文件',
    ' Save: Please wait -- writing session file...':
        ' 保存：请稍候 -- 正在写入会话文件...',
    ' Spectrum: Expression is non-numeric, enumerating values':
        ' 光谱着色：表达式非数值型，将逐个枚举取值',
    ' Using Python 2 compatible legacy pickler':
        ' 正在使用兼容 Python 2 的旧式 pickle 序列化器',
    ' Util: Assigning Amber 99 charges and radii...':
        ' 工具：正在指定 Amber 99 电荷与半径...',
    ' Util: Calculating electrostatic potential...': ' 工具：正在计算静电势...',
    ' Util: Fixing termini and assigning formal charges...':
        ' 工具：正在修补末端并指定形式电荷...',
    " WARNING: formal and partial charge sums don't match -- there is a problem!":
        " 警告：形式电荷与部分电荷之和不一致 -- 存在问题！",
    ' WARNING: some unassigned atoms are being deleted:':
        ' 警告：正在删除若干未指定参数的原子：',
    ' WARNING: unrecognized or incomplete residues are being deleted:':
        ' 警告：正在删除无法识别或不完整的残基：',
    ' Warning: --nospnav not available in Open-Source PyMOL':
        ' 警告：开源版 PyMOL 不支持 --nospnav',
    ' Warning: No atoms in state %d for object %s':
        ' 警告：状态 %d 中的对象 %s 没有原子',
    ' Warning: SCHRODINGER environment variable not set':
        ' 警告：未设置 SCHRODINGER 环境变量',
    ' Warning: failed to backport session:': ' 警告：无法将会话降级保存：',
    ' Warning: failed to connect to recent DB:': ' 警告：无法连接最近文件数据库：',
    ' Warning: failed to query "My Documents" from registry':
        ' 警告：无法从注册表查询 "My Documents"',
    ' Warning: group and object arguments given': ' 警告：同时给出了组参数和对象参数',
    ' Warning: no coordinates for atom': ' 警告：该原子没有坐标',
    ' Warning: non-boolean extract values are deprecated!':
        ' 警告：非布尔型的 extract 取值已被弃用！',
    ' Warning: retry with grid =': ' 警告：请调整 grid 后重试 =',
    ' Warning: use get_color_index instead of get_color_tuple(mode=3)':
        ' 警告：请改用 get_color_index，不要使用 get_color_tuple(mode=3)',
    ' Wizard: No neighbors found.': ' 向导：未找到邻近残基。',
    ' Written results to %s': ' 已将结果写入 %s',
    ' cache: no scenes defined -- optimizing current display.':
        ' 缓存：未定义任何场景 -- 正在优化当前显示。',
    ' cmd.intra_fit: %5.3f in state %d vs mixed target':
        ' cmd.intra_fit：%5.3f（状态 %d，对照混合目标）',
    ' feedback: Please specify masks:': ' feedback：请指定掩码（mask）：',
    ' feedback: Please specify module names:': ' feedback：请指定模块名称：',
    ' get_symmetry: No symmetry defined.': ' get_symmetry：未定义对称性。',
    ' get_view: matrix written to log file.': ' get_view：矩阵已写入日志文件。',
    ' get_viewport: data written to log file.': ' get_viewport：数据已写入日志文件。',
    ' parser: no matching files.': ' 解析器：没有匹配的文件。',
    ' protonate: pdb2pqr not found, using textbook pKa values':
        ' protonate：未找到 pdb2pqr，改用教科书 pKa 值',
    'CEalign-Error: Your mobile selection is too short.':
        'CEalign 错误：您的动体（mobile）选择太短。',
    'CEalign-Error: Your target selection is too short.':
        'CEalign 错误：您的目标（target）选择太短。',
    'CEalign-Error: window size must be an integer greater than 2.':
        'CEalign 错误：窗口大小必须是大于 2 的整数。',
    'Current residue is the end of a chain.': '当前残基位于某条链的末端。',
    'Diagnostics written to "%s"': '诊断信息已写入 "%s"',
    'Double helix RNA building is not currently supported.':
        '目前不支持构建 RNA 双螺旋。',
    "Error Parsing MTZ Header: bad column name: '%s'":
        "解析 MTZ 头信息出错：无效的列名：'%s'",
    "Error: File '%s' cannot be parsed because PyMOL cannot find the header.  If you think":
        "错误：无法解析文件 '%s'，因为 PyMOL 找不到文件头。如果您认为",
    'Error: Parsing MTZ Header poorly formatted MTZ file':
        '错误：解析 MTZ 头信息失败，MTZ 文件格式不规范',
    "Error: Please provide the setting 'default_%s_names' a comma separated string":
        "错误：请为设置 'default_%s_names' 提供一个以逗号分隔的字符串",
    'Error: Python blocks disallowed in this file.':
        '错误：此文件不允许包含 Python 代码块。',
    "Error: ambiguous feedback action '%s'.": "错误：feedback 动作 '%s' 存在歧义。",
    "Error: ambiguous feedback mask '%s'.": "错误：feedback 掩码 '%s' 存在歧义。",
    "Error: ambiguous feedback module '%s'.": "错误：feedback 模块 '%s' 存在歧义。",
    'Error: an object with than name already exists': '错误：同名对象已存在',
    'Error: embed only legal in special files (e.g. p1m)':
        '错误：仅允许在特定文件（如 p1m）中嵌入',
    'Error: invalid arguments for %s command.': '错误：%s 命令的参数无效。',
    "Error: invalid connection point: must be C for residue '%s'":
        "错误：连接点无效：残基 '%s' 必须使用 C 原子",
    "Error: invalid connection point: must be N for residue '%s'":
        "错误：连接点无效：残基 '%s' 必须使用 N 原子",
    'Error: invalid connection point: must be one atom, name N or C.':
        '错误：连接点无效：必须是单个原子，且名称为 N 或 C。',
    "Error: invalid feedback action '%s'.": "错误：无效的 feedback 动作 '%s'。",
    "Error: invalid feedback mask '%s'.": "错误：无效的 feedback 掩码 '%s'。",
    "Error: invalid feedback module '%s'.": "错误：无效的 feedback 模块 '%s'。",
    'Error: missing path to root content': '错误：缺少指向根内容的路径',
    'Error: no matching files': '错误：没有匹配的文件',
    'Error: please pick a nitrogen or carbonyl carbon to grow from.':
        '错误：请拾取一个氮原子或羰基碳作为生长起点。',
    "Error: requested path '%s' does not exist.": "错误：所请求的路径 '%s' 不存在。",
    'Error: sorry no help available on that command.':
        '错误：抱歉，该命令没有可用的帮助信息。',
    'Error: unable to attach fragment.': '错误：无法连接片段。',
    'Error: unable to handle PWG file': '错误：无法处理 PWG 文件',
    "Error: unable to launch web application'%s'.": "错误：无法启动 Web 应用 '%s'。",
    "Error: unable to open log file '%s'": "错误：无法打开日志文件 '%s'",
    'Identified bond targets were too far apart, so this will not be bound':
        '识别到的成键目标相距过远，因此不会成键',
    "Improper Auto Center setting. 'ON' or 'OFF' accepted only":
        "自动居中设置无效，仅接受 'ON' 或 'OFF'",
    'Improper Nucleic Acid': '核酸类型无效',
    'Incorrect type found when resetting defaults': '重置默认值时发现类型不正确',
    "Load-Error: Unable to load file '%s'.": "加载错误：无法加载文件 '%s'。",
    'More than one bond target was found on opposing chain, so this will not be bound.':
        '在互补链上找到多个成键目标，因此不会成键。',
    'More than one bond target was found on selected chain, so this will not be bound.':
        '在所选链上找到多个成键目标，因此不会成键。',
    'More than one bond target was identified, so this will not be bound':
        '识别到多个成键目标，因此不会成键',
    'Multiple residues meet base pairing requirements. Building as if no opposing strand detected.':
        '有多个残基满足碱基配对要求，将按未检测到互补链的方式构建。',
    'No active selection': '没有活动选择',
    'No based pair was found on chain ': '该链上未找到碱基配对 ',
    'No shortcut save file has been loaded.': '尚未加载任何快捷键保存文件。',
    'Nothing on clipboard': '剪贴板为空',
    'Phosphate has been successfully added': '磷酸基团已成功添加',
    'PyMOL Command Reference written to %s': 'PyMOL 命令参考已写入 %s',
    'Restored default keybindings': '已恢复默认按键绑定',
    'Saved shortcuts to file ': '已将快捷键保存至文件 ',
    'Session-Warning: unable to restore wizard.': '会话警告：无法恢复向导状态。',
    'The program did not detect a double stranded structure, so the opposing residue will not be attached.':
        '程序未检测到双链结构，因此不会连接互补残基。',
    "This building selection has an unphosphorylated O5' end.":
        "当前构建选择含有一个未磷酸化的 O5' 末端。",
    'This cannot be bound.': '此处无法成键。',
    'This key is reserved.': '该按键已被保留。',
    'Unable to save to file.': '无法保存到文件。',
    'Warning: --retina option has been removed': '警告：--retina 选项已被移除',
    'Warning: Byte order of file unknown.  Guessing header location.':
        '警告：无法确定文件字节序，正在推测文件头位置。',
    "Warning: use 'run' instead of '@' with Python files?":
        "警告：Python 文件请改用 'run' 而不是 '@'？",
    'Your "fetch_path" setting might point to a read-only directory':
        '您的 "fetch_path" 设置可能指向只读目录',
    'Z chain was detected. New chain will append A': '检测到 Z 链。新链将追加至 A',
    'action=ungroup is deprecated, use the "ungroup" command':
        'action=ungroup 已被弃用，请使用 "ungroup" 命令',
    'check_DNA_base_pair has no opposing residue to check':
        'check_DNA_base_pair 没有可供检查的互补残基',
    "cmd-Error: The 'pk1' selection is undefined.": "命令错误：'pk1' 选择未定义。",
    "cmd-Error: The 'pk2' selection is undefined.": "命令错误：'pk2' 选择未定义。",
    "cmd-Error: The 'pk3' selection is undefined.": "命令错误：'pk3' 选择未定义。",
    "cmd-Error: The 'pk4' selection is undefined.": "命令错误：'pk4' 选择未定义。",
    'cmd-Error: atom %s not found by id_atom.': '命令错误：id_atom 未找到原子 %s。',
    'cmd-Error: multiple atoms %s found by id_atom.':
        '命令错误：id_atom 找到多个原子 %s。',
    'import socket failed': '导入 socket 失败',
    'no prior image available, fall back to rendering':
        '没有可用的上一帧图像，将回退为重新渲染',
    'produce-error: Unable to create mpeg file.': '生成错误：无法创建 mpeg 文件。',
    'produce-error: Unable to import module pymol.mpeg_encode.':
        '生成错误：无法导入模块 pymol.mpeg_encode。',
    'produce-error: Unable to validate pymol.mpeg_encode.':
        '生成错误：无法校验 pymol.mpeg_encode。',
    'xml-rpc server could not be started': 'xml-rpc 服务器无法启动',
    'xml-rpc server running on host %s, port %d':
        'xml-rpc 服务器已在主机 %s、端口 %d 上运行',
    'z chain was detected. New chain will append a': '检测到 z 链。新链将追加至 a',
}
