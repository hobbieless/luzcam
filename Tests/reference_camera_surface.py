"""Frozen full-frame reference from 7d0345aa; regression oracle, not runtime code."""
from pathlib import Path
import numpy as np
from PIL import Image,ImageDraw
from PySide6.QtGui import QImage

def load_reference_plate(path):
    image=QImage(str(path)).convertToFormat(QImage.Format_RGBA8888)
    if image.isNull():return image
    w,h=image.width(),image.height()
    rgba=np.frombuffer(image.constBits(),np.uint8).reshape(h,image.bytesPerLine())[:,:w*4].reshape(h,w,4).copy()
    rgb=rgba[:,:,:3].astype(np.float32)
    border=np.concatenate((rgb[0],rgb[-1],rgb[:,0],rgb[:,-1]))
    paper=np.median(border,axis=0)
    distance=np.max(np.abs(rgb-paper),axis=2)
    eligible=(distance<55)&(rgb.min(axis=2)>125)
    # The clear prism belongs to the camera, even where it resembles paper.
    if Path(path).name.startswith('reflex'):
        protect=Image.new('L',(w,h));draw=ImageDraw.Draw(protect)
        draw.polygon([(int(x*w/1376),int(y*h/768)) for x,y in [(650,215),(702,174),(759,161),(834,182),(875,223),(870,270),(794,309),(667,289)]],fill=255)
        eligible &= np.asarray(protect)==0
    small=Image.fromarray((eligible*255).astype('uint8')).resize((688,384),Image.Resampling.NEAREST)
    flood=Image.new('L',(690,386),255);flood.paste(small,(1,1));ImageDraw.floodfill(flood,(0,0),128)
    connected=Image.fromarray((np.asarray(flood)[1:-1,1:-1]==128).astype('uint8')*255).resize((w,h),Image.Resampling.NEAREST)
    connected=(np.asarray(connected)>0)&eligible
    yy,xx=np.ogrid[:h,:w]
    edge=np.minimum(np.minimum(xx,w-1-xx),np.minimum(yy,h-1-yy))
    alpha=np.clip((distance-2)/53,0,1)**2*np.clip(edge/24,0,1)
    rgba[:,:,3]=np.where(connected,np.rint(alpha*255),255).astype('uint8')
    return QImage(rgba.data,w,h,w*4,QImage.Format_RGBA8888).copy()
