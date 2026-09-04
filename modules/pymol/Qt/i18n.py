import os

from . import QtCore


def _norm_lang(lang):
    if not lang:
        return ''
    lang = str(lang).strip().replace('-', '_')
    if '.' in lang:
        lang = lang.split('.', 1)[0]
    return lang


def _detect_lang():
    for k in ('PYMOL_LANG', 'LC_ALL', 'LANG'):
        v = os.environ.get(k, '')
        v = _norm_lang(v)
        if v:
            return v
    return _norm_lang(QtCore.QLocale.system().name())


def _translations_dir():
    base = os.environ.get('PYMOL_DATA', '')
    if not base:
        # Try to find data directory relative to this file
        try:
            # __file__ is modules/pymol/Qt/i18n.py
            # root is 3 levels up
            root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
            potential_base = os.path.join(root, 'data')
            if os.path.isdir(potential_base):
                base = potential_base
        except:
            pass
    if not base:
        return ''
    return os.path.join(base, 'pmg_qt', 'i18n')


def _load_first(translator, candidates, directory):
    if not directory:
        return False
    for name in candidates:
        if translator.load(name, directory):
            return True
    return False


def _settings():
    return QtCore.QSettings('PyMOL', 'PyMOL')


def get_preferred_language():
    v = _settings().value('i18n/lang', '')
    v = _norm_lang(v)
    return v


def set_preferred_language(lang):
    _settings().setValue('i18n/lang', _norm_lang(lang))


def install(app, lang=None, domain='pymol'):
    lang = _norm_lang(lang)
    if not lang:
        lang = get_preferred_language()
    if not lang:
        lang = _detect_lang()
    tdir = _translations_dir()

    translators = []

    qt_translator = QtCore.QTranslator(app)
    qt_candidates = []
    if lang:
        qt_candidates.append(f'qtbase_{lang}.qm')
        qt_candidates.append(f'qt_{lang}.qm')
    if qt_candidates:
        li = QtCore.QLibraryInfo
        if hasattr(li, 'path'):
            qtp = li.path(li.LibraryPath.TranslationsPath)
        else:
            qtp = li.location(li.TranslationsPath)
        if _load_first(qt_translator, qt_candidates, qtp):
            translators.append(qt_translator)

    app_translator = QtCore.QTranslator(app)
    app_candidates = []
    if lang:
        # 1. Try language-specific directory (e.g., i18n/zh_CN/*.qm)
        lang_dir = os.path.join(tdir, lang)
        if os.path.isdir(lang_dir):
            for entry in os.listdir(lang_dir):
                if entry.endswith('.qm'):
                    qm_path = os.path.join(lang_dir, entry)
                    t = QtCore.QTranslator(app)
                    if t.load(qm_path):
                        translators.append(t)
        
        # 2. Try legacy single file (e.g., i18n/pymol_zh_CN.qm)
        app_candidates.append(f'{domain}_{lang}.qm')
        app_candidates.append(f'{domain}_{lang.split("_", 1)[0]}.qm')
    
    if app_candidates and _load_first(app_translator, app_candidates, tdir):
        translators.append(app_translator)

    # Re-install translators to ensure correct order
    current_app = QtCore.QCoreApplication.instance()
    for t in getattr(app, '_pymol_translators', []):
        if current_app:
            current_app.removeTranslator(t)

    for t in translators:
        if current_app:
            current_app.installTranslator(t)

    app._pymol_translators = translators
    app._pymol_lang = lang
    return lang


def set_language(app, lang, domain='pymol'):
    for t in getattr(app, '_pymol_translators', []):
        app.removeTranslator(t)
    lang = install(app, lang=lang, domain=domain)
    set_preferred_language(lang)
    return lang


def tr(context, text, disambiguation=None, n=-1):
    return QtCore.QCoreApplication.translate(context, text, disambiguation, n)


# Settings 798-810 (see layer1/SettingInfo.h): viewport texts drawn by
# layer1/ButMode.cpp, which reads them from settings instead of literals.
# Their defaults are the English source strings; when translators are
# installed, push the translated values so the viewport follows the UI
# language.
_VIEWPORT_TEXT_SETTINGS = {
    'mouse_mode_text': 'Mouse Mode ',
    'selecting_text': 'Selecting ',
    'picking_text': 'Picking ',
    'sel_mode_atoms': 'Atoms',
    'sel_mode_residues': 'Residues',
    'sel_mode_chains': 'Chains',
    'sel_mode_segments': 'Segments',
    'sel_mode_objects': 'Objects',
    'sel_mode_molecules': 'Molecules',
    'sel_mode_ca': 'C-alphas',
    'sel_mode_atoms_joints': 'Atoms (and Joints)',
    'movie_frame_text': 'Frame ',
    'movie_state_text': 'State ',
}


def apply_viewport_texts(cmd):
    for setting, source in _VIEWPORT_TEXT_SETTINGS.items():
        translated = tr('Menu', source)
        if translated and translated != source:
            cmd.set(setting, translated, quiet=1)
