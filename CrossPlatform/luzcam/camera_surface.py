"""Composite the existing studio plates onto the panel, preserving registration/RGB.

Only the light exterior connected to the image border becomes transparent.
This is a presentation layer; source photographs are never rewritten.
"""
from functools import lru_cache
from pathlib import Path
import numpy as np
from PIL import Image,ImageDraw
from PySide6.QtGui import QImage

@lru_cache(maxsize=3)
def load_plate(path):
    image=QImage(str(path)).convertToFormat(QImage.Format_RGBA8888)
    if image.isNull():return image
    w,h=image.width(),image.height()
    # The converted QImage owns this writable buffer. Keep its RGB intact and
    # write alpha in place instead of copying the complete plate twice.
    rgba=np.frombuffer(image.bits(),np.uint8).reshape(h,image.bytesPerLine())[:,:w*4].reshape(h,w,4)
    border=np.concatenate((rgba[0,:,:3],rgba[-1,:,:3],rgba[:,0,:3],rgba[:,-1,:3])).astype(np.float32)
    paper=np.median(border,axis=0)
    # Two bounded passes preserve the exact float32 arithmetic while avoiding
    # several full-resolution RGB/float64/edge-distance temporary images.
    rows=64;eligible=np.empty((h,w),dtype=np.bool_)
    for y in range(0,h,rows):
        rgb=rgba[y:y+rows,:,:3].astype(np.float32)
        distance=np.max(np.abs(rgb-paper),axis=2)
        eligible[y:y+rows]=(distance<55)&(rgb.min(axis=2)>125)
    # The clear prism belongs to the camera, even where it resembles paper.
    if Path(path).name.startswith('reflex'):
        protect=Image.new('L',(w,h));draw=ImageDraw.Draw(protect)
        draw.polygon([(int(x*w/1376),int(y*h/768)) for x,y in [(650,215),(702,174),(759,161),(834,182),(875,223),(870,270),(794,309),(667,289)]],fill=255)
        eligible &= np.asarray(protect)==0
    small=Image.fromarray(eligible.astype('uint8')*np.uint8(255)).resize((688,384),Image.Resampling.NEAREST)
    flood=Image.new('L',(690,386),255);flood.paste(small,(1,1));ImageDraw.floodfill(flood,(0,0),128)
    connected=Image.fromarray((np.asarray(flood)[1:-1,1:-1]==128).astype('uint8')*255).resize((w,h),Image.Resampling.NEAREST)
    connected=(np.asarray(connected)>0)&eligible
    xx=np.arange(w)[None,:];edge_x=np.minimum(xx,w-1-xx)
    for y in range(0,h,rows):
        rgb=rgba[y:y+rows,:,:3].astype(np.float32)
        distance=np.max(np.abs(rgb-paper),axis=2)
        yy=np.arange(y,min(y+rows,h))[:,None]
        edge=np.minimum(edge_x,np.minimum(yy,h-1-yy))
        alpha=np.clip((distance-2)/53,0,1)**2*np.clip(edge/24,0,1)
        rgba[y:y+rows,:,3]=np.where(connected[y:y+rows],np.rint(alpha*255),255).astype('uint8')
    return image
