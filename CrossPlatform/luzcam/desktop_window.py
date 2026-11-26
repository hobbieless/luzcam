"""Native window chrome integration; shared UI remains platform-neutral."""
import sys

def _integrate_windows_chrome(window):
    import ctypes
    from ctypes import wintypes
    from PySide6.QtGui import QGuiApplication
    if QGuiApplication.platformName()!='windows':return False
    # Caption colours are a public Windows 11 API. Keep native controls,
    # resizing and snapping; older systems retain their standard decoration.
    if sys.getwindowsversion().build<22000:return False
    class HighContrast(ctypes.Structure):
        _fields_=[('cbSize',wintypes.UINT),('dwFlags',wintypes.DWORD),('scheme',wintypes.LPWSTR)]
    hc=HighContrast();hc.cbSize=ctypes.sizeof(hc)
    if not ctypes.windll.user32.SystemParametersInfoW(0x42,hc.cbSize,ctypes.byref(hc),0) or hc.dwFlags&1:return False
    dwm=ctypes.WinDLL('dwmapi')
    dwm.DwmSetWindowAttribute.argtypes=[wintypes.HWND,wintypes.DWORD,ctypes.c_void_p,wintypes.DWORD]
    dwm.DwmSetWindowAttribute.restype=ctypes.c_long
    results=[]
    for attribute,rgb in ((35,(222,222,212)),(36,(35,35,32)),(34,(222,222,212))):
        color=wintypes.DWORD(rgb[0]|rgb[1]<<8|rgb[2]<<16)
        results.append(dwm.DwmSetWindowAttribute(int(window.winId()),attribute,ctypes.byref(color),ctypes.sizeof(color))==0)
    window.setProperty('nativeChromeIntegrated',all(results))
    return all(results)

def integrate_window_chrome(window):
    if sys.platform=='win32':return _integrate_windows_chrome(window)
    if sys.platform!='darwin': return False
    from PySide6.QtGui import QGuiApplication
    if QGuiApplication.platformName()!='cocoa': return False
    import ctypes
    from ctypes.util import find_library
    objc=ctypes.CDLL(find_library('objc'))
    objc.sel_registerName.argtypes=[ctypes.c_char_p]; objc.sel_registerName.restype=ctypes.c_void_p
    objc.objc_getClass.argtypes=[ctypes.c_char_p]; objc.objc_getClass.restype=ctypes.c_void_p
    def send(result,argtypes,obj,name,*args):
        function=ctypes.CFUNCTYPE(result,ctypes.c_void_p,ctypes.c_void_p,*argtypes)(('objc_msgSend',objc))
        return function(obj,objc.sel_registerName(name.encode()),*args)
    native=send(ctypes.c_void_p,[],int(window.winId()),'window')
    if not native: return False
    class NativeSize(ctypes.Structure):
        _fields_=[('width',ctypes.c_double),('height',ctypes.c_double)]
    send(None,[NativeSize],native,'setContentAspectRatio:',NativeSize(16.,9.))
    mask=send(ctypes.c_ulong,[],native,'styleMask')
    send(None,[ctypes.c_ulong],native,'setStyleMask:',(mask|1|2|4|8)&~(1<<15))
    send(None,[ctypes.c_long],native,'setTitleVisibility:',1)
    send(None,[ctypes.c_bool],native,'setTitlebarAppearsTransparent:',True)
    send(None,[ctypes.c_bool],native,'setMovableByWindowBackground:',True)
    send(None,[ctypes.c_bool],native,'setMovable:',True)
    for kind in (0,1,2):
        control=send(ctypes.c_void_p,[ctypes.c_ulong],native,'standardWindowButton:',kind)
        if control:
            send(None,[ctypes.c_bool],control,'setHidden:',False)
            send(None,[ctypes.c_bool],control,'setEnabled:',True)
    color_class=objc.objc_getClass(b'NSColor')
    color=send(ctypes.c_void_p,[ctypes.c_double]*4,color_class,'colorWithSRGBRed:green:blue:alpha:',222/255,222/255,212/255,1.)
    send(None,[ctypes.c_void_p],native,'setBackgroundColor:',color)
    integrated=not bool(send(ctypes.c_ulong,[],native,'styleMask')&(1<<15)) and bool(send(ctypes.c_bool,[],native,'titlebarAppearsTransparent')) and send(ctypes.c_long,[],native,'titleVisibility')==1
    controls=[]
    for kind in (0,1,2):
        control=send(ctypes.c_void_p,[ctypes.c_ulong],native,'standardWindowButton:',kind)
        controls.append(bool(control) and not send(ctypes.c_bool,[],control,'isHidden') and send(ctypes.c_bool,[],control,'isEnabled'))
    window.setProperty('nativeWindowControlsVisible',all(controls))
    window.setProperty('nativeWindowMovable',bool(send(ctypes.c_bool,[],native,'isMovable')))
    window.setProperty('nativeChromeIntegrated',integrated and all(controls))
    return integrated and all(controls)
