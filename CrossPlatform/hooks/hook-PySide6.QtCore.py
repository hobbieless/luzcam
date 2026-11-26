"""Keep Qt dependencies and native translations for LuzCam's supported languages."""
from pathlib import Path
from PyInstaller.utils.hooks.qt import add_qt6_dependencies

hiddenimports, binaries, datas = add_qt6_dependencies(__file__)

def needed(item):
    source = Path(item[0])
    if source.suffix.lower() != '.qm':
        return True
    # Qt file names may include a regional suffix (e.g. qtbase_en_GB).
    return any('_' + language in source.stem for language in ('es', 'en'))

datas = [item for item in datas if needed(item)]
