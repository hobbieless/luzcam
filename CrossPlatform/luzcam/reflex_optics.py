"""Convex roof-pentaprism and floating mirror in a calibrated technical 3D view.

Three reflecting planes follow the reflex-prism construction in Greivenkamp,
OPTI 201/202, Mirror and Prism Systems, slide 14. Geometry is ideal; the common
camera projection is illustrative, not a measured commercial camera model.
"""
import math
from functools import lru_cache

def dot(a,b): return sum(x*y for x,y in zip(a,b))
def add(a,b,t=1): return tuple(x+t*y for x,y in zip(a,b))
def reflect(direction,normal): return add(direction,normal,-2*dot(direction,normal))
def cross(a,b): return (a[1]*b[2]-a[2]*b[1],a[2]*b[0]-a[0]*b[2],a[0]*b[1]-a[1]*b[0])

THETA=math.radians(67.5)
N=(math.cos(THETA),math.sin(THETA),0.)
K=.63213
ROOF_NORMALS=tuple(tuple((N[i]+sign*(i==2))/math.sqrt(2) for i in range(3)) for sign in (-1,1))
FRONT_NORMAL=(-math.cos(THETA-math.pi/4),-math.sin(THETA-math.pi/4),0.)
FRONT_LEVEL=-.4873
DEPTH=.41336
FRONT_CLIP=.44876
ENTRY_X=.8074
ENTRY_Z=-.184
ENTRY_Y=-.155

def planes():
    return [('entry',(0.,-1.,0.),-ENTRY_Y),('exit',(1.,0.,0.),1.),
            ('front-edge',(-1.,0.,0.),-FRONT_CLIP),
            ('roof-a',ROOF_NORMALS[0],K/math.sqrt(2)),
            ('roof-b',ROOF_NORMALS[1],K/math.sqrt(2)),
            ('front-reflector',FRONT_NORMAL,FRONT_LEVEL),
            ('side-near',(0.,0.,-1.),DEPTH),('side-far',(0.,0.,1.),DEPTH)]

def inside(point,tolerance=1e-9):
    return all(dot(normal,point)<=level+tolerance for _,normal,level in planes())

def trace(z=ENTRY_Z,x=ENTRY_X):
    point=(x,ENTRY_Y,z); direction=(0.,1.,0.); points=[point]; directions=[direction]
    for normal,level in [(ROOF_NORMALS[0],K/math.sqrt(2)),(ROOF_NORMALS[1],K/math.sqrt(2)),(FRONT_NORMAL,FRONT_LEVEL)]:
        distance=(level-dot(normal,point))/dot(normal,direction)
        if distance<=0: raise ValueError('Ray misses the ordered reflecting faces')
        point=add(point,direction,distance)
        if not inside(point): raise ValueError('Reflection is on an extension outside the physical face')
        points.append(point); direction=reflect(direction,normal); directions.append(direction)
    point=add(point,direction,(1-point[0])/direction[0])
    if not inside(point): raise ValueError('Exit misses the physical exit aperture')
    points.append(point)
    return points,directions

def section(z):
    """Intersect all real half-spaces, also when a cut eliminates a corner."""
    from itertools import combinations
    lines=[(normal,level-normal[2]*z) for _,normal,level in planes() if abs(normal[0])+abs(normal[1])>1e-9]
    vertices=[]
    for (a,da),(b,db) in combinations(lines,2):
        det=a[0]*b[1]-a[1]*b[0]
        if abs(det)<1e-9:continue
        point=((da*b[1]-a[1]*db)/det,(a[0]*db-da*b[0])/det,z)
        if inside(point) and not any(sum((x-y)**2 for x,y in zip(point,q))<1e-16 for q in vertices):vertices.append(point)
    if not vertices:return []
    center=tuple(sum(p[i] for p in vertices)/len(vertices) for i in range(3))
    return sorted(vertices,key=lambda p:math.atan2(p[1]-center[1],p[0]-center[0]))

# Calibrated technical projection of the illustrated section. Its three
# directions are measured in source pixels: the light axis, gate vertical and
# receding gate edge. This oblique drawing projection is intentionally not an
# orthographic reconstruction of a measured commercial camera. Reflection laws
# are evaluated in Euclidean 3D before projection, never from screen angles.
U=(132/192,0.,140/192)
V=(0.,-1.,20/192)
VIEW=cross(U,V)
SCALE=192.
WIDTH,HEIGHT=1671.,941.
AXIS_Y=508.
FOCUS_PIXEL_Y=337.
SENSOR_PIXEL_X=1048.
MIRROR_PIXEL_X=SENSOR_PIXEL_X-(AXIS_Y-FOCUS_PIXEL_Y)*132/192
_exit=trace()[0][-1]
ORIGIN_Y=251/HEIGHT-SCALE/HEIGHT*dot(V,_exit)
MIRROR_Y=(AXIS_Y/HEIGHT-ORIGIN_Y-SCALE/HEIGHT*V[2]*ENTRY_Z)/(SCALE/HEIGHT*V[1])
ORIGIN_X=MIRROR_PIXEL_X/WIDTH-SCALE/WIDTH*dot(U,(ENTRY_X,MIRROR_Y,ENTRY_Z))
FOCUS_Y=(FOCUS_PIXEL_Y/HEIGHT-ORIGIN_Y-SCALE/HEIGHT*V[2]*ENTRY_Z)/(SCALE/HEIGHT*V[1])
SENSOR_X=ENTRY_X+(SENSOR_PIXEL_X-MIRROR_PIXEL_X)/132

def project(point):
    return [ORIGIN_X+SCALE/WIDTH*dot(U,point),ORIGIN_Y+SCALE/HEIGHT*dot(V,point)]

@lru_cache(maxsize=1)
def surfaces():
    """Faces come from the same convex solid used for every ray intersection."""
    from itertools import combinations
    boundaries=planes(); vertices=[]
    for (_,a,da),(_,b,db),(_,c,dc) in combinations(boundaries,3):
        bc=cross(b,c);det=dot(a,bc)
        if abs(det)<1e-10:continue
        ca=cross(c,a);ab=cross(a,b)
        point=tuple((da*bc[i]+db*ca[i]+dc*ab[i])/det for i in range(3))
        if inside(point) and not any(sum((x-y)**2 for x,y in zip(point,q))<1e-16 for q in vertices):vertices.append(point)
    result=[]
    for name,normal,level in boundaries:
        points=[p for p in vertices if abs(dot(normal,p)-level)<1e-8]
        if len(points)<3:continue
        center=tuple(sum(p[i] for p in points)/len(points) for i in range(3))
        axis=cross(normal,(0.,0.,1.))
        if dot(axis,axis)<1e-9:axis=cross(normal,(1.,0.,0.))
        length=math.sqrt(dot(axis,axis));axis=tuple(v/length for v in axis);other=cross(normal,axis)
        points.sort(key=lambda p:math.atan2(dot(other,add(p,center,-1)),dot(axis,add(p,center,-1))))
        material='reflector' if name in ('roof-a','roof-b','front-reflector') else name if name in ('entry','exit') else 'glass'
        result.append(dict(name=name,vertices=points,points=[project(p) for p in points],material=material,depth=dot(VIEW,center),visible=dot(normal,VIEW)<0))
    return sorted(result,key=lambda f:f['depth'],reverse=True)

def faces():
    return [(f['points'],'#64929c' if f['material']=='reflector' else '#40676e') for f in surfaces()]

def mirror_center(): return (ENTRY_X,MIRROR_Y,ENTRY_Z)
def focus_point(): return project((ENTRY_X,FOCUS_Y,ENTRY_Z))
def ocular_point():
    exit=project(_exit)
    return [1074/WIDTH,exit[1]]

def sensor_vertices():
    return [(SENSOR_X,MIRROR_Y+y,ENTRY_Z+z) for y,z in ((.5,-.3),(.5,.3),(-.5,.3),(-.5,-.3))]

def mirror_vertices(down):
    angle=-(1-max(0,min(1,down)))*math.pi/4
    hinge=(ENTRY_X+.55,MIRROR_Y+.55,ENTRY_Z)
    result=[]
    for t,z in ((-.40,ENTRY_Z-.225),(-.40,ENTRY_Z+.225),(.55,ENTRY_Z+.225),(.55,ENTRY_Z-.225)):
        x=ENTRY_X+t-hinge[0]; y=MIRROR_Y+t-hinge[1]
        result.append((hinge[0]+x*math.cos(angle)-y*math.sin(angle),hinge[1]+x*math.sin(angle)+y*math.cos(angle),z))
    return result

MIRROR_THICKNESS=.035

def mirror_back_vertices(down):
    angle=-(1-max(0,min(1,down)))*math.pi/4
    normal=((math.cos(angle)+math.sin(angle))/math.sqrt(2),(math.sin(angle)-math.cos(angle))/math.sqrt(2),0.)
    return [add(vertex,normal,MIRROR_THICKNESS) for vertex in mirror_vertices(down)]

def mirror_intersection(down):
    angle=-(1-max(0,min(1,down)))*math.pi/4
    n0=(1/math.sqrt(2),-1/math.sqrt(2),0.)
    normal=(n0[0]*math.cos(angle)-n0[1]*math.sin(angle),n0[0]*math.sin(angle)+n0[1]*math.cos(angle),0.)
    if abs(normal[0])<1e-9: return None
    hinge=(ENTRY_X+.55,MIRROR_Y+.55,ENTRY_Z)
    x=hinge[0]-normal[1]*(MIRROR_Y-hinge[1])/normal[0]
    vertices=mirror_vertices(down)
    if not min(v[0] for v in vertices)-1e-9<=x<=max(v[0] for v in vertices)+1e-9: return None
    point=(x,MIRROR_Y,ENTRY_Z)
    return point,reflect((1.,0.,0.),normal)

def viewfinder_route():
    points,_=trace()
    return [project(p) for p in points]+[ocular_point()]

@lru_cache(maxsize=1)
def prism_footprint():
    """Exact convex projected outline, used as the visible camera cutout."""
    points=sorted(set(tuple(p) for surface in surfaces() for p in surface['points']))
    def turn(a,b,c):return (b[0]-a[0])*(c[1]-a[1])-(b[1]-a[1])*(c[0]-a[0])
    lower=[];upper=[]
    for point in points:
        while len(lower)>1 and turn(lower[-2],lower[-1],point)<=0:lower.pop()
        lower.append(point)
    for point in reversed(points):
        while len(upper)>1 and turn(upper[-2],upper[-1],point)<=0:upper.pop()
        upper.append(point)
    return tuple(lower[:-1]+upper[:-1])
