from pathlib import Path
import sys,time,json
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'CrossPlatform'))
from PySide6.QtGui import QImage,QColor
from PySide6.QtCore import QBuffer,QIODevice
from luzcam.review_cache import ReviewCache
from luzcam.liveview import exposure_preview,exposure_table
import numpy as np
calls=[]
def decode(data):calls.append(1);return QImage.fromData(data,'PNG')
image=QImage(960,540,QImage.Format_RGB32);image.fill(QColor('#846c51'));buffer=QBuffer();buffer.open(QIODevice.WriteOnly);image.save(buffer,'PNG');data=bytes(buffer.data());cache=ReviewCache(decoder=decode)
start=time.perf_counter()
for i in range(30):assert QImage.fromData(data,'PNG')==image
uncached=time.perf_counter()-start;start=time.perf_counter()
for i in range(30):assert cache.image('one',data)==image
cached=time.perf_counter()-start;assert len(calls)==1
returned=cache.image('one',data);returned.setPixelColor(0,0,QColor('blue'));assert cache.image('one',data)==image
for key in ('two','three'):cache.image(key,data)
assert len(cache.items)==2 and 'one' not in cache.items
for fmt in (QImage.Format_RGB888,QImage.Format_RGBA8888,QImage.Format_ARGB32):
 original=QImage(17,13,fmt);original.fill(QColor(90,150,30,133));snapshot=original.copy();shared=QImage(original);result=exposure_preview(original,3)
 assert original==snapshot and shared==snapshot
 source=snapshot.convertToFormat(QImage.Format_RGBA8888);pixels=np.frombuffer(source.constBits(),np.uint8).reshape(13,source.bytesPerLine())[:,:68].reshape(13,17,4).copy();pixels[:,:,:3]=exposure_table(3)[pixels[:,:,:3]]
 expected=QImage(pixels.data,17,13,68,QImage.Format_RGBA8888).copy();assert result==expected
print('PASS: decode once, two-photo bound, eviction, shared input unchanged, RGB/RGBA/ARGB pixel and alpha equivalence')
print(json.dumps({'uncached30Seconds':uncached,'cached30Seconds':cached,'scope':'uniform synthetic 960x540 PNG; not real capture latency'}))
