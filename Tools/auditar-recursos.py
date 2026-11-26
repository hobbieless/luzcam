"""Read-only inventory: distinguish active delivery from preserved authoring history."""
import json,argparse
from pathlib import Path
root=Path(__file__).resolve().parents[1];p=argparse.ArgumentParser();p.add_argument('--output',type=Path,required=True);a=p.parse_args()
manifest=json.loads((root/'CrossPlatform/runtime-resources.json').read_text());active=set(manifest['files'])
allfiles=[f for folder in ('Portable','CameraArt','Scene') for f in (root/folder).rglob('*') if f.is_file()]
report={'required':[{'path':name,'bytes':(root/name).stat().st_size} for name in sorted(active)],'preservedNotDelivered':[{'path':f.relative_to(root).as_posix(),'bytes':f.stat().st_size} for f in allfiles if f.relative_to(root).as_posix() not in active],'sourceHistory':['Design','Sources','Tests','Tools','Catalogue','CatalogueThirds'],'notes':'Source originals/catalogues remain intact. Build caches and previous packages are not runtime resources. No deletion performed by this inventory.'}
report['requiredBytes']=sum(f['bytes'] for f in report['required']);report['excludedBytes']=sum(f['bytes'] for f in report['preservedNotDelivered']);a.output.parent.mkdir(parents=True,exist_ok=True);a.output.write_text(json.dumps(report,indent=2));print('Runtime:',len(active),'files,',round(report['requiredBytes']/1024**2,2),'MiB; excluded historical assets:',round(report['excludedBytes']/1024**2,2),'MiB')
