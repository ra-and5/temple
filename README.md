# Juego serio de meditación y ejercicio con visión por computador

Práctica 2 de **Interacción Persona-Máquina** (Grado en Ingeniería en Inteligencia Artificial, Universidad de Alicante, curso 2026-2027).

Un entrenador diario que se maneja con la webcam. Primero te guía para **meditar** unos minutos (la cámara comprueba que estás quieto y con la espalda recta), luego hace **estiramientos** guiados y termina con un **reto de flexiones** que cuenta solo las repeticiones bien hechas. El progreso se guarda día a día para crear el hábito.

## Estado

🚧 En desarrollo. Entrega el 26/11/2026.

| Fase | Qué es | Estado |
|---|---|---|
| 0 | Entender el juego base del profesor | ✅ |
| 1 | Script de pruebas que dibuja el esqueleto y enseña los números de los puntos clave | 🟡 Esqueleto hecho, faltan los números |
| 2 | Medir espalda recta y quietud con datos reales | ⏳ |
| 3 | Temporizador de meditación con sus estados (preparado, meditando, pausa, terminado) | ⏳ |
| 4 | Interfaz en Pygame aplicando las heurísticas de Nielsen y las pautas HAX | ⏳ |
| 5 | Progresión semanal y guardado del progreso | ⏳ |

## Cómo probarlo ahora

Funciona igual en Ubuntu y en macOS. Hace falta tener [Miniconda](https://www.anaconda.com/docs/getting-started/miniconda/install).

**1. Entorno** (solo la primera vez)

```bash
conda create -n IPM python=3.12
conda activate IPM
pip install mediapipe==0.10.21 opencv-contrib-python==4.11.0.86 numpy==1.26.4
```

Si ya tienes el entorno `IPM` del repositorio base del profesor, sirve tal cual.

**2. Modelo de pose** (solo la primera vez, no se sube a GitHub)

```bash
mkdir -p models
curl -L -o models/pose_landmarker_full.task https://storage.googleapis.com/mediapipe-models/pose_landmarker/pose_landmarker_full/float16/latest/pose_landmarker_full.task
```

**3. Ejecutar** siempre desde la carpeta raíz del repositorio, porque la ruta del modelo se cuenta desde ahí

```bash
conda activate IPM
python herramientas/explorar_pose.py
```

Se abre la cámara en modo espejo con el esqueleto dibujado. Se sale con ESC o cerrando la ventana. En macOS la primera vez pide permiso de cámara para la Terminal.

## Decisiones técnicas

| Decisión | Por qué |
|---|---|
| La imagen se pasa de BGR a RGB antes de dársela a MediaPipe | OpenCV guarda los colores en orden BGR y el modelo los espera en RGB. El juego base no hace la conversión |
| El instante de cada fotograma se toma de la hora real en milisegundos | En modo vídeo MediaPipe necesita marcas de tiempo crecientes que se correspondan con el tiempo de verdad |
| La ventana se cierra con ESC o con la X | En el juego base solo funcionaba ESC y la X dejaba el programa colgado. Salir por la vía habitual es la heurística de control y libertad del usuario |

## Tecnología

- [MediaPipe](https://ai.google.dev/edge/mediapipe) (Pose Landmarker) para detectar el cuerpo
- OpenCV para la cámara
- Pygame para la interfaz
- Python 3.12 con Conda

## Autores

- Rares Andrei Mocanu
- Nikolas Kaplan
