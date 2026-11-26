"""One diffuse cross-section for incident, transmitted and reflected light."""
import math
from PySide6.QtCore import Qt,QPointF
from PySide6.QtGui import QPainterPath,QPainterPathStroker,QColor

def ribbon(points,widths,radius):
    """Variable-width joined ribbon; width is total Gaussian support diameter."""
    normals=[]
    for a,b in zip(points,points[1:]):
        dx=b.x()-a.x(); dy=b.y()-a.y(); length=math.hypot(dx,dy)
        normals.append((-dy/length,dx/length) if length>1e-9 else (0.,1.))
    left=[];right=[]
    for i,(point,width) in enumerate(zip(points,widths)):
        if i==0: nx,ny=normals[0]; factor=1
        elif i==len(points)-1: nx,ny=normals[-1]; factor=1
        else:
            a,b=normals[i-1:i+1]; nx=a[0]+b[0];ny=a[1]+b[1];length=math.hypot(nx,ny)
            if length<1e-8:nx,ny=b;factor=1
            else:
                nx/=length;ny/=length;factor=min(2.,1/max(.001,nx*b[0]+ny*b[1]))
        distance=width*.5*radius*factor
        left.append(QPointF(point.x()+nx*distance,point.y()+ny*distance))
        right.append(QPointF(point.x()-nx*distance,point.y()-ny*distance))
    path=QPainterPath(left[0]);path.setFillRule(Qt.WindingFill)
    for point in left[1:]+right[::-1]:path.lineTo(point)
    path.closeSubpath();return path

def draw_beam(painter,points,widths,intensity=.66):
    if len(points)<2 or intensity<=0:return
    constant=max(widths)-min(widths)<1e-6
    if constant:
        center=QPainterPath(points[0])
        for point in points[1:]:center.lineTo(point)
        stroke=QPainterPathStroker();stroke.setCapStyle(Qt.FlatCap);stroke.setJoinStyle(Qt.RoundJoin)
    previous=0.;painter.setPen(Qt.NoPen)
    for layer in range(24,0,-1):
        radius=layer/24;target=intensity*math.exp(-5*radius*radius)
        alpha=(target-previous)/max(.001,1-previous);previous=target
        color=QColor('white');color.setAlphaF(max(0,min(1,alpha)))
        if constant:
            stroke.setWidth(widths[0]*radius);shape=stroke.createStroke(center)
        else:shape=ribbon(points,widths,radius)
        painter.fillPath(shape,color)
