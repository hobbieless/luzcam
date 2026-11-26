"""Shared three-blade curtains; unit coordinates run top-to-bottom on the sensor.

Each blade keeps its height while the three leaves progressively overlap/retract.
This is a slowed didactic kinematic model, not timing data for a specific camera.
"""
BLADE_COUNT = 3

def curtain_blades(progress, second=False):
    progress=max(0.,min(1.,progress))
    height=1/BLADE_COUNT
    blades=[]
    for index in range(BLADE_COUNT):
        top=(index+1)*progress/BLADE_COUNT-height if second else progress+index*(1-progress)/BLADE_COUNT
        bottom=min(1.,top+height)
        top=max(0.,top)
        if bottom>top+1e-9: blades.append((top,bottom,index))
    return blades
