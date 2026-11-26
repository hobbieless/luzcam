"""One vector command recording per camera, excluding photographic/video data.

QPicture preserves paths at the destination scale. Replaced immediately on a
mechanism/light change; bounded to the three registered camera geometries.
"""
from PySide6.QtCore import QPointF
from PySide6.QtGui import QPicture,QPainter
_layers={}
def draw_layer(p,slot,key,render):
    current=_layers.get(slot)
    if current is None or current[0]!=key:
        picture=QPicture();recorder=QPainter(picture)
        recorder.setRenderHints(QPainter.Antialiasing|QPainter.SmoothPixmapTransform)
        try:render(recorder)
        finally:recorder.end()
        current=(key,picture);_layers[slot]=current
    p.drawPicture(QPointF(),current[1])
def clear():_layers.clear()
def bytes_used():return sum(picture.size() for _,picture in _layers.values())
