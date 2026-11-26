"""Sizes persist in physical pixels; positions use logical desktop coordinates."""
BASE_WIDTH,BASE_HEIGHT=1920,1080

def initial_geometry(saved,screens):
    """Return an accessible 16:9 client rectangle, preserving larger saved sizes."""
    x=y=None; width=BASE_WIDTH
    try:
        sx,sy,sw,sh=map(int,saved)
        if sw>BASE_WIDTH and sh>BASE_HEIGHT:
            x,y,width=sx,sy,sw
    except (TypeError,ValueError): pass
    screen=screens[0]
    if x is not None:
        screen=next((r for r in screens if r[0]<=x+width/(2*(r[4] if len(r)>4 else 1))<r[0]+r[2] and r[1]<=y+width*9/(32*(r[4] if len(r)>4 else 1))<r[1]+r[3]),screen)
    left,top,available_width,available_height=screen[:4]
    dpr=screen[4] if len(screen)>4 else 1
    width=round(width/dpr)
    width=min(width,available_width,int(available_height*16/9)); height=round(width*9/16)
    if x is None: x=left+(available_width-width)//2; y=top+(available_height-height)//2
    x=max(left,min(x,left+available_width-width)); y=max(top,min(y,top+available_height-height))
    return x,y,width,height
