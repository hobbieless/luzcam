"""Development shared CPU renderer, connected to the desktop photo service.

Uses the approved v5 workshop and its rendered motion/shadows. Depth and ISO
remain educational approximations. Motion is sampled at 30 Hz with the source
1/60 s blur; very fast shutters cannot recover detail absent from these frames.
"""
from collections import OrderedDict
from dataclasses import replace
import json
from pathlib import Path
import numpy as np
from PIL import Image, ImageDraw, ImageFilter
from .model import ROOT

REVISION='temporary-photo-lighting3d-v5-focused-motion'

class TemporaryPhoto:
    def __init__(self,root=ROOT,cache_mib=16):
        self.root=Path(root)
        self.limit=max(0,int(cache_mib*1024**2))
        self.cache=OrderedDict(); self.cache_bytes=0
        self.width,self.height=960,540
        self.scene=json.loads((self.root/'Scene/scene.json').read_text())
        subject=Image.new('L',(960,540)); draw=ImageDraw.Draw(subject)
        draw.polygon([(285,195),(356,195),(397,397),(274,397)],fill=255)
        self.subject=np.asarray(subject.filter(ImageFilter.GaussianBlur(3)),dtype=np.float32)[...,None]/255
        table=Image.new('L',(960,540)); ImageDraw.Draw(table).rectangle((0,380,960,540),fill=255)
        self.table=np.asarray(table.filter(ImageFilter.GaussianBlur(16)),dtype=np.float32)[...,None]/255
        state=42; noise=bytearray(960*540)
        for i in range(len(noise)):
            state=(state*6364136223846793005+1)&((1<<64)-1); noise[i]=(state>>33)&255
        self.noise=np.frombuffer(noise,dtype=np.uint8).reshape(540,960,1)[::-1].astype(np.float32)/255

    @staticmethod
    def smooth(a,b,value):
        t=np.clip((value-a)/(b-a),0,1); return t*t*(3-2*t)

    @staticmethod
    def linear(rgb): return np.where(rgb<=.04045,rgb/12.92,((rgb+.055)/1.055)**2.4)

    @staticmethod
    def encoded(rgb):
        rgb=np.clip(rgb,0,1)
        return np.where(rgb<=.0031308,rgb*12.92,1.055*rgb**(1/2.4)-.055)

    def _prepared(self,setting):
        # Reflex and mirrorless share their photographic response, as before.
        key=(setting.light,setting.camera==2,setting.optical_f,setting.seconds,setting.scene_frame)
        if key in self.cache:
            self.cache.move_to_end(key); return self.cache[key]
        name=('day','dusk','night')[setting.light]
        source=self.root/'Scene'/f'{name}.png'
        with Image.open(source) as image:
            base=image.convert('RGB').resize((960,540),Image.Resampling.LANCZOS)
        # Integrate exactly the same rendered poses, including their light and
        # shadow changes, in linear light. Only the moving rectangle is decoded.
        box=self.scene['lights'][name]['box']; x0,y0,x1,y1=box; height=y1-y0
        samples=45 if setting.seconds>=self.scene['period'] else 17 if setting.seconds>=1/60 else 3
        total=np.zeros((height,x1-x0,3),np.float32)
        reference=base.crop(box)
        focus_spec=self.scene['focusMotion'];fx0,fy0,fx1,fy1=focus_spec['box'];fh=fy1-fy0
        moving_focus=np.zeros((fh,fx1-fx0),np.uint8)
        with Image.open(self.root/'Scene'/f'{name}-motion.png') as atlas, Image.open(self.root/'Scene'/focus_spec['file']) as focus_atlas:
            for i in range(samples):
                t=setting.scene_frame/self.scene['fps']+(i+.5)/samples*setting.seconds
                phase=int(t*self.scene['fps']+.5)%self.scene['frames']
                moving_focus |= np.asarray(focus_atlas.crop((0,phase*fh,fx1-fx0,(phase+1)*fh)))>0
                delta=atlas.crop((0,phase*height,x1-x0,(phase+1)*height))
                frame=reference.copy(); frame.paste(delta,mask=delta.getchannel('A'))
                patch=np.asarray(frame,dtype=np.float32)/255
                total+=self.linear(patch)
        base.paste(Image.fromarray(np.rint(self.encoded(total/samples)*255).astype(np.uint8)),(x0,y0))
        depth=max(0,9/setting.optical_f-.55)*(.35 if setting.camera==2 else 1)
        distant=np.asarray(base.filter(ImageFilter.GaussianBlur(depth)),dtype=np.float32)/255
        near=np.asarray(base.filter(ImageFilter.GaussianBlur(depth*.4)),dtype=np.float32)/255
        original=np.asarray(base,dtype=np.float32)/255
        # The old static body polygon excluded the swinging metal arm, so
        # changing aperture incorrectly defocused part of the focused subject.
        # Use the exact registered authoring alpha for every integrated phase.
        focus=Image.new('L',(960,540));focus.paste(Image.fromarray(moving_focus*255),(fx0,fy0))
        core=np.asarray(focus,dtype=np.float32)[...,None]/255
        feather=np.asarray(focus.filter(ImageFilter.MaxFilter(5)).filter(ImageFilter.GaussianBlur(1)),dtype=np.float32)[...,None]/255
        subject=np.maximum(self.subject,np.maximum(core,feather))
        focused=original*subject+(near*self.table+distant*(1-self.table))*(1-subject)
        prepared=np.clip(np.rint(focused*255),0,255).astype(np.uint8)
        prepared.flags.writeable=False
        if prepared.nbytes<=self.limit:
            while self.cache and self.cache_bytes+prepared.nbytes>self.limit:
                _,old=self.cache.popitem(last=False); self.cache_bytes-=old.nbytes
            self.cache[key]=prepared; self.cache_bytes+=prepared.nbytes
        return prepared

    def render(self,setting):
        # Return an independent image; future settings/cache changes cannot alter it.
        setting=replace(setting)
        prepared=self._prepared(setting).astype(np.float32)/255
        exposed=self.encoded(self.linear(prepared)*(2**setting.offset))
        alpha=setting.gain*.008*(1.3 if setting.camera==2 else 1)
        pixels=np.clip(np.rint((exposed*(1-alpha)+self.noise*alpha)*255),0,255).astype(np.uint8)
        return Image.fromarray(pixels)
