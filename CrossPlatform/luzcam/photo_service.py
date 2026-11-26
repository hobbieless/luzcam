"""Bounded, coalescing photo work queue shared by both desktop targets."""
from collections import OrderedDict
from dataclasses import replace
from PySide6.QtCore import QObject, Signal, Slot, QRunnable, QThreadPool
from PySide6.QtGui import QImage

class _Signals(QObject):
    done=Signal(str,object,str)

class _Job(QRunnable):
    def __init__(self,service,key,setting):
        super().__init__(); self.service=service; self.key=key; self.setting=setting
    def run(self):
        try:
            if self.service.renderer is None:
                from .temporary_photo import TemporaryPhoto
                self.service.renderer=TemporaryPhoto(cache_mib=16)
            image=self.service.renderer.render(self.setting).convert('RGB')
            data=image.tobytes()
            result=QImage(data,image.width,image.height,image.width*3,QImage.Format_RGB888).copy()
            self.service.signals.done.emit(self.key,result,'')
        except Exception as error:
            detail=str(error)
            cause=error.__cause__
            while cause is not None:
                detail+='; '+str(cause); cause=cause.__cause__
            self.service.signals.done.emit(self.key,None,detail)

class PhotoService(QObject):
    ready=Signal(str,object)
    failed=Signal(str,str)
    def __init__(self,parent=None,cache_mib=16):
        super().__init__(parent)
        self.pool=QThreadPool(self); self.pool.setMaxThreadCount(1)
        self.signals=_Signals(self); self.signals.done.connect(self._done)
        self.renderer=None; self.active=None; self.pending=OrderedDict()
        self.cache=OrderedDict(); self.cache_bytes=0; self.limit=int(cache_mib*1024**2)
        self.errors={}; self.closing=False

    def request(self,setting,channel='preview'):
        key=setting.key
        if key in self.cache:
            self.cache.move_to_end(key); return self.cache[key]
        if self.closing or key in self.errors: return None
        if key!=self.active:
            # At most one latest request per purpose: sliders cannot build an
            # unbounded queue. Capture/history requests take priority.
            self.pending[channel]=(key,replace(setting))
            self._pump()
        return None

    def _pump(self):
        if self.active is not None or not self.pending or self.closing: return
        if 'capture' in self.pending: key,setting=self.pending.pop('capture')
        else: _,(key,setting)=self.pending.popitem()
        if key in self.cache:
            self._pump(); return
        self.active=key; self.pool.start(_Job(self,key,setting))

    @Slot(str,object,str)
    def _done(self,key,image,error):
        self.active=None
        if self.closing: return
        if error:
            self.errors[key]=error; self.failed.emit(key,error)
        else:
            size=image.sizeInBytes()
            if size<=self.limit:
                while self.cache and self.cache_bytes+size>self.limit:
                    _,old=self.cache.popitem(last=False); self.cache_bytes-=old.sizeInBytes()
                self.cache[key]=image; self.cache_bytes+=size
            self.ready.emit(key,image)
        self._pump()

    def close(self):
        self.closing=True; self.pending.clear(); self.pool.clear()
        self.pool.waitForDone()
