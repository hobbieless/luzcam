"""Local projective registration of photographic parts, without replacing the body."""
from PySide6.QtCore import Qt,QPointF,QRectF
from PySide6.QtGui import QImage,QPainter,QPainterPath,QPainterPathStroker,QPolygonF,QTransform,QLinearGradient,QColor

def registered_sensor_patch(patch,size,source,opening):
    overlay=QImage(size,QImage.Format_ARGB32_Premultiplied);overlay.fill(Qt.transparent)
    if patch.isNull():return overlay
    source=QPolygonF([QPointF(x*patch.width(),y*patch.height()) for x,y in source])
    target=QPolygonF([QPointF(x*size.width(),y*size.height()) for x,y in opening])
    p=QPainter(overlay);p.setRenderHint(QPainter.SmoothPixmapTransform)
    p.setTransform(QTransform.quadToQuad(source,target));p.drawImage(QPointF(),patch);p.resetTransform()
    # A localized feathered mask leaves every other camera component untouched.
    region=QRectF(976,347,153,311)
    p.setCompositionMode(QPainter.CompositionMode_DestinationIn)
    for horizontal in (True,False):
        g=QLinearGradient(region.left() if horizontal else 0,0 if horizontal else region.top(),region.right() if horizontal else 0,0 if horizontal else region.bottom())
        fraction=10/(region.width() if horizontal else region.height())
        for stop,alpha in ((0,0),(fraction,255),(1-fraction,255),(1,0)):g.setColorAt(stop,QColor(255,255,255,alpha))
        p.fillRect(overlay.rect(),g)
    p.end();return overlay

def registered_prism_housing(patch,size,crop,old_window,new_window):
    """Repair the old oversized hole and its rim; expose only the real crystal."""
    overlay=QImage(size,QImage.Format_ARGB32_Premultiplied);overlay.fill(Qt.transparent)
    if patch.isNull():return overlay
    def path(points):
        shape=QPainterPath();shape.addPolygon(QPolygonF([QPointF(x*size.width(),y*size.height()) for x,y in points]));shape.closeSubpath();return shape
    old=path(old_window);opening=path(new_window)
    mask=QImage(size,QImage.Format_ARGB32_Premultiplied);mask.fill(Qt.transparent)
    painter=QPainter(mask);painter.setRenderHint(QPainter.Antialiasing);painter.setPen(Qt.NoPen);painter.setCompositionMode(QPainter.CompositionMode_Source)
    stroke=QPainterPathStroker();stroke.setJoinStyle(Qt.RoundJoin)
    for radius in (15,14,13,12,11):
        stroke.setWidth(radius*2);alpha=round(255*(16-radius)/6)
        painter.fillPath(old.united(stroke.createStroke(old)),QColor(255,255,255,alpha))
    stroke.setWidth(20);painter.fillPath(old.united(stroke.createStroke(old)),QColor('white'))
    painter.setCompositionMode(QPainter.CompositionMode_Clear);painter.fillPath(opening,QColor('white'));painter.end()
    painter=QPainter(overlay);painter.setRenderHint(QPainter.SmoothPixmapTransform);painter.drawImage(QRectF(*crop),patch)
    painter.setCompositionMode(QPainter.CompositionMode_DestinationIn);painter.drawImage(QPointF(),mask);painter.end()
    return overlay
