"""Switch languages without touching exposure, immutable captures or layout."""
import sys,os
from pathlib import Path
os.environ.setdefault('QT_QPA_PLATFORM','offscreen')
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'CrossPlatform'))
from PySide6.QtWidgets import QApplication
from PySide6.QtGui import QFontMetrics
from PySide6.QtCore import Qt
from luzcam.ui import Window
from luzcam.i18n import set_language,language
from luzcam.i18n import CATALOG
import string
for source,target in CATALOG.items():
    fields=lambda value: sorted(name for _,name,_,_ in string.Formatter().parse(value) if name is not None)
    assert target.strip() and fields(source)==fields(target),(source,target)
for source in ('Ampliar imagen','Volver al visor','Volver a la escena sin borrar el carrete'):
    assert source in CATALOG and CATALOG[source]!=source
app=QApplication([]);w=Window();w.moving=False;w.show();app.processEvents()
try:
    for camera in range(3):
        w.change_camera(camera);key=w.session.setting.key
        for code in ('en','es','en'):
            set_language(code);w.refresh();app.processEvents()
            assert w.session.setting.key==key
            assert w.camera_name.text()==(('DSLR','Mirrorless','Compact') if code=='en' else ('Réflex','Sin espejo','Compacta'))[camera]
            for phase in range(8):
                while w.session.phase<phase:w.advance()
                app.processEvents();m=QFontMetrics(w.expl.font())
                assert m.boundingRect(w.expl.contentsRect(),Qt.TextWordWrap,w.expl.text()).height()<=w.expl.height(),(camera,code,phase,w.expl.text())
            saved=w.session.history[-1].key;set_language('es' if code=='en' else 'en');w.refresh()
            assert w.session.history[-1].key==saved
            w.reset()
        w.enlarge_camera();set_language('en');w.refresh();set_language('es');app.processEvents()
        assert w.detail_phase.text()=='Preparar la cámara';w.close_presentation()
    w.configure();w.language_picker.setCurrentIndex(1);assert language.code=='en'
    w.close_presentation();w.configure();assert w.language_picker.currentIndex()==1
    w.language_picker.setCurrentIndex(0);w.close_presentation()
    print('PASS: ES/EN labels, all phases/cameras fit, settings/captures unchanged and language preference retained')
finally:set_language('es');w.close()
