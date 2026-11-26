"""Compare the actual portable implementation against Swift-exported fixtures."""
import json, math, sys
from pathlib import Path
root=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(root/'CrossPlatform'))
from luzcam.model import Setting,Session,pose,interval
cases=json.loads((root/'Portable/parity-v1.json').read_text())['cases']
for c in cases:
 s=Setting(legacy=True,**{k:c[k] for k in ('camera','a','s','i','light','thirds')})
 for actual,key in ((s.key,'imageKey'),(s.f,'labelF'),(s.isos[s.i],'labelISO'),(s.shutters[s.s],'labelShutter'),(s.meter_third,'meterThird'),(s.meter_fraction,'meterFraction')): assert actual==c[key],(actual,key,c)
 for actual,key in ((s.optical_f,'opticalF'),(s.seconds,'seconds'),(s.offset,'offsetEV'),(s.gain,'gainEV')): assert math.isclose(actual,c[key],abs_tol=1e-12)
 for p in c['phases']:
  for k,v in pose(p['phase'],s,c.get('preview',False)).items(): assert math.isclose(v,p[k],abs_tol=1e-12),(k,c,p,v)
  assert math.isclose(interval(p['phase'],s),p['presentationSeconds'],abs_tol=1e-12)
# Boundaries, Swift rounding, camera changes, immutable captures and replay.
s=Setting(a=7,s=7,legacy=True); s.select_camera(2); assert s.a==4
s.set_thirds(True); assert (s.a,s.s,s.i)==(12,21,0)
s.set_thirds(False); assert (s.a,s.s,s.i)==(4,7,0)
session=Session(); session.advance(); frozen=session.shot.key
session.setting.i=2
while session.phase<7: session.advance()
assert session.history[0].key==frozen
session.back(); session.advance(); assert len(session.history)==1
session.reset(); assert len(session.history)==1
print(f'PASS: portable engine, {len(cases)} Swift cases, 6480 poses, camera limits, thirds and capture lifecycle')
