"""Language menu stays legible, vectorial and keyboard-operable inside the scene."""
import os,sys,tempfile
from pathlib import Path
os.environ.setdefault('QT_QPA_PLATFORM','offscreen')
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'CrossPlatform'))
from PySide6.QtCore import QSettings,Qt,QTimer,QEvent
from PySide6.QtGui import QPainterPath
from PySide6.QtWidgets import QApplication,QMessageBox,QTextEdit
from PySide6.QtTest import QTest
from luzcam.ui import Window
from luzcam.i18n import language,set_language

app=QApplication([])
with tempfile.TemporaryDirectory(prefix='luzcam-language-') as prefs:
    QSettings.setDefaultFormat(QSettings.IniFormat);QSettings.setPath(QSettings.IniFormat,QSettings.UserScope,prefs)
    w=Window();w.moving=False;w.show()
    def settle():
        for _ in range(4):app.processEvents()
    try:
        w.configure();settle();c=w.language_picker;key=w.session.setting.key
        assert c.count()==2 and c.accessibleName()=='Idioma'
        c.grab();assert isinstance(c._outline_cache[1][0],QPainterPath)
        for expected,nav,name in [('en',Qt.Key_End,'Language'),('es',Qt.Key_Home,'Idioma')]:
            c.showPopup();settle()
            assert c.view().geometry().top()<=1,'Native menu bands returned'
            assert c.view().visualRect(c.model().index(0,0)).height()==c.view().visualRect(c.model().index(1,0)).height()
            QTest.keyClick(c.view(),nav);QTest.keyClick(c.view(),Qt.Key_Return);settle()
            assert language.code==expected and c.accessibleName()==name
            assert w.settings_overlay is not None and not w.main_page.isEnabled()
            assert w.session.setting.key==key and not w.session.history
        c.showPopup();settle();QTest.keyClick(c.view(),Qt.Key_Escape);settle()
        assert not c.view().window().isVisible() and w.settings_overlay is not None
        w.close_presentation();settle();assert w.main_page.isEnabled()
        for code,show,hide in [('es','Mostrar detalles…','Ocultar detalles…'),('en','Show details…','Hide details…')]:
            set_language(code);failures=[]
            def inspect_credits():
                d=app.activeModalWidget()
                try:
                    assert isinstance(d,QMessageBox)
                    b=next(b for b in d.buttons() if d.buttonRole(b)==QMessageBox.ActionRole)
                    assert b.text()==show,b.text()
                    assert b.width()>=b.fontMetrics().horizontalAdvance(b.text())+24,'Details label clipped'
                    b.click();settle();assert b.text()==hide,b.text()
                    assert b.width()>=b.fontMetrics().horizontalAdvance(b.text())+24,'Hide label clipped'
                    assert any(e.isVisibleTo(d) for e in d.findChildren(QTextEdit))
                    b.click();settle();assert b.text()==show,b.text()
                except Exception as e:failures.append(repr(e))
                finally:
                    if isinstance(d,QMessageBox):d.accept()
            QTimer.singleShot(30,inspect_credits);w.show_credits()
            assert not failures,failures
            app.sendPostedEvents(None,QEvent.DeferredDelete);settle()
            assert not w.findChildren(QMessageBox),'Closed credits retained in memory'
        print('PASS: no menu bands, vector combo, equal rows, ES/EN keyboard selection, Escape and accessible name; exposure/history unchanged')
    finally:w.close();set_language('es')
