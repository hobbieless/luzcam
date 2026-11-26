"""The autonomous delivery contains exactly the reviewed runtime resources."""
from pathlib import Path
import json
root=Path(__file__).resolve().parents[1];manifest=json.loads((root/'CrossPlatform/runtime-resources.json').read_text(encoding='utf8'));files=manifest['files']
assert len(files)==len(set(files))==18
for name in files:
 path=Path(name);assert not path.is_absolute() and '..' not in path.parts;assert (root/path).is_file()
assert 'Portable/parity-v1.json' not in files
assert all(not name.endswith('.png') for name in files if name.startswith('CameraArt/'))
s=(root/'CrossPlatform/luzcam/ui.py').read_text(encoding='utf8')
assert 'registered_sensor_patch' not in s and 'prism_housing_patch' not in s and 'layout=LAYOUTS' not in s
print('PASS: 18 required local resources, no old camera plates/parity/catalogues, no obsolete camera initialization')
