"""Build on the target OS, keeping shared resources outside the executable."""
import subprocess,sys,shutil,hashlib,json,platform,argparse,os
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from importlib.metadata import version
root=Path(__file__).resolve().parents[1]
out=root/'build'/'portable-light'
runtime=root/'build'/'runtime'
parser=argparse.ArgumentParser()
parser.add_argument('--resources-only',action='store_true',help='Resume resource copying for an already built executable.')
parser.add_argument('--output',type=Path,help='Write a separate package without replacing a running version.')
parser.add_argument('--reuse-runtime',action='store_true',help='Package the runtime just built on this system without rebuilding it.')
parser.add_argument('--macos-12-compatibility',action='store_true',help='Use the pinned Mac runtime profile compatible with macOS 12+; same app source, distinct runtime.')
args=parser.parse_args()
if args.macos_12_compatibility and sys.platform!='darwin':parser.error('--macos-12-compatibility is available only on macOS')
profile=root/'CrossPlatform'/('requirements-macos12.txt' if args.macos_12_compatibility else 'requirements.txt')
for line in profile.read_text().splitlines():
 if '==' in line and not line.startswith('#'):
  name,wanted=line.split('==');installed=version(name)
  if installed!=wanted:raise SystemExit(f'Dependency mismatch {name}: {installed}, expected {wanted} from {profile.name}')
dependency_versions={name:version(name) for name in ('PySide6','PySide6_Essentials','PySide6_Addons','shiboken6','numpy','Pillow','PyInstaller')}
if args.output: out=args.output.resolve()
def source_fingerprints():
 sources=[root/'CrossPlatform/runtime-resources.json',root/'CrossPlatform/main.py',root/'CrossPlatform/build-desktop.py',root/'CrossPlatform/requirements.txt',profile]
 sources += [root/name for name in ('LICENSE','COPYRIGHT.md','CREDITS.md')]
 sources += [root/'Tools/recopilar-licencias.py']+sorted((root/'docs/legal/licencias-base').glob('*'))
 sources += sorted(p for p in (root/('docs/legal/qt-native-notices-'+dependency_versions['PySide6'])).rglob('*') if p.is_file())
 sources += sorted(p for p in (root/'docs/legal/native-supplement').rglob('*') if p.is_file())
 sources += sorted((root/'CrossPlatform/hooks').glob('*.py'))
 sources += [root/'CrossPlatform/windows-app.manifest']
 sources += sorted(p for p in (root/'CrossPlatform/luzcam').rglob('*') if p.is_file() and p.suffix in ('.py','.json','.ttf','.txt','.png','.ico','.icns'))
 return {p.relative_to(root).as_posix():hashlib.sha256(p.read_bytes()).hexdigest() for p in sources}
build_sources=source_fingerprints()
origin_file=runtime/'build-origin.json'
if args.reuse_runtime or args.resources_only:
 if not origin_file.is_file() or json.loads(origin_file.read_text())['sources']!=build_sources or json.loads(origin_file.read_text()).get('dependencies')!=dependency_versions:
  raise SystemExit('Runtime provenance missing or sources changed: run a full build before reusing it.')
if not args.resources_only and not args.reuse_runtime:
 build_env=os.environ.copy()
 for name in ('PYTHONHOME','PYTHONPATH','QT_PLUGIN_PATH','QT_QPA_PLATFORM_PLUGIN_PATH'):
  build_env.pop(name,None)
 if sys.platform=='win32':
  # Host tools (e.g. Poppler) can carry an incompatible icuuc.dll on PATH.
  # Let Qt resolve Windows system ICU rather than shipping an unrelated DLL.
  windows=Path(os.environ.get('SystemRoot','C:/Windows'))
  build_env['PATH']=os.pathsep.join(map(str,(Path(sys.executable).parent,Path(sys.base_prefix),windows/'System32',windows)))
 version_args=[]
 if sys.platform=='win32':
  info=json.loads((root/'CrossPlatform/luzcam/release-info.json').read_text(encoding='utf8'))
  version=tuple(info['windowsVersion']);version_file=root/'build/windows-version.txt';version_file.parent.mkdir(parents=True,exist_ok=True)
  fields={'CompanyName':info['publisher'],'FileDescription':info['product'],'FileVersion':'.'.join(map(str,version)),'ProductName':info['product'],'ProductVersion':info['version'],'OriginalFilename':'LuzCam.exe','LegalCopyright':'Copyright '+info['publisher']}
  entries=','.join('StringStruct('+repr(k)+','+repr(v)+')' for k,v in fields.items())
  version_file.write_text('VSVersionInfo(ffi=FixedFileInfo(filevers='+repr(version)+',prodvers='+repr(version)+',mask=0x3f,flags=0,OS=0x40004,fileType=1,subtype=0,date=(0,0)),kids=[StringFileInfo([StringTable("040904B0",['+entries+'])]),VarFileInfo([VarStruct("Translation",[1033,1200])])])',encoding='utf8')
  version_args=['--version-file',str(version_file),'--manifest',str(root/'CrossPlatform/windows-app.manifest')]
 subprocess.run([sys.executable,'-m','PyInstaller','--clean','--noconfirm','--windowed','--onedir','--name','LuzCam',
 '--distpath',str(runtime),'--workpath',str(root/'build'/'pyinstaller'),
 '--specpath',str(root/'build'),
 '--additional-hooks-dir',str(root/'CrossPlatform/hooks'),
 '--exclude-module','PySide6.QtMultimediaWidgets',
 '--exclude-module','PIL._avif','--exclude-module','PIL.AvifImagePlugin',
 '--exclude-module','PIL._webp','--exclude-module','PIL.WebPImagePlugin',
 '--icon',str(root/'CrossPlatform/luzcam/icons'/('luzcam.icns' if sys.platform=='darwin' else 'luzcam.ico')),
 '--add-data',str(root/'CrossPlatform/luzcam/icons/luzcam.png')+':luzcam/icons',
 '--add-data',str(root/'CrossPlatform'/'luzcam'/'exposure-ranges.json')+':luzcam',
 '--add-data',str(root/'CrossPlatform'/'luzcam'/'translations.json')+':luzcam',
 '--add-data',str(root/'CrossPlatform'/'luzcam'/'release-info.json')+':luzcam',
 *version_args,
 '--add-data',str(root/'CrossPlatform'/'luzcam'/'fonts')+':luzcam/fonts',
 str(root/'CrossPlatform'/'main.py')],check=True,cwd=root,env=build_env)
 if source_fingerprints()!=build_sources:
  raise SystemExit('Sources changed during compilation: rebuild before packaging.')
 origin_file.write_text(json.dumps({'sources':build_sources,'system':platform.system(),'python':platform.python_version(),'dependencies':dependency_versions,'profile':profile.name},indent=2),encoding='utf8')
app=out/'LuzCam'
resource_root=app/'resources'
runtime_app=runtime/'LuzCam'
if sys.platform=='darwin':
 app=out/'LuzCam.app'; runtime_app=runtime/'LuzCam.app'
 resource_root=app/'Contents'/'Resources'/'LuzCamData'
if not args.resources_only:
 if app.exists():
  import datetime
  previous=out/'previous'/datetime.datetime.now().strftime('%Y%m%d-%H%M%S')
  previous.mkdir(parents=True,exist_ok=True)
  app.rename(previous/app.name)
 shutil.copytree(runtime_app,app,symlinks=sys.platform=='darwin')
executable=out/'LuzCam.app'/'Contents'/'MacOS'/'LuzCam' if sys.platform=='darwin' else app/'LuzCam.exe'
if not executable.is_file():
 raise SystemExit('Executable missing: run the full build first.')
resource_root.mkdir(parents=True,exist_ok=True)
def copy_resource(pair):
 source,target=pair
 source_stat=source.stat()
 if target.exists():
  target_stat=target.stat()
  if source_stat.st_size==target_stat.st_size and source_stat.st_mtime_ns==target_stat.st_mtime_ns:
   return
 shutil.copy2(source,target)
manifest=json.loads((root/'CrossPlatform/runtime-resources.json').read_text())
resources=[]
for name in manifest['files']:
 source=(root/name).resolve()
 if root.resolve() not in source.parents or not source.is_file():raise SystemExit('Invalid runtime resource: '+name)
 target=resource_root/name;target.parent.mkdir(parents=True,exist_ok=True);resources.append((source,target))
with ThreadPoolExecutor(max_workers=8) as pool:
 for _ in pool.map(copy_resource,resources):pass
shutil.copy2(root/'CrossPlatform/runtime-resources.json',resource_root/'runtime-resources.json')
expected=set(manifest['files'])
for folder in ('Portable','CameraArt','Scene'):
 actual={str(p.relative_to(resource_root)).replace('\\','/') for p in (resource_root/folder).rglob('*') if p.is_file()}
 if actual!={name for name in expected if name.startswith(folder+'/')}:raise SystemExit('Stale or missing runtime resources: '+folder+'; perform a full clean build.')
print(f'Resources ready: {len(resources)} explicitly required files',flush=True)
shared=root/'CrossPlatform'/'luzcam'
files=sorted(p for p in shared.rglob('*') if p.is_file() and p.suffix in ('.py','.json','.ttf','.txt','.png','.ico','.icns'))
hashes={str(p.relative_to(shared)).replace('\\','/'):hashlib.sha256(p.read_bytes()).hexdigest() for p in files}
(resource_root/'shared-build.json').write_text(json.dumps({'system':platform.system(),'sharedFiles':hashes},indent=2),encoding='utf-8')
shutil.copy2(origin_file,resource_root/'build-origin.json')
for name in ('LICENSE','COPYRIGHT.md','CREDITS.md'):shutil.copy2(root/name,resource_root/name)
subprocess.run([sys.executable,str(root/'Tools/recopilar-licencias.py'),str(resource_root/'ThirdParty')],check=True,cwd=root)
if sys.platform=='darwin':
 subprocess.run(['codesign','--force','--deep','--sign','-',str(app)],check=True)
 subprocess.run(['codesign','--verify','--deep','--strict',str(app)],check=True)
 print(f'Build local preparado en {out}. Firma ad hoc local; sin notarizar ni validar otros sistemas.')
else:
 print(f'Build local preparado en {out}. No firmado ni validado en otros sistemas.')

