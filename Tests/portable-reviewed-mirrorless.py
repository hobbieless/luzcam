"""Native mirrorless registration, live/review LCD and covered curtain rearm."""
from pathlib import Path
import os,sys,json
os.environ.setdefault('QT_QPA_PLATFORM','offscreen')
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'CrossPlatform'))
from PySide6.QtWidgets import QApplication
from PySide6.QtGui import QImage,QColor
from luzcam.model import ROOT,Setting,pose
from luzcam.ui import Camera
from luzcam.reviewed_mirrorless import geometry,lcd_image
from luzcam.reviewed_reflex import curtain_leaves
app=QApplication([]);camera=Camera();camera.camera=1;s=Setting();s.camera=1
assert geometry()==json.loads((ROOT/'Tests/fixtures/reviewed-cameras/mirrorless-geometry.json').read_text())
assert camera.plates[1].size().width()==1376
assert pose(0,s)['front']==1 and pose(0,s)['rear']==0
camera.start=pose(5,s);camera.target=pose(6,s)
for i in range(101):
 t=i/100;camera.interpolate(t)
 if t<=2/3:
  for j in range(101):
   assert any(a<=j/100<=b for progress,second in ((camera.pose['front'],False),(camera.pose['rear'],True)) for a,b in curtain_leaves(progress,second))
assert camera.pose['front']==1 and camera.pose['rear']==0
photo=QImage(160,90,QImage.Format_RGB32);photo.fill(QColor('red'))
for review in (False,True):
 image=lcd_image(s,review,photo);assert image.pixelColor(320,240)==QColor('red')
print('PASS: registered plate/geometry, open live sensor, covered rearm and 16:9 photo preserved in live/review LCD')
