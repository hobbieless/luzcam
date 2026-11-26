"""Freeze the displayed video timestamp, render that phase, retain distinct shots."""
import sys,time,tempfile
from dataclasses import replace
from pathlib import Path
import numpy as np
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'CrossPlatform'))
from luzcam.model import Setting
from luzcam.temporary_photo import TemporaryPhoto
from PySide6.QtWidgets import QApplication
from PySide6.QtCore import QSettings
from PySide6.QtGui import QImage,QColor
from PySide6.QtMultimedia import QVideoFrame
from luzcam.ui import Window
renderer=TemporaryPhoto()
for light in range(3):
    setting=Setting(s=10,light=light,scene_frame=11)
    original=renderer._prepared(setting).copy()
    assert not np.array_equal(original,renderer._prepared(replace(setting,scene_frame=0)))
    assert np.array_equal(original,renderer._prepared(setting))
app=QApplication([])
with tempfile.TemporaryDirectory() as folder:
    w=Window(QSettings(str(Path(folder)/'test.ini'),QSettings.IniFormat)); w.show(); app.processEvents()
    w.player.stop(); w.pause.setChecked(True); w.sliders[1].setValue(10)
    for phase,color in ((11,'#448866'),(29,'#886644')):
        w.show_live(); w.player.stop()
        image=QImage(960,540,QImage.Format_RGB32); image.fill(QColor(color))
        frame=QVideoFrame(image); frame.setStartTime(round(phase/30*1000000))
        w.video_frame(frame); assert w.video_scene_frame==phase
        w.advance()
        assert w.session.shot.scene_frame==phase
        assert w.photo.image==frame.toImage(), 'Busy scene jumped away from displayed frame'
        frozen=w.session.shot.key
        late=QVideoFrame(image); late.setStartTime(0); w.video_frame(late)
        assert w.session.shot.key==frozen and w.video_scene_frame==phase
        for _ in range(6): w.advance()
        deadline=time.monotonic()+20
        while frozen not in w.saved_photos and time.monotonic()<deadline: app.processEvents(); time.sleep(.01)
        assert frozen in w.saved_photos
        assert w.session.history[-1].scene_frame==phase
    assert w.session.history[0].key!=w.session.history[1].key
    first=bytes(w.saved_photos[w.session.history[0].key]); w.review(0); app.processEvents()
    assert bytes(w.saved_photos[w.session.history[0].key])==first
    assert w.photo.image==QImage.fromData(first,'PNG')
    w.close()
print('PASS: timestamp freeze, exposure phase, late-frame rejection, distinct immutable shots and review')
