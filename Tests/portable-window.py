"""Shared size/position restoration and proportional resize regression checks."""
import sys,tempfile
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'CrossPlatform'))
from luzcam.window_geometry import initial_geometry
assert initial_geometry(None,[(0,0,3840,2160)])[2:]==(1920,1080)
assert initial_geometry([120,80,2560,1440],[(0,0,3840,2160)])==(120,80,2560,1440)
assert initial_geometry([2,4,1600,900],[(0,0,3840,2160)])[2:]==(1920,1080)
assert initial_geometry([8000,8000,2560,1440],[(0,0,1280,720)])==(0,0,1280,720)
assert initial_geometry([-2500,50,2400,1350],[(-2560,0,2560,1440),(0,0,3840,2160)])[0]<0
assert initial_geometry(None,[(0,0,1920,1080,2)])[2:]==(960,540)
assert initial_geometry([50,40,2560,1440],[(0,0,1920,1080,2)])==(50,40,1280,720)
from PySide6.QtWidgets import QApplication
from PySide6.QtCore import QSettings
from luzcam.ui import Window
app=QApplication([])
with tempfile.TemporaryDirectory() as folder:
    settings=QSettings(str(Path(folder)/'window.ini'),QSettings.IniFormat)
    w=Window(settings); w.show(); app.processEvents()
    for width,height in [(1600,700),(1500,900),(2100,1200)]:
        w.resize(width,height); app.processEvents()
        assert abs(w.width()*9/16-w.height())<=1,(w.width(),w.height())
    w.resize(2240,1260); w.move(37,51); app.processEvents(); w.close()
    saved=list(map(int,settings.value('windowPixels16x9')))
    assert saved==[37,51,2240,1260],saved
    w=Window(settings); w.show(); app.processEvents()
    # Closing an automatically fitted window preserves the original larger preference.
    w.close(); assert list(map(int,settings.value('windowPixels16x9')))==saved
    w=Window(settings); w.show(); app.processEvents(); w.resize(1200,675); app.processEvents(); w.close()
    assert not settings.contains('windowPixels16x9')
print('PASS: Full HD, larger geometry, screen fitting, position and 16:9 resize')
