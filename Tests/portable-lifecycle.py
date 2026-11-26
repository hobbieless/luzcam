"""Close during real photo work and reopen without orphaned workers."""
import os,sys,tempfile
from pathlib import Path
os.environ.setdefault('QT_QPA_PLATFORM','offscreen')
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'CrossPlatform'))
from PySide6.QtWidgets import QApplication
from PySide6.QtCore import QSettings
from luzcam.ui import Window
app=QApplication([])
with tempfile.TemporaryDirectory() as folder:
    for camera in range(3):
        w=Window(QSettings(folder+'/prefs.ini',QSettings.IniFormat))
        w.moving=False;w.change_camera(camera)
        s=w.session.setting;s.scene_frame=13
        w.photos.request(s,'capture')
        assert w.photos.active is not None
        w.close();app.processEvents()
        assert w.photos.closing and not w.photos.pending
        assert w.photos.pool.activeThreadCount()==0
        assert not w.timer.isActive()
    windows=[Window(QSettings(folder+f'/second-{i}.ini',QSettings.IniFormat)) for i in range(2)]
    for w in windows:w.photos.request(w.session.setting,'capture')
    for w in windows:
        w.close();app.processEvents()
        assert w.photos.pool.activeThreadCount()==0
print('PASS: three reopen/close-during-calculation cycles and two windows leave no active photo workers')
