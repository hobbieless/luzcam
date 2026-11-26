"""Stage a desktop MSIX with the actual Partner Center identity; never sign/install it."""
import argparse,json,shutil,subprocess,hashlib,xml.etree.ElementTree as ET
from pathlib import Path
from PySide6.QtGui import QImage
from PySide6.QtCore import Qt
ROOT=Path(__file__).resolve().parents[1]
p=argparse.ArgumentParser()
p.add_argument('--app',type=Path,required=True);p.add_argument('--output',type=Path,required=True)
p.add_argument('--identity',help='Package/Identity/Name from Partner Center')
p.add_argument('--publisher',help='Package/Identity/Publisher from Partner Center')
p.add_argument('--identity-file',type=Path,help='Observed Partner Center public identity JSON')
p.add_argument('--publisher-display-name',help='Exact registered PublisherDisplayName')
p.add_argument('--makeappx',type=Path,help='Windows SDK MakeAppx.exe; omit to stage files only')
p.add_argument('--store-vclibs',action='store_true',help='Declare the Microsoft VCLibs desktop framework dependency and omit standard app-local VC runtime DLLs')
args=p.parse_args();app=args.app.resolve();out=args.output.resolve()
if not (app/'LuzCam.exe').is_file():p.error('Application missing')
identity={}
if args.identity_file:
 identity=json.loads(args.identity_file.read_text(encoding='utf8'))
 for field,key in (('identity','identityName'),('publisher','publisher'),('publisher_display_name','publisherDisplayName')):
  value=identity.get(key)
  if not value:p.error('Missing identity field: '+key)
  if getattr(args,field) and getattr(args,field)!=value:p.error('CLI identity conflicts with identity file: '+key)
  setattr(args,field,value)
if not args.identity or not args.publisher:p.error('Provide identity/publisher or an identity file')
origin_path=app/'resources/build-origin.json'
if not origin_path.is_file():p.error('Package build provenance missing')
origin=json.loads(origin_path.read_text(encoding='utf8'))
for name,digest in origin['sources'].items():
 if hashlib.sha256((ROOT/name).read_bytes()).hexdigest()!=digest:p.error('Package/source mismatch: '+name)
if out==app or out.is_relative_to(app):p.error('Output must be outside the application')
if out.exists():p.error('Choose a new empty output directory')
info=json.loads((ROOT/'CrossPlatform/luzcam/release-info.json').read_text(encoding='utf8'))
out.mkdir(parents=True);shutil.copytree(app,out/'LuzCam')
runtime_import_patch=[]
if args.store_vclibs:
    # NumPy's Windows wheel privately renames MSVCP140.dll and two extension
    # modules import that renamed filename. Rebind only those PE import-name
    # strings to the standard VCLibs-provided name, then omit the private DLL.
    # Assert the exact pinned NumPy payload so a future wheel cannot be patched
    # accidentally under this release-specific rule.
    private_name='msvcp140-a4c2229bdc2a2a630acdc095b4d86008.dll'
    private_file=out/'LuzCam/_internal/numpy.libs'/private_name
    private_hash='a4c2229bdc2a2a630acdc095b4d86008e5c3e3bc7773174354f3da4f5beb9cde'
    if not private_file.is_file() or hashlib.sha256(private_file.read_bytes()).hexdigest()!=private_hash:
        p.error('Store VCLibs rule only covers the reviewed NumPy 2.3.5 MSVCP payload')
    old_name=private_name.encode('ascii')
    new_name=b'MSVCP140.dll'
    for relative in ('_internal/numpy/fft/_pocketfft_umath.cp312-win_amd64.pyd',
                     '_internal/numpy/_core/_multiarray_umath.cp312-win_amd64.pyd'):
        binary=out/'LuzCam'/relative
        data=binary.read_bytes()
        if data.count(old_name)!=1:p.error('Expected one pinned NumPy runtime import in '+relative)
        replacement=new_name+b'\0'*(len(old_name)-len(new_name))
        binary.write_bytes(data.replace(old_name,replacement,1))
        runtime_import_patch.append({'file':'LuzCam/'+relative,'from':private_name,'to':'MSVCP140.dll',
                                     'originalSHA256':hashlib.sha256((app/relative).read_bytes()).hexdigest(),
                                     'patchedSHA256':hashlib.sha256(binary.read_bytes()).hexdigest()})
    private_file.unlink()
    standard_runtime={'vcruntime140.dll','vcruntime140_1.dll','vcruntime140_2.dll',
                      'msvcp140.dll','msvcp140_1.dll','msvcp140_2.dll'}
    for runtime in (out/'LuzCam').rglob('*.dll'):
        if runtime.name.lower() in standard_runtime:
            runtime.unlink()
assets=out/'Assets';assets.mkdir()
icon=QImage(str(ROOT/'CrossPlatform/luzcam/icons/luzcam.png'))
for name,size in [('Square150x150Logo.png',150),('Square44x44Logo.png',44),('StoreLogo.png',50)]:
    if not icon.scaled(size,size,Qt.IgnoreAspectRatio,Qt.SmoothTransformation).save(str(assets/name)):raise RuntimeError('Icon export failed')
ns='http://schemas.microsoft.com/appx/manifest/foundation/windows10'
uap='http://schemas.microsoft.com/appx/manifest/uap/windows10'
res='http://schemas.microsoft.com/appx/manifest/foundation/windows10/restrictedcapabilities'
ET.register_namespace('',ns);ET.register_namespace('uap',uap);ET.register_namespace('rescap',res)
tag=lambda n:'{'+ns+'}'+n
package=ET.Element(tag('Package'),{'IgnorableNamespaces':'uap rescap'})
ET.SubElement(package,tag('Identity'),Name=args.identity,Publisher=args.publisher,Version='.'.join(map(str,info['windowsVersion'])),ProcessorArchitecture='x64')
props=ET.SubElement(package,tag('Properties'))
for key,value in [('DisplayName','LuzCam'),('PublisherDisplayName',args.publisher_display_name or info['publisher']),('Logo','Assets/StoreLogo.png')]:ET.SubElement(props,tag(key)).text=value
deps=ET.SubElement(package,tag('Dependencies'))
ET.SubElement(deps,tag('TargetDeviceFamily'),Name='Windows.Desktop',MinVersion='10.0.19041.0',MaxVersionTested='10.0.26200.0')
if args.store_vclibs:
    ET.SubElement(deps,tag('PackageDependency'),Name='Microsoft.VCLibs.140.00.UWPDesktop',
                  MinVersion='14.0.30704.0',Publisher='CN=Microsoft Corporation, O=Microsoft Corporation, L=Redmond, S=Washington, C=US')
resources=ET.SubElement(package,tag('Resources'))
for code in ('es-ES','en-US'):ET.SubElement(resources,tag('Resource'),Language=code)
apps=ET.SubElement(package,tag('Applications'));a=ET.SubElement(apps,tag('Application'),Id='LuzCam',Executable='LuzCam/LuzCam.exe',EntryPoint='Windows.FullTrustApplication')
ET.SubElement(a,'{'+uap+'}VisualElements',DisplayName='LuzCam',Description='Photography learning simulator / Simulador didáctico de fotografía',BackgroundColor='transparent',Square150x150Logo='Assets/Square150x150Logo.png',Square44x44Logo='Assets/Square44x44Logo.png')
cap=ET.SubElement(package,tag('Capabilities'));ET.SubElement(cap,'{'+res+'}Capability',Name='runFullTrust')
ET.ElementTree(package).write(out/'AppxManifest.xml',encoding='utf-8',xml_declaration=True)
if args.makeappx:
    artifact=out.parent/(out.name+'.msix')
    subprocess.run([str(args.makeappx),'pack','/d',str(out),'/p',str(artifact)],check=True)
    print('Unsigned MSIX built:',artifact)
else:print('Staging only. No MSIX built: supply Windows SDK MakeAppx.exe.')
(out/'store-staging.json').write_text(json.dumps({'identityName':args.identity,'publisher':args.publisher,'publisherDisplayName':args.publisher_display_name or info['publisher'],'storeId':identity.get('storeId'),'version':info['windowsVersion'],'packageSourceChecksPassed':True,'vclibsFrameworkDependency':args.store_vclibs,'numpyMsvcImportRebindings':runtime_import_patch,'msixBuilt':bool(args.makeappx),'signed':False,'installed':False,'submitted':False,'publicReleaseApproved':False},ensure_ascii=False,indent=2),encoding='utf8')
print('Not signed, installed, uploaded, Store-certified or publicly released.')
