#!/usr/bin/env python3
"""Stage a small, self-contained LuzCam browser build from approved shared assets."""
from __future__ import annotations
import argparse
import hashlib
import json
from pathlib import Path
import shutil

ROOT = Path(__file__).resolve().parents[1]

def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path, default=ROOT / 'build' / 'web')
    args = parser.parse_args()
    output = args.output.resolve()
    if output == ROOT or ROOT not in output.parents:
        parser.error('output must be a directory inside this checkout and cannot be the repository root')
    if output.exists():
        parser.error(f'output already exists; choose a new path to preserve it: {output}')
    (output / 'assets' / 'cameras').mkdir(parents=True)
    (output / 'assets' / 'scene').mkdir(parents=True)
    (output / 'assets' / 'data').mkdir(parents=True)
    (output / 'assets' / 'fonts').mkdir(parents=True)
    shutil.copy2(ROOT / 'Web' / 'index.html', output / 'index.html')
    css = (ROOT / 'Web' / 'app.css').read_text(encoding='utf-8').replace('../CrossPlatform/luzcam/fonts/', 'assets/fonts/')
    (output / 'app.css').write_text(css, encoding='utf-8')
    js = (ROOT / 'Web' / 'app.js').read_text(encoding='utf-8')
    for old, new in (
        ('../Portable/', 'assets/data/'),
        ('../CrossPlatform/luzcam/', 'assets/data/'),
        ('../CameraArt/', 'assets/cameras/'),
        ('../Scene/', 'assets/scene/'),
    ):
        js = js.replace(old, new)
    (output / 'app.js').write_text(js, encoding='utf-8')
    html = (output / 'index.html').read_text(encoding='utf-8').replace('../CrossPlatform/luzcam/icons/luzcam.png', 'assets/icon.png').replace('../Scene/', 'assets/scene/')
    (output / 'index.html').write_text(html, encoding='utf-8')
    for relative in ('Portable/contract-v1.json', 'CrossPlatform/luzcam/exposure-ranges.json', 'CrossPlatform/luzcam/translations.json'):
        shutil.copy2(ROOT / relative, output / 'assets' / 'data' / Path(relative).name)
    for camera in ('reflex', 'mirrorless', 'compact'):
        for suffix in ('-reviewed.jpg', '-reviewed-geometry.json'):
            shutil.copy2(ROOT / 'CameraArt' / f'{camera}{suffix}', output / 'assets' / 'cameras' / f'{camera}{suffix}')
    for light in ('day', 'dusk', 'night'):
        for suffix in ('.png', '.mp4'):
            shutil.copy2(ROOT / 'Scene' / f'{light}{suffix}', output / 'assets' / 'scene' / f'{light}{suffix}')
    for name in ('scene.json', 'focus-motion.png', 'day-motion.png', 'dusk-motion.png', 'night-motion.png'):
        shutil.copy2(ROOT / 'Scene' / name, output / 'assets' / 'scene' / name)
    for font in ('NotoSans.ttf', 'NotoSansMono.ttf', 'notosans-OFL.txt', 'notosansmono-OFL.txt'):
        shutil.copy2(ROOT / 'CrossPlatform' / 'luzcam' / 'fonts' / font, output / 'assets' / 'fonts' / font)
    shutil.copy2(ROOT / 'CrossPlatform' / 'luzcam' / 'icons' / 'luzcam.png', output / 'assets' / 'icon.png')
    shutil.copy2(ROOT / 'Web' / 'manifest.webmanifest', output / 'manifest.webmanifest')
    html_path=output/'index.html'
    html=html_path.read_text(encoding='utf-8').replace('<html lang="es">','<html lang="es" data-offline="true">')
    html=html.replace('<link rel="icon" href="assets/icon.png">','<link rel="icon" href="assets/icon.png">\n  <link rel="manifest" href="manifest.webmanifest">')
    html_path.write_text(html,encoding='utf-8')
    fingerprint=hashlib.sha256()
    for path in sorted(p for p in output.rglob('*') if p.is_file() and p.name not in {'build-report.json','sw.js'}):
        fingerprint.update(path.relative_to(output).as_posix().encode('utf-8')+b'\0')
        fingerprint.update(path.read_bytes())
    worker=(ROOT/'Web'/'sw.js').read_text(encoding='utf-8').replace('luzcam-web-development',f"luzcam-web-{fingerprint.hexdigest()[:16]}")
    (output/'sw.js').write_text(worker,encoding='utf-8')
    report = {
        'product': 'LuzCam Web', 'source': 'shared project resources',
        'files': sum(1 for p in output.rglob('*') if p.is_file()),
        'bytes': sum(p.stat().st_size for p in output.rglob('*') if p.is_file()),
        'offline': True, 'offlineStrategy': 'The app shell is cached at install; camera, scene and motion assets are cached as they are selected or used. Unvisited assets need an initial connection.',
        'included': ['HTML5', 'CSS', 'JavaScript', 'approved cameras', 'three scene loops', 'on-demand shutter motion atlases', 'shared JSON', 'OFL font notices'],
        'excluded': ['Catalogue', 'CatalogueThirds', 'Design', 'Sources', 'Qt', 'Python', 'NumPy', 'Pillow', 'build history'],
    }
    (output / 'build-report.json').write_text(json.dumps(report, indent=2, ensure_ascii=False) + '\n', encoding='utf-8')
    print(f"Prepared {report['files']} files ({report['bytes'] / 1024 / 1024:.1f} MiB) at {output}")
    return 0

if __name__ == '__main__':
    raise SystemExit(main())
