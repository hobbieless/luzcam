"""Run with QT_QPA_PLATFORM=offscreen for non-interactive smoke checks."""
import sys,time
from pathlib import Path
root=Path(__file__).resolve().parents[1]; sys.path.insert(0,str(root/'CrossPlatform'))
from PySide6.QtWidgets import QApplication
from luzcam.ui import Window
app=QApplication([]); w=Window(); w.show(); app.processEvents()
for camera in range(3):
 w.change_camera(camera); w.session.setting.set_thirds(True); w.reload_controls(); w.refresh(); w.session.setting.set_thirds(False); w.reload_controls(); w.refresh()
 for light in range(3):
  w.light.setCurrentIndex(light)
  for _ in range(7): w.advance(); app.processEvents()
  deadline=time.monotonic()+20
  while w.photo.image.isNull() and time.monotonic()<deadline:
   app.processEvents(); time.sleep(.005)
  assert not w.photo.image.isNull(),w.photo.message
  assert w.selected==len(w.session.history)-1
  w.review(0); w.reset()
assert len(w.session.history)==9
w.resize(1920,1080); app.processEvents()
assert abs(w.view.transform().m11()-w.view.transform().m22())<1e-12
w.close(); print('PASS: Qt host, 3 cameras × 3 lights, frozen captures, review/reset and proportional scaling')
