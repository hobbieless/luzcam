"""Diagnostic output must stay bounded and preserve valid UTF-8."""
import sys,tempfile
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'CrossPlatform'))
from main import BoundedDiagnostics
with tempfile.TemporaryDirectory() as folder:
    path=Path(folder)/'application.log'
    with BoundedDiagnostics(path) as stream:
        assert stream.write('startup\n')==8
        for _ in range(1000):stream.write(chr(225)*2048)
    data=path.read_bytes()
    assert len(data)<=1024*1024
    text=data.decode('utf-8')
    assert text.startswith('startup\n')
    assert text.count('[LuzCam: diagnostic size limit reached]')==1
    with BoundedDiagnostics(path) as stream:stream.write('new session')
    assert path.read_text(encoding='utf-8')=='new session'
print('PASS: bounded UTF-8 diagnostics and fresh-session reset')
