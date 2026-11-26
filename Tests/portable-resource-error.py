"""A missing local scene produces a readable error and clean worker shutdown."""
import os,sys,tempfile,time
from pathlib import Path
os.environ.setdefault('QT_QPA_PLATFORM','offscreen')
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'CrossPlatform'))
from PySide6.QtWidgets import QApplication
from PySide6.QtCore import QSettings
from luzcam.ui import Window
from luzcam.temporary_photo import TemporaryPhoto
app=QApplication([])
with tempfile.TemporaryDirectory() as folder:
    class MissingScene:
        def render(self,setting):return TemporaryPhoto(root=Path(folder)/'missing').render(setting)
    w=Window(QSettings(folder+'/prefs.ini',QSettings.IniFormat));w.moving=False;w.photos.renderer=MissingScene()
    for _ in range(7):w.advance();w.timer.stop()
    key=w.session.history[-1].key;deadline=time.monotonic()+5
    while key not in w.photo_errors and time.monotonic()<deadline:app.processEvents();time.sleep(.01)
    assert key in w.photo_errors and 'No se pudo calcular' in w.photo.message
    assert key not in w.saved_photos and len(w.session.history)==1
    w.reset();assert w.session.phase==0 and w.fire.isEnabled();w.close()
    assert w.photos.pool.activeThreadCount()==0
print('PASS: missing resource reported, no fake photo, reset usable and no worker left running')
