"""The explicit 100-shot policy never silently removes or replaces a capture."""
import os,sys,tempfile
from pathlib import Path
os.environ.setdefault('QT_QPA_PLATFORM','offscreen')
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'CrossPlatform'))
from luzcam.model import Session
s=Session()
for i in range(100):
    s.setting.i=i%len(s.setting.isos)
    for _ in range(7):s.advance()
assert len(s.history)==100
keys=[x.key for x in s.history];last=s.shot
for _ in range(20):s.advance()
assert len(s.history)==100 and keys==[x.key for x in s.history] and s.shot is last
s.reset();s.advance();assert s.phase==0 and len(s.history)==100
from PySide6.QtWidgets import QApplication,QMessageBox
from PySide6.QtCore import QSettings,QTimer,QEvent
from luzcam.ui import Window
app=QApplication([])
with tempfile.TemporaryDirectory() as folder:
    w=Window(QSettings(folder+'/prefs.ini',QSettings.IniFormat));w.moving=False
    w.session=s;w.saved_photos['sentinel']=b'unchanged';w.refresh()
    assert not w.fire.isEnabled() and w.clear_film.isEnabled()
    w.advance();assert w.session.phase==0 and w.saved_photos['sentinel']==b'unchanged'
    def cancel():
        dialog=app.activeModalWidget();assert dialog.defaultButton()==dialog.button(QMessageBox.Cancel);dialog.reject()
    QTimer.singleShot(0,cancel);w.confirm_clear_film()
    app.sendPostedEvents(None,QEvent.DeferredDelete);assert not w.findChildren(QMessageBox)
    assert len(w.session.history)==100 and w.saved_photos['sentinel']==b'unchanged'
    QTimer.singleShot(0,lambda:app.activeModalWidget().done(QMessageBox.Yes));w.confirm_clear_film()
    app.sendPostedEvents(None,QEvent.DeferredDelete);assert not w.findChildren(QMessageBox)
    assert not w.session.history and not w.saved_photos and w.fire.isEnabled()
    w.close()
print('PASS: 100-shot limit, disabled capture/shortcut, no automatic deletion, cancel preserved, explicit clear releases saved photos')
