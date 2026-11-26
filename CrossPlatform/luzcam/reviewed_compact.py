"""Registered compact camera: native iris, electronic sensor and live/review LCD."""
import json
from functools import lru_cache
from .model import ROOT
from .reviewed_mirrorless import draw as draw_registered

@lru_cache(maxsize=1)
def geometry():
    return json.loads((ROOT/'CameraArt/compact-reviewed-geometry.json').read_text())

def draw(p,frame,plate,state,setting,review,photo):
    draw_registered(p,frame,plate,state,setting,review,photo,
                    registered_geometry=geometry(),electronic=True)
