"""Shared Windows and Mac runtime profiles use their documented dependency pins."""
from pathlib import Path
from importlib.metadata import version
from PySide6.QtCore import qVersion
root=Path(__file__).resolve().parents[1]
def pins(file):
    return dict(line.strip().split('==') for line in file.read_text(encoding='utf8').splitlines() if '==' in line and not line.startswith('#'))
common=pins(root/'CrossPlatform/requirements.txt')
build_file=root/'CrossPlatform/requirements-build.txt'
assert '-r requirements.txt' in build_file.read_text(encoding='utf8')
assert pins(build_file)['PyInstaller']=='6.22.3'
mac=pins(root/'CrossPlatform/requirements-macos12.txt')
assert mac['PySide6']=='6.8.3' and mac['numpy']=='1.26.4'
for name,wanted in common.items():assert version(name)==wanted,(name,version(name),wanted)
assert qVersion()==common['PySide6']
print('PASS: desktop runtime matches common pins; build and Mac profiles are consistent')
