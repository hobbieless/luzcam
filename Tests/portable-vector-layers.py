"""Cached commands must reproduce uncached vectors and invalidate on mechanisms."""
from pathlib import Path
import os,sys
os.environ.setdefault('QT_QPA_PLATFORM','offscreen');sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'CrossPlatform'))
from PySide6.QtWidgets import QApplication
from PySide6.QtGui import QImage,QPainter
from PySide6.QtCore import QRectF
from luzcam.model import Setting,pose,ROOT
from luzcam.reviewed_mirrorless import draw
from luzcam import vector_layers
app=QApplication([]);plate=QImage(str(ROOT/'CameraArt/mirrorless-reviewed.jpg'));s=Setting();s.camera=1
original=vector_layers.draw_layer
for scale in (1,2):
 def render(cached,phase):
  image=QImage(1376*scale,768*scale,QImage.Format_ARGB32);image.fill(0);p=QPainter(image);p.setRenderHints(QPainter.Antialiasing|QPainter.SmoothPixmapTransform)
  vector_layers.draw_layer=original if cached else lambda p,slot,key,render:render(p)
  draw(p,QRectF(0,0,image.width(),image.height()),plate,pose(phase,s),s,False,QImage());p.end();return image
 for phase in (0,1,4,5,6,7):
  assert render(True,phase)==render(False,phase),(scale,phase)
vector_layers.draw_layer=original
assert len(vector_layers._layers)<=3 and vector_layers.bytes_used()<1024*1024
print('PASS: cached/uncached pixels identical at 1x/2x, six mechanism states; vector recording bounded under 1 MiB')
