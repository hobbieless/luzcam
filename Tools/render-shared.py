"""Render the same deterministic review states on each target system.

Run with the CrossPlatform environment; output defaults to build/qa-shared.
The images support visual comparison, not a claim of parity by themselves.
"""
import argparse
import hashlib
import json
import os
import platform
import sys
import time
import tempfile
from pathlib import Path
os.environ.setdefault('QT_QPA_PLATFORM','offscreen')
root=Path(__file__).resolve().parents[1]; sys.path.insert(0,str(root/'CrossPlatform'))
from PySide6.QtCore import qVersion,QSettings
from PySide6.QtWidgets import QApplication
from luzcam.ui import Window

parser=argparse.ArgumentParser(); parser.add_argument('--output',type=Path,default=root/'build/qa-shared')
parser.add_argument('--language',choices=('es','en'),default='es')
parser.add_argument('--width',type=int,choices=(800,1280,1600,1920,2240),default=1600)
args=parser.parse_args()
args.output.mkdir(parents=True,exist_ok=True)
app=QApplication([])
# Review runs must neither load nor overwrite the owner's preferences.
preferences=tempfile.TemporaryDirectory(prefix='luzcam-review-')
settings=QSettings(str(Path(preferences.name)/'settings.ini'),QSettings.IniFormat)
settings.setValue('language',args.language)
w=Window(settings); w.moving=False; w.show(); app.processEvents()
# Complete native-screen restoration before requesting the review viewport.
# The offscreen screen can be smaller than the requested test dimensions.
w.resize(args.width,round(args.width*9/16)); app.processEvents()
manifest={'system':platform.system(),'python':platform.python_version(),'qt':qVersion(),'design':[1600,900],
          'language':args.language,'requestedWidth':args.width,'viewport':[w.view.viewport().width(),w.view.viewport().height()],
          'isolatedPreferences':True,'images':{}}
def save(name):
    app.processEvents()
    if w.displayed_key:
        deadline=time.monotonic()+20
        while w.displayed_key not in w.saved_photos and w.displayed_key not in w.photos.cache and time.monotonic()<deadline:
            app.processEvents(); time.sleep(.01)
        assert not w.photo.image.isNull() and not w.photo.message,w.photo.message
    for camera in (w.camera,getattr(w,'detail_camera',None)):
        if camera:
            camera.animation.stop(); camera.pose=dict(camera.target); camera.update()
    app.processEvents()
    surface=w.root if args.width==1600 else w.view.viewport()
    file=args.output/(name+'.png'); assert surface.grab().save(str(file))
    manifest['images'][file.name]=hashlib.sha256(file.read_bytes()).hexdigest()
try:
    for camera in range(3):
        w.reset(); w.change_camera(camera)
        for phase in (0,4,7):
            while w.session.phase<phase: w.advance()
            w.refresh(); save(f'camera-{camera}-phase-{phase}')
            if phase==4:
                w.enlarge_camera(); save(f'camera-{camera}-detail'); w.close_presentation()
    w.enlarge_photo(); save('photo-detail'); w.close_presentation()
    w.reset(); w.configure(); save('settings'); w.close_presentation()
finally:
    w.close()
    preferences.cleanup()
(args.output/'manifest.json').write_text(json.dumps(manifest,indent=2),encoding='utf-8')
print(f'Rendered {len(manifest["images"])} shared review states in {args.output}')
