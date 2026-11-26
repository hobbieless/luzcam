"""Native Qt rendering of the approved v18 study; no HTML/browser runtime.

Coordinates are the reviewed 1376x768 plate registration, not commercial CAD.
"""
import json,math
from functools import lru_cache
from PySide6.QtCore import Qt,QPointF,QRectF
from PySide6.QtGui import QImage,QPainter,QPainterPath,QPainterPathStroker,QPolygonF,QColor,QPen,QFont,QLinearGradient,QTransform
from .model import ROOT
from .light_beam import ribbon

LCD_QUAD=((988,347.5),(1119,305.5),(1117,452.5),(986.5,501))

@lru_cache(maxsize=1)
def geometry():return json.loads((ROOT/'CameraArt/reflex-reviewed-geometry.json').read_text())
def _path(points):
    path=QPainterPath(QPointF(*points[0]))
    for point in points[1:]:path.lineTo(QPointF(*point))
    return path

def curtain_leaves(progress,second=False):
    height=.37;stride=(1-height)/2
    result=[]
    for i in range(2,-1,-1):
        closed=i*stride;parked=-.39-(2-i)*.025 if second else 1.02+i*.025
        top=parked+(closed-parked)*progress if second else closed+(parked-closed)*progress
        result.append((top,top+height))
    return result

def beam_appearance(width,g=None):
    maximum=74*.86*(g or geometry())['irisVisualScale'];q=max(0,min(1,width/maximum));closed=(1-q)**2
    return 5-3.7*closed,1-.7*closed

def _beam(p,points,widths,opacity,g=None):
    if len(points)<2 or opacity<=0:return
    if isinstance(widths,(float,int)):widths=[widths]*len(points)
    points=[QPointF(*v) for v in points];constant=max(widths)-min(widths)<1e-6
    falloff,peak=beam_appearance(min(widths),g);edge=math.exp(-falloff);previous=0
    center=QPainterPath(points[0])
    for point in points[1:]:center.lineTo(point)
    stroke=QPainterPathStroker();stroke.setCapStyle(Qt.FlatCap);stroke.setJoinStyle(Qt.RoundJoin)
    for layer in range(64,0,-1):
        radius=layer/64;target=opacity*peak*(math.exp(-falloff*radius*radius)-edge)/(1-edge)
        alpha=(target-previous)/max(.001,1-previous);previous=target
        if alpha<=0:continue
        color=QColor('white');color.setAlphaF(max(0,min(1,alpha)))
        if constant:stroke.setWidth(widths[0]*radius);shape=stroke.createStroke(center)
        else:shape=ribbon(points,widths,radius)
        p.fillPath(shape,color)

def _gradient(points,colors):
    xs=[v[0] for v in points];ys=[v[1] for v in points]
    g=QLinearGradient(min(xs),min(ys),max(xs),max(ys))
    for i,c in enumerate(colors):g.setColorAt(i/(len(colors)-1),QColor(c))
    return g

def _fill(p,points,colors,outline=None):
    shape=_path(points);shape.closeSubpath();p.fillPath(shape,_gradient(points,colors))
    if outline:p.strokePath(shape,QPen(QColor(outline),.9))

def _exclude(p,points):
    path=QPainterPath();path.addRect(QRectF(0,0,1376,768));hole=_path(points);hole.closeSubpath();path.addPath(hole);path.setFillRule(Qt.OddEvenFill);p.setClipPath(path,Qt.IntersectClip)

def _iris(p,g,opening):
    scale=g['irisVisualScale'];basis=[v*scale for v in g['irisBasis']];x,y=g['irisDisplay'];R=37;r=R*opening
    def polar(radius,angle):return QPointF(radius*math.cos(angle),radius*math.sin(angle))
    carrier_visible=g.get('irisCarrierVisible',True)
    for dx,dy,back in (((3.8,-1.15,True),(0,0,False)) if carrier_visible else ()):
        p.save();p.translate(x+dx*scale,y+dy*scale);p.setTransform(QTransform(*basis,0,0),True)
        grad=QLinearGradient(-45,-45,45,45)
        for stop,color in ((0,'#354047' if back else '#cccccc'),(.5,'#202a30' if back else '#616b6d'),(1,'#10191d' if back else '#b8bfc0')):grad.setColorAt(stop,QColor(color))
        ring=QPainterPath();ring.addEllipse(QPointF(),44,44);ring.addEllipse(QPointF(),36.8,36.8);ring.setFillRule(Qt.OddEvenFill)
        p.fillPath(ring,grad);p.strokePath(ring,QPen(QColor('#293338'),.8));p.restore()
    p.save();p.translate(x,y);p.setTransform(QTransform(*basis,0,0),True)
    pupil=QPainterPath();pupil.moveTo(polar(r,0))
    for i in range(1,7):pupil.lineTo(polar(r,i*2*math.pi/7))
    pupil.closeSubpath();outside=QPainterPath();outside.addRect(QRectF(-60,-60,120,120));outside.addPath(pupil);outside.setFillRule(Qt.OddEvenFill)
    p.save();p.setClipPath(outside,Qt.IntersectClip)
    for i in range(7):
        a=i*2*math.pi/7;path=QPainterPath(polar(r,a));path.lineTo(polar(r,a+2*math.pi/7));path.quadTo(polar(.8*R,a+1.1),polar(R,a+1.7))
        for k in range(1,25):path.lineTo(polar(R,a+1.7-1.25*k/24))
        path.quadTo(polar(.8*R,a+.1),polar(r,a));path.closeSubpath();grad=QLinearGradient(polar(R,a),QPointF());grad.setColorAt(0,QColor('#999999'));grad.setColorAt(1,QColor('#252525'))
        p.fillPath(path,grad);p.strokePath(path,QPen(QColor('#151515'),.555))
    p.restore()
    if carrier_visible:
        for i in range(7):
            center=polar(40,i*2*math.pi/7+.48);p.setPen(QPen(QColor('#475357'),.45));p.setBrush(QColor('#cbd1d2'));p.drawEllipse(center,1.1,1.1)
    p.restore()

def lcd_labels(p,setting,review):
    from .vector_text import draw_vector_text
    p.setPen(QColor('#edf0e7'));font=QFont('Noto Sans Mono');font.setPixelSize(40);p.setFont(font)
    draw_vector_text(p,QRectF(20,12,600,60),Qt.AlignCenter,'PLAY' if review else 'M')
    if review:
        font.setPixelSize(25);p.setFont(font);draw_vector_text(p,QRectF(10,397,620,65),Qt.AlignCenter,f'f/{setting.f:g}  {setting.shutters[setting.s]}  ISO {setting.isos[setting.i]}')
    else:
        font.setPixelSize(58);p.setFont(font)
        for y,value in zip((100,210,320),(f'f/{setting.f:g}',setting.shutters[setting.s],f'ISO {setting.isos[setting.i]}')):draw_vector_text(p,QRectF(15,y,610,85),Qt.AlignCenter,value)

def lcd_image(setting,review,photo,labels=True):
    image=QImage(640,480,QImage.Format_ARGB32_Premultiplied);image.fill(QColor('#101617'));p=QPainter(image);p.setRenderHint(QPainter.SmoothPixmapTransform)
    if review and not photo.isNull():
        size=photo.size().scaled(600,300,Qt.KeepAspectRatio);p.drawImage(QRectF((640-size.width())/2,80+(300-size.height())/2,size.width(),size.height()),photo)
    if labels:lcd_labels(p,setting,review)
    p.end();return image

def draw(p,frame,plate,state,setting,review,photo):
    g=geometry();p.save();p.translate(frame.x(),frame.y());p.scale(frame.width()/1376,frame.height()/768)
    p.drawImage(QRectF(0,0,1376,768),plate)
    def render_optics(p):
        gate=g['shutterGate']
        def at(u,v):return [(1-v)*((1-u)*gate[0][i]+u*gate[1][i])+v*((1-u)*gate[3][i]+u*gate[2][i]) for i in range(2)]
        shape=_path(gate);shape.closeSubpath();p.strokePath(shape,QPen(QColor('#141b1d'),7));_fill(p,gate,['#345865','#40696d','#24444d'])
        p.save();p.setClipPath(shape,Qt.IntersectClip)
        for progress,second in ((state['front'],False),(state['rear'],True)):
            for top,bottom in curtain_leaves(progress,second):
                poly=[at(0,top),at(1,top),at(1,bottom),at(0,bottom)];_fill(p,poly,['#717777','#353e40','#4e595a'] if second else ['#485153','#242c2e','#475052']);p.strokePath(_path([at(0,top),at(1,top)]),QPen(QColor('#899291'),.7))
        p.restore()
        index=max(0,min(100,state['mirrorDown']*100));lo=int(index);hi=min(100,lo+1);t=index-lo;frames=g['mirrorDisplay'];a,b=frames[lo],frames[hi]
        def interp(key):return [[x+(y-x)*t for x,y in zip(v,w)] for v,w in zip(a[key],b[key])]
        mirror={key:interp(key) for key in ('front','back')}
        for key in ('hit','bounce'):mirror[key]=[x+(y-x)*t for x,y in zip(a[key],b[key])] if a[key] is not None and b[key] is not None else None
        opening=max(0,min(.86,state['aperture']/.85*.86));admitted=74*opening*g['irisVisualScale'];illum=state['illumination']
        _beam(p,[g['front'],g['iris']],[135,72*g['irisVisualScale']],.50*illum)
        stop=mirror['hit'] or at(.5,.5)
        if not (mirror['hit'] and state['mirrorDown']>.999):_beam(p,[g['iris'],stop],admitted,.55*illum)
        p.save();_exclude(p,g['foreground'])
        for i in range(4):_fill(p,[mirror['front'][i],mirror['front'][(i+1)%4],mirror['back'][(i+1)%4],mirror['back'][i]],['#a3afb0','#53636a','#1e2d34'],'#34434a')
        _fill(p,mirror['front'],['#cad3d3','#89979a','#b7c3c4'],'#738183');p.restore()
        if mirror['hit'] and state['mirrorDown']>.999:_beam(p,[g['iris'],mirror['hit'],g['focus']]+g['route'],admitted,.55*illum)
        elif mirror['hit'] and mirror['bounce']:_beam(p,[mirror['hit'],mirror['bounce']],admitted,.45*illum)
        p.save();_exclude(p,g['irisForeground']);_iris(p,g,opening);p.restore()
    from .vector_layers import draw_layer
    key=(id(g),tuple(sorted(state.items())))
    draw_layer(p,'reflex',key,render_optics)
    lcd=lcd_image(setting,review,photo,labels=False);source=QPolygonF([QPointF(0,0),QPointF(640,0),QPointF(640,480),QPointF(0,480)])
    target=QPolygonF([QPointF(*v) for v in LCD_QUAD]);p.save();p.setTransform(QTransform.quadToQuad(source,target),True);p.drawImage(QPointF(),lcd);lcd_labels(p,setting,review);p.restore();p.restore()
