# LuzCam en el navegador

Versión educativa en HTML, CSS y JavaScript nativo. Incluye tres modelos de cámara, controles manuales, fotómetro, recorrido explicativo de la luz, escena animada y carrete temporal de hasta 100 capturas.

Para ejecutarla localmente, inicia un servidor desde la raíz del proyecto:

```text
python -m http.server 8000
```

Abre `http://localhost:8000/Web/`. Para preparar una carpeta publicable independiente:

```text
python Tools/build-web.py --output build/web
```

El empaquetador incorpora los recursos necesarios para la aplicación web sin dependencias JavaScript externas. Consulta [la guía de compilación](../docs/BUILDING.md) y [privacidad](../docs/PRIVACY.md).
