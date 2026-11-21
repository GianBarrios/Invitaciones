# Migraciones: videos verticales "Un año de migración"

Genera reels 9:16 (1080×1920, 30 fps, ~42 s), un ave por video, con este estilo: mapa oscuro,
enjambre de aves simuladas con estela, ruta resaltada de un ejemplar, dial de meses con kilómetros
y capítulos por temporada, todo en español.

## Uso

```bash
pip install matplotlib numpy pillow      # también hace falta ffmpeg
python3 generar.py                       # todas las aves de aves.py
python3 generar.py colibri               # solo una
python3 generar.py charran --preview     # 4 fotogramas PNG de prueba en videos/.frames_charran
```

Los MP4 quedan en `videos/`. Llevan una pista de audio en silencio: agrega la música en CapCut,
Instagram o Facebook al publicar.

## Añadir un ave

Copia un bloque en `aves.py` y ajusta `mapa`, `ida`, `vuelta`, las zonas, `lugares`, `agenda` y `capitulos`
(la cabecera del archivo explica cada campo). Usa `--preview` para revisar el encuadre antes de renderizar.

Las aves son una simulación ilustrativa: las rutas y fechas son aproximadas, no datos de rastreo reales.
Mapa: Natural Earth vía world-atlas (ver LICENSE-world-atlas).
