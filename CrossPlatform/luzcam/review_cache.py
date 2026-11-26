"""Bounded lossless decode reuse; the immutable session PNG remains authoritative."""
from collections import OrderedDict
from PySide6.QtGui import QImage
class ReviewCache:
    def __init__(self,capacity=2,decoder=None):
        self.capacity=max(1,capacity);self.items=OrderedDict();self.decoder=decoder or (lambda data:QImage.fromData(data,'PNG'))
    def image(self,key,data):
        previous=self.items.get(key)
        if previous is None or previous[0] is not data:
            previous=(data,self.decoder(data));self.items[key]=previous
        self.items.move_to_end(key)
        while len(self.items)>self.capacity:self.items.popitem(last=False)
        return QImage(previous[1])
    def clear(self):self.items.clear()
