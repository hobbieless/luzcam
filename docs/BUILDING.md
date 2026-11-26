# Ejecutar y compilar

## Aplicación de escritorio

Windows y macOS comparten el código y la interfaz. Se recomienda Python 3.12 o 3.13.

- Windows: instalar `CrossPlatform/requirements-build.txt` en un entorno virtual y ejecutar `python CrossPlatform/main.py`.
- macOS Apple Silicon (macOS 12 o posterior): ejecutar `CrossPlatform/setup-mac.sh` y después `python CrossPlatform/main.py`.
- Para crear una compilación de escritorio, ejecutar `python CrossPlatform/build-desktop.py` desde la raíz del proyecto. Para el perfil compatible con macOS 12, usar `python CrossPlatform/build-desktop.py --macos-12-compatibility` en el Mac de destino.

Las compilaciones deben generarse y comprobarse en el sistema operativo de destino. No compartas entornos virtuales entre equipos.

## Aplicación web

La versión del navegador usa HTML, CSS y JavaScript. Desde la raíz del proyecto, iniciar un servidor local:

```text
python -m http.server 8000
```

Abrir `http://localhost:8000/Web/`. Para preparar la carpeta web publicable:

```text
python Tools/build-web.py --output build/web
```

Se requiere Python para ejecutar la herramienta de empaquetado; el simulador web no depende de bibliotecas JavaScript externas.

## Dependencias y avisos

Los perfiles de dependencias están en `CrossPlatform/requirements*.txt`. Los textos de licencia de Qt/PySide y otros componentes están en `docs/legal/`; los avisos para una compilación deben corresponder al perfil usado.
