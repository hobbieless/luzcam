"""Brightness-only electronic preview; never integrates motion or adds blur/noise."""
from functools import lru_cache
import numpy as np
from PySide6.QtGui import QImage

@lru_cache(maxsize=64)
def exposure_table(thirds):
    value=np.arange(256,dtype=np.float32)/255
    linear=np.where(value<=.04045,value/12.92,((value+.055)/1.055)**2.4)
    linear=np.clip(linear*2**(max(-30,min(30,thirds))/3),0,1)
    encoded=np.where(linear<=.0031308,linear*12.92,1.055*linear**(1/2.4)-.055)
    return np.rint(encoded*255).astype(np.uint8)

def exposure_preview(image,thirds):
    if image.isNull() or thirds==0:return image
    source=image.convertToFormat(QImage.Format_RGBA8888)
    pixels=np.frombuffer(source.bits(),np.uint8).reshape(source.height(),source.bytesPerLine())
    rgba=pixels[:,:source.width()*4].reshape(source.height(),source.width(),4)
    rgba[:,:,:3]=exposure_table(thirds)[rgba[:,:,:3]]
    return source
