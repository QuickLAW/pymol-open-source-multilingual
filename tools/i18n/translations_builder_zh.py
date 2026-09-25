"""zh_CN for the Builder panel's tooltips and the security wizard's prompt.

Both live in data tables rather than at a call site, so no call-site gate can
see them; scan_data_tables.py registers them and enforces that every value has
an entry here.

Residue and atom-selection tokens that the user has to type (pk1, Ala as a
selection word, "set security,off", "accept"/"decline"/"mdump") stay English
inside the translated sentence. The banner rows keep their '=' rules at the
same width so the block still lines up.
"""

BUILDER_ZH = {
    # elements
    'Hydrogen': '氢',
    'Carbon': '碳',
    'Nitrogen': '氮',
    'Oxygen': '氧',
    'Phosphorus': '磷',
    'Sulfur': '硫',
    'Fluorine': '氟',
    'Chlorrine': '氯',          # (spelled "Chlorrine" in the source)
    'Bromine': '溴',
    'Iodine': '碘',
    # groups and linkers
    'Trifluoromethane': '三氟甲烷',
    'Methanol': '甲醇',
    'Methyl': '甲基',
    'Ethylene': '乙烯',
    'Acetylene': '乙炔',
    'Cyanide': '氰基',
    'Aldehyde': '醛',
    'Formic Acid': '甲酸',
    'C->N amide': 'C->N 酰胺',
    'N->C amide': 'N->C 酰胺',
    'Sulfone': '砜',
    'Phosphite': '亚磷酸酯',
    'Nitro': '硝基',
    'Cyclopropane': '环丙烷',
    'Cyclobutane': '环丁烷',
    'Cyclopentane': '环戊烷',
    'Cyclohexane': '环己烷',
    'Cycloheptane': '环庚烷',
    'Cyclopentadiene': '环戊二烯',
    'Benzene': '苯',
    'Indane': '茚满',
    'Napthylene': '萘',          # (spelled "Napthylene" in the source)
    'Benzocycloheptane': '苯并环庚烷',
    # nucleosides and bases
    'Deoxyadenosine': '脱氧腺苷',
    'Deoxycytidine': '脱氧胞苷',
    'Deoxythymidine': '脱氧胸苷',
    'Deoxyguanosine': '脱氧鸟苷',
    'Adenosine': '腺苷',
    'Cytosine': '胞嘧啶',
    'Guanine': '鸟嘌呤',
    'Uracil': '尿嘧啶',
    # amino acids shown as tooltips on the one-letter buttons
    'Ala': '丙氨酸',
    'Met': '甲硫氨酸',
    # editing actions
    'Add hydrogens to entire molecule': '为整个分子添加氢原子',
    'Cleanup structure': '清理结构',
    'Create aromatic bond': '创建芳香键',
    'Create bond between pk1 and pk2': '在 pk1 与 pk2 之间创建化学键',
    'Create double bond': '创建双键',
    'Create single bond': '创建单键',
    'Create triple bond': '创建三键',
    'Cycle bond valence': '循环切换键价',
    'Delete bond between pk1 and pk2': '删除 pk1 与 pk2 之间的化学键',
    'Delete everything': '删除所有内容',
    "Electrostatics term for 'Clean' action": '执行"清理"时使用的静电项',
    'Fix atom positions': '固定原子位置',
    'Fix hydrogens on picked atoms': '固定所选原子上的氢原子',
    'Invert stereochemistry around pk1 (pk2 and pk3 will remain fixed)':
        '反转 pk1 周围的立体构型（pk2 与 pk3 保持固定）',
    'Molecular sculpting': '分子雕刻',
    'Negative Charge': '负电荷',
    'Neutral Charge': '中性电荷',
    'Positive Charge': '正电荷',
    'Redo last change': '重做上次修改',
    'Undo last change': '撤销上次修改',
    'Remove atoms': '删除原子',
    'Remove residue': '删除残基',
    'Restrain atom positions': '约束原子位置',
    'Show VDW contacts during sculpting': '雕刻时显示范德华接触',
}

SECURITY_ZH = {
    # keep the rule width so the block still lines up with the untranslated
    # '=====' separator rows
    '========================= PyMOL SECURITY WARNING =========================':
        '=========================== PyMOL 安全警告 ===========================',
    'CAUTION! Do you know and trust the person who created this session file? ':
        '注意！您是否了解并信任创建此会话文件的人？ ',
    'It contains GENERAL PURPOSE movie commands which could be used':
        '其中包含通用电影命令，可能被恶意利用，',
    'maliciously to take control your of computer or damage your files.':
        '从而控制您的计算机或破坏您的文件。',
    'Click or enter "accept" to assume the risks of running the commands.':
        '点击或输入 "accept" 以自行承担运行这些命令的风险。',
    'Click or enter "decline" to decline the risks and delete the commands.':
        '点击或输入 "decline" 以拒绝承担风险并删除这些命令。',
    'Click or enter "mdump" to print out the commands in the movie.':
        '点击或输入 "mdump" 以打印电影中包含的命令。',
    'To avoid this message in the future, "set security,off" before loading':
        '若希望今后不再出现此提示，请在加载会话文件前执行 "set security,off"，',
    'the session file, or just launch pymol with the "-o" option.':
        '或者在启动 pymol 时使用 "-o" 选项。',
}
