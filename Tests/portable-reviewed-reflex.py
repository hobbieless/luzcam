from pathlib import Path
import sys,os,tempfile,numpy as np
os.environ.setdefault("QT_QPA_PLATFORM","offscreen")
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'CrossPlatform'))
from PySide6.QtWidgets import QApplication
from PySide6.QtGui import QImage,QPainter
from PySide6.QtCore import QRectF
from luzcam.reviewed_reflex import draw,geometry,curtain_leaves
from luzcam.model import ROOT,Setting
from luzcam.ui import Camera,configure_style
app=QApplication([]);configure_style();plate=QImage(str(ROOT/'CameraArt/reflex-reviewed.jpg'))
for name,aperture,mirror,front,rear in [('rest',.85,1,0,0),('iris-f4',.85*2**(-1.5),1,0,0),('iris-closed',.85/16,1,0,0),('mirror-half',.85*2**(-1.5),.5,0,0)]:
 image=QImage(1376,768,QImage.Format_ARGB32);p=QPainter(image);p.setRenderHints(QPainter.Antialiasing|QPainter.SmoothPixmapTransform);draw(p,QRectF(0,0,1376,768),plate,dict(aperture=aperture,mirrorDown=mirror,front=front,rear=rear,illumination=1),Setting(),False,QImage());p.end();image.save(str(Path(tempfile.gettempdir())/('luzcam-native-'+name+'.png')))
 source=QImage(str(Path(__file__).resolve().parent/'fixtures/reviewed-cameras'/f'{name}.png')).convertToFormat(QImage.Format_ARGB32)
 a=np.frombuffer(image.constBits(),np.uint8).reshape(768,1376,4).astype(int);b=np.frombuffer(source.constBits(),np.uint8).reshape(768,1376,4).astype(int);mask=np.ones((768,1376),bool);mask[280:555,965:1135]=False
 diff=np.max(np.abs(a[:,:,:3]-b[:,:,:3]),axis=2);print(name,'mean error',round(diff[mask].mean(),4),'pixels >8',np.count_nonzero((diff>8)&mask));assert diff[mask].mean()<3 and np.count_nonzero((diff>8)&mask)<50000
print('PASS: native checkpoints within RGB mean 3/255 and 5% pixels beyond 8/255; photo filtering differs from the recorded reference')
camera=Camera();camera.camera=0;camera.start=dict(camera.pose,front=1,rear=1,mirrorDown=0);camera.target=dict(camera.pose,front=0,rear=0,mirrorDown=1)
for i in range(101):
 camera.interpolate(i/100)
 for j in range(101):
  v=j/100
  assert any(a<=v<=b for progress,second in ((camera.pose['front'],False),(camera.pose['rear'],True)) for a,b in curtain_leaves(progress,second)),(i,v)
assert camera.pose['front']==camera.pose['rear']==0
assert geometry()==__import__('json').loads((ROOT/'Tests/fixtures/reviewed-cameras/reflex-geometry.json').read_text())
print('PASS: approved geometry identical; app rearm stays covered through 101 states and returns to rest')
# Audit actual native blade fills/strokes at high resolution, before front-group
# occlusion; alpha measures the unobstructed physical pupil, not photo contrast.
from luzcam.reviewed_reflex import _iris
size=1536;zoom=12;g=geometry();basis=np.array(g['irisBasis']).reshape(2,2).T*g['irisVisualScale']*zoom
rows,cols=np.mgrid[:size,:size];local=np.linalg.inv(basis)@np.stack((cols.ravel()-size/2,rows.ravel()-size/2));roi=(local[0]**2+local[1]**2<34**2).reshape(size,size)
previous=None
for index in range(9):
    image=QImage(size,size,QImage.Format_ARGB32_Premultiplied);image.fill(0);p=QPainter(image);p.setRenderHint(QPainter.Antialiasing);p.translate(size/2-g['irisDisplay'][0]*zoom,size/2-g['irisDisplay'][1]*zoom);p.scale(zoom,zoom);_iris(p,g,.86*2**(-index/2));p.end()
    alpha=np.frombuffer(image.constBits(),np.uint8).reshape(size,size,4)[:,:,3];area=((255-alpha[roi].astype(float))/255).sum()
    if previous is not None:assert abs(area/previous-.5)<.005,(index,area/previous)
    previous=area
print('PASS: actual native pupil area halves at every full stop, including stroke clipping')
