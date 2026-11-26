"""DSLR display mode, frozen review, noise graphic and shutter placement."""
import sys,time
from pathlib import Path
root=Path(__file__).resolve().parents[1]; sys.path.insert(0,str(root/'CrossPlatform'))
from PySide6.QtWidgets import QApplication
from luzcam.ui import Window,ShutterButton
app=QApplication([]); w=Window(); w.moving=False; w.show(); app.processEvents()
try:
 assert isinstance(w.fire,ShutterButton)
 assert w.fire.parentWidget() is w.shutter_controls
 assert w.fire.width()==w.fire.height()
 assert w.shutter_controls.y()<w.camera.height()/2
 assert not w.camera.lcd_review and w.camera.electronic.isNull()
 w.sliders[2].setValue(0); w.camera.animation.stop(); w.camera.pose=dict(w.camera.target); w.sensitivity.update(); app.processEvents(); quiet=w.sensitivity.grab().toImage()
 w.sliders[2].setValue(5); w.camera.animation.stop(); w.camera.pose=dict(w.camera.target); w.sensitivity.update(); app.processEvents(); noisy=w.sensitivity.grab().toImage()
 assert quiet!=noisy
 assert w.camera.lcd_setting.isos[w.camera.lcd_setting.i]==3200
 for _ in range(7):w.advance()
 deadline=time.monotonic()+20
 while w.session.history[-1].key not in w.saved_photos and time.monotonic()<deadline:app.processEvents(); time.sleep(.01)
 w.refresh(); app.processEvents()
 assert w.camera.lcd_review and not w.camera.electronic.isNull()
 shot=w.session.history[-1]; key=shot.key
 w.sliders[2].setValue(0); app.processEvents()
 assert w.camera.lcd_setting.key==key and w.camera.lcd_setting.isos[w.camera.lcd_setting.i]==3200
 w.enlarge_camera(); app.processEvents()
 assert isinstance(w.detail_fire,ShutterButton)
 assert w.detail_camera.lcd_setting.key==key and w.detail_camera.lcd_review
 w.close_presentation(); w.show_live()
 assert not w.camera.lcd_review and w.camera.electronic.isNull()
 print('PASS: round shutter near camera, ISO noise response, settings LCD and immutable review photo on both camera views')
finally:w.close()
