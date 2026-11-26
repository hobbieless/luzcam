"""Process memory using OS facilities only; no resident monitor or extra package."""
import os,platform,subprocess

def memory():
    if platform.system()=='Windows':
        import ctypes
        from ctypes import wintypes
        class Counters(ctypes.Structure):
            _fields_=[('cb',wintypes.DWORD),('PageFaultCount',wintypes.DWORD)]+[(name,ctypes.c_size_t) for name in
                ('PeakWorkingSetSize','WorkingSetSize','QuotaPeakPagedPoolUsage','QuotaPagedPoolUsage',
                 'QuotaPeakNonPagedPoolUsage','QuotaNonPagedPoolUsage','PagefileUsage','PeakPagefileUsage','PrivateUsage')]
        kernel=ctypes.WinDLL('kernel32',use_last_error=True);psapi=ctypes.WinDLL('psapi',use_last_error=True)
        kernel.GetCurrentProcess.restype=wintypes.HANDLE
        psapi.GetProcessMemoryInfo.argtypes=[wintypes.HANDLE,ctypes.POINTER(Counters),wintypes.DWORD]
        values=Counters();values.cb=ctypes.sizeof(values)
        if not psapi.GetProcessMemoryInfo(kernel.GetCurrentProcess(),ctypes.byref(values),values.cb):raise ctypes.WinError(ctypes.get_last_error())
        return {'rssBytes':values.WorkingSetSize,'peakRssBytes':values.PeakWorkingSetSize,'privateBytes':values.PrivateUsage}
    import resource
    rss=int(subprocess.check_output(['ps','-o','rss=','-p',str(os.getpid())],text=True))*1024
    peak=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss
    return {'rssBytes':rss,'peakRssBytes':int(peak if platform.system()=='Darwin' else peak*1024)}
