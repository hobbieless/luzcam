"""Presentation matte preserves image registration and foreground RGB."""
import sys
from pathlib import Path
import numpy as np
from PySide6.QtGui import QImage
root=Path(__file__).resolve().parents[1];sys.path.insert(0,str(root/'CrossPlatform'))
from luzcam.camera_surface import load_plate
from reference_camera_surface import load_reference_plate
for name in ('reflex','mirrorless','compact'):
    path=root/'CameraArt'/f'{name}-reviewed.jpg'
    source=QImage(str(path)).convertToFormat(QImage.Format_RGBA8888);result=load_plate(str(path))
    assert source.size()==result.size()
    reference=load_reference_plate(str(path))
    assert result==reference,'Chunked preparation must exactly reproduce full-frame reference'
    assert result.colorSpace()==reference.colorSpace() and result.devicePixelRatio()==reference.devicePixelRatio()
    def pixels(im):return np.frombuffer(im.constBits(),np.uint8).reshape(im.height(),im.bytesPerLine())[:,:im.width()*4].reshape(im.height(),im.width(),4)
    a,b=pixels(source),pixels(result)
    assert np.array_equal(a[:,:,:3],b[:,:,:3]),'Foreground RGB must never be repainted'
    assert b[0,0,3]==0 and b[-1,-1,3]==0
    assert np.mean(b[:,:,3]==0)>.1
    assert np.all(b[:,:,3][a[:,:,:3].max(axis=2)<100]==255),'Dark camera/shadows must stay opaque'
print('PASS: three plate dimensions/RGB unchanged, exterior transparent, dark camera geometry preserved')
