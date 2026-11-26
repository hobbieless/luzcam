"""Verify unsigned MSIX payload bytes and block hashes; not Store certification."""
import argparse, base64, hashlib, json, zipfile
from pathlib import Path
from urllib.parse import unquote
from xml.etree import ElementTree as ET

p = argparse.ArgumentParser(description=__doc__)
p.add_argument('--package', type=Path, required=True)
p.add_argument('--staging', type=Path, required=True)
p.add_argument('--identity-file', type=Path, required=True)
p.add_argument('--output', type=Path, required=True)
a = p.parse_args()
blocks = 0
with zipfile.ZipFile(a.package) as z:
    assert z.testzip() is None, 'ZIP CRC failure'
    lookup = {unquote(name): name for name in z.namelist()}
    assert len(lookup) == len(z.namelist()), 'Ambiguous ZIP entries'
    bm = ET.fromstring(z.read('AppxBlockMap.xml'))
    ns = {'b': 'http://schemas.microsoft.com/appx/2010/blockmap'}
    assert bm.get('HashMethod') == 'http://www.w3.org/2001/04/xmlenc#sha256'
    files = bm.findall('b:File', ns)
    names = set()
    for file in files:
        name = file.get('Name').replace('\\', '/')
        assert name not in names, 'Duplicate block-map path'
        names.add(name)
        target = (a.staging / name).resolve()
        assert target.is_relative_to(a.staging.resolve()), 'Unsafe payload path'
        data = z.read(lookup[name])
        assert len(data) == int(file.get('Size')), name
        assert data == target.read_bytes(), 'Payload differs from staging: ' + name
        rows = file.findall('b:Block', ns)
        assert len(rows) == (len(data) + 65535) // 65536, name
        for i, row in enumerate(rows):
            digest = hashlib.sha256(data[i * 65536:(i + 1) * 65536]).digest()
            assert base64.b64encode(digest).decode() == row.get('Hash'), name
            blocks += 1
    assert set(lookup) == names | {'AppxBlockMap.xml', '[Content_Types].xml'}, 'Unexpected entries in unsigned package'
    manifest = ET.fromstring(z.read('AppxManifest.xml'))
    ns = {'a': 'http://schemas.microsoft.com/appx/manifest/foundation/windows10'}
    identity = manifest.find('a:Identity', ns).attrib
    expected = json.loads(a.identity_file.read_text(encoding='utf8'))
    assert identity['Name'] == expected['identityName']
    assert identity['Publisher'] == expected['publisher']
    release = json.loads((a.staging / 'LuzCam/_internal/luzcam/release-info.json').read_text(encoding='utf8'))
    assert identity['Version'] == '.'.join(map(str, release['windowsVersion']))
report = {'package': str(a.package), 'bytes': a.package.stat().st_size,
          'sha256': hashlib.sha256(a.package.read_bytes()).hexdigest(), 'identity': identity,
          'crcPassed': True, 'blockMapSHA256Passed': True, 'allPayloadMatchesStaging': True,
          'payloadFiles': len(files), 'blocksChecked': blocks,
          'signed': False, 'storeCertified': False, 'publicReleaseApproved': False}
a.output.parent.mkdir(parents=True, exist_ok=True)
a.output.write_text(json.dumps(report, indent=2), encoding='utf8')
print('PASS:', len(files), 'payload files and', blocks, 'SHA256 blocks. Unsigned; not Store certification.')
