"""A burst of decoded frames retains only the latest displayed timestamp."""
import os,sys,tempfile
from pathlib import Path
os.environ.setdefault('QT_QPA_PLATFORM','offscreen')
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'CrossPlatform'))
from PySide6.QtWidgets import QApplication
from PySide6.QtGui import QImage,QColor
from PySide6.QtMultimedia import QVideoFrame
from PySide6.QtCore import QSettings
from luzcam.ui import Window
app=QApplication([])
with tempfile.TemporaryDirectory() as folder:
    w=Window(QSettings(folder+'/prefs.ini',QSettings.IniFormat));w.player.stop();w.video_poll.stop();w.moving=True
    image=QImage(48,32,QImage.Format_RGB32);image.fill(QColor('#448866'))
    for i in range(100):
        frame=QVideoFrame(image);frame.setStartTime(round(i/30*1000000));w.sink.setVideoFrame(frame)
    assert w.video_frames_presented==0
    w.poll_video();assert w.video_frames_presented==1 and w.video_scene_frame==99%45
    w.poll_video();assert w.video_frames_presented==1
    w.advance();assert w.session.shot.scene_frame==99%45
    w.close();assert not w.video_poll.isActive()
print('PASS: latest-frame polling coalesces 100 frames, skips duplicates, captures displayed phase and stops on close')
