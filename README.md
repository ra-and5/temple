# Temple

[![Tests](https://github.com/ra-and5/temple/actions/workflows/tests.yml/badge.svg)](https://github.com/ra-and5/temple/actions/workflows/tests.yml)

**Juego serio de respiración, meditación y estiramientos que se maneja con la webcam.**

*Temple* es la serenidad para mantener la calma y también el valor para afrontar un reto. En inglés es un templo, el sitio al que vuelves cada día.

Práctica 2 de **Interacción Persona-Máquina** (Grado en Ingeniería en Inteligencia Artificial, Universidad de Alicante, curso 2026-2027).

## Por qué lo hicimos

Meditar y cuidar el cuerpo cada día es algo que siempre hemos querido hacer y nunca nos hemos atrevido a empezar. Queríamos un entrenador que guiara paso a paso y que comprobara de verdad que lo hacemos bien, sin tocar el teclado y sin tener que fiarnos de nosotros mismos.

## Qué hace

Un ritual diario guiado por la cámara, que va de la calma al cuerpo. La cámara no se limita a poner un temporizador. Comprueba que haces lo que pide y solo entonces avanza.

| Fase | Qué comprueba la cámara | Estado |
|---|---|---|
| **Respiración** | Respiración alterna (Anuloma Viloma). El juego marca el ritmo y la cámara mira qué orificio de la nariz tapas | ✅ |
| **Meditación** | Que estés quieto, con la espalda recta y los ojos cerrados | ✅ |
| **Estiramientos** | Siete posturas de cuello, hombros y brazos, sentado | ✅ |
| Flexiones | Un reto que cuente solo las repeticiones bien hechas | Fuera de esta entrega |

Las tres fases tienen **tutorial** la primera vez, **lotos** de 0 a 3 según el tiempo que lo haces bien, **racha** de días seguidos y los días de la semana practicados.

### Respiración

Sigue el vídeo [Pranayama para principiantes (Anuloma Viloma)](https://www.youtube.com/watch?v=CacBxE8bXao), de Anabel Otero, que la recomienda justo antes de meditar. Cada vuelta es inhalar 4 tiempos por la izquierda, exhalar 8 por la derecha, inhalar 4 por la derecha y exhalar 8 por la izquierda. Se eligen de 1 a 9 vueltas (5 por defecto). Con 5 sesiones de 3 lotos se desbloquea la **avanzada**, que retiene 16 tiempos con los dos lados tapados.

La cámara no ve el aire. Comprueba qué lado tapas, y el ritmo lo marca el juego. Temple es una ayuda para practicar, no una herramienta médica.

### Meditación

Al empezar mide tu postura recta y arranca cuando cierras los ojos. Si algo falla 3 s seguidos suenan dos golpes suaves, porque con los ojos cerrados no se ve la pantalla, y cada minuto una campana. El tiempo sube por una **escalera** de 5, 8, 12, 17, 23, 30 y 40 minutos, y después **sin límite**. Si una semana meditas 5 días con tu tiempo más alto y al menos 2 lotos, la siguiente se desbloquea el de arriba.

### Estiramientos

Siete posturas sentado, de 20 s cada una. La cuenta solo avanza mientras estás en la postura, y abajo te dice qué te falta ("Pon la mano sobre la cabeza", "Sujeta el codo con la otra mano"…). Sobre la cámara, una raya discontinua marca hasta dónde llegar.

| Postura | Cómo la reconoce la cámara |
|---|---|
| Cabeza a la derecha y a la izquierda | Las orejas inclinadas 20° respecto a los hombros, con la mano de ese lado sobre la cabeza |
| Brazos arriba | Los dos codos por encima de la nariz |
| Brazo derecho e izquierdo cruzados | La muñeca pasa al otro lado del pecho y la otra mano sujeta el codo |
| Tríceps derecho e izquierdo | El codo por encima de la cabeza, el brazo doblado con la mano a la espalda y la otra mano sujetando el codo |

> Capturas pendientes. Se añadirán con el vídeo.

## Instalación

Funciona en **macOS** (chip de Apple o Intel, macOS 13 o más nuevo) y en **Ubuntu**. Hace falta una webcam e internet para instalar.

```bash
git clone https://github.com/ra-and5/temple.git
cd temple
bash instalar.sh
```

El script lo hace todo y se puede repetir sin miedo.

1. Busca Conda y, si no está, instala Miniconda en `~/miniconda3` (pregunta antes).
2. Crea el entorno `temple` con Python 3.12, porque MediaPipe 0.10.21 no funciona con versiones más nuevas.
3. Instala las librerías de `requirements.txt`, con las versiones fijadas.
4. Descarga los tres modelos de MediaPipe en `models/` y comprueba que son los mismos con los que probamos el juego.
5. Pasa todos los tests para confirmar que funciona.

Tarda unos 5 minutos. Para jugar.

```bash
bash jugar.sh
```

En macOS, la primera vez pide permiso para usar la cámara desde la Terminal. Si no sale la imagen, se activa en Ajustes del Sistema → Privacidad y seguridad → Cámara, y se vuelve a abrir.

Para quitarlo todo.

```bash
bash desinstalar.sh
```

Borra el entorno y los modelos, y pregunta antes de borrar tu progreso. Si Miniconda la instaló Temple, también pregunta si quitarla. Después ya se puede borrar la carpeta.

## Tu primera sesión

Unos 20 minutos. Para que no se haga largo, arráncalo con la meditación y los estiramientos acortados.

```bash
bash jugar.sh --segundos 5 --minutos 1
```

1. **Colócate.** Sentado, a medio metro de la cámara y con luz de frente, de forma que se te vea de la cabeza al pecho y los codos.
2. **Respiración.** Señala con el índice, apuntando a la pantalla, el botón "Aprender a respirar" y espera a que se rellene. El tutorial enseña a tapar cada lado. Después haz una sesión.
3. **Meditación.** Al acabar la respiración, un botón te lleva a meditar. Haz el tutorial y una sesión con los ojos cerrados. Para pausar, palma abierta, quieta y por encima de los hombros. Para seguir, cierra los ojos 2 s.
4. **Estiramientos.** Al acabar la meditación, un botón te lleva a estirar. Haz el tutorial y una sesión. Abajo te dice qué te falta en cada postura. Aquí se pausa con Espacio.
5. **Al acabar las tres**, el resultado dice "Ritual de hoy completo" y en el inicio sale tu racha.

Si algo tarda en reconocerse, la tecla **D** enseña los números que mide la cámara.

## Si algo falla

| Qué pasa | Qué hacer |
|---|---|
| "No se puede abrir la cámara" | Cierra los programas que la usan (videollamadas). Si tienes varias, prueba `bash jugar.sh --camara 1` |
| "La cámara no da imagen" (macOS) | Ajustes del Sistema → Privacidad y seguridad → Cámara, activa la Terminal y vuelve a abrir Temple |
| En un Mac coge la cámara del iPhone | `bash jugar.sh --camara 1` |
| "Faltan los modelos de MediaPipe" | `bash instalar.sh` |
| "Temple no está instalado" al usar `jugar.sh` | `bash instalar.sh` |
| "No te veo" | Aléjate un poco y pon luz de frente, que se te vea de la cabeza al pecho |
| "No veo tu mano, aléjate un poco" | Muy cerca solo se ve el dedo y no la mano entera |
| Señalas y no se pulsa | El índice estirado apuntando a la pantalla o hacia arriba, los demás dedos cerrados, y quieto 1,5 s |
| La instalación falla en los tests | Copia lo que sale en la Terminal y abre un *issue* en el repositorio |

## Cómo se maneja

De lejos, con la mano. De cerca, con el teclado o el ratón, como cualquier programa.

| Gesto o tecla | Qué hace |
|---|---|
| Señalar un botón con el índice 1,5 s | Lo pulsa. El dedo tiene que apuntar a la pantalla o hacia arriba |
| Palma abierta, de frente, quieta y lejos de la nariz | Pausa la respiración (1 s) y la meditación (1,5 s, por encima de los hombros) |
| Cerrar los ojos 2 s en la pausa de la meditación | Sigue meditando |
| Espacio | Empezar, pausar o seguir. En los estiramientos es la única pausa, porque ahí las manos están siempre abiertas |
| Flechas o Tab, y Enter | Moverse entre los botones y pulsar |
| Clic | Pulsar un botón |
| R, E, I | Elegir respiración, meditación o estiramientos en el inicio |
| M | Sonido |
| D | Ver los números que mide la cámara |
| Esc | Volver al inicio, o salir |

Opciones para probar, que no cuentan para subir de nivel.

```bash
bash jugar.sh --vueltas 2     # respiración corta
bash jugar.sh --avanzada      # respiración avanzada sin desbloquearla
bash jugar.sh --minutos 1     # meditación corta (0 es sin límite)
bash jugar.sh --segundos 5    # estiramientos cortos
bash jugar.sh --camara 1      # otra cámara, si hay varias
```

El progreso se guarda en `datos/progreso.json`, en tu equipo. Cada meditación y cada sesión de estiramientos apunta además lo que mide la cámara en un CSV de `datos/`, cuatro veces por segundo, para ajustar los umbrales con números reales.

## Tests

`instalar.sh` los pasa al final. Para pasarlos otra vez basta con repetirlo, porque lo que ya está instalado se lo salta y en menos de un minuto solo comprueba.

```bash
bash instalar.sh
```

Son más de 100 y no necesitan cámara. Prueban la lógica de las tres fases con cuerpos inventados (cada postura, la calibración, los avisos, la escalera de minutos y los desbloqueos), los gestos (señalar, la palma que pausa y la que solo pasa por delante, la mano apoyada en la cabeza), la navegación con el teclado y la instalación (los scripts, las versiones fijadas y que los modelos cargan). `tests/test_interfaz.py` abre la aplicación sin ventana con una cámara falsa y hace el ritual entero como un usuario, sin tocar tu progreso.

En GitHub se pasan solos en cada push (`.github/workflows/tests.yml`). Además, un Ubuntu y un Mac de GitHub ejecutan `instalar.sh` desde cero, arrancan con `jugar.sh` y lo quitan con `desinstalar.sh`, igual que un usuario nuevo.

## Arquitectura

Tres capas. Los **ojos** ven puntos, el **cerebro** decide qué pasa y la **interfaz** lo enseña y suena. El cerebro no importa Pygame ni OpenCV, así que se prueba con datos inventados.

```
main.py                    arranque y opciones
instalar.sh, jugar.sh      instalación en un equipo limpio, arranque y desinstalar.sh para quitarlo
temple/
  camara.py                ojos     cámara y detección en un hilo aparte, y los avisos si fallan
  vision.py                ojos     Pose (cuerpo), Hands (mano) y Face (ojos), y qué orificio se tapa
  respiracion.py           cerebro  guion de la respiración
  meditacion.py            cerebro  calibración de la postura, quieto, recto y ojos
  estiramientos.py         cerebro  las siete posturas, qué falta en cada una y su guion
  puntero.py               cerebro  señalar, el imán de los botones y la palma que pausa
  navegacion.py            cerebro  moverse por los botones con el teclado
  progreso.py              cerebro  historial, racha, lotos, escalera y desbloqueos en JSON
  interfaz/
    app.py                 el bucle, las teclas, la pausa y el cambio de pantalla
    fases/                 una clase por fase (respiración, meditación y estiramientos)
    inicio.py, marco.py, botones.py, piezas.py, textos.py, dibujo.py, estilo.py, sonido.py
herramientas/              scripts de los experimentos
tests/
```

La aplicación no sabe nada de respirar ni de estirar. Le pide a la fase activa lo suyo (sus botones del inicio, su panel, lo que dibuja sobre la cámara y su resultado). Los estiramientos entraron así, con su lógica en `temple/`, su clase en `temple/interfaz/fases/` y una línea en la lista `FASES`, sin tocar las otras fases.

La cámara y los modelos van en un hilo aparte porque tardan de 30 a 50 ms por fotograma. El modelo de cara solo trabaja al meditar.

## Decisiones técnicas

| Decisión | Por qué |
|---|---|
| Detección por reglas, con distancias entre puntos medidas en anchos de hombros | No hace falta entrenar ningún modelo y da igual lo lejos que estés |
| En la respiración vale cualquier dedo pegado a la nariz para el lado izquierdo | Con la mano doblada MediaPipe confunde qué dedo es cuál (experimento con `herramientas/explorar_manos.py`) |
| La espalda se mide por la cabeza, comparada con tu postura recta calibrada al empezar | Sentado cerca la cámara no ve las caderas |
| Ojos cerrados con los *blendshapes* de Face Landmarker, corte en 0,4 | En nuestras pruebas, abiertos daban 0,15-0,25 y cerrados 0,6-0,77 |
| Un fallo solo cuenta si dura más de 1 s en la meditación y 0,5 s en los estiramientos | Un parpadeo o un salto del modelo no deben quitar puntos |
| En los estiramientos el lado sale de dónde está en la pantalla, no de la etiqueta de MediaPipe | Con la imagen en espejo, sus etiquetas de izquierda y derecha se cruzan |
| La cabeza inclinada se mide contra la línea de los hombros | Así da igual que la cámara esté algo torcida |
| Las muñecas se usan aunque MediaPipe no esté seguro de verlas | Con el brazo estirado la muñeca se sale de la imagen y el modelo estima bien dónde está |
| "Sujeta el codo" mira la muñeca más cercana al codo del otro brazo | Con los brazos cruzados MediaPipe intercambia a ratos qué muñeca es cuál |
| Señalar solo cuenta con el índice estirado, los demás dedos cerrados y apuntando a la pantalla o hacia arriba | Con la mano apoyada en la cabeza se pulsaban botones solos |
| La palma que pausa tiene que estar de frente, quieta y lejos de la nariz | Al bajar la mano después de meditar saltaba la pausa. Una mano que pide pausa está quieta, una que baja no |
| En los estiramientos la palma no pausa | Las manos están siempre abiertas por arriba, en la cabeza o en el codo |
| Cada texto en un hueco fijo de una línea que se encoge si no cabe | Así nada se pisa, diga lo que diga |
| Una clase por fase y la aplicación solo habla con la fase activa | `app.py` había llegado a 1.300 líneas con dos fases mezcladas |
| Instalación con Conda y conda-forge, y tests en GitHub en Ubuntu y Mac | Es lo más parecido al equipo limpio que pide la entrega, y conda-forge no pide aceptar condiciones |
| Sonidos generados con numpy | No hace falta ningún archivo de audio |

## Tecnología

- [MediaPipe](https://ai.google.dev/edge/mediapipe) (Pose Landmarker, Hand Landmarker y Face Landmarker)
- OpenCV para la cámara y Pygame para la interfaz
- Python 3.12 con Conda
- Fuentes Cormorant Garamond y Nunito, con licencia SIL Open Font License (en `assets/fuentes/`)

## Lo que aprendimos y lo que haríamos distinto

- **Que pase los tests no significa que funcione.** Una primera versión de la meditación pasaba todos los tests y la borramos entera porque no la habíamos probado con la cámara. Rehecha y probada, salieron fallos que ningún test veía.
- **Medir antes de ajustar.** El juego apunta lo que mide en un CSV. Con él vimos que los fallos de recto venían de los hombros y no de encorvarse, y que el brazo cruzado fallaba porque la muñeca se salía de la imagen.
- **Los gestos chocan con los movimientos normales.** La palma que pausa saltaba al estirar con la mano en la cabeza y al bajar la mano después de meditar, y señalar se activaba con la mano apoyada. Lo que funcionó fue pensar qué distingue el gesto de verdad (una mano que pide pausa está quieta y de frente, un dedo que señala apunta a la pantalla). Ahora empezaríamos probando cada gesto con lo que el cuerpo hace sin querer.
- **Los dedos de MediaPipe no son fiables con la mano doblada ni con los brazos cruzados.** Funciona mejor medir algo que no dependa de qué dedo o qué muñeca es cuál.
- **Si no se ve la palma, no hay mano.** Muy cerca de la cámara solo salía el dedo y MediaPipe no detectaba la mano. Ahora el juego avisa con "No veo tu mano, aléjate un poco".
- **Manejar menús con la mano es más difícil de lo que parece.** Fueron cuatro intentos (cursor fino, imán largo, gesto de señalar e imán corto) antes de que no se pulsara nada sin querer.
- **Reorganizar sin cambiar nada, y demostrarlo.** Antes de partir `app.py` grabamos 385 capturas de un recorrido automático por todas las pantallas, y después del cambio salieron idénticas píxel a píxel.
- **Decir qué hacer, no qué fallaste.** "Lo que más te ha costado, abrir los ojos" se entendía al revés. Ahora dice "Para mejorar, mantén los ojos cerrados", y en los estiramientos, lo que falta para estar en la postura.

## Autores

- Rares Andrei Mocanu
- Nikolas Kaplan
