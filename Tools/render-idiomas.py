"""Offline review of both languages; never drives the desktop."""
import os,sys
from pathlib import Path
os.environ.setdefault('QT_QPA_PLATFORM','offscreen')
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'CrossPlatform'))
from PySide6.QtWidgets import QApplication
from PySide6.QtCore import QEvent
from luzcam.ui import Window
from luzcam.i18n import set_language
out=ROOT/'build/windows-free-review';out.mkdir(parents=True,exist_ok=True)
app=QApplication([]);w=Window();w.moving=False;w.resize(1600,900);w.show()
try:
    for code in ('es','en'):
        set_language(code)
        for camera in range(3):
            w.reset();w.change_camera(camera);app.processEvents()
            w.camera.animation.stop();w.camera.pose=dict(w.camera.target)
            app.processEvents();assert w.root.grab().save(str(out/f'{code}-camera-{camera}.png'))
        w.configure();app.processEvents();assert w.root.grab().save(str(out/f'{code}-settings.png'));w.close_presentation();app.sendPostedEvents(None,QEvent.DeferredDelete)
finally:set_language('es');w.close()
print('Rendered both languages and settings:',out)
