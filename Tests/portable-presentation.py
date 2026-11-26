"""Interaction checks for the single desktop presentation (Windows and macOS)."""
import sys
from pathlib import Path
root=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(root/'CrossPlatform'))
from PySide6.QtWidgets import QApplication
from PySide6.QtGui import QFontDatabase
from luzcam.ui import Window

app=QApplication([])
w=Window(); w.moving=False; w.show(); app.processEvents()
try:
    assert {'Noto Sans','Noto Serif','Noto Sans Mono'} <= set(QFontDatabase.families())
    # Configuration applies immediately, including when dismissed with Escape.
    w.configure(); w.config_thirds.setChecked(True); w.close_presentation()
    assert w.session.setting.thirds and w.sliders[1].maximum()>10
    w.configure(); w.config_thirds.setChecked(False); w.close_presentation()
    w.sliders[0].setValue(4)
    for _ in range(7): w.advance()
    saved=w.session.history[0]; saved_key=saved.key
    w.sliders[0].setValue(1)
    assert w.session.history[0].key==saved_key
    w.enlarge_photo(); app.processEvents()
    assert w.detail_photo.image==w.photo.image
    assert w.root.currentWidget() is not w.main_page
    w.close_presentation(); assert w.root.currentWidget() is w.main_page
    w.show_live(); assert w.selected is None and w.session.phase==0
    w.enlarge_camera(); app.processEvents()
    for camera in range(3):
        w.detail_camera_buttons[camera].click()
        assert w.session.setting.camera==camera
        assert w.detail_camera.camera==camera
    w.advance(); assert w.session.busy
    assert not any(b.isEnabled() for b in w.detail_camera_buttons)
    w.reset(); w.close_presentation()
    # Continuous capture can pause without advancing and reset cancels its timer.
    w.enlarge_camera(); w.pause.setChecked(False); w.advance(); phase=w.session.phase
    assert w.timer.isActive() and w.fire.text()=='Pausar'
    assert w.detail_fire.text()==w.fire.text()
    w.advance(); assert not w.timer.isActive() and w.session.phase==phase
    w.advance(); assert w.timer.isActive() and w.session.phase==phase+1
    w.reset(); assert not w.timer.isActive()
    for width,height in ((960,540),(1920,1080),(1200,1000),(3840,2160)):
        w.resize(width,height); app.processEvents()
        transform=w.view.transform()
        assert abs(transform.m11()-transform.m22())<1e-12
        assert w.root.size().width()==1600 and w.root.size().height()==900
    print('PASS: shared fonts, settings, immutable review, in-stage enlargements, camera selection, pause/cancel and scaling')
finally:
    w.close()
