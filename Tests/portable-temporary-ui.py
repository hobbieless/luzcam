"""Exercise real asynchronous photos, responsiveness and immutable history."""
import sys,time
from pathlib import Path
root=Path(__file__).resolve().parents[1]; sys.path.insert(0,str(root/'CrossPlatform'))
from PySide6.QtWidgets import QApplication
from PySide6.QtCore import QTimer
from luzcam.ui import Window

app=QApplication([]); w=Window(); w.moving=False; w.show(); app.processEvents()
def wait_for(check):
    deadline=time.monotonic()+20
    while not check() and time.monotonic()<deadline:
        app.processEvents(); time.sleep(.005)
    assert check(),w.photo_errors
try:
    ticks=[]; heartbeat=QTimer(); heartbeat.setInterval(10); heartbeat.timeout.connect(lambda:ticks.append(1)); heartbeat.start()
    for camera in range(3):
        w.change_camera(camera)
        if camera: w.preview.setChecked(True)
        for _ in range(7): w.advance()
        shot=w.session.history[-1]; key=shot.key
        wait_for(lambda:key in w.saved_photos)
        assert not w.photo.image.isNull() and not w.photo.message
        assert w.displayed_key==key
        snapshot=w.saved_photos[key]
        w.reset(); w.sliders[0].setValue(0)
        assert w.saved_photos[key]==snapshot
    # A rapid stream of previews has one active job and bounded pending work.
    w.change_camera(1); w.preview.setChecked(True)
    # Live view now adjusts only the visible video brightness. Exercise the
    # photo queue explicitly: slider changes intentionally do not render a
    # synthetic capture or replace live view with that generated photograph.
    for value in range(w.sliders[0].maximum()+1):
        w.sliders[0].setValue(value)
        w.photos.request(w.session.setting,'preview')
    target=w.session.setting.key
    assert len(w.photos.pending)<=2
    wait_for(lambda:target in w.photos.cache)
    assert w.displayed_key is None and not w.camera.lcd_review
    assert w.photos.cache_bytes<=w.photos.limit
    assert len(ticks)>10,'The event loop was blocked by photo rendering'
    w.review(0); assert w.photo.image==__import__('PySide6.QtGui',fromlist=['QImage']).QImage.fromData(w.saved_photos[w.session.history[0].key],'PNG')
    print('PASS: generated captures for 3 cameras, immutable history, responsive live view and bounded photo queue/cache')
finally:
    w.close()
