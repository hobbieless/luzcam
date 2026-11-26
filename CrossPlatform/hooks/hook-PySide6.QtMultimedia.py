"""Keep Qt Multimedia runtime dependencies with ES/EN native catalogues only."""
from pathlib import Path
from PyInstaller.utils.hooks.qt import add_qt6_dependencies

hiddenimports, binaries, datas = add_qt6_dependencies(__file__)
# Preserve the upstream hook's signature-helper import (explicitly excluded by
# the app build because this application does not use QtMultimediaWidgets).
hiddenimports += ['PySide6.QtMultimediaWidgets']
datas = [item for item in datas if Path(item[0]).suffix.lower() != '.qm'
         or any('_' + language in Path(item[0]).stem for language in ('es', 'en'))]
