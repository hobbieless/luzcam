"""Exercise translated UI flows offline and validate catalogue placeholders."""
import os,sys,json,argparse,string,re,tempfile
from pathlib import Path
os.environ.setdefault('QT_QPA_PLATFORM','offscreen')
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'CrossPlatform'))
p=argparse.ArgumentParser();p.add_argument('--output',type=Path,required=True);a=p.parse_args()
from luzcam import i18n
original=i18n.text;observed={}
def record(source):
    result=original(source)
    if i18n.language.code=='en' and source:observed[source]=result
    return result
i18n.text=record
from luzcam.ui import Window
from PySide6.QtWidgets import QApplication
from PySide6.QtCore import QSettings
app=QApplication([])
with tempfile.TemporaryDirectory() as folder:
    w=Window(QSettings(folder+'/prefs.ini',QSettings.IniFormat));w.moving=False
    try:
        i18n.set_language('en');w.show();app.processEvents()
        for camera in range(3):
            w.reset();w.change_camera(camera)
            for light in range(3):
                w.light.setCurrentIndex(light)
                for phase in range(8):
                    while w.session.phase<phase:w.advance();w.timer.stop()
                    w.refresh();app.processEvents()
                w.reset()
            w.enlarge_camera();w.refresh();app.processEvents();w.close_presentation()
        w.configure();app.processEvents();w.close_presentation()
    finally:w.close();i18n.set_language('es')
def fields(value):
    return sorted(name for _,name,_,_ in string.Formatter().parse(value) if name is not None)
errors=[s for s,t in i18n.CATALOG.items() if not t.strip() or fields(s)!=fields(t)]
# Unchanged values are candidates for review, not necessarily missing translations.
unchanged=sorted(s for s,t in observed.items() if s==t and re.search('[A-Za-zÀ-ÿ]',s))
report={'catalogueEntries':len(i18n.CATALOG),'placeholderErrors':errors,'observedStrings':len(observed),
 'unchangedCandidates':unchanged,'scope':'Three cameras, three lights, eight phases, enlarged camera and settings. Candidates may be technical units or proper names; not a full accessibility certification.'}
a.output.parent.mkdir(parents=True,exist_ok=True);a.output.write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf8')
print(json.dumps(report,ensure_ascii=False,indent=2));assert not errors
