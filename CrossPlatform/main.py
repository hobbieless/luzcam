"""Desktop entry point, retaining diagnostics when launched without a console."""
import sys
import io
from pathlib import Path

class BoundedDiagnostics(io.TextIOBase):
    """Keep console-free diagnostics local and bounded during error loops."""
    def __init__(self, path, limit=1024*1024):
        self._stream=Path(path).open('wb')
        self._remaining=limit
        self._truncated=False
    @property
    def encoding(self): return 'utf-8'
    def writable(self): return True
    def write(self, value):
        if self.closed: raise ValueError('write to closed diagnostics')
        marker=b'\n[LuzCam: diagnostic size limit reached]\n'
        data=value.encode('utf-8',errors='replace')
        if not self._truncated:
            room=max(0,self._remaining-len(marker))
            part=data[:room].decode('utf-8',errors='ignore').encode('utf-8')
            self._stream.write(part);self._remaining-=len(part)
            if len(data)>room:
                self._stream.write(marker);self._remaining-=len(marker)
                self._truncated=True
            self._stream.flush()
        return len(value)
    def flush(self):
        if not self._stream.closed:self._stream.flush()
    def close(self):
        if not self.closed:
            super().close();self._stream.close()

def prepare_diagnostics():
    if sys.stderr is not None and sys.stdout is not None: return
    import os
    folder=Path(os.environ.get('LOCALAPPDATA',str(Path.home())))/'LuzCam'/'Logs'
    try:
        folder.mkdir(parents=True,exist_ok=True)
        log=BoundedDiagnostics(folder/'application.log')
    except OSError:
        # Diagnostics must not prevent startup if their folder is unwritable.
        log=open(os.devnull,'w',encoding='utf-8')
    if sys.stderr is None: sys.stderr=log
    if sys.stdout is None: sys.stdout=log

if __name__ == '__main__':
    prepare_diagnostics()
    import os
    if os.environ.get('LUZCAM_TRACE_STARTUP'):
        import faulthandler
        trace = open(os.environ['LUZCAM_TRACE_STARTUP'], 'w', buffering=1)
        faulthandler.enable(file=trace)
        faulthandler.dump_traceback_later(20, repeat=True, file=trace)
    from luzcam.ui import main
    main()
