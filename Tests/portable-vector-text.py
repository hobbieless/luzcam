"""Text retains shaping/accessibility and caches outlines, never rendered bitmaps."""
import os,sys
from pathlib import Path
os.environ.setdefault('QT_QPA_PLATFORM','offscreen')
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'CrossPlatform'))
from PySide6.QtWidgets import QApplication
from PySide6.QtGui import QFont,QImage,QPainter,QPainterPath,QColor
from PySide6.QtCore import Qt,QRectF
from luzcam.vector_text import VectorLabel,VectorButton,VectorCheckBox,outline,paint_text
app=QApplication([]);font=QFont('Arial');font.setPixelSize(18)
text='Cámara · exposición ⅓ EV\nCésar González'
path,height=outline(text,font,220,True)
assert not path.isEmpty() and height>25
cache=[None,None]
for scale in (0.75,1,1.25,1.5,2,3):
    image=QImage(round(260*scale),round(100*scale),QImage.Format_ARGB32);image.fill(Qt.white)
    p=QPainter(image);p.scale(scale,scale)
    paint_text(p,QRectF(0,0,260,100),text,font,QColor('black'),wrap=True,cache=cache);p.end()
    assert isinstance(cache[1][0],QPainterPath) and not cache[1][0].isEmpty()
for cls in (VectorLabel,VectorButton,VectorCheckBox):
    w=cls('Exposición');w.setAccessibleName('Exposición');w.resize(180,50);w.show();app.processEvents()
    assert w.text()=='Exposición' and w.accessibleName()=='Exposición'
    assert not w.grab().isNull();assert isinstance(w._outline_cache[1][0],QPainterPath)
    w.close()
print('PASS: shaped accents/multiline, six fractional scales, glyph outlines only, original widget text/accessibility retained')
