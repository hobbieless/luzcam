"""Moving subject stays focused as aperture changes, with background DOF intact."""
import sys,json
from pathlib import Path
from dataclasses import replace
import numpy as np
from PIL import Image
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'CrossPlatform'))
from luzcam.model import Setting,ROOT
from luzcam.temporary_photo import TemporaryPhoto
renderer=TemporaryPhoto();spec=renderer.scene['focusMotion'];x0,y0,x1,y1=spec['box'];h=y1-y0
with Image.open(ROOT/'Scene'/spec['file']) as atlas:
    for phase in (0,11,22,33):
        core=np.zeros((540,960),bool)
        for i in range(17):
            frame=int((phase/30+(i+.5)/17*.25)*30+.5)%45
            core[y0:y1,x0:x1]|=np.asarray(atlas.crop((0,frame*h,x1-x0,(frame+1)*h)))>0
        missing=np.count_nonzero(core & (renderer.subject[:,:,0]<.5))
        assert missing>0,'The regression must exercise metal outside the old body polygon'
        for light in range(3):
            setting=Setting(camera=0,light=light,scene_frame=phase)
            setting.s=setting.shutters.index('1/4 s');setting.a=setting.apertures.index(16)
            sharp=renderer._prepared(setting)
            wide=replace(setting);wide.a=wide.apertures.index(5.6)
            opened=renderer._prepared(wide)
            assert np.array_equal(sharp[core],opened[core]),(phase,light)
            assert np.any(sharp[~core]!=opened[~core]),'Background depth effect must remain'
print('PASS: arm remains focused at four integrated phases in all lights; background aperture response remains')
