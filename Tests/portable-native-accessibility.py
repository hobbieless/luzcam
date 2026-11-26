"""Shared Qt accessibility tree/actions/scaled bounds; not a native reader certification."""
import os,sys,tempfile,gc
from pathlib import Path
os.environ.setdefault('QT_QPA_PLATFORM','offscreen')
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'CrossPlatform'))
from PySide6.QtWidgets import QApplication
from PySide6.QtGui import QAccessible,QAccessibleActionInterface
from PySide6.QtCore import QSettings,QPoint,QEvent,Qt
from luzcam.ui import Window
from luzcam.i18n import set_language,language
from luzcam import accessibility
app=QApplication([])
def iface(widget):return QAccessible.queryAccessibleInterface(widget)
def tree(widget):
    result=[];seen=set()
    def walk(a,depth=0):
        if not a or depth>20:return
        key=QAccessible.uniqueId(a)
        if key in seen:return
        seen.add(key);result.append(a)
        for i in range(a.childCount()):walk(a.child(i),depth+1)
    walk(iface(widget));return result
with tempfile.TemporaryDirectory() as folder:
    for cycle in range(3):
        w=Window(QSettings(folder+f'/prefs-{cycle}.ini',QSettings.IniFormat));w.moving=False;w.show();app.processEvents()
        nodes=tree(w);assert len(nodes)>50 and sum(a.role()==QAccessible.Slider for a in nodes)==3
        for width,height in ((800,450),(1600,900),(2240,1260)):
            w.resize(width,height);app.processEvents()
            for widget in [*w.sliders,w.fire,w.config]:
                a=iface(widget);assert a.text(QAccessible.Name)
                point=widget.mapTo(w.root,QPoint(widget.width()//2,widget.height()//2))
                expected=w.view.viewport().mapToGlobal(w.view.mapFromScene(w.root.graphicsProxyWidget().mapToScene(point)))
                assert (a.rect().center()-expected).manhattanLength()<=3,(a.rect(),expected)
                assert abs(a.rect().width()-widget.width()*w.view.transform().m11())<=2
        slider=w.sliders[0];a=iface(slider);old=slider.value()
        a.actionInterface().doAction(QAccessibleActionInterface.increaseAction());assert slider.value()==old+1
        a.valueInterface().setCurrentValue(old);assert slider.value()==old
        assert a.text(QAccessible.Value).startswith('f/')
        w.configure();app.processEvents();assert not w.main_page.isEnabled() and w.language_picker.isEnabled() and not w.shortcut.isEnabled()
        assert iface(w.fire).state().disabled
        before=w.session.phase;iface(w.fire).actionInterface().doAction(QAccessibleActionInterface.pressAction());assert w.session.phase==before
        combo=w.language_picker;iface(combo).actionInterface().doAction(QAccessibleActionInterface.showMenuAction());app.processEvents()
        options=iface(combo.view());assert options.role()==QAccessible.List and options.childCount()==2
        assert options.rect().width()<combo.view().width()+2 or w.view.transform().m11()>=.99
        row=options.child(1);assert row.text(QAccessible.Name)=='English'
        assert row.rect().width()<=combo.view().visualRect(combo.view().model().index(1,0)).width()*w.view.transform().m11()+2
        selection=options.selectionInterface();assert selection is not None
        assert selection.select(row) and language.code=='en'
        assert selection.selectedItemCount()==1 and selection.isSelected(row)
        assert iface(slider).text(QAccessible.Name).startswith('Aperture · f/')
        w.close_presentation();app.sendPostedEvents(None,QEvent.DeferredDelete);app.processEvents();assert w.main_page.isEnabled()
        fire=iface(w.fire);fire.actionInterface().doAction(QAccessibleActionInterface.pressAction());assert w.session.phase==1
        old=slider.value();iface(slider).valueInterface().setCurrentValue(old+1);assert slider.value()==old
        w.close();w.deleteLater();app.sendPostedEvents(None,QEvent.DeferredDelete);app.processEvents();nodes.clear();gc.collect()
    set_language('es')
assert not accessibility._instances,len(accessibility._instances)
print('PASS: accessible tree, roles, scaled bounds at 3 sizes, range/button/list actions, disabled modal controls, EN names and 3 clean lifecycles')
