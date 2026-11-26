"""Shape text normally, then paint scalable glyph outlines instead of glyph bitmaps."""
from .i18n import Translatable,text
from functools import lru_cache
from PySide6.QtCore import Qt,QPointF
from PySide6.QtGui import QPainter,QFont,QPainterPath,QTextLayout,QTextOption,QPalette,QColor,QPen
from PySide6.QtWidgets import QLabel,QPushButton,QCheckBox,QStyle,QStyleOptionButton,QComboBox,QListView,QStyledItemDelegate,QStyleOptionComboBox,QStyleOptionViewItem

@lru_cache(maxsize=256)
def _cached_outline(text,font_key,width,wrap,alignment):
    font=QFont();font.fromString(font_key)
    alignment=Qt.AlignmentFlag(alignment)
    layout=QTextLayout(text.replace('\n','\u2028'),font)
    option=QTextOption();option.setWrapMode(QTextOption.WrapAtWordBoundaryOrAnywhere if wrap else QTextOption.NoWrap)
    option.setAlignment(alignment & (Qt.AlignLeft|Qt.AlignRight|Qt.AlignHCenter|Qt.AlignJustify))
    layout.setTextOption(option);layout.beginLayout();height=0
    while True:
        line=layout.createLine()
        if not line.isValid():break
        line.setLineWidth(max(1,width));line.setPosition(QPointF(0,height));height+=line.height()
    layout.endLayout();path=QPainterPath()
    for run in layout.glyphRuns():
        raw=run.rawFont()
        for index,position in zip(run.glyphIndexes(),run.positions()):
            glyph=raw.pathForGlyph(index);glyph.translate(position);path.addPath(glyph)
    path.setFillRule(Qt.WindingFill)
    return path,height

def outline(text,font,width,wrap=False,alignment=Qt.AlignLeft):
    return _cached_outline(text,font.toString(),width,wrap,int(alignment))

def paint_text(p,rect,text,font,color,alignment=Qt.AlignLeft|Qt.AlignVCenter,wrap=False,cache=None):
    key=(text,font.toString(),rect.width(),wrap,int(alignment))
    if cache is not None and cache[0]==key:path,height=cache[1]
    else:
        path,height=outline(text,font,rect.width(),wrap,alignment)
        if cache is not None:cache[:]=[key,(path,height)]
    y=rect.y()
    if alignment & Qt.AlignVCenter:y+=(rect.height()-height)/2
    elif alignment & Qt.AlignBottom:y+=rect.height()-height
    p.save();p.setRenderHint(QPainter.Antialiasing);p.setClipRect(rect,Qt.IntersectClip)
    p.translate(rect.x(),y);p.fillPath(path,color);p.restore()

def draw_vector_text(p,rect,alignment,value):
    paint_text(p,rect,text(value),p.font(),p.pen().color(),alignment)

class VectorLabel(Translatable,QLabel):
    def __init__(self,*args,**kwargs):
        super().__init__(*args,**kwargs);self._outline_cache=[None,None];self._bind_language()
    def paintEvent(self,event):
        # QLabel keeps its original string, sizing, font and accessibility role.
        p=QPainter(self);group=QPalette.Active if self.isEnabled() else QPalette.Disabled
        paint_text(p,self.contentsRect(),self.text(),self.font(),self.palette().color(group,QPalette.WindowText),
                   self.alignment(),self.wordWrap(),self._outline_cache)

class VectorButton(Translatable,QPushButton):
    def __init__(self,*args,**kwargs):
        super().__init__(*args,**kwargs);self._outline_cache=[None,None];self._bind_language()
    def paintEvent(self,event):
        if not self.text():return super().paintEvent(event)
        option=QStyleOptionButton();self.initStyleOption(option);option.text=''
        p=QPainter(self);self.style().drawControl(QStyle.CE_PushButton,option,p,self)
        rect=self.style().subElementRect(QStyle.SE_PushButtonContents,option,self)
        if self.isDown():rect.translate(self.style().pixelMetric(QStyle.PM_ButtonShiftHorizontal),self.style().pixelMetric(QStyle.PM_ButtonShiftVertical))
        group=QPalette.Active if self.isEnabled() else QPalette.Disabled
        color=QColor('white') if self.isEnabled() and (self.isChecked() or self.objectName()=='primary') else self.palette().color(group,QPalette.ButtonText)
        paint_text(p,rect,self.text(),self.font(),color,Qt.AlignCenter,cache=self._outline_cache)

class VectorCheckBox(Translatable,QCheckBox):
    def __init__(self,*args,**kwargs):
        super().__init__(*args,**kwargs);self._outline_cache=[None,None];self._bind_language()
    def paintEvent(self,event):
        option=QStyleOptionButton();self.initStyleOption(option)
        rect=self.style().subElementRect(QStyle.SE_CheckBoxContents,option,self);option.text=''
        p=QPainter(self);self.style().drawControl(QStyle.CE_CheckBox,option,p,self)
        group=QPalette.Active if self.isEnabled() else QPalette.Disabled
        paint_text(p,rect,self.text(),self.font(),self.palette().color(group,QPalette.WindowText),cache=self._outline_cache)
        if self.isChecked():
            box=self.style().subElementRect(QStyle.SE_CheckBoxIndicator,option,self)
            tick=QPainterPath();tick.moveTo(box.left()+box.width()*.22,box.top()+box.height()*.51);tick.lineTo(box.left()+box.width()*.43,box.top()+box.height()*.72);tick.lineTo(box.left()+box.width()*.79,box.top()+box.height()*.28)
            p.setRenderHint(QPainter.Antialiasing);p.strokePath(tick,QPen(QColor('white'),1.8,Qt.SolidLine,Qt.RoundCap,Qt.RoundJoin))

class VectorItemDelegate(QStyledItemDelegate):
    """Normal Qt selection/background, with the same scalable text as the app."""
    def paint(self,painter,option,index):
        option=QStyleOptionViewItem(option);self.initStyleOption(option,index)
        value=option.text;option.text=''
        option.widget.style().drawControl(QStyle.CE_ItemViewItem,option,painter,option.widget)
        color=QColor('white') if option.state & QStyle.State_Selected else option.palette.color(QPalette.Text)
        paint_text(painter,option.rect.adjusted(8,0,-8,0),value,option.font,color)

class VectorComboBox(QComboBox):
    def __init__(self,*args,**kwargs):
        super().__init__(*args,**kwargs);self._outline_cache=[None,None]
        view=QListView();view.setSpacing(0);view.setAlternatingRowColors(False)
        self.setView(view);self.setItemDelegate(VectorItemDelegate(self))
    def paintEvent(self,event):
        option=QStyleOptionComboBox();self.initStyleOption(option);value=option.currentText;option.currentText=''
        painter=QPainter(self);self.style().drawComplexControl(QStyle.CC_ComboBox,option,painter,self)
        rect=self.style().subControlRect(QStyle.CC_ComboBox,option,QStyle.SC_ComboBoxEditField,self)
        paint_text(painter,rect,value,self.font(),self.palette().color(QPalette.Text),cache=self._outline_cache)
        arrow=self.style().subControlRect(QStyle.CC_ComboBox,option,QStyle.SC_ComboBoxArrow,self).center()
        path=QPainterPath();path.moveTo(arrow.x()-4,arrow.y()-2);path.lineTo(arrow.x()+4,arrow.y()-2);path.lineTo(arrow.x(),arrow.y()+3);path.closeSubpath()
        painter.setRenderHint(QPainter.Antialiasing);painter.fillPath(path,self.palette().color(QPalette.Text))
