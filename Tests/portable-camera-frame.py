"""All capture phases must keep the camera body registered at a fixed scale."""
import os, sys, tempfile
from pathlib import Path
os.environ.setdefault('QT_QPA_PLATFORM', 'offscreen')
root=Path(__file__).resolve().parents[1];sys.path.insert(0,str(root/'CrossPlatform'))
from PySide6.QtCore import QSettings
from PySide6.QtWidgets import QApplication
from luzcam.ui import Window
from luzcam.i18n import set_language

app=QApplication([])
with tempfile.TemporaryDirectory(prefix='luzcam-frame-') as prefs:
    QSettings.setDefaultFormat(QSettings.IniFormat)
    QSettings.setPath(QSettings.IniFormat,QSettings.UserScope,prefs)
    w=Window();w.moving=False;w.show()
    def settle():
        for _ in range(4):app.processEvents()
    def frame(camera):
        return (camera.geometry(),camera.artwork_frame())
    try:
        for code in ('es','en'):
            set_language(code)
            for camera in range(3):
                w.reset();w.change_camera(camera);settle()
                expected=frame(w.camera)
                w.enlarge_camera();settle();detail=frame(w.detail_camera)
                for phase in range(8):
                    assert w.session.phase==phase
                    w.refresh();settle()
                    for time in (0,450,900):
                        w.camera.animation.setCurrentTime(time);settle()
                        assert frame(w.camera)==expected,(code,camera,phase,'main')
                        assert frame(w.detail_camera)==detail,(code,camera,phase,'detail')
                    assert w.phase_title.heightForWidth(w.phase_title.width())<=w.phase_title.height(),(code,camera,phase,'title clipped')
                    assert w.expl.heightForWidth(w.expl.width())<=w.expl.height(),(code,camera,phase,'explanation clipped')
                    if phase<7:w.advance()
                w.close_presentation();w.reset();settle()
                assert frame(w.camera)==expected,(code,camera,'reset')
                if camera==0:
                    w.check_aperture();settle()
                    assert frame(w.camera)==expected,(code,'aperture preview')
                    assert w.expl.heightForWidth(w.expl.width())<=w.expl.height()
                    w.check_aperture()
        print('PASS: three camera frames stable in eight phases, tween, reset, ES/EN and enlarged view; text fits')
    finally:
        w.close();set_language('es')
