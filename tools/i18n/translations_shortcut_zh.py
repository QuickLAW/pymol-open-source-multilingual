"""zh_CN for the Description column of the keyboard-shortcut editor.

The strings live in pymol/shortcut_dict.py as *data*: they are stored in
cmd.shortcut_dict, compared against, and written back, so they must stay
English there. shortcut_menu_gui.py translates them on the way to the widget
instead. tools/i18n/scan_data_tables.py enforces that every value in that table
has an entry here, because no call-site gate can see this pairing.

Residue and fragment codes (ala, nme, ...) stay lowercase-English: they are the
identifiers PyMOL accepts.
"""

SHORTCUT_ZH = {
    'attach ace': '连接 ace',
    'attach acetylene': '连接乙炔基',
    'attach ala': '连接 ala',
    'attach amide C->N': '连接酰胺 C->N',
    'attach amide N->C': '连接酰胺 N->C',
    'attach arg': '连接 arg',
    'attach asn': '连接 asn',
    'attach asp': '连接 asp',
    'attach benzene': '连接苯基',
    'attach cyclobutane': '连接环丁烷',
    'attach cycloheptane': '连接环庚烷',
    'attach cyclohexane': '连接环己烷',
    'attach cyclopentadiene': '连接环戊二烯',
    'attach cyclopentane': '连接环戊烷',
    'attach cys': '连接 cys',
    'attach formaldehyde': '连接甲醛',
    'attach gln': '连接 gln',
    'attach glu': '连接 glu',
    'attach gly': '连接 gly',
    'attach his': '连接 his',
    'attach ile': '连接 ile',
    'attach leu': '连接 leu',
    'attach lys': '连接 lys',
    'attach met': '连接 met',
    'attach nme': '连接 nme',
    'attach phe': '连接 phe',
    'attach pro': '连接 pro',
    'attach ser': '连接 ser',
    'attach sulfone': '连接砜基',
    'attach thr': '连接 thr',
    'attach trp': '连接 trp',
    'attach tyr': '连接 tyr',
    'attach val': '连接 val',
    'auto measure': '自动测量',
    'copy': '复制',
    'create bond': '创建化学键',
    'cut': '剪切',
    'find': '查找',
    'help': '帮助',
    'insert scene after current': '在当前场景后插入场景',
    'insert scene before current': '在当前场景前插入场景',
    'invert selection': '反选',
    'last scene': '末尾场景',
    'next movie frame': '下一电影帧',
    'next scene': '下一个场景',
    'paste': '粘贴',
    'play/pause movie': '播放/暂停电影',
    'previous movie frame': '上一电影帧',
    'previous scene': '上一个场景',
    'select all': '全选',
    'store auto scene': '存储自动场景',
    'store new scene': '存储新场景',
    'zoom all': '缩放至全部',
    'zoom next ligand': '缩放到下一个配体',
}
