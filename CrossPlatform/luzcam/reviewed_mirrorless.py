"""Native rendering of the reviewed mirrorless camera in plate coordinates."""
import json
from functools import lru_cache
from PySide6.QtCore import Qt,QPointF,QRectF
from PySide6.QtGui import QImage,QPainter,QPolygonF,QTransform,QColor,QPen,QFont
from .model import ROOT
from .reviewed_reflex import _path,_fill,_exclude,_iris,_beam,curtain_leaves

@lru_cache(maxsize=1)
def geometry():
    return json.loads((ROOT/'CameraArt/mirrorless-reviewed-geometry.json').read_text())

def lcd_image(setting,review,photo,labels=True):
    image=QImage(640,480,QImage.Format_ARGB32_Premultiplied);image.fill(QColor('#101617'))
    p=QPainter(image);p.setRenderHint(QPainter.SmoothPixmapTransform)
    if not photo.isNull():
        size=photo.size().scaled(640,360,Qt.KeepAspectRatio)
        p.drawImage(QRectF((640-size.width())/2,60+(360-size.height())/2,size.width(),size.height()),photo)
    if labels:lcd_labels(p,setting,review)
    p.end();return image

def lcd_labels(p,setting,review):
    from .vector_text import draw_vector_text
    font=QFont('Noto Sans Mono');font.setPixelSize(25);p.setFont(font);p.setPen(QColor('#edf0e7'))
    draw_vector_text(p,QRectF(15,8,610,42),Qt.AlignLeft|Qt.AlignVCenter,'PLAY' if review else 'M · LIVE')
    draw_vector_text(p,QRectF(10,430,620,42),Qt.AlignCenter,f'f/{setting.f:g}  {setting.shutters[setting.s]}  ISO {setting.isos[setting.i]}')

def draw(p,frame,plate,state,setting,review,photo,*,registered_geometry=None,electronic=False):
    g=geometry() if registered_geometry is None else registered_geometry
    p.save();p.translate(frame.x(),frame.y());p.scale(frame.width()/1376,frame.height()/768)
    p.drawImage(QRectF(0,0,1376,768),plate)
    def render_optics(p):
        gate=g['shutterGate']
        def at(u,v):return [(1-v)*((1-u)*gate[0][i]+u*gate[1][i])+v*((1-u)*gate[3][i]+u*gate[2][i]) for i in range(2)]
        shape=_path(gate);shape.closeSubpath();p.strokePath(shape,QPen(QColor('#141b1d'),2))
        p.save();p.setClipPath(shape,Qt.IntersectClip)
        for progress,second in (() if electronic else ((state['front'],False),(state['rear'],True))):
            for top,bottom in curtain_leaves(progress,second):
                poly=[at(0,top),at(1,top),at(1,bottom),at(0,bottom)]
                _fill(p,poly,['#717777','#353e40','#4e595a'] if second else ['#485153','#242c2e','#475052'])
                p.strokePath(_path([at(0,top),at(1,top)]),QPen(QColor('#899291'),.7))
        if electronic and state['sensorActive']>0:
            color=QColor(111,222,225);color.setAlphaF(.3*state['sensorActive'])
            p.fillPath(shape,color)
        p.restore()
        opening=max(0,min(.86,state['aperture']/.85*.86));admitted=74*opening*g['irisVisualScale'];illum=state['illumination']
        _beam(p,[g['front'],g['iris']],[145,72*g['irisVisualScale']],.50*illum,g)
        _beam(p,[g['iris'],at(.5,.5)],admitted,.55*illum,g)
        p.save();_exclude(p,g['irisForeground']);_iris(p,g,opening);p.restore()
    from .vector_layers import draw_layer
    key=(id(g),tuple(sorted(state.items())))
    draw_layer(p,'compact' if electronic else 'mirrorless',key,render_optics)
    lcd=lcd_image(setting,review,photo,labels=False)
    source=QPolygonF([QPointF(0,0),QPointF(640,0),QPointF(640,480),QPointF(0,480)])
    target=QPolygonF([QPointF(*v) for v in g['lcd']]);p.save();p.setTransform(QTransform.quadToQuad(source,target),True);p.drawImage(QPointF(),lcd);lcd_labels(p,setting,review);p.restore();p.restore()

