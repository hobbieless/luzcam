"""Compact integration keeps electronic registration and captured LCD independent."""
import os,sys,json
from pathlib import Path
os.environ.setdefault('QT_QPA_PLATFORM','offscreen')
root=Path(__file__).resolve().parents[1];sys.path.insert(0,str(root/'CrossPlatform'))
from PySide6.QtWidgets import QApplication
from PySide6.QtGui import QImage,QPainter,QColor
from PySide6.QtCore import QRectF,Qt
from luzcam.model import Setting,pose
from luzcam.reviewed_compact import draw,geometry
app=QApplication([]);s=Setting(camera=2);g=geometry()
assert g==json.loads((root/'Tests/fixtures/reviewed-cameras/compact-geometry.json').read_text())
assert g['irisVisualScale']==1.5 and g['irisReviewPercent']==75
plate=QImage(str(root/'CameraArt/compact-reviewed.jpg'));assert plate.width()==1376
photo=QImage(160,90,QImage.Format_RGB32);photo.fill(QColor('red'))
def render(state):
 image=QImage(1376,768,QImage.Format_ARGB32);image.fill(Qt.transparent)
 p=QPainter(image);draw(p,QRectF(0,0,1376,768),plate,state,s,False,photo);p.end();return image
state=pose(0,s);first=render(state)
assert first==render(dict(state,front=0,rear=1)), 'Compact must never draw mechanical curtains'
assert first!=render(dict(state,sensorActive=1)), 'Electronic registration must highlight sensor'
assert first.pixelColor(1100,390)==QColor('red'), 'LCD must use supplied live/captured photo'
print('PASS: compact geometry75%, no mechanical curtains, electronic highlight, registered LCD')
