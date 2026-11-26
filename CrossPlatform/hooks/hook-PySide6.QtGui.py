"""LuzCam only loads bundled PNG/JPEG art and icons; no PDF/document importer."""
from PyInstaller.utils.hooks.qt import add_qt6_dependencies
hiddenimports,binaries,datas=add_qt6_dependencies(__file__)
def needed(item):
    name=item[0].replace('\\','/').lower()
    # This Widgets app has no QML/Qt Virtual Keyboard or SVG inputs. Keep
    # native platform input handling, but omit the optional plugin chains.
    if 'qtvirtualkeyboardplugin' in name:return False
    if '/iconengines/' in name and name.rsplit('/',1)[-1].startswith(('qsvgicon','libqsvgicon')):return False
    if '/imageformats/' not in name:return True
    return any(x in name for x in ('qjpeg','qico'))
binaries=[item for item in binaries if needed(item)]
