# Temple

**Juego serio de respiración, meditación y ejercicio que se maneja con la webcam.**

*Temple* es la serenidad para mantener la calma y también el valor para afrontar un reto. Son las dos mitades del juego, primero respirar y meditar con calma y después darlo todo en las flexiones. En inglés, *temple* es un templo, el sitio al que vuelves cada día.

Práctica 2 de **Interacción Persona-Máquina** (Grado en Ingeniería en Inteligencia Artificial, Universidad de Alicante, curso 2026-2027).

## Por qué lo hice

Meditar y entrenar cada día es algo que siempre he querido hacer y nunca me he atrevido a empezar. Quería un entrenador que me guiara paso a paso y que comprobara de verdad que lo hago bien, sin tocar el teclado y sin tener que fiarme de mí mismo.

## La historia

Temple es un ritual diario que va de la calma a la fuerza. Empieza respirando, sigue meditando, estira el cuerpo y termina con un reto de flexiones. Cada fase prepara la siguiente, igual que en una práctica de yoga o un entrenamiento de verdad.

La idea nació con la meditación. Pero ponerse a meditar sin más cuesta, porque la mente va a mil. Por eso añadí antes un ejercicio de respiración que la calma y la deja lista para meditar. Las flexiones cierran la sesión con un reto físico, la otra mitad del nombre.

La cámara hace de entrenador. No se limita a poner un temporizador, sino que comprueba que haces lo que pide y solo entonces avanza. En la respiración mira qué lado de la nariz tapas, y en las fases siguientes mirará que estés quieto o que bajes bien en cada flexión. El progreso se guarda día a día con lotos, rachas y niveles, para que volver mañana apetezca.

### De dónde sale la respiración

El **pranayama** es el conjunto de técnicas de control de la respiración del yoga. Una de las más conocidas es la **respiración alterna** o **Anuloma Viloma**, en la que el aire entra por un orificio de la nariz y sale por el otro, tapando cada lado con los dedos de una mano.

El juego sigue paso a paso el vídeo [Pranayama para principiantes (Anuloma Viloma)](https://www.youtube.com/watch?v=CacBxE8bXao), de Anabel Otero. En él la técnica se presenta como una forma de calmar la mente y ganar concentración, y se recomienda hacerla justo antes de meditar. Es exactamente el papel que tiene en Temple.

| Del vídeo | En el juego |
|---|---|
| Sentado, con la columna recta | Hay que verse de la cabeza al pecho |
| Antes de empezar, tapar el orificio derecho y soltar todo el aire por el izquierdo | Es el primer paso de cada sesión |
| Una vuelta es inhalar 4 por la izquierda, exhalar 8 por la derecha, inhalar 4 por la derecha y exhalar 8 por la izquierda | La cuenta sale en pantalla, un tiempo por segundo, con un golpecito suave en cada uno |
| Cinco vueltas | 5 por defecto, y se pueden elegir de 1 a 9 |
| Para quien ya tiene práctica, retener 16 tiempos con los dos lados tapados después de cada inhalación | Es la respiración avanzada, que se desbloquea con la práctica |
| La instructora se graba en espejo para que sea más fácil seguirla | La cámara también se ve en espejo |

La cámara no puede ver el aire. Lo que comprueba es qué orificio está tapado en cada momento, y el ritmo lo marca el juego. Temple es una ayuda para practicar, no una herramienta médica.

## Qué hace

Una sesión diaria guiada por la cámara, en este orden.

| Fase | Qué es | Estado |
|---|---|---|
| Respiración | Respiración alterna (Anuloma Viloma). El juego marca el ritmo y la cámara comprueba qué orificio de la nariz tapas | ✅ Hecha |
| Meditación | Unos minutos quieto y con la espalda recta, con más tiempo según avanzas | ⏳ Siguiente |
| Estiramientos | Estiramientos guiados para preparar el cuerpo | ⏳ |
| Flexiones | Reto que cuenta solo las repeticiones bien hechas | ⏳ Si da tiempo |

### La respiración

- **Tutorial** la primera vez, que enseña a tapar cada lado antes de empezar.
- **Sesión** de 1 a 9 vueltas (5 por defecto). Cada vuelta es inhalar 4 por la izquierda, exhalar 8 por la derecha, inhalar 4 por la derecha y exhalar 8 por la izquierda. La cuenta no avanza al cambiar de lado hasta que la cámara ve la mano bien puesta, así nadie va con prisa.
- **Lotos** de 0 a 3 según el tiempo que has tapado bien el lado que tocaba, **racha** de días seguidos y los días de la semana practicados.
- **Respiración avanzada**, que se desbloquea con 5 sesiones de 3 lotos y 5 vueltas o más. Añade 16 tiempos de retención con los dos lados tapados.
- **Con la mano, el teclado o el ratón.** De lejos, los menús se manejan señalando con el índice, y durante la respiración la palma abierta pausa. De cerca, las flechas mueven la selección entre los botones y Enter pulsa, o se hace clic con el ratón.

> Capturas pendientes. Se añadirán al cerrar la fase, con la pantalla de inicio, el tutorial, una sesión y el desbloqueo.

## Instalación

Funciona igual en Ubuntu y en macOS. Hace falta tener [Miniconda](https://www.anaconda.com/docs/getting-started/miniconda/install).

**1. Entorno** (solo la primera vez)

```bash
conda create -n IPM python=3.12
conda activate IPM
pip install mediapipe==0.10.21 opencv-contrib-python==4.11.0.86 numpy==1.26.4 pygame==2.6.1
```

**2. Modelos de MediaPipe** (solo la primera vez, no se suben a GitHub)

```bash
mkdir -p models
curl -L -o models/pose_landmarker_full.task https://storage.googleapis.com/mediapipe-models/pose_landmarker/pose_landmarker_full/float16/latest/pose_landmarker_full.task
curl -L -o models/hand_landmarker.task https://storage.googleapis.com/mediapipe-models/hand_landmarker/hand_landmarker/float16/latest/hand_landmarker.task
```

## Cómo jugar

Siempre desde la carpeta raíz del repositorio.

```bash
conda activate IPM
python main.py
```

Siéntate de forma que la cámara te vea de la cabeza al pecho. En macOS la primera vez pide permiso de cámara para la Terminal.

| Gesto o tecla | Qué hace |
|---|---|
| Señalar un botón con el índice 1,5 s | Lo pulsa. El botón se va rellenando mientras esperas |
| Señalar la mitad izquierda o derecha de la fila de vueltas | Quita o pone una vuelta |
| Palma abierta, lejos de la nariz, 0,8 s | Pausa la respiración |
| Clic con el ratón | Pulsa el botón |
| Flechas arriba y abajo, o Tab | Mover la selección entre los botones |
| Enter | Pulsar el botón seleccionado |
| Espacio | Empezar, pausar o seguir (o pulsar el seleccionado) |
| Flechas izquierda y derecha | Cambiar las vueltas en el inicio, o elegir Seguir o Salir en la pausa |
| M | Activar o apagar el sonido |
| Esc | Salir |

Opciones para probar, que no se guardan en el progreso.

```bash
python main.py --vueltas 2
python main.py --avanzada
```

El progreso se guarda en `datos/progreso.json`, que se queda en tu equipo y no se sube.

## Tests

```bash
python -m unittest discover tests
```

Prueban la lógica sin cámara ni ventana (guion de la respiración, progreso y desbloqueos, gesto de señalar e imán de los botones).

## Arquitectura

```
main.py                  arranque y opciones
temple/
  camara.py              cámara y detección en un hilo aparte
  vision.py              nariz (Pose) y mano (Hands), y qué orificio se tapa
  respiracion.py         guion de pasos del tutorial y la sesión, sin cámara
  puntero.py             cursor con el índice, imán, gesto de señalar y palma
  progreso.py            historial, racha, lotos y desbloqueos en JSON
  interfaz/
    app.py               pantallas de Pygame
    dibujo.py, estilo.py dibujo y colores
    sonido.py            sonidos generados con numpy
herramientas/            scripts de los experimentos
tests/
```

La cámara y los dos modelos van en un hilo aparte porque tardan unos 30 a 50 ms por fotograma, y en el mismo bucle que la interfaz las animaciones irían a saltos. La lógica (respiración, puntero, progreso) no depende de Pygame, así se puede probar sin ventana.

## Decisiones técnicas

| Decisión | Por qué |
|---|---|
| Respiración alterna antes de meditar, con detección | Prepara para meditar y es salud. Usa dos modelos de MediaPipe a la vez (Pose para la nariz y los hombros, Hands para los dedos). La cámara no ve el aire, así que el ritmo lo marca el juego |
| Detección por reglas, con distancias entre puntos | No hace falta entrenar ningún modelo. Las distancias se miden en anchos de hombros para que no importe lo lejos que estés |
| Lado derecho tapado si la punta del pulgar está a menos de 0,25 anchos de hombros de la nariz, e izquierdo si lo está la punta de cualquier otro dedo | En el experimento con `herramientas/explorar_manos.py`, con la mano doblada MediaPipe confundía qué dedo era cuál. Así vale para cualquier forma de tapar |
| El veredicto se suaviza en 8 fotogramas y aguanta 0,6 s si se pierde la mano | Delante de la cara el modelo pierde la mano a ratos |
| Interfaz en Pygame, una fase entera antes de empezar la siguiente | Pygame da una interfaz mucho más cuidada que las ventanas de OpenCV. Mejor una fase completa y pulida que todas a medias |
| Lotos, racha y desbloqueo de la avanzada | Gamificación con niveles que no sean demasiado fáciles |
| Vueltas de 1 a 9, pero solo las de 5 o más cuentan para desbloquear | Un día con prisa sirve para la racha, pero el reto no se abarata |
| Menús señalando con el índice y espera de 1,5 s | Se respira sentado y lejos del teclado. Se descartó el pellizco porque desde lejos MediaPipe confunde los dedos, y contar dedos porque hay que aprenderse los gestos |
| Solo cuenta el gesto de señalar (índice estirado y al menos dos dedos cerrados), y hay que soltar antes de volver a pulsar | Con la mano relajada se pulsaban botones solos |
| El gesto de señalar se mide con los puntos 3D de la mano | Al señalar hacia la cámara el índice se ve corto en la imagen aunque esté estirado |
| Imán corto, que solo resalta un botón si el cursor está encima o a menos de 28 px | Con un imán al botón más cercano, señalar un hueco pulsaba el botón de al lado |
| La imagen se pasa de BGR a RGB antes de MediaPipe y las marcas de tiempo son la hora real en ms | OpenCV guarda los colores en BGR y el modelo los espera en RGB. En modo vídeo MediaPipe necesita marcas de tiempo crecientes |
| Sonidos generados con numpy | No hace falta ningún archivo de audio, y si el equipo no tiene audio todo sigue funcionando |

## Tecnología

- [MediaPipe](https://ai.google.dev/edge/mediapipe) (Pose Landmarker y Hand Landmarker)
- OpenCV para la cámara
- Pygame para la interfaz
- Python 3.12 con Conda
- Fuentes Cormorant Garamond y Nunito, con licencia SIL Open Font License (en `assets/fuentes/`)

## Lo que aprendí y lo que haría distinto

- **Los dedos de MediaPipe no son fiables con la mano doblada.** Al principio quería distinguir pulgar y anular, y el modelo los confundía. Lo resolví midiendo solo si hay un dedo cualquiera pegado a la nariz.
- **Si no se ve la palma, no hay mano.** Muy cerca de la cámara solo salía el dedo y MediaPipe no detectaba la mano, así que el juego decía que tapaba mal. Ahora avisa con "No veo tu mano, aléjate un poco".
- **Manejar menús con la mano es más difícil de lo que parece.** Fueron cuatro intentos (cursor fino, imán largo, gesto de señalar e imán corto) antes de que no se pulsara nada sin querer. Ahora empezaría por el gesto y el soltar desde el principio.
- **La fuente también cuenta.** Cormorant tiene números de estilo antiguo que bajan de la línea, y la cuenta tapaba el texto de debajo. Se centra el número por su tinta real.

## Autores

- Rares Andrei Mocanu
- Nikolas Kaplan
