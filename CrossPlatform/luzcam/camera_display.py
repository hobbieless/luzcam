"""DSLR rear LCD: settings while metering, immutable photograph in review."""
from PySide6.QtCore import Qt,QRectF
from PySide6.QtGui import QImage,QPainter,QColor,QFont,QPen,QPolygonF
from PySide6.QtCore import QPointF

def display_image(setting,review,photo):
    image=QImage(480,900,QImage.Format_ARGB32_Premultiplied); image.fill(QColor('#101617'))
    p=QPainter(image); p.setRenderHint(QPainter.Antialiasing)
    def text(rect,value,size,bold=False):
        font=QFont('Noto Sans Mono'); font.setPixelSize(size); font.setBold(bold); p.setFont(font); p.setPen(QColor('#edf0e7')); p.drawText(rect,Qt.AlignCenter,value)
    text(QRectF(20,25,440,100),'PLAY' if review else 'M',76,True)
    if review:
        frame=QRectF(16,170,448,252)
        if not photo.isNull():
            fitted=photo.size().scaled(int(frame.width()),int(frame.height()),Qt.KeepAspectRatio)
            target=QRectF(frame.center().x()-fitted.width()/2,frame.center().y()-fitted.height()/2,fitted.width(),fitted.height())
            p.setRenderHint(QPainter.SmoothPixmapTransform); p.drawImage(target,photo)
        else: text(frame,'…',72)
        y=465
    else: y=170
    for value in (f'f/{setting.f:g}',setting.shutters[setting.s],f'ISO {setting.isos[setting.i]}'):
        text(QRectF(15,y,450,100),value,60,True); y+=115
    if not review:
        left,span=50,380
        text(QRectF(22,610,436,60),'−2   1   0   1   2+',32)
        p.setPen(QPen(QColor('#edf0e7'),3))
        for tick in range(13):
            x=left+span*tick/12; p.drawLine(QPointF(x,680),QPointF(x,694 if tick%3==0 else 687))
        x=left+span*setting.meter_fraction
        p.setBrush(QColor('#edf0e7')); p.drawPolygon(QPolygonF([QPointF(x,700),QPointF(x+5,710),QPointF(x+5,733),QPointF(x-5,733),QPointF(x-5,710)]))
        text(QRectF(30,790,420,50),'⅓ EV' if setting.thirds else '1 EV',32)
    p.end(); return image
