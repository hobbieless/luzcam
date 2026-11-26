"""Electronic LCD follows each video frame; exposure simulation only maps RGB."""
import sys,tempfile
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'CrossPlatform'))
from PySide6.QtWidgets import QApplication
from PySide6.QtCore import QSettings
from PySide6.QtGui import QImage,QColor
from PySide6.QtMultimedia import QVideoFrame
from luzcam.ui import Window
from luzcam.liveview import exposure_preview
app=QApplication([])
with tempfile.TemporaryDirectory() as folder:
    for camera in (1,2):
        w=Window(QSettings(str(Path(folder)/'prefs.ini'),QSettings.IniFormat));w.change_camera(camera);w.player.stop()
        for preview in (False,True):
            w.preview.setChecked(preview);w.player.stop()
            for phase,color in ((11,'#306040'),(29,'#704020')):
                image=QImage(80,45,QImage.Format_RGB32);image.fill(QColor(color));image.setPixelColor(phase,20,QColor('#e0a080'))
                frame=QVideoFrame(image);frame.setStartTime(round(phase/30*1e6));w.video_frame(frame)
                expected=exposure_preview(frame.toImage(),w.session.setting.meter_third) if preview else frame.toImage()
                assert w.camera.electronic==w.photo.image==expected
                assert w.video_scene_frame==phase
        w.preview.setChecked(False);w.player.stop();w.video_frame(frame)
        assert w.camera.electronic==frame.toImage()
        w.close()
print('PASS: live LCD matches video frames; brightness-only simulation preserves frame positions; disabling restores source')
