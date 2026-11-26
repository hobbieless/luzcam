"""Limited readability checks; not a WCAG or native screen-reader certification."""
import os,sys
from pathlib import Path
os.environ.setdefault('QT_QPA_PLATFORM','offscreen')
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'CrossPlatform'))
from PySide6.QtWidgets import QApplication
from PySide6.QtGui import QColor,QFontMetrics
from PySide6.QtCore import Qt
from luzcam.ui import Window,ACCENT,PAPER,INK,BACKGROUND

def luminance(value):
    c=QColor(value);rgb=[c.redF(),c.greenF(),c.blueF()]
    rgb=[x/12.92 if x<=.04045 else ((x+.055)/1.055)**2.4 for x in rgb]
    return sum(x*w for x,w in zip(rgb,(.2126,.7152,.0722)))
def contrast(a,b):
    a,b=sorted((luminance(a),luminance(b)));return (b+.05)/(a+.05)
for a,b in [(INK,PAPER),(INK,'white'),(INK,BACKGROUND),('white',ACCENT),(ACCENT,BACKGROUND)]:
    ratio=contrast(a,b);assert ratio>=4.5,(a,b,ratio)
    print('contrast',QColor(a).name(),QColor(b).name(),round(ratio,2))
app=QApplication([]);w=Window();w.moving=False;w.show();app.processEvents()
try:
    assert all(slider.accessibleName() and slider.focusPolicy()!=Qt.NoFocus for slider in w.sliders)
    assert w.expl.font().pixelSize()>=14
    for camera in range(3):
        w.reset();w.change_camera(camera)
        for phase in range(8):
            while w.session.phase<phase:w.advance()
            app.processEvents()
            metrics=QFontMetrics(w.expl.font())
            bounds=metrics.boundingRect(w.expl.contentsRect(),Qt.TextWordWrap,w.expl.text())
            assert bounds.height()<=w.expl.contentsRect().height(),(camera,phase,bounds,w.expl.size())
    assert 'QPushButton:focus' in app.styleSheet() and 'QSlider:focus' in app.styleSheet()
    print('PASS: primary text contrast, readable explanations without clipping, named focusable sliders and visible focus styles')
finally:w.close()
