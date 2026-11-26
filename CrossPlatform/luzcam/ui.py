"""Offline Qt desktop host. Local temporary photos and one shared desktop presentation."""
import json
import math
import sys
from pathlib import Path
from PySide6.QtCore import Qt, QEvent, QRectF, QPointF, QUrl, QTimer, QSettings, QVariantAnimation, QEasingCurve, QSize, QBuffer, QIODevice, QTemporaryDir
from PySide6.QtGui import QColor, QPainter, QPen, QBrush, QPolygonF, QPixmap, QImage, QLinearGradient, QPainterPath, QPainterPathStroker, QShortcut, QKeySequence, QFont, QFontDatabase, QIcon,QTransform
from PySide6.QtWidgets import (QApplication,QMainWindow,QWidget,QGraphicsView,QGraphicsScene,QVBoxLayout,QHBoxLayout,
    QLabel,QPushButton,QComboBox,QCheckBox,QSlider,QScrollArea,QSizePolicy,QMessageBox,QStackedWidget,QFrame,QButtonGroup,QTextEdit)
from PySide6.QtMultimedia import QMediaPlayer,QVideoSink
from .model import ROOT,CONTRACT,Session,Setting,pose,interval,title,explanation
from .photo_service import PhotoService
from .review_cache import ReviewCache
from .camera_mechanics import curtain_blades
from .reviewed_reflex import draw as draw_reviewed_reflex
from .reviewed_mirrorless import draw as draw_reviewed_mirrorless
from .reviewed_compact import draw as draw_reviewed_compact
from .vector_text import VectorLabel,VectorButton,VectorCheckBox,VectorComboBox,paint_text,draw_vector_text
from .liveview import exposure_preview
from .i18n import set_language,language,text as translate
from .camera_surface import load_plate

PAPER=QColor('#f0ebdb')
INK=QColor('#293338')
ACCENT='#a14119'
BACKGROUND='#deded4'

def configure_style():
    app=QApplication.instance()
    if app.property('luzcamStyle'): return
    for file in Path(__file__).with_name('fonts').glob('*.ttf'):
        QFontDatabase.addApplicationFont(str(file))
    app.setStyle('Fusion')
    app.setFont(QFont('Noto Sans',13))
    app.setStyleSheet("""
        QWidget {color:#293338; background:transparent; font-family:'Noto Sans'; font-size:15px;}
        QStackedWidget {background:#deded4;}
        QComboBox {background:white; color:#293338; border:1px solid #979d9d; border-radius:4px; padding:5px 24px 5px 8px; combobox-popup:0;}
        QComboBox:focus {border:2px solid #293338;}
        QComboBox::drop-down {border:0; background:transparent; width:22px;}
        QComboBox QAbstractItemView {background:white; color:#293338; selection-background-color:#a14119; selection-color:white; border:1px solid #979d9d; outline:0;}
        QComboBox QAbstractItemView::item {min-height:28px; padding:3px 8px; border:0;}
        QComboBox QAbstractItemView::item:selected {background:#a14119; color:white;}
        QMessageBox {background:#f0ebdb;}
        QMessageBox QLabel {background:transparent; color:#293338;}
        QMessageBox QPushButton {background:white; color:#293338;}
        QMessageBox QTextEdit {background:white; color:#293338;}
        QFrame#cameraPanel {background:#f0ebdb; border-radius:10px;}
        QFrame#whitePanel {background:white; border-radius:10px;}
        QFrame#segments {background:rgba(0,0,0,23); border-radius:7px;}
        QPushButton {padding:4px 9px; border:2px solid transparent; border-radius:5px; min-height:24px;}
        QPushButton:focus {border:2px solid #293338;}
        QSlider:focus {border:2px solid #293338; border-radius:5px;}
        QPushButton:hover {background:rgba(0,0,0,18);}
        QPushButton:checked {background:#a14119; color:white;}
        QPushButton#primary {background:#a14119; color:white; font-size:15px; font-weight:600;}
        QPushButton#primary:hover {background:#a6451a;}
        QPushButton:disabled,QCheckBox:disabled {color:#979a97;}
        QSlider::groove:horizontal {height:3px; background:#c5c8c8; border-radius:1px;}
        QSlider::sub-page:horizontal {background:#bf5221;}
        QSlider::handle:horizontal {background:white; border:1px solid #b8b9b8; width:23px; height:23px; margin:-10px 0; border-radius:12px;}
        QCheckBox {font-size:14px; spacing:6px;}
        QCheckBox::indicator {width:13px; height:13px; border:1px solid #979d9d; border-radius:3px; background:white;}
        QCheckBox::indicator:checked {background:#bf5221; border-color:#bf5221; image:none;}
        QScrollArea {background:transparent; border:0;}
        QScrollBar:horizontal {height:7px; background:transparent;}
        QScrollBar::handle:horizontal {background:#c5c8c8; min-width:25px; border-radius:3px;}
        QScrollBar::add-line:horizontal,QScrollBar::sub-line:horizontal {width:0;}
        QToolTip {background:#293338; color:white; padding:5px;}
    """)
    app.setProperty('luzcamStyle',True)

def label(text,size=13,kind='sans',bold=False):
    size={9:12,10:13,11:14,12:15,13:16,14:16,16:18,18:20,22:24,26:28}.get(size,size)
    widget=VectorLabel(text)
    family={'sans':'Noto Sans','serif':'Noto Serif','mono':'Noto Sans Mono'}[kind]
    widget.setStyleSheet(f'font-family:"{family}";font-size:{size}px;font-weight:{600 if bold else 400};')
    return widget

def button(text,description,callback):
    widget=VectorButton(text); widget.setToolTip(description); widget.setAccessibleName(description); widget.clicked.connect(callback)
    if text in ('⚙','⤢','↶','‹'):
        pix=QPixmap(26,26); pix.fill(Qt.transparent); p=QPainter(pix); p.setRenderHint(QPainter.Antialiasing); p.setPen(QPen(INK,1.6,Qt.SolidLine,Qt.RoundCap,Qt.RoundJoin)); p.setBrush(Qt.NoBrush)
        if text=='⚙':
            p.drawEllipse(QPointF(13,13),7,7); p.drawEllipse(QPointF(13,13),3,3)
            for i in range(8):
                a=i*math.pi/4; p.drawLine(QPointF(13+7*math.cos(a),13+7*math.sin(a)),QPointF(13+10*math.cos(a),13+10*math.sin(a)))
        elif text=='⤢':
            for points in (((5,11),(5,5),(11,5)),((15,21),(21,21),(21,15)),((5,5),(11,11)),((21,21),(15,15))): p.drawPolyline(QPolygonF([QPointF(*point) for point in points]))
        elif text=='‹': p.drawPolyline(QPolygonF([QPointF(16,6),QPointF(9,13),QPointF(16,20)]))
        else:
            p.drawArc(QRectF(5,5,16,16),90*16,-300*16); p.drawPolyline(QPolygonF([QPointF(9,2),QPointF(13,5),QPointF(9,9)]))
        p.end(); widget.setText(''); widget.setIcon(QIcon(pix)); widget.setIconSize(QSize(23,23))
    return widget

class Photo(QWidget):
    def __init__(self):
        super().__init__(); self.image=QImage(); self.message=''; self.setMinimumHeight(280)
    def set_image(self,path):
        self.image=QImage(str(path)); self.message='' if not self.image.isNull() else 'Falta este recurso: '+Path(path).name; self.update()
    def frame(self,frame):
        image=frame.toImage()
        if not image.isNull(): self.image=image; self.message=''; self.update()
    def paintEvent(self,event):
        p=QPainter(self); p.fillRect(self.rect(),QColor('#151a1a'))
        if not self.image.isNull():
            size=self.image.size().scaled(self.size(),Qt.KeepAspectRatio)
            r=QRectF((self.width()-size.width())/2,(self.height()-size.height())/2,size.width(),size.height())
            p.setRenderHint(QPainter.SmoothPixmapTransform); p.drawImage(r,self.image)
        if self.message: p.setPen(QColor('white')); draw_vector_text(p,self.rect(),Qt.AlignCenter,self.message)

class Meter(QWidget):
    def __init__(self): super().__init__(); self.third=0; self.setFixedSize(166,38)
    def paintEvent(self,event):
        p=QPainter(self); p.setRenderHint(QPainter.Antialiasing); p.setPen(Qt.NoPen); p.setBrush(QColor(BACKGROUND)); p.drawRoundedRect(QRectF(self.rect()),19,19)
        p.translate(7,5); width=self.width()-14; left=15; span=width-30
        p.setPen(QColor('black')); font=QFont('Noto Sans Mono'); font.setPixelSize(13); font.setBold(True); p.setFont(font)
        for step in range(13):
            x=left+span*step/12
            if step%3==0: draw_vector_text(p,QRectF(x-8,0,16,16),Qt.AlignCenter,str(abs(step//3-2)))
            else: p.fillRect(QRectF(x-.7,8,1.4,3 if step%3==1 else 5),QColor('black'))
        draw_vector_text(p,QRectF(-2,0,12,16),Qt.AlignCenter,'◀' if self.third < -6 else '−'); draw_vector_text(p,QRectF(width-10,0,12,16),Qt.AlignCenter,'▶' if self.third>6 else '+')
        x=left+span*(max(-6,min(6,self.third))+6)/12
        p.setPen(Qt.NoPen); p.setBrush(QColor('black')); p.drawPolygon(QPolygonF([QPointF(x,15),QPointF(x+2,19),QPointF(x+2,25),QPointF(x-2,25),QPointF(x-2,19)]))

class StepCheckBox(VectorCheckBox):
    """An explicit tick, independent of platform stylesheet indicator rendering."""
    def paintEvent(self,event):
        p=QPainter(self); p.setRenderHint(QPainter.Antialiasing)
        color=INK if self.isEnabled() else QColor('#979a97')
        y=(self.height()-16)/2
        p.setPen(QPen(color,1)); p.setBrush(QColor('#293338') if self.isChecked() else QColor('#faf8ef'))
        p.drawRoundedRect(QRectF(1,y,16,16),3,3)
        if self.isChecked():
            p.setPen(QPen(QColor('white'),2,Qt.SolidLine,Qt.RoundCap,Qt.RoundJoin))
            p.drawPolyline(QPolygonF([QPointF(4,y+8),QPointF(7,y+11),QPointF(13,y+5)]))
        p.setPen(color); font=QFont('Noto Sans'); font.setPixelSize(14); p.setFont(font)
        paint_text(p,QRectF(24,0,self.width()-24,self.height()),self.text(),font,color,cache=self._outline_cache)
        if self.hasFocus(): p.setPen(QPen(color,1,Qt.DotLine)); p.setBrush(Qt.NoBrush); p.drawRoundedRect(QRectF(self.rect()).adjusted(0,0,-1,-1),3,3)
    def hitButton(self,pos): return self.rect().contains(pos)

class ShutterButton(VectorButton):
    def __init__(self,callback):
        super().__init__('Disparar'); self.setFixedSize(68,68); self.setAccessibleName('Disparar'); self.clicked.connect(callback); self.setCursor(Qt.PointingHandCursor)
    def paintEvent(self,event):
        p=QPainter(self); p.setRenderHint(QPainter.Antialiasing)
        p.setPen(Qt.NoPen); p.setBrush(QColor(0,0,0,35)); p.drawEllipse(QRectF(3,5,62,62))
        rim=QLinearGradient(0,2,0,64); rim.setColorAt(0,QColor('#626767')); rim.setColorAt(1,QColor('#181c1d')); p.setBrush(rim); p.drawEllipse(QRectF(2,2,62,62))
        face=QLinearGradient(0,8,0,58); face.setColorAt(0,QColor('#171b1c' if self.isDown() else '#404648')); face.setColorAt(1,QColor('#080a0b' if self.isDown() else '#111516')); p.setBrush(face); p.setPen(QPen(QColor('#747a7b'),1)); p.drawEllipse(QRectF(9,9,48,48))
        if self.text()==translate('Pausar'):
            p.setPen(Qt.NoPen); p.setBrush(QColor('#eef0e8')); p.drawRoundedRect(QRectF(24,23,6,21),1,1); p.drawRoundedRect(QRectF(36,23,6,21),1,1)

class Camera(QWidget):
    def __init__(self):
        super().__init__(); self.setMinimumHeight(220); self.camera=0; self.pose=pose(0,Session().setting); self.electronic=QImage(); self.lcd_setting=Setting(); self.lcd_review=False
        self.plates=[load_plate(str(ROOT/'CameraArt'/f'{name}-reviewed.jpg')) for name in ('reflex','mirrorless','compact')]
        self.animation=QVariantAnimation(self); self.animation.setDuration(900); self.animation.setStartValue(0.); self.animation.setEndValue(1.); self.animation.setEasingCurve(QEasingCurve.InOutCubic); self.animation.valueChanged.connect(self.interpolate)
    def set_pose(self,camera,target):
        if camera==self.camera and getattr(self,'target',None)==target:
            self.update(); return
        self.animation.stop(); self.camera=camera; self.start=dict(self.pose); self.target=target; self.animation.start()
    def interpolate(self,t):
        self.pose={k:self.start[k]+(v-self.start[k])*t for k,v in self.target.items()}
        if self.camera==0 and self.start['front']>.999 and self.start['rear']>.999 and self.target['front']==0 and self.target['rear']==0:
            self.pose['front']=max(0,1-2*t);self.pose['rear']=min(1,2-2*t)
        if self.camera==1 and self.start['front']>.999 and self.start['rear']>.999 and self.target['front']==1 and self.target['rear']==0:
            if t<1/3:self.pose['front']=1-3*t;self.pose['rear']=1
            elif t<2/3:self.pose['front']=0;self.pose['rear']=2-3*t
            else:self.pose['front']=3*t-2;self.pose['rear']=0
        self.update()
    def artwork_frame(self):
        image=self.plates[self.camera]
        if self.camera==0:
            # Fit the camera, not the unused studio margins. Artwork coordinates
            # and every optical layer keep the same single uniform transform.
            bounds=QRectF(image.width()*.24,image.height()*.15,image.width()*.60,image.height()*.69)
            scale=min(self.width()/bounds.width(),self.height()/bounds.height())
            w=image.width()*scale; h=image.height()*scale
            ox=(self.width()-bounds.width()*scale)/2-bounds.x()*scale
            oy=(self.height()-bounds.height()*scale)/2-bounds.y()*scale
        elif self.camera in (1,2):
            # The physical articulated screen is already part of the artwork.
            bounds=QRectF(image.width()*.045,image.height()*.09,image.width()*.93,image.height()*.80) if self.camera==1 else QRectF(image.width()*.025,image.height()*.12,image.width()*.96,image.height()*.76)
            scale=min(self.width()/bounds.width(),self.height()/bounds.height())*(.90 if self.camera==2 else .78)
            w=image.width()*scale; h=image.height()*scale
            ox=(self.width()-bounds.width()*scale)/2-bounds.x()*scale
            oy=(self.height()-bounds.height()*scale)/2-bounds.y()*scale+(self.height()*.055 if self.camera==2 else 0)
        else:
            footprint=1.28
            w=min(self.width()/footprint,self.height()*image.width()/image.height()); h=w*image.height()/image.width(); ox=(self.width()-w*footprint)/2; oy=(self.height()-h)/2
        return QRectF(ox,oy,w,h)
    def paintEvent(self,event):
        p=QPainter(self); p.setRenderHints(QPainter.Antialiasing|QPainter.SmoothPixmapTransform); p.fillRect(self.rect(),PAPER)
        image=self.plates[self.camera]
        if image.isNull(): draw_vector_text(p,self.rect(),Qt.AlignCenter,'Falta la ilustración de cámara'); return
        frame=self.artwork_frame(); ox,oy,w,h=frame.x(),frame.y(),frame.width(),frame.height()
        if self.camera==0:
            draw_reviewed_reflex(p,frame,image,self.pose,self.lcd_setting,self.lcd_review,self.electronic)
            return
        if self.camera==1:
            draw_reviewed_mirrorless(p,frame,image,self.pose,self.lcd_setting,self.lcd_review,self.electronic)
            return
        if self.camera==2:
            draw_reviewed_compact(p,frame,image,self.pose,self.lcd_setting,self.lcd_review,self.electronic)
            return

class Mechanism(QWidget):
    def __init__(self,kind,camera):
        super().__init__(); self.kind=kind; self.camera_widget=camera; self.setFixedSize(110,85); camera.animation.valueChanged.connect(self.update)
    def paintEvent(self,event):
        p=QPainter(self); p.setRenderHint(QPainter.Antialiasing); p.fillRect(self.rect(),PAPER); state=self.camera_widget.pose
        if self.kind=='iris':
            p.translate(self.width()/2,self.height()/2); scale=min(self.width(),self.height())/90; p.scale(scale,scale); radius=37.4; opening=radius*max(0,min(.86,state['aperture']))
            g=QLinearGradient(-40,-40,40,40); g.setColorAt(0,QColor('#cccccc')); g.setColorAt(.5,QColor('#616161')); g.setColorAt(1,QColor('#b8b8b8'))
            p.setBrush(g); p.setPen(QPen(INK,1.5)); p.drawEllipse(QPointF(),radius+7,radius+7)
            p.setBrush(INK); p.drawEllipse(QPointF(),radius,radius)
            def polar(r,a): return QPointF(r*math.cos(a),r*math.sin(a))
            for n in range(7):
                a=n*2*math.pi/7; blade=QPainterPath(); blade.moveTo(polar(opening,a)); blade.lineTo(polar(opening,a+2*math.pi/7)); blade.quadTo(polar(radius*.8,a+1.1),polar(radius,a+1.7))
                blade.arcTo(QRectF(-radius,-radius,2*radius,2*radius),-math.degrees(a+1.7),math.degrees(1.25)); blade.quadTo(polar(radius*.8,a+.1),polar(opening,a)); blade.closeSubpath()
                g=QLinearGradient(polar(radius,a),QPointF()); g.setColorAt(0,QColor('#a3a3a3')); g.setColorAt(1,QColor('#474747')); p.setBrush(g); p.setPen(QPen(INK,1)); p.drawPath(blade)
                p.setBrush(QColor('#cccccc')); p.drawEllipse(polar(radius*.88,a+.48),2,2)
            p.setBrush(PAPER); p.setPen(QPen(INK,.7)); p.drawPolygon(QPolygonF([polar(opening,n*2*math.pi/7) for n in range(7)]))
        elif self.kind=='sensitivity':
            p.scale(self.width()/110,self.height()/85); frame=QRectF(8,9,94,67)
            p.setPen(Qt.NoPen); p.setBrush(QColor('#808080')); p.drawRoundedRect(frame.adjusted(-5,-5,5,5),4,4)
            gain=state['gain']; amplitude=.012+.034*gain
            for row in range(24):
                for col in range(32):
                    code=((row+1)*73856093)^((col+1)*19349663); code=(code^(code>>13))*1274126177
                    noise=((code&65535)/65535-.5)*2*amplitude
                    c=QColor.fromRgbF(*[max(0,min(1,base+noise)) for base in (.25,.42,.47)])
                    p.fillRect(QRectF(8+94*col/32,9+67*row/24,94/32+.1,67/24+.1),c)
            p.setPen(QPen(INK,1.5)); p.setBrush(Qt.NoBrush); p.drawRect(frame)
        else:
            p.scale(self.width()/110,self.height()/85)
            frame=QRectF(8,9,94,67); p.setPen(Qt.NoPen); p.setBrush(QColor('#808080')); p.drawRoundedRect(frame.adjusted(-5,-5,5,5),4,4)
            active=state['sensorActive']; compact=self.camera_widget.camera==2
            g=QLinearGradient(frame.topLeft(),frame.bottomRight()); g.setColorAt(0,QColor.fromRgbF(.10,.30+active*.35,.36+active*.4) if compact else QColor('#69a8a6')); g.setColorAt(1,QColor.fromRgbF(.08,.16+active*.20,.28+active*.4) if compact else QColor('#4769a6')); p.fillRect(frame,g)
            p.setPen(QPen(QColor(255,255,255,46),.5))
            for x in range(8,102,9): p.drawLine(QPointF(x,9),QPointF(x,76))
            for y in range(9,76,9): p.drawLine(QPointF(8,y),QPointF(102,y))
            if compact:
                p.setPen(QColor(255,255,255,180)); font=QFont('Noto Sans Mono'); font.setPixelSize(12); p.setFont(font); draw_vector_text(p,frame,Qt.AlignCenter,'REGISTRANDO' if active>.1 else 'SENSOR')
                if active: p.setPen(QPen(QColor(50,220,255,round(active*255)),2)); p.setBrush(Qt.NoBrush); p.drawRect(frame)
            else:
                for progress,second in ((state['front'],False),(state['rear'],True)):
                    for top,bottom,index in reversed(curtain_blades(progress,second)):
                        rect=QRectF(8,9+67*top,94,67*(bottom-top))
                        g=QLinearGradient(rect.topLeft(),rect.bottomRight()); g.setColorAt(0,QColor('#696f70' if second else '#454a4c')); g.setColorAt(1,QColor('#343a3c' if second else '#252a2c')); p.fillRect(rect,g)
                        p.setPen(QPen(QColor('#929999'),.8)); p.drawLine(rect.topLeft(),rect.topRight())
            p.setPen(QPen(INK,1.5)); p.setBrush(Qt.NoBrush); p.drawRect(frame)

def camera_icon(camera):
    from PySide6.QtGui import QIcon,QTransform
    pix=QPixmap(52,36); pix.fill(Qt.transparent); p=QPainter(pix); p.setRenderHint(QPainter.Antialiasing); p.setPen(QPen(INK,1.7)); p.setBrush(Qt.NoBrush)
    p.drawRoundedRect(QRectF(4,9,43,24),4,4); p.drawEllipse(QPointF(27,21),8,8)
    if camera==0: p.drawPolyline(QPolygonF([QPointF(13,9),QPointF(18,3),QPointF(29,3),QPointF(35,9)]))
    elif camera==1: p.drawRect(QRectF(11,4,12,5))
    else: p.drawLine(QPointF(8,14),QPointF(16,14))
    p.end(); return QIcon(pix)

class Window(QMainWindow):
    def __init__(self, settings=None):
        super().__init__()
        self._sizing=False
        self._window_ready=False
        self._last_normal=None
        configure_style()
        self.release_info=json.loads(Path(__file__).with_name('release-info.json').read_text(encoding='utf8'))
        QApplication.instance().setApplicationVersion(self.release_info['version'])
        self.setWindowTitle('LuzCam')
        self.setWindowIcon(QIcon(str(Path(__file__).with_name('icons')/'luzcam.png')))
        self.session=Session(); self.selected=None; self.loaded_light=-1
        self.photos=PhotoService(self); self.photos.ready.connect(self.photo_ready); self.photos.failed.connect(self.photo_failed)
        self.review_cache=ReviewCache(); self.saved_photos={}; self.photo_errors={}; self.displayed_key=None; self.scene_images={}
        self.moving=True; self.diaphragm_preview=False
        self.scene_timing=json.loads((ROOT/'Scene/scene.json').read_text())
        self.video_scene_frame=0; self.last_video_image=QImage(); self.shot_video_image=QImage()
        self._test_settings=QTemporaryDir() if QApplication.platformName()=='offscreen' and settings is None else None
        self.settings=settings if settings is not None else QSettings(self._test_settings.path()+'/settings.ini',QSettings.IniFormat) if self._test_settings else QSettings('LuzCam','SharedDesktop')
        set_language(str(self.settings.value('language','es')))
        self.timer=QTimer(self); self.timer.setSingleShot(True); self.timer.timeout.connect(self.auto_advance)
        self.root=QStackedWidget(); self.root.setFixedSize(1600,900)
        self.main_page=QWidget(); self.root.addWidget(self.main_page)
        main=QVBoxLayout(self.main_page); main.setContentsMargins(22,22,22,22); main.setSpacing(14)
        header=QHBoxLayout(); heading=QVBoxLayout(); heading.setSpacing(3)
        brand=label('L U Z  /  C Á M A R A',11,'mono',True); brand.setStyleSheet('color:'+ACCENT)
        heading.addWidget(brand); heading.addWidget(label('El instante, por dentro.',26,'serif'))
        header.addLayout(heading); header.addStretch()
        self.config=button('⚙','Configuración',self.configure); self.config.setFixedSize(44,44); header.addWidget(self.config)
        main.addLayout(header)
        columns=QHBoxLayout(); columns.setSpacing(16); main.addLayout(columns,1)
        left=QVBoxLayout(); left.setSpacing(12); columns.addLayout(left,1)
        camera_panel=QFrame(); camera_panel.setObjectName('cameraPanel'); left.addWidget(camera_panel,1)
        camera_layout=QVBoxLayout(camera_panel); camera_layout.setContentsMargins(18,18,18,18); camera_layout.setSpacing(8)
        camera_header=QHBoxLayout(); names=QVBoxLayout(); names.setSpacing(5)
        self.camera_name=label('',30,'serif',True); self.detail=label('',12)
        names.addWidget(self.camera_name); names.addWidget(self.detail); camera_header.addLayout(names,1)
        picker,self.camera_buttons=self.make_camera_picker(); camera_header.addWidget(picker,0,Qt.AlignTop)
        camera_layout.addLayout(camera_header)
        cutaway=QWidget(); cutaway_layout=QVBoxLayout(cutaway); cutaway_layout.setContentsMargins(0,0,0,0)
        self.camera=Camera(); cutaway_layout.addWidget(self.camera)
        self.meter=Meter(); self.meter.setParent(cutaway)
        cutaway.resizeEvent=lambda event:self.meter.move(max(0,cutaway.width()-self.meter.width()),8)
        camera_layout.addWidget(cutaway,1)
        # Phase descriptions wrap differently, especially when showing a photo.
        # Reserve their tallest ES/EN row so they cannot resize the camera above.
        mechanisms_panel=QWidget(); mechanisms_panel.setFixedHeight(112)
        mechanisms=QHBoxLayout(mechanisms_panel); mechanisms.setContentsMargins(0,0,0,0); mechanisms.setSpacing(24)
        def mechanism_block(graph,title,value):
            block=QHBoxLayout(); block.setSpacing(12); block.addWidget(graph,0,Qt.AlignVCenter)
            text=QVBoxLayout(); text.setSpacing(5); text.addWidget(title); text.addWidget(value); text.addStretch()
            block.addLayout(text,1); mechanisms.addLayout(block,1)
            return text
        iris=Mechanism('iris',self.camera); iris.setFixedSize(90,90)
        self.iris_value=label('',22,'mono')
        aperture=mechanism_block(iris,label('DIAFRAGMA',10,'mono'),self.iris_value)
        self.check_iris=button('Comprobar','Previsualizar el diafragma sin disparar',self.check_aperture)
        self.check_iris.setFixedHeight(34); aperture.addWidget(self.check_iris,0,Qt.AlignLeft)
        self.shutter=Mechanism('shutter',self.camera); self.shutter.setFixedSize(90,72)
        self.shutter_title=label('OBTURADOR',10,'mono'); self.shutter_value=label('',22,'mono')
        mechanism_block(self.shutter,self.shutter_title,self.shutter_value)
        self.sensitivity=Mechanism('sensitivity',self.camera); self.sensitivity.setFixedSize(90,72)
        self.sensitivity_value=label('100',22,'mono')
        sensitivity=mechanism_block(self.sensitivity,label('SENSIBILIDAD',10,'mono'),self.sensitivity_value)
        sensitivity.addWidget(label('Ruido',11))
        camera_layout.addWidget(mechanisms_panel)
        explanation_box=QVBoxLayout(); explanation_box.setSpacing(5)
        self.phase_title=label('',16,'serif',True); self.phase_title.setWordWrap(True); self.phase_title.setSizePolicy(QSizePolicy.Preferred,QSizePolicy.Maximum); explanation_box.addWidget(self.phase_title)
        self.expl=label('',11); self.expl.setWordWrap(True); self.expl.setAlignment(Qt.AlignTop|Qt.AlignLeft); explanation_box.addWidget(self.expl)
        mechanisms.addLayout(explanation_box,1)
        footer=QHBoxLayout(); footer.setSpacing(8)
        self.fire=ShutterButton(self.advance)
        self.pause=StepCheckBox('Paso a paso'); self.pause.setChecked(True); self.pause.toggled.connect(self.pause_changed)
        self.shutter_controls=QWidget(cutaway); shutter_controls=QHBoxLayout(self.shutter_controls); shutter_controls.setContentsMargins(0,0,0,0); shutter_controls.setSpacing(8); shutter_controls.addWidget(self.fire); shutter_controls.addWidget(self.pause); self.shutter_controls.setFixedSize(235,74)
        def position_controls(event):
            self.meter.move(max(0,cutaway.width()-self.meter.width()),8)
            self.shutter_controls.move(max(0,cutaway.width()-self.shutter_controls.width()),52)
        cutaway.resizeEvent=position_controls
        footer.addStretch(); self.back=button('‹','Paso anterior',self.go_back); footer.addWidget(self.back)
        footer.addWidget(button('↶','Reiniciar secuencia',self.reset)); footer.addWidget(button('⤢','Ampliar cámara',self.enlarge_camera)); camera_layout.addLayout(footer)
        controls_panel=QFrame(); controls_panel.setObjectName('whitePanel'); controls=QHBoxLayout(controls_panel)
        controls.setContentsMargins(18,12,18,12); controls.setSpacing(24); left.addWidget(controls_panel)
        self.sliders=[]; self.value_labels=[]
        for n,text in enumerate(('DIAFRAGMA','VELOCIDAD','ISO')):
            box=QVBoxLayout(); box.setSpacing(8); box.addWidget(label(text,10,'mono'))
            value=label('',26,'mono'); box.addWidget(value)
            slider=QSlider(Qt.Horizontal); slider.setAccessibleName(text.capitalize()); slider.setMinimumHeight(38); slider.valueChanged.connect(lambda v,n=n:self.setting_changed(n,v)); box.addWidget(slider)
            controls.addLayout(box,1); self.sliders.append(slider); self.value_labels.append(value)
        scene_panel=QFrame(); scene_panel.setObjectName('whitePanel'); scene_panel.setFixedWidth(580); columns.addWidget(scene_panel)
        right=QVBoxLayout(scene_panel); right.setContentsMargins(18,18,18,18); right.setSpacing(12)
        scenehead=QHBoxLayout(); self.scene_title=label('ESCENA / VISOR',10,'mono'); scenehead.addWidget(self.scene_title); scenehead.addStretch()
        self.live=button('Volver al visor','Volver a la escena sin borrar el carrete',self.show_live); scenehead.addWidget(self.live)
        scenehead.addWidget(button('⤢','Ampliar imagen',self.enlarge_photo)); right.addLayout(scenehead)
        self.photo=Photo(); self.photo.setFixedSize(544,306); right.addWidget(self.photo)
        # A hidden combobox is the single selection model used by both segmented controls.
        self.light=QComboBox(self.main_page); self.light.addItems([l['name'] for l in CONTRACT['lights']]); self.light.hide()
        self.light.currentIndexChanged.connect(self.light_changed)
        lights=QFrame(); lights.setObjectName('segments'); lightrow=QHBoxLayout(lights); lightrow.setContentsMargins(2,2,2,2); lightrow.setSpacing(1)
        self.light_buttons=[]
        for i,item in enumerate(CONTRACT['lights']):
            b=button(item['name'],item['name'],lambda checked=False,i=i:self.light.setCurrentIndex(i)); b.setCheckable(True); lightrow.addWidget(b,1); self.light_buttons.append(b)
        right.addWidget(lights)
        self.scene_name=label('El taller del tiempo',22,'serif'); right.addWidget(self.scene_name)
        self.scene_hint=label('Observa el péndulo, predice el resultado y dispara.',13); self.scene_hint.setWordWrap(True); right.addWidget(self.scene_hint)
        self.metadata=label('',12,'mono'); self.metadata.setWordWrap(True); right.addWidget(self.metadata)
        self.preview=VectorCheckBox('Simular exposición en el visor'); self.preview.toggled.connect(self.refresh); right.addWidget(self.preview)
        right.addStretch(1)
        filmhead=QHBoxLayout(); self.film_title=label('CARRETE · 0 / 100',10,'mono'); self.film_title.setToolTip('Selecciona una fotografía para revisarla'); filmhead.addWidget(self.film_title); filmhead.addStretch()
        self.clear_film=button('Vaciar carrete','Eliminar las fotografías de esta sesión',self.confirm_clear_film); filmhead.addWidget(self.clear_film); right.addLayout(filmhead)
        self.film=QHBoxLayout(); self.film.setContentsMargins(0,0,0,0); self.film.setSpacing(9); self.film.setAlignment(Qt.AlignLeft)
        filmwidget=QWidget(); filmwidget.setLayout(self.film)
        self.film_empty=label('Las fotografías aparecerán aquí después del disparo.',12); self.film.addWidget(self.film_empty)
        scroll=QScrollArea(); scroll.setFrameShape(QFrame.NoFrame); scroll.setWidgetResizable(True); scroll.setWidget(filmwidget); scroll.setFixedHeight(112); right.addWidget(scroll)
        scene=QGraphicsScene(self); scene.addWidget(self.root); scene.setSceneRect(0,0,1600,900)
        self.view=QGraphicsView(scene); self.view.setRenderHints(QPainter.Antialiasing|QPainter.TextAntialiasing|QPainter.SmoothPixmapTransform); self.view.setFrameShape(QGraphicsView.NoFrame)
        self.view.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff); self.view.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOff); self.view.setBackgroundBrush(QColor(BACKGROUND)); self.setCentralWidget(self.view)
        from .accessibility import bind_scene
        bind_scene(self.view,self.root)
        self.player=QMediaPlayer(self); self.sink=QVideoSink(self); self.player.setVideoSink(self.sink)
        # Read the latest frame instead of queueing an image conversion for
        # every decoder signal. A slow repaint must not retain stale frames.
        self._video_token=None;self.video_frames_presented=0
        self.video_poll=QTimer(self);self.video_poll.setInterval(17);self.video_poll.setTimerType(Qt.PreciseTimer)
        self.video_poll.timeout.connect(self.poll_video)
        self.player.playbackStateChanged.connect(lambda state:self.video_poll.start() if state==QMediaPlayer.PlayingState else self.video_poll.stop())
        self.player.setLoops(QMediaPlayer.Infinite); self.player.errorOccurred.connect(self.video_error)
        self.shortcut=QShortcut(QKeySequence('Space'),self); self.shortcut.activated.connect(self.advance)
        self.escape=QShortcut(QKeySequence('Escape'),self); self.escape.activated.connect(self.close_presentation)
        self.fullscreen=QShortcut(QKeySequence('F11'),self); self.fullscreen.activated.connect(lambda:self.showNormal() if self.isFullScreen() else self.showFullScreen())
        self.reload_controls(); self.refresh()
        from .window_geometry import initial_geometry
        screens=[screen.availableGeometry() for screen in QApplication.screens()]
        saved=self.settings.value('windowPixels16x9',None)
        x,y,width,height=initial_geometry(saved,[(r.x(),r.y(),r.width(),r.height(),s.devicePixelRatio()) for r,s in zip(screens,QApplication.screens())])
        self.resize(width,height); self.move(x,y)
        self._restored_geometry=(x,y,width,height)
        self._saved_geometry=saved
    def make_camera_picker(self):
        picker=QFrame(); picker.setObjectName('segments'); picker.setFixedSize(216,40)
        row=QHBoxLayout(picker); row.setContentsMargins(3,3,3,3); row.setSpacing(2); buttons=[]
        for i,text in enumerate(('Réflex','Sin espejo','Compacta')):
            b=button('',text,lambda checked=False,i=i:self.change_camera(i)); b.setIcon(camera_icon(i)); b.setIconSize(QSize(34,26)); b.setCheckable(True); b.setMinimumHeight(34); row.addWidget(b,1); buttons.append(b)
        return picker,buttons
    def resizeEvent(self,event):
        super().resizeEvent(event)
        if not self._sizing and not (self.isFullScreen() or self.isMaximized() or self.isMinimized()):
            old=event.oldSize(); width=self.width(); height=self.height()
            # Keep the edge being dragged authoritative; corners follow the larger change.
            if old.isValid() and abs(height-old.height())>abs(width-old.width())*9/16:
                width=round(height*16/9)
            else:
                height=round(width*9/16)
            if (width,height)!=(self.width(),self.height()):
                self._sizing=True; self.resize(width,height); self._sizing=False
        if hasattr(self,'view'): self.view.fitInView(self.view.sceneRect(),Qt.KeepAspectRatio)
        self._remember_normal()
    def moveEvent(self,event):
        super().moveEvent(event); self._remember_normal()
    def _remember_normal(self):
        if self._window_ready and not (self.isFullScreen() or self.isMaximized() or self.isMinimized()):
            self._last_normal=[self.x(),self.y(),self.width(),self.height()]
    def showEvent(self,event):
        super().showEvent(event); self.view.fitInView(self.view.sceneRect(),Qt.KeepAspectRatio)
        if not self._window_ready: QTimer.singleShot(0,self._finish_window_restore)
    def changeEvent(self,event):
        super().changeEvent(event)
        if event.type()!=QEvent.WindowStateChange or not hasattr(self,'player'):return
        if self.isMinimized():
            self._resume_video=self.player.playbackState()==QMediaPlayer.PlayingState
            self._resume_sequence=self.timer.isActive()
            self.player.pause();self.video_poll.stop();self.timer.stop()
        elif event.oldState() & Qt.WindowMinimized:
            if getattr(self,'_resume_video',False) and self.moving and self.selected is None and not self.session.busy:self.player.play()
            if getattr(self,'_resume_sequence',False) and self.session.busy:self.schedule()
    def _finish_window_restore(self):
        # Native frame sizes are available only after showing the window.
        screen=self.screen().availableGeometry(); frame=self.frameGeometry()
        extra_w=frame.width()-self.width(); extra_h=frame.height()-self.height()
        scale=min(1,(screen.width()-extra_w)/self.width(),(screen.height()-extra_h)/self.height())
        if scale<1: self.resize(int(self.width()*scale),round(int(self.width()*scale)*9/16))
        frame=self.frameGeometry()
        self.move(max(screen.left(),min(self.x(),screen.right()-frame.width()+1)),
                  max(screen.top(),min(self.y(),screen.bottom()-frame.height()+1)))
        self._window_ready=True
        self._initial_normal=[self.x(),self.y(),self.width(),self.height()]
        self._last_normal=self._initial_normal[:]
    def closeEvent(self,event):
        geometry=self._last_normal
        # An automatic fit to a smaller monitor must not erase a larger saved window.
        if geometry and (geometry!=self._initial_normal or not self._saved_geometry):
            dpr=self.screen().devicePixelRatio()
            pixels=geometry[:2]+[round(geometry[2]*dpr),round(geometry[3]*dpr)]
            if pixels[2]>1920 and pixels[3]>1080:
                self.settings.setValue('windowPixels16x9',pixels)
            else: self.settings.remove('windowPixels16x9')
        self.settings.sync()
        self.timer.stop(); self.video_poll.stop(); self.player.stop(); self.photos.close(); self.review_cache.clear(); super().closeEvent(event)
    def check_aperture(self):
        self.diaphragm_preview=not self.diaphragm_preview; self.refresh()
    def close_presentation(self):
        if getattr(self,'settings_overlay',None):
            self.settings_overlay.deleteLater(); self.settings_overlay=None
            self.main_page.setEnabled(True);self.shortcut.setEnabled(True);self.refresh();self.config.setFocus(Qt.OtherFocusReason)
            if getattr(self,'_settings_resume_sequence',False):self.schedule()
            return
        page=self.root.currentWidget()
        if page is not self.main_page:
            self.root.setCurrentWidget(self.main_page); self.root.removeWidget(page); page.deleteLater()
            self.detail_camera=None; self.detail_photo=None
    def presentation(self):
        self.close_presentation()
        page=QWidget(); page.setObjectName('presentation'); page.setStyleSheet('QWidget#presentation {background:#f0ebdb;}')
        box=QVBoxLayout(page); box.setContentsMargins(28,28,28,28); box.setSpacing(16)
        self.root.addWidget(page); self.root.setCurrentWidget(page)
        return page,box
    def enlarge_photo(self):
        page,box=self.presentation()
        self.detail_photo=Photo(); self.detail_photo.image=self.photo.image; box.addWidget(self.detail_photo,1)
        footer=QHBoxLayout(); footer.addWidget(label('Fotografía capturada' if self.selected is not None else 'Vista de escena',22,'serif')); footer.addStretch()
        footer.addWidget(button('Cerrar','Cerrar ampliación',self.close_presentation)); box.addLayout(footer)
    def enlarge_camera(self):
        page,box=self.presentation()
        header=QHBoxLayout(); header.addWidget(label('La cámara, por dentro',27,'serif')); header.addStretch()
        picker,self.detail_camera_buttons=self.make_camera_picker(); header.addWidget(picker); header.addWidget(button('Cerrar','Cerrar ampliación',self.close_presentation)); box.addLayout(header)
        self.detail_camera=Camera(); self.detail_camera.setFixedHeight(510); box.addWidget(self.detail_camera)
        self.detail_fire=ShutterButton(self.advance); self.detail_fire.setParent(self.detail_camera)
        self.detail_pause=StepCheckBox('Paso a paso',self.detail_camera); self.detail_pause.toggled.connect(self.pause.setChecked)
        def detail_controls(event):
            self.detail_fire.move(max(0,self.detail_camera.width()-215),20); self.detail_pause.move(max(0,self.detail_camera.width()-137),43)
        self.detail_camera.resizeEvent=detail_controls
        row=QHBoxLayout(); row.setSpacing(50)
        irisbox=QVBoxLayout(); iris=Mechanism('iris',self.detail_camera); iris.setFixedSize(155,155); irisbox.addWidget(iris); irisbox.addWidget(label('Diafragma · palas superpuestas',12)); row.addLayout(irisbox)
        shutterbox=QVBoxLayout(); shutter=Mechanism('shutter',self.detail_camera); shutter.setFixedSize(225,155); shutterbox.addWidget(shutter)
        self.detail_shutter_title=label('',12); shutterbox.addWidget(self.detail_shutter_title); row.addLayout(shutterbox); sensitivitybox=QVBoxLayout(); sensitivity=Mechanism('sensitivity',self.detail_camera); sensitivity.setFixedSize(225,155); sensitivitybox.addWidget(sensitivity); self.detail_iso=label('ISO 100 · ruido ilustrativo',12); sensitivitybox.addWidget(self.detail_iso); row.addLayout(sensitivitybox); row.addStretch()
        text=QVBoxLayout(); text.setSpacing(10); text.addStretch(); self.detail_phase=label('',18,'serif',True); self.detail_phase.setFixedHeight(28); text.addWidget(self.detail_phase); self.detail_expl=label('',14); self.detail_expl.setWordWrap(True); self.detail_expl.setFixedSize(340,70); text.addWidget(self.detail_expl); text.addStretch(); row.addLayout(text); box.addLayout(row)
        box.addStretch(); footer=QHBoxLayout(); footer.addStretch(); footer.addWidget(button('‹','Paso anterior',self.go_back)); footer.addWidget(button('↶','Reiniciar secuencia',self.reset)); box.addLayout(footer)
        self.refresh()
    def configure(self):
        if getattr(self,'settings_overlay',None): return
        self._settings_resume_sequence=self.timer.isActive();self.timer.stop();self.shortcut.setEnabled(False)
        overlay=QFrame(self.root); overlay.setGeometry(0,0,1600,900); overlay.setStyleSheet('QFrame#settingsOverlay {background:rgba(0,0,0,50);}')
        self.main_page.setEnabled(False)
        overlay.setObjectName('settingsOverlay'); self.settings_overlay=overlay
        panel=QFrame(overlay); panel.setObjectName('whitePanel'); panel.setGeometry(535,185,530,530)
        box=QVBoxLayout(panel); box.setContentsMargins(30,30,30,30); box.setSpacing(16); box.addWidget(label('Configuración',24,'serif'))
        language_row=QHBoxLayout();language_row.addWidget(label('Idioma',13));self.language_picker=VectorComboBox();self.language_picker.setAccessibleName(translate('Idioma'));self.language_picker.addItems(['Español','English']);self.language_picker.setCurrentIndex(1 if language.code=='en' else 0);self.language_picker.currentIndexChanged.connect(self.change_language);language_row.addWidget(self.language_picker);box.addLayout(language_row)
        self.config_steps=VectorCheckBox('Pausar en cada paso'); self.config_steps.setChecked(self.pause.isChecked()); self.config_steps.setEnabled(not self.session.busy); box.addWidget(self.config_steps)
        self.config_moving=VectorCheckBox('Escena en movimiento'); self.config_moving.setChecked(self.moving); box.addWidget(self.config_moving)
        self.config_thirds=VectorCheckBox('Ajustes en tercios de exposición (⅓ EV)'); self.config_thirds.setChecked(self.session.setting.thirds); self.config_thirds.setEnabled(not self.session.busy); box.addWidget(self.config_thirds)
        box.addWidget(label('LuzCam '+self.release_info['version']+' · '+self.release_info['publisher'],12));box.addWidget(label('LuzCam · Manual\nModelos didácticos · tiempo ralentizado\nEl carrete se conserva durante esta sesión.',12))
        for check in (self.config_steps,self.config_moving,self.config_thirds): check.toggled.connect(self.apply_configuration)
        box.addWidget(button('Créditos e inspiración','Consultar los créditos de LuzCam',self.show_credits))
        box.addWidget(button('Cerrar','Cerrar configuración',self.close_presentation)); overlay.show(); overlay.raise_();self.language_picker.setFocus(Qt.OtherFocusReason)
    def show_credits(self):
        dialog=QMessageBox(self);dialog.setWindowTitle(translate('Créditos e inspiración'))
        dialog.setText(translate('LuzCam · César González / Hobbieless'))
        dialog.setInformativeText(translate('Inspiración didáctica: CameraSim, creado por Jon Arnold (https://www.camerasim.com), y Canon Outside of Auto (Canon Canada). LuzCam es un proyecto independiente, sin afiliación ni respaldo de estos proyectos.')+'\n\n'+translate('Utiliza Qt/PySide6 y FFmpeg. Consulte sus licencias en los detalles y en ThirdParty.'))
        dialog.setDetailedText(translate('Qt/PySide6: licencias GPLv3/LGPLv3 y avisos propios de cada componente.')+'\n\nCameraSim: https://www.camerasim.com/about\nCanon Outside of Auto: https://www.canon.ca/dam/about/News/Press-Releases/2013/2013-JAN-24-OUTSIDEOFAUTO-EN.pdf\n\n'+translate('LuzCam utiliza bibliotecas de FFmpeg bajo LGPLv2.1 o posterior. Los avisos y licencias de terceros se incluyen en los recursos de la aplicación, carpeta ThirdParty.')+'\nFFmpeg: https://ffmpeg.org')
        dialog.setStandardButtons(QMessageBox.Close);dialog.button(QMessageBox.Close).setText(translate('Cerrar'))
        details_button=next(b for b in dialog.buttons() if dialog.buttonRole(b)==QMessageBox.ActionRole)
        def update_details_text():
            expanded=any(edit.isVisibleTo(dialog) for edit in dialog.findChildren(QTextEdit))
            details_button.setText(translate('Ocultar detalles…' if expanded else 'Mostrar detalles…'))
        update_details_text();details_button.ensurePolished()
        details_button.setMinimumWidth(max(details_button.fontMetrics().horizontalAdvance(translate(value)) for value in ('Mostrar detalles…','Ocultar detalles…'))+32)
        details_button.clicked.connect(lambda:QTimer.singleShot(0,dialog,update_details_text))
        try:dialog.exec()
        finally:dialog.deleteLater()
    def change_language(self,index):
        code=('es','en')[index];self.settings.setValue('language',code);set_language(code);self.refresh()
        self.language_picker.setAccessibleName(translate('Idioma'))
        if getattr(self,'detail_camera',None):self.detail_camera.update()
    def apply_configuration(self):
        self.pause.setChecked(self.config_steps.isChecked()); self.moving=self.config_moving.isChecked()
        self.session.setting.set_thirds(self.config_thirds.isChecked()); self.reload_controls(); self.refresh()
    def reload_controls(self):
        s=self.session.setting
        for slider,value,count in zip(self.sliders,(s.a,s.s,s.i),(len(s.apertures),len(s.shutters),len(s.isos))):
            slider.blockSignals(True); slider.setRange(0,count-1); slider.setValue(value); slider.blockSignals(False)
        self.config.setToolTip('Pasos actuales: '+('⅓ EV' if s.thirds else '1 EV')+'. Pulsar para cambiar.')
    def setting_changed(self,n,value):
        if self.session.busy: return
        setattr(self.session.setting,('a','s','i')[n],value); self.refresh()
    def change_camera(self,i):
        if self.session.busy: return
        self.timer.stop(); self.selected=None; self.session.reset(); self.diaphragm_preview=False
        self.session.setting.select_camera(i); self.reload_controls(); self.refresh()
    def light_changed(self,i):
        if self.session.busy: return
        self.selected=None; self.session.reset(); self.session.setting.light=i; self.refresh()
    def pause_changed(self,checked):
        if checked: self.timer.stop()
        elif self.session.busy: self.schedule()
    def schedule(self):
        if self.session.busy and not self.pause.isChecked(): self.timer.start(round(interval(self.session.phase,self.session.shot)*1000))
    def auto_advance(self): self.advance()
    def advance(self):
        if getattr(self,'settings_overlay',None):return
        if self.session.phase in (0,7) and len(self.session.history)>=self.session.history_limit:
            self.timer.stop();self.refresh();return
        if self.timer.isActive():
            self.timer.stop(); self.refresh(); return
        if self.session.phase in (0,7):
            self.session.setting.scene_frame=self.video_scene_frame if self.moving else 0
            self.shot_video_image=self.last_video_image.copy() if self.moving else self.scene_image(self.session.setting.light)
        self.selected=None; self.diaphragm_preview=False; before=len(self.session.history); self.session.advance()
        self.session.setting.scene_frame=0
        if self.session.phase==1: self.photos.request(self.session.shot,'capture')
        if len(self.session.history)>before:
            index=len(self.session.history)-1; shot=self.session.history[index]
            cached=self.photos.cache.get(shot.key)
            if cached is not None:
                buffer=QBuffer(); buffer.open(QIODevice.WriteOnly); cached.save(buffer,'PNG'); self.saved_photos[shot.key]=bytes(buffer.data())
            from PySide6.QtGui import QIcon,QTransform
            from PySide6.QtCore import QSize
            b=QPushButton(); b.setCheckable(True); b.setProperty('captureIndex',index); b.setToolTip(shot.label); b.setAccessibleName(f'Captura {index+1}: {shot.label}'); b.setFixedSize(132,96)
            thumbnail=QLabel(b); thumbnail.setGeometry(6,4,120,68); thumbnail.setObjectName('captureThumbnail'); self.update_thumbnail(b,index); thumbnail.setAttribute(Qt.WA_TransparentForMouseEvents)
            caption=label(f'f/{shot.f:g} · {shot.shutters[shot.s]}',9,'mono'); caption.setParent(b); caption.setGeometry(4,74,124,20); caption.setAlignment(Qt.AlignCenter); caption.setAttribute(Qt.WA_TransparentForMouseEvents)
            b.clicked.connect(lambda checked=False,index=index:self.review(index)); self.film.insertWidget(0,b); self.film_empty.hide(); self.selected=index

        elif self.session.phase==7: self.selected=len(self.session.history)-1
        self.schedule(); self.refresh()
    def go_back(self): self.timer.stop(); self.selected=None; self.session.back(); self.refresh()
    def reset(self): self.timer.stop(); self.selected=None; self.diaphragm_preview=False; self.session.reset(); self.refresh()
    def confirm_clear_film(self):
        if self.session.busy or not self.session.history:return
        dialog=QMessageBox(self);dialog.setWindowTitle(translate('Vaciar carrete'))
        dialog.setText(translate('¿Eliminar todas las fotografías de esta sesión? No se pueden recuperar.'))
        dialog.setStandardButtons(QMessageBox.Yes|QMessageBox.Cancel);dialog.setDefaultButton(QMessageBox.Cancel)
        dialog.button(QMessageBox.Yes).setText(translate('Eliminar fotografías'));dialog.button(QMessageBox.Cancel).setText(translate('Cancelar'))
        try:
            if dialog.exec()==QMessageBox.Yes:self.clear_history()
        finally:dialog.deleteLater()
    def clear_history(self):
        self.reset();self.session.history.clear();self.session.shot=None;self.session.recorded=False
        self.saved_photos.clear();self.photo_errors.clear();self.review_cache.clear()
        while self.film.count():
            widget=self.film.takeAt(0).widget()
            if widget is not self.film_empty:widget.deleteLater()
        self.film_empty.show();self.film.addWidget(self.film_empty);self.refresh()
    def review(self,index):
        if self.session.busy: return
        self.selected=index; self.refresh()
    def show_live(self):
        if self.session.busy: return
        self.selected=None
        if self.session.phase==7: self.session.reset()
        self.refresh()
    def scene_image(self,light):
        if light not in self.scene_images:
            self.scene_images[light]=QImage(str(ROOT/'Scene'/(('day','dusk','night')[light]+'.png'))).scaled(960,540,Qt.KeepAspectRatio,Qt.SmoothTransformation)
        return self.scene_images[light]
    def image_for(self,setting,channel='preview'):
        if setting.key in self.saved_photos: return self.review_cache.image(setting.key,self.saved_photos[setting.key])
        image=self.photos.request(setting,channel)
        return image if image is not None else QImage()
    def update_thumbnail(self,button,index):
        thumbnail=button.findChild(QLabel,'captureThumbnail')
        if thumbnail is None: return
        key=self.session.history[index].key
        if button.property('thumbnailKey')==key:return
        image=self.review_cache.image(key,self.saved_photos[key]) if key in self.saved_photos else self.photos.cache.get(key)
        if image is not None and not image.isNull():
            thumbnail.setPixmap(QPixmap.fromImage(image).scaled(120,68,Qt.KeepAspectRatio,Qt.SmoothTransformation));button.setProperty('thumbnailKey',key)
    def photo_ready(self,key,image):
        if any(shot.key==key for shot in self.session.history):
            buffer=QBuffer(); buffer.open(QIODevice.WriteOnly); image.save(buffer,'PNG'); self.saved_photos[key]=bytes(buffer.data())
            for n in range(self.film.count()):
                item=self.film.itemAt(n).widget()
                if isinstance(item,QPushButton) and self.session.history[item.property('captureIndex')].key==key:self.update_thumbnail(item,item.property('captureIndex'))
        self.refresh()
    def photo_failed(self,key,error):
        self.photo_errors[key]='No se pudo calcular la fotografía: '+error
        self.refresh()
    def poll_video(self):
        frame=self.sink.videoFrame()
        if not frame.isValid():return
        token=(self.loaded_light,frame.startTime() if frame.startTime()>=0 else self.player.position())
        if token==self._video_token:return
        self._video_token=token;self.video_frame(frame)
    def video_frame(self,frame):
        if not frame.isValid(): return
        if self.selected is None and not self.session.busy:
            timestamp=frame.startTime()/1000000 if frame.startTime()>=0 else self.player.position()/1000
            self.video_scene_frame=round(timestamp*self.scene_timing['fps'])%self.scene_timing['frames']
            self.last_video_image=frame.toImage().copy()
            self.video_frames_presented+=1
            self.photo.image=self.live_image(self.last_video_image); self.photo.update()
            if getattr(self,'detail_photo',None): self.detail_photo.image=self.photo.image; self.detail_photo.update()
            self.update_electronic_live(self.photo.image)
    def live_image(self,image):
        s=self.session.setting
        return exposure_preview(image,s.meter_third) if self.preview.isChecked() and s.camera!=0 else image
    def update_electronic_live(self,image):
        if self.session.setting.camera==0 or self.camera.lcd_review:return
        self.camera.electronic=image; self.camera.update()
        if getattr(self,'detail_camera',None):
            self.detail_camera.electronic=image; self.detail_camera.update()
    def video_error(self,*args):
        self.photo.message='Vídeo no disponible. Se muestra la escena fija.'; self.photo.update()
    def refresh(self,*args):
        s=self.session.setting; observed=self.session.observed; phase=self.session.phase; busy=self.session.busy
        for i,b in enumerate(self.camera_buttons): b.setChecked(i==s.camera); b.setEnabled(not busy)
        for slider in self.sliders: slider.setEnabled(not busy)
        for control in (self.light,self.preview,self.pause): control.setEnabled(not busy)
        for i,b in enumerate(self.light_buttons): b.setChecked(i==s.light); b.setEnabled(not busy)
        self.sensitivity_value.setText(str(observed.isos[observed.i])); self.shutter_value.setText(observed.shutters[observed.s]); self.iris_value.setText(f'f/{observed.f:g}'); self.shutter_title.setText('SENSOR' if s.camera==2 else 'OBTURADOR')
        self.preview.setVisible(s.camera!=0); self.camera_name.setText(s.spec['name']); self.detail.setText(s.spec['detail']); self.meter.third=s.meter_third; self.meter.update(); self.meter.setAccessibleName(f'Fotómetro: {s.offset:+.2f} EV')
        for slider,label,text in zip(self.sliders,self.value_labels,(f'f/{s.f:g}',s.shutters[s.s],str(s.isos[s.i]))):
            label.setText(text);slider.setProperty('luzcamValueText',text)
        self.phase_title.setText(title(phase,observed)); self.expl.setText(f'Previsualización del diafragma: las palas cierran hasta f/{observed.f:g} sin disparar. Al soltar, vuelve la abertura de observación.' if phase==0 and self.diaphragm_preview and s.camera==0 else explanation(phase,observed)); self.back.setEnabled(phase>0); self.fire.setText('Pausar' if self.timer.isActive() else 'Siguiente' if busy else 'Disparar')
        full=len(self.session.history)>=self.session.history_limit
        self.fire.setEnabled(busy or not full);self.clear_film.setEnabled(not busy and bool(self.session.history))
        if full and not busy:self.fire.setText('Carrete lleno');self.fire.setToolTip('Máximo de 100 fotos. Vacía el carrete para seguir; no se borra ninguna automáticamente.')
        self.check_iris.setVisible(s.camera==0); self.check_iris.setEnabled(phase==0); self.check_iris.setText('Soltar' if self.diaphragm_preview else 'Comprobar'); self.camera.set_pose(s.camera,pose(phase,observed,self.diaphragm_preview))
        if s.camera!=0 and not busy:
            self.camera.electronic=self.scene_image(s.light)
        else: self.camera.electronic=QImage()
        reviewed=self.session.history[self.selected] if self.selected is not None else self.session.shot if phase==7 else None
        self.camera.lcd_review=reviewed is not None; self.camera.lcd_setting=reviewed or observed
        if reviewed is not None: self.camera.electronic=self.image_for(reviewed,'capture')
        self.camera.update(); self.fire.setAccessibleName(self.fire.text()); self.fire.setToolTip('Máximo de 100 fotos. Vacía el carrete para seguir; no se borra ninguna automáticamente.' if full and not busy else self.fire._source_text+' · Espacio'); self.fire.update()
        displayed=self.session.history[self.selected] if self.selected is not None else None
        self.displayed_key=displayed.key if displayed else None
        if displayed:
            self.player.pause()
            image=self.image_for(displayed,'capture' if self.selected is not None else 'preview')
            self.photo.image=image; self.photo.message=self.photo_errors.get(displayed.key,'Calculando fotografía…') if image.isNull() else ''; self.photo.update()
            self.metadata.setText(displayed.label+' · '+CONTRACT['lights'][displayed.light]['name']); self.scene_title.setText('REVISIÓN / PLAY' if self.selected is not None else 'ESCENA / VISOR')
        else:
            self.metadata.setText(''); self.scene_title.setText('ESCENA / VISOR'); self.photo.image=self.shot_video_image if busy and not self.shot_video_image.isNull() else self.last_video_image if self.moving and self.loaded_light==s.light and not self.last_video_image.isNull() else self.scene_image(s.light); self.photo.message=''; self.photo.update()
            if self.loaded_light!=s.light:
                self.player.stop(); self.video_scene_frame=0; self.last_video_image=QImage(); self.loaded_light=s.light; self.player.setSource(QUrl.fromLocalFile(str(ROOT/'Scene'/(('day','dusk','night')[s.light]+'.mp4'))))
            self.photo.image=self.live_image(self.photo.image); self.photo.update()
            self.update_electronic_live(self.photo.image)
            if busy: self.player.pause()
            elif self.moving and not self.isMinimized(): self.player.play()
            else: self.player.pause(); self.player.setPosition(0)

        self.live.setVisible(self.selected is not None)
        self.scene_name.setVisible(self.selected is None); self.scene_hint.setVisible(self.selected is None)
        self.metadata.setVisible(displayed is not None)
        self.film_title.setText(f'CARRETE · {len(self.session.history)} / 100')
        for n in range(self.film.count()):
            item=self.film.itemAt(n).widget()
            if isinstance(item,QPushButton): item.setChecked(item.property('captureIndex')==self.selected)
        if getattr(self,'detail_photo',None): self.detail_photo.image=self.photo.image; self.detail_photo.update()
        if getattr(self,'detail_camera',None):
            self.detail_camera.electronic=self.camera.electronic; self.detail_camera.lcd_setting=self.camera.lcd_setting; self.detail_camera.lcd_review=self.camera.lcd_review; self.detail_pause.blockSignals(True); self.detail_pause.setChecked(self.pause.isChecked()); self.detail_pause.blockSignals(False); self.detail_pause.setEnabled(not busy); self.detail_iso.setText(f'ISO {observed.isos[observed.i]} · ruido ilustrativo'); self.detail_camera.set_pose(s.camera,pose(phase,observed,self.diaphragm_preview))
            self.detail_phase.setText(self.phase_title.text()); self.detail_expl.setText(self.expl.text()); self.detail_fire.setText(self.fire.text()); self.detail_fire.setEnabled(self.fire.isEnabled()); self.detail_fire.setAccessibleName(self.fire.text()); self.detail_fire.setToolTip(self.fire.toolTip()); self.detail_fire.update()
            self.detail_shutter_title.setText('Sensor · brillo durante el registro' if s.camera==2 else 'Primera cortinilla → exposición → segunda cortinilla')
            for i,b in enumerate(self.detail_camera_buttons): b.setChecked(i==s.camera); b.setEnabled(not busy)

def main():
    app=QApplication(sys.argv); app.setApplicationName('LuzCam'); app.setWindowIcon(QIcon(str(Path(__file__).with_name('icons')/'luzcam.png'))); window=Window()
    if '--verify-installation' in sys.argv:
        import platform
        from PySide6.QtCore import qVersion
        output=Path(sys.argv[sys.argv.index('--verify-installation')+1])
        report={'system':platform.system(),'qt':qVersion(),'resources':str(ROOT),'captures':0}
        try:
            window.moving=False; window.show(); app.processEvents()
            for camera in range(3):
                window.change_camera(camera)
                assert not window.camera.plates[camera].isNull()
                for light in range(3):
                    window.light.setCurrentIndex(light)
                    for _ in range(7): window.advance(); app.processEvents()
                    import time
                    deadline=time.monotonic()+20
                    while window.session.history[-1].key not in window.saved_photos and time.monotonic()<deadline:
                        app.processEvents(); time.sleep(.01)
                    assert window.session.history[-1].key in window.saved_photos, str(window.photo_errors)
                    assert not window.photo.image.isNull()
                    window.reset()
            report['captures']=len(window.session.history)
            assert report['captures']==9
            assert {'Noto Sans','Noto Serif','Noto Sans Mono'} <= set(QFontDatabase.families())
            report['passed']=True
        except Exception as error:
            import traceback
            report['passed']=False; report['error']=str(error); report['traceback']=traceback.format_exc()
        finally:
            window.close(); output.write_text(json.dumps(report,indent=2),encoding='utf-8')
        sys.exit(0 if report['passed'] else 1)
    window.show()
    from .desktop_window import integrate_window_chrome
    QTimer.singleShot(0,lambda:integrate_window_chrome(window))
    sys.exit(app.exec())
