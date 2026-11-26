"""Validate staging metadata without SDK, certificate, registration or publication."""
import sys,tempfile,json,hashlib,subprocess,xml.etree.ElementTree as ET
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
with tempfile.TemporaryDirectory(prefix='store-metadata-',dir=ROOT/'build') as temp:
    folder=Path(temp).resolve();assert folder.is_relative_to(ROOT/'build')
    app=folder/'app';app.mkdir();(app/'LuzCam.exe').write_bytes(b'metadata test only; never executed')
    (app/'resources').mkdir();source='CrossPlatform/luzcam/release-info.json'
    (app/'resources/build-origin.json').write_text(json.dumps({'sources':{source:hashlib.sha256((ROOT/source).read_bytes()).hexdigest()}}),encoding='utf8')
    stage=folder/'stage'
    subprocess.run([sys.executable,str(ROOT/'Tools/preparar-store.py'),'--app',str(app),'--output',str(stage),
                    '--identity','Internal.LuzCam.Test','--publisher','CN=Internal Test Only','--publisher-display-name','Registered Publisher Test'],check=True)
    doc=ET.parse(stage/'AppxManifest.xml');ns={'a':'http://schemas.microsoft.com/appx/manifest/foundation/windows10',
        'r':'http://schemas.microsoft.com/appx/manifest/foundation/windows10/restrictedcapabilities'}
    assert doc.find('a:Identity',ns).attrib['Publisher']=='CN=Internal Test Only'
    assert doc.find('a:Properties/a:PublisherDisplayName',ns).text=='Registered Publisher Test'
    identity=folder/'identity.json';identity.write_text(json.dumps({'identityName':'File.Identity.Test','publisher':'CN=File Test','publisherDisplayName':'File Publisher'}),encoding='utf8')
    second=folder/'from-file'
    subprocess.run([sys.executable,str(ROOT/'Tools/preparar-store.py'),'--app',str(app),'--output',str(second),'--identity-file',str(identity)],check=True)
    actual=ET.parse(second/'AppxManifest.xml');assert actual.find('a:Identity',ns).attrib['Name']=='File.Identity.Test'
    assert actual.find('a:Properties/a:PublisherDisplayName',ns).text=='File Publisher'
    bad=folder/'conflict'
    run=subprocess.run([sys.executable,str(ROOT/'Tools/preparar-store.py'),'--app',str(app),'--output',str(bad),'--identity-file',str(identity),'--publisher','CN=Wrong'],capture_output=True,text=True)
    assert run.returncode!=0 and 'conflicts' in run.stderr and not bad.exists()
    assert {x.attrib['Language'] for x in doc.findall('a:Resources/a:Resource',ns)}=={'es-ES','en-US'}
    assert [x.attrib['Name'] for x in doc.findall('a:Capabilities/r:Capability',ns)]==['runFullTrust']
    assert (stage/'LuzCam/LuzCam.exe').read_bytes()==(app/'LuzCam.exe').read_bytes()
    assert not list(folder.glob('*.msix'))
    (app/'resources/build-origin.json').write_text(json.dumps({'sources':{source:'0'*64}}),encoding='utf8')
    stale=folder/'stale'
    run=subprocess.run([sys.executable,str(ROOT/'Tools/preparar-store.py'),'--app',str(app),'--output',str(stale),'--identity-file',str(identity)],capture_output=True,text=True)
    assert run.returncode!=0 and 'Package/source mismatch' in run.stderr and not stale.exists()
print('PASS: Store staging ES/EN, exact provided identity, desktop capability, no signature/install/publication')
