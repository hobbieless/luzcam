"""Cross-platform plugin selection and native licence delivery, without building Qt."""
import ast,hashlib,json,subprocess,sys,tempfile
from pathlib import Path
root=Path(__file__).resolve().parents[1]
# Exercise the actual hook predicate without importing PyInstaller/collecting host plugins.
tree=ast.parse((root/'CrossPlatform/hooks/hook-PySide6.QtGui.py').read_text())
function=next(n for n in tree.body if isinstance(n,ast.FunctionDef) and n.name=='needed')
namespace={};exec(compile(ast.Module(body=[function],type_ignores=[]),'<hook predicate>','exec'),namespace)
needed=namespace['needed']
for base in ('C:/Qt/plugins/','/Qt/plugins/'):
 for file in ('iconengines/qsvgicon.dll','iconengines/libqsvgicon.dylib','iconengines/libqsvgicon.so','platforminputcontexts/qtvirtualkeyboardplugin.dll'):
  assert not needed((base+file,'plugins')),file
 for file in ('platforms/qwindows.dll','platforms/libqcocoa.dylib','platforminputcontexts/libqcocoa.dylib','imageformats/qjpeg.dll','imageformats/libqjpeg.dylib','imageformats/qico.dll'):
  assert needed((base+file,'plugins')),file
 assert not needed((base+'imageformats/qtiff.dll','plugins'))
# The language filter must preserve non-catalogue data and ES/EN regional variants.
tree=ast.parse((root/'CrossPlatform/hooks/hook-PySide6.QtCore.py').read_text())
function=next(n for n in tree.body if isinstance(n,ast.FunctionDef) and n.name=='needed')
namespace={'Path':Path};exec(compile(ast.Module(body=[function],type_ignores=[]),'<Qt language filter>','exec'),namespace)
for name in ('qtbase_es.qm','qtbase_en.qm','qtbase_en_GB.qm','qtbase_es_MX.qm','icudtl.dat'):
 assert namespace['needed']((name,'translations')),name
for name in ('qtbase_fr.qm','qt_ar.qm','qtbase_de.qm'):
 assert not namespace['needed']((name,'translations')),name
with tempfile.TemporaryDirectory() as temp:
 subprocess.run([sys.executable,str(root/'Tools/recopilar-licencias.py'),temp],check=True,stdout=subprocess.DEVNULL)
 out=Path(temp);data=json.loads((out/'components.json').read_text());assert not data['reviewComplete']
 origins=json.loads((out/'native-base/sources.json').read_text())
 assert len(origins['records'])==4
 for record in origins['records']:
  assert hashlib.sha256((out/'native-base'/record['file']).read_bytes()).hexdigest()==record['sha256']
 assert (out/'PYTHON-LICENSE.txt').is_file()
 assert len(list((out/'fonts').glob('*OFL.txt')))==3
 notices=json.loads((out/'qt-native-notices/manifest.json').read_text())
 assert not notices['unresolvedLicenseFiles'] and not notices['reviewComplete']
 assert data['qtNativeNotices']['files']==len(notices['files'])
 for row in notices['files']:
  assert hashlib.sha256((out/'qt-native-notices'/row['path']).read_bytes()).hexdigest()==row['sha256']
 supplement=json.loads((out/'native-supplement/manifest.json').read_text())
 for row in supplement['files']:
  assert hashlib.sha256((out/'native-supplement'/row['path']).read_bytes()).hexdigest()==row['sha256']
print('PASS: Windows/Mac/Linux SVG filtering retains native input; exact native licence texts/Python/font notices delivered')
