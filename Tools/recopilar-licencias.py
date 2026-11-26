"""Collect installed component metadata and available license texts, without granting rights."""
from importlib.metadata import distribution
from pathlib import Path
import argparse,json,shutil,sys,hashlib

ROOT=Path(__file__).resolve().parents[1]
parser=argparse.ArgumentParser();parser.add_argument('output',type=Path);args=parser.parse_args()
out=args.output;out.mkdir(parents=True,exist_ok=True);inventory=[]
for name in ['PySide6','PySide6_Essentials','PySide6_Addons','shiboken6','numpy','Pillow','PyInstaller']:
    d=distribution(name);copied=[]
    for item in d.files or []:
        if not any(x in str(item).lower() for x in ('license','copying','notice')):continue
        source=Path(d.locate_file(item))
        if not source.is_file():continue
        # Keep wheel-relative names below their component directory.
        target=out/name/Path(*[p for p in Path(item).parts if p not in ('..','/','\\')])
        target.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(source,target)
        copied.append(target.relative_to(out).as_posix())
    inventory.append({'name':d.metadata['Name'],'version':d.version,
                      'licenseExpression':d.metadata.get('License-Expression'),
                      'declaredLicense':d.metadata.get('License'),'texts':copied,
                      'scope':'build/bootloader' if name=='PyInstaller' else 'runtime'})
for source in (ROOT/'CrossPlatform/luzcam/fonts').glob('*OFL.txt'):
    target=out/'fonts'/source.name;target.parent.mkdir(exist_ok=True);shutil.copy2(source,target)
for name in ('LICENSE.txt','LICENSE'):
    source=Path(sys.base_prefix)/name
    if source.is_file():shutil.copy2(source,out/'PYTHON-LICENSE.txt');break
# Include the exact, previously reviewed tag texts instead of leaving them
# only in the development repository. They are not a native dependency SBOM.
base=ROOT/'docs/legal/licencias-base'
origins=json.loads((base/'sources.json').read_text(encoding='utf8'))
for record in origins['records']:
    source=base/record['file']
    if source.parent!=base or hashlib.sha256(source.read_bytes()).hexdigest()!=record['sha256']:
        raise SystemExit('Native license provenance mismatch: '+record['file'])
    target=out/'native-base'/record['file'];target.parent.mkdir(exist_ok=True);shutil.copy2(source,target)
shutil.copy2(base/'sources.json',out/'native-base/sources.json')
notices=ROOT/('docs/legal/qt-native-notices-'+distribution('PySide6').version)
notice_manifest=json.loads((notices/'manifest.json').read_text(encoding='utf8'))
if notice_manifest['version']!=distribution('PySide6').version:
    raise SystemExit('Qt notice version differs from installed PySide6: collect the exact tag first')
if notice_manifest['unresolvedLicenseFiles']:
    raise SystemExit('Qt notice collection has unresolved license references')
for record in notice_manifest['files']:
    source=(notices/record['path']).resolve()
    if not source.is_relative_to(notices.resolve()) or hashlib.sha256(source.read_bytes()).hexdigest()!=record['sha256']:
        raise SystemExit('Qt notice integrity mismatch: '+record['path'])
    target=out/'qt-native-notices'/record['path'];target.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(source,target)
shutil.copy2(notices/'manifest.json',out/'qt-native-notices/manifest.json')
supplement=ROOT/'docs/legal/native-supplement'
supplement_manifest=json.loads((supplement/'manifest.json').read_text(encoding='utf8'))
for record in supplement_manifest['files']:
    source=(supplement/record['path']).resolve()
    if not source.is_relative_to(supplement.resolve()) or hashlib.sha256(source.read_bytes()).hexdigest()!=record['sha256']:
        raise SystemExit('Native supplement integrity mismatch: '+record['path'])
    target=out/'native-supplement'/record['path'];target.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(source,target)
shutil.copy2(supplement/'manifest.json',out/'native-supplement/manifest.json')
(out/'components.json').write_text(json.dumps({'python':sys.version,'components':inventory,
    'nativeBaseTexts':origins['records'],
    'qtNativeNotices':{'version':notice_manifest['version'],'files':len(notice_manifest['files']),
        'attributions':len(notice_manifest['components']),'scope':notice_manifest['scope'],
        'index':'qt-native-notices/manifest.json','binaryInclusionVerified':False},
    'nativeSupplement':supplement_manifest,
    'projectCodeLicense':'GPL-3.0-only','reviewComplete':False,'pending':['Complete corresponding-source assessment, including exact Qt/FFmpeg modifications and relinking/install information',
    'Verify remaining native Python, NumPy/OpenBLAS and vendor binary provenance/licence mapping','Verify installation and certification checks for each remaining target platform',
    'Publish the exact corresponding sources and review the final release notices']},indent=2),encoding='utf8')
(out/'README.txt').write_text('LuzCam: inventario de componentes y textos disponibles en este entorno.\n'
    'NO es una autorización ni una revisión completa de licencias.\n'
    'Antes de distribuir: cerrar fuentes correspondientes y opciones de relink de Qt/LGPL y FFmpeg,\n'
    'origen/licencias de componentes nativos, y pruebas de instalacion del paquete por plataforma.\n'
    'Codigo original de LuzCam: GPLv3, elegida por el propietario. El propietario confirma que las imagenes son originales generados para LuzCam.\n',encoding='utf8')
print('Collected license evidence:',out)
