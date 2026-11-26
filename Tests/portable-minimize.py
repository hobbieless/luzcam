"""Minimizing pauses media/work progression without changing user settings."""
import os,sys,tempfile,time
from pathlib import Path
os.environ.setdefault('QT_QPA_PLATFORM','offscreen')
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'CrossPlatform'))
from PySide6.QtWidgets import QApplication
from PySide6.QtCore import QSettings
from PySide6.QtMultimedia import QMediaPlayer
from luzcam.ui import Window
app=QApplication([])
with tempfile.TemporaryDirectory() as folder:
    w=Window(QSettings(folder+'/prefs.ini',QSettings.IniFormat));w.show();w.moving=True;w.refresh()
    deadline=time.monotonic()+5
    while w.player.playbackState()!=QMediaPlayer.PlayingState and time.monotonic()<deadline:app.processEvents();time.sleep(.01)
    assert w.player.playbackState()==QMediaPlayer.PlayingState
    key=w.session.setting.key;w.showMinimized();app.processEvents()
    assert not w.video_poll.isActive() and w.player.playbackState()!=QMediaPlayer.PlayingState and w.moving
    w.showNormal();app.processEvents();assert w.player.playbackState()==QMediaPlayer.PlayingState
    w.moving=False;w.refresh();w.advance();w.pause.setChecked(False);w.schedule();assert w.timer.isActive()
    w.showMinimized();app.processEvents();assert not w.timer.isActive() and not w.video_poll.isActive()
    w.showNormal();app.processEvents();assert w.timer.isActive() and not w.moving
    assert w.session.setting.key==key;w.close()
print('PASS: media and progression pause when minimized; resume preserves user pause/settings')
