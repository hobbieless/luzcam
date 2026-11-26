"""Platform-neutral implementation of Portable/contract-v1.json (no Qt imports)."""
from dataclasses import dataclass, replace
from copy import deepcopy
import json
import math
import sys
from pathlib import Path

if getattr(sys, 'frozen', False):
    executable = Path(sys.executable).resolve()
    ROOT = executable.parent.parent / 'Resources' / 'LuzCamData' if sys.platform == 'darwin' else executable.parent / 'resources'
else:
    ROOT = Path(__file__).resolve().parents[2]
LEGACY_CONTRACT = json.loads((ROOT / 'Portable/contract-v1.json').read_text(encoding='utf-8'))
RANGES=json.loads(Path(__file__).with_name('exposure-ranges.json').read_text())
CONTRACT=deepcopy(LEGACY_CONTRACT)
for name in ('fullShutterLabels','thirdShutterLabels','fullISOs','thirdISOs'): CONTRACT[name]=RANGES[name]
for camera in CONTRACT['cameras'][:2]:
    for name in ('fullApertures','thirdApertures'): camera[name]=RANGES[name]

@dataclass
class Setting:
    camera: int = 0
    a: int = 3
    s: int = 8
    i: int = 0
    light: int = 0
    thirds: bool = False
    scene_frame: int = 0
    legacy: bool = False

    @property
    def contract(self): return LEGACY_CONTRACT if self.legacy else CONTRACT
    @property
    def spec(self): return self.contract['cameras'][self.camera]
    @property
    def divisor(self): return 3 if self.thirds else 1
    @property
    def apertures(self): return self.spec['thirdApertures' if self.thirds else 'fullApertures']
    @property
    def shutters(self): return self.contract['thirdShutterLabels' if self.thirds else 'fullShutterLabels']
    @property
    def isos(self): return self.contract['thirdISOs' if self.thirds else 'fullISOs']
    @property
    def f(self): return self.apertures[self.a]
    @property
    def optical_f(self): return 2 ** ((self.spec['apertureBaseEV'] + self.a/self.divisor)/2)
    @property
    def shutter_ev(self): return self.s/self.divisor if self.legacy else RANGES['thirdShutterEV' if self.thirds else 'fullShutterEV'][self.s]
    @property
    def seconds(self): return 2 ** (-self.shutter_ev)
    @property
    def gain(self): return self.i/self.divisor
    @property
    def meter_third(self):
        return round((CONTRACT['lights'][self.light]['referenceEV']-self.spec['apertureBaseEV']+self.gain-self.a/self.divisor-self.shutter_ev)*3)
    @property
    def offset(self): return self.meter_third/3
    @property
    def meter_fraction(self): return (max(-6,min(6,self.meter_third))+6)/12
    @property
    def key(self):
        c = 0 if self.thirds and self.camera == 1 else self.camera
        return ('' if self.legacy else 'r2-')+f'{"t-" if self.thirds else ""}c{c}-l{self.light}-a{self.a}-s{self.s}-i{self.i}'+(f'-p{self.scene_frame}' if self.scene_frame else '')
    @property
    def image_path(self): return ROOT / ('CatalogueThirds' if self.thirds else 'Catalogue') / (self.key+'.jpg')
    @property
    def label(self): return f'f/{self.f:g} · {self.shutters[self.s]} · ISO {self.isos[self.i]}'
    def select_camera(self, camera):
        old = self.optical_f
        self.camera = camera
        self.a = min(range(len(self.apertures)), key=lambda a: abs(math.log2(2**((self.spec['apertureBaseEV']+a/self.divisor)/2)/old)))
    def set_thirds(self, enabled):
        if enabled == self.thirds: return
        previous_ev=self.shutter_ev
        factor = 3 if enabled else 1/3
        self.a,self.s,self.i = (math.floor(x*factor+.5) for x in (self.a,self.s,self.i))
        self.thirds = enabled
        self.a=min(self.a,len(self.apertures)-1)
        self.s=min(self.s,len(self.shutters)-1)
        if not self.legacy:
            speeds=RANGES['thirdShutterEV' if self.thirds else 'fullShutterEV']
            self.s=min(range(len(speeds)),key=lambda index:abs(speeds[index]-previous_ev))
        self.i=min(self.i,len(self.isos)-1)

def pose(phase, setting, preview=False):
    s=setting
    reflex=s.camera==0
    aperture=.85 if reflex and ((phase==0 and not preview) or phase>=6) else .85*2**(s.spec['apertureBaseEV']/2)/s.optical_f
    gap=min(1,max(0,s.seconds/(1/250)))
    if s.camera==1 and (phase==0 or phase>=6): front,rear=1,0
    elif phase<=2 or phase>=6: front,rear=0,0
    elif phase==3: front,rear=.35,max(0,.35-gap)
    elif phase==4: front,rear=(1,0) if gap>=1 else (.85,max(0,.85-gap))
    else: front,rear=1,1
    return dict(aperture=aperture,mirrorDown=1 if reflex and (phase<2 or phase>=6) else 0,
                front=1 if s.camera==2 else front,rear=0 if s.camera==2 else rear,
                leaf=.85 if s.camera==2 or phase in (0,3,4,6,7) else 0,
                sensorActive=(.55 if phase==3 else 1 if phase==4 else 0) if s.camera==2 else 0,
                illumination=(1,.6,.3)[s.light],gain=s.gain)

def interval(phase,s): return 1.2+4*math.sqrt(s.seconds) if phase==4 else 1.8

TITLES=('Preparar la cámara','Ajustar el diafragma','Preparar la exposición','Comienza la exposición','La luz se registra','Termina la exposición','Volver al reposo','Examinar la fotografía')
def title(phase,s):
    return {2:'Preparar el sensor',3:'Activar el registro',4:'El sensor registra',5:'Finalizar el registro'}.get(phase,TITLES[phase]) if s.camera==2 else TITLES[phase]

def explanation(phase,s):
    if phase==0: return 'La luz llega al espejo y sube al visor óptico.' if s.camera==0 else 'La luz llega al sensor y produce la imagen de la pantalla. Todavía no es una captura.'
    if phase==1: return f'Las palas forman la abertura f/{s.f:g}. El área de paso cambia con el cuadrado del diámetro.'
    if phase==2: return ('El espejo se levanta y deja libre el camino al sensor.','Se prepara el obturador mecánico. No hay espejo.','Se prepara el registro electrónico. Esta compacta no utiliza cortinillas.')[s.camera]
    if phase==3: return 'Empieza el registro electrónico.' if s.camera==2 else 'La primera cortinilla empieza a descubrir el sensor.'
    if phase==4: return f'Cada zona registra luz durante {s.shutters[s.s]}. La animación está ralentizada para explicarlo.'
    if phase==5: return 'Termina la exposición. ISO modifica la respuesta de salida; no añade luz.'
    if phase==6: return 'La cámara vuelve al reposo y recupera la vista de la escena.'
    return 'Estos ajustes quedaron guardados al disparar. Los controles no alteran esta fotografía.'

class Session:
    """Capture settings are frozen at shutter press; finishing twice never duplicates a shot."""
    history_limit=100
    def __init__(self):
        self.setting=Setting()
        self.shot=None
        self.phase=0
        self.history=[]
        self.recorded=False
    @property
    def busy(self): return 0<self.phase<7
    @property
    def observed(self): return self.shot if self.busy else self.setting
    def advance(self):
        if self.phase in (0,7):
            if len(self.history)>=self.history_limit:return
            self.shot=replace(self.setting); self.recorded=False; self.phase=1
        else: self.phase+=1
        if self.phase==7 and not self.recorded:
            self.history.append(replace(self.shot)); self.recorded=True
    def back(self): self.phase=max(0,self.phase-1)
    def reset(self): self.phase=0
