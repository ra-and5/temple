# Temple

[![Tests](https://github.com/ra-and5/temple/actions/workflows/tests.yml/badge.svg)](https://github.com/ra-and5/temple/actions/workflows/tests.yml)

**Juego serio de respiración, meditación, estiramientos y flexiones que se maneja con la webcam.**

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
| **Flexiones** | En el suelo y de lado a la cámara. Cuenta las repeticiones y mira que bajes y que el cuerpo vaya recto | ✅ |

### El juego en una frase

> Cada fase te da de **0 a 3 lotos** según lo bien que lo hagas. **5 días con 3 lotos te suben de nivel.** Haz el ritual cada día para mantener la **racha**.

Es la misma regla en todas las fases que suben, para que se entienda a la primera. Lo que cambia al subir depende de la fase.

| Fase | Niveles |
|---|---|
| Respiración | Principiante → Avanzada (retienes 16 tiempos con los dos lados tapados) |
| Meditación | 5 → 8 → 12 → 17 → 23 → 30 → 40 minutos → sin límite |
| Estiramientos | Sin niveles. Son el calentamiento antes de las flexiones, para no lesionarse |
| Flexiones | Fácil 5 → Técnico 5 → Técnico 10 |

Los lotos salen del porcentaje del tiempo (o de las flexiones) que lo haces bien, con los mismos cortes en todas las fases (40, 65 y 85 %). Cada día cuenta una vez, y solo jugando tu nivel más alto. Se puede bajar de nivel para un día flojo, pero así no se sube. Nunca se pierde un nivel.

### Las pantallas

Como el menú de un videojuego, una cosa en cada pantalla.

| Pantalla | Qué tiene |
|---|---|
| **Menú** | Ritual de hoy, Practicar una fase, Tu progreso, Ajustes y Salir. Arriba, las cuatro fases con la marca de las hechas hoy |
| **Ritual de hoy** | Las cuatro fases seguidas, desde la primera que te falta. Antes de cada una, una pantalla dice cómo colocarte. En la fila de arriba (tu práctica de hoy) se puede elegir otra fase con el dedo, el ratón o las flechas, y el ritual empieza desde ella |
| **Antes de empezar** | Cómo ponerte delante de la cámara (en las flexiones, una silueta de perfil sobre la imagen), lo que te falta para subir, el nivel y Empezar |
| **Tu progreso** | La racha, los días de esta semana y el nivel de cada fase |
| **Ajustes** | Sonido, pantalla completa y vueltas de respiración |

### Respiración

Sigue el vídeo [Pranayama para principiantes (Anuloma Viloma)](https://www.youtube.com/watch?v=CacBxE8bXao), de Anabel Otero, que la recomienda justo antes de meditar. Cada vuelta es inhalar 4 tiempos por la izquierda, exhalar 8 por la derecha, inhalar 4 por la derecha y exhalar 8 por la izquierda. Las vueltas se eligen en Ajustes, de 1 a 9 (5 por defecto). Con menos de 5 la sesión vale para la racha pero no para subir.

La cámara no ve el aire. Comprueba qué lado tapas, y el ritmo lo marca el juego. Temple es una ayuda para practicar, no una herramienta médica.

### Meditación

Al empezar mide tu postura recta y arranca cuando cierras los ojos. Si algo falla 3 s seguidos suenan dos golpes suaves, porque con los ojos cerrados no se ve la pantalla, y cada minuto una campana. Cada nivel es más tiempo, y el último es **sin límite**, que se acaba con Terminar en la pausa.

### Estiramientos

Siete posturas sentado, de 20 s cada una. No suben de nivel, porque no son un reto sino el calentamiento que prepara cuello, hombros y brazos antes de las flexiones. La cuenta solo avanza mientras estás en la postura, y abajo te dice qué te falta ("Pon la mano sobre la cabeza", "Sujeta el codo con la otra mano"…). Sobre la cámara, una raya discontinua marca hasta dónde llegar.

| Postura | Cómo la reconoce la cámara |
|---|---|
| Cabeza a la derecha y a la izquierda | Las orejas inclinadas 20° respecto a los hombros, con la mano de ese lado sobre la cabeza |
| Brazos arriba | Los dos codos por encima de la nariz |
| Brazo derecho e izquierdo cruzados | La muñeca pasa al otro lado del pecho. Se pide sujetar el codo con la otra mano, pero no se comprueba, porque la mano lo tapa y MediaPipe lo coloca mal |
| Tríceps derecho e izquierdo | El codo por encima de la cabeza, el brazo doblado con la mano a la espalda y la otra mano sujetando el codo |

### Flexiones

Se hacen en el suelo, con el portátil también en el suelo, de lado y a unos 2 m, para que la cámara te vea de la cabeza a los pies. Al empezar tienes 5 s para colocarte, y después hay que aguantar la plancha 2 s antes de que empiece a contar. Cada vez que completas una suena un tono, y si no ha salido bien suenan dos golpes, porque desde el suelo no se ve la pantalla.

| Qué mira | Cómo lo mide la cámara |
|---|---|
| Una flexión | El ángulo del codo (hombro, codo y muñeca) baja de un límite y vuelve a subir |
| Que bajes hasta el suelo | Lo que le queda al hombro hasta la altura de la muñeca |
| El cuerpo recto | Que la cadera no se salga de la línea entre el hombro y el tobillo |

**Fácil** cuenta casi todo y es para quien está empezando. **Técnico** pide bajar hasta el suelo con el cuerpo recto.

## Instalación

Funciona en **macOS** (chip de Apple o Intel, macOS 13 o más nuevo) y en **Ubuntu**. Hace falta una webcam e internet para instalar.

Descomprime el zip, abre una terminal dentro de la carpeta y ejecuta el instalador.

```bash
bash instalar.sh
```

Desde GitHub es lo mismo, después de `git clone https://github.com/ra-and5/temple.git` y `cd temple`.

El script lo hace todo y se puede repetir sin miedo.

1. Busca Conda y, si no está, instala Miniconda en `~/miniconda3` (pregunta antes).
2. Crea el entorno `temple` con Python 3.12, porque MediaPipe 0.10.21 no funciona con versiones más nuevas.
3. Instala las librerías de `requirements.txt`, con las versiones fijadas.
4. Descarga los tres modelos de MediaPipe en `models/` y comprueba que son los mismos con los que probamos el juego.
5. Pasa todos los tests para confirmar que funciona.

Tarda unos 5 minutos (en nuestro Ubuntu, 2 minutos y medio con Conda ya instalada). Para jugar.

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

Unos 25 minutos con las duraciones de verdad.

```bash
bash jugar.sh
```

### Probarlo entero en menos de 10 minutos

Para corregir o enseñar el juego sin meditar 5 minutos ni hacer todas las vueltas, `--rapido` acorta todo a la vez. Son 1 vuelta de respiración, 1 minuto de meditación, 4 s por postura y 2 flexiones, y los mensajes entre paso y paso ("Prepárate", "Muy bien"…) duran 1,5 s en vez de 3 a 6 s. Se ven las cuatro fases con su tutorial, su sesión y su resultado, pero esas sesiones no cuentan para subir de nivel (el resultado lo dice).

```bash
bash jugar.sh --rapido
```

Se puede combinar con las demás opciones, y lo que se diga aparte manda (`bash jugar.sh --rapido --minutos 3`). Para ver una subida de nivel de verdad, sin `--rapido`, está la demo del final de [Cómo se maneja](#cómo-se-maneja).

Los pasos, con o sin `--rapido`.

1. **Colócate.** Sentado, a medio metro de la cámara y con luz de frente, de forma que se te vea de la cabeza al pecho y los codos.
2. **Ritual de hoy.** En el menú, señala con el índice, apuntando a la pantalla, el botón "Ritual de hoy" y espera a que se rellene. Te lleva a la respiración.
3. **Respiración.** Pulsa "Aprender con el tutorial", que enseña a tapar cada lado. Al acabar vuelves a la pantalla de la fase. Pulsa Empezar y haz la sesión.
4. **Meditación.** En el resultado, "Seguir" te lleva a meditar. Tutorial y sesión con los ojos cerrados. Para pausar, palma abierta, quieta y por encima de los hombros. Para seguir, cierra los ojos 2 s, o abre la palma y ciérrala en un puño.
5. **Estiramientos.** Igual, tutorial y sesión. Abajo te dice qué te falta en cada postura. Para pausar, palma abierta, quieta y por encima de los hombros entre postura y postura, o sal de la cámara.
6. **Flexiones.** Pon el portátil en el suelo a unos 2 m y ponte **de perfil**, como la silueta que sale sobre la cámara. Tutorial y sesión. Para pausar, ponte de rodillas y enseña la palma, o levántate.
7. **Al acabar las cuatro**, el resultado dice "Ritual de hoy completo" y vuelves al menú. En Tu progreso salen la racha y lo que te falta para subir en cada fase.

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
| "No te veo entero" en las flexiones | Aléjate hasta que se te vean los pies, con el portátil en el suelo y de lado |
| "No veo tu mano, aléjate un poco" | Muy cerca solo se ve el dedo y no la mano entera |
| Señalas y no se pulsa | El índice estirado apuntando a la pantalla o hacia arriba, los demás dedos cerrados, y quieto 1,5 s |
| La instalación falla en los tests | Copia lo que sale en la Terminal y abre un *issue* en el repositorio |

## Cómo se maneja

De lejos, con la mano. De cerca, con el teclado o el ratón, como cualquier programa.

| Gesto o tecla | Qué hace |
|---|---|
| Señalar un botón con el índice 1,5 s | Lo pulsa. El dedo tiene que apuntar a la pantalla o hacia arriba. Si la mano no tiene forma de señalar, ni sale el cursor ni se elige nada |
| Palma abierta, de frente, quieta y lejos de la nariz | Pausa en cualquier fase y en cualquier momento, tutorial o sesión (1 s, y 1,5 s por encima de los hombros al meditar). En los estiramientos, solo entre postura y postura, por encima de los hombros y pasados 2 s de la última |
| En la pausa, abrir la palma de frente y cerrarla en un puño | Sigue. En la cámara se ve cada paso ("Para seguir, palma abierta…" y "Cierra el puño para seguir") |
| Cerrar los ojos 2 s en la pausa de la meditación | Sigue meditando |
| Espacio | Empezar, pausar o seguir |
| Flechas o Tab, y Enter | Moverse entre los botones y pulsar |
| Clic | Pulsar un botón |
| R, E, I, X | Abrir respiración, meditación, estiramientos o flexiones desde el menú |
| ← → en la pantalla de una fase | Bajar o subir el nivel que juegas |
| M | Sonido |
| F | Pantalla completa, y otra vez para volver a la ventana |
| D | Ver los números que mide la cámara |
| Esc | Volver a la pantalla de antes. En el menú pregunta si quieres salir, igual que el botón Salir |

Opciones para probar, que no cuentan para subir de nivel. Para enseñar el juego con unas semanas de progreso inventado, `python herramientas/crear_demo.py` y después `bash jugar.sh --datos datos/demo`. Con `--dia5` deja 4 días con 3 lotos en cada fase, para ver hoy la subida de nivel de todas.

```bash
bash jugar.sh --rapido        # todo corto a la vez, para probarlo entero
bash jugar.sh --vueltas 2     # respiración corta
bash jugar.sh --avanzada      # respiración avanzada sin desbloquearla
bash jugar.sh --minutos 1     # meditación corta (0 es sin límite)
bash jugar.sh --segundos 5    # estiramientos cortos
bash jugar.sh --flexiones 2   # flexiones cortas
bash jugar.sh --camara 1      # otra cámara, si hay varias
```

El progreso se guarda en `datos/progreso.json`, en tu equipo. Cada meditación, sesión de estiramientos y de flexiones apunta además lo que mide la cámara en un CSV de `datos/`, varias veces por segundo, para ajustar los umbrales con números reales.

## Tests

`instalar.sh` los pasa al final. Para pasarlos otra vez basta con repetirlo, porque lo que ya está instalado se lo salta y en unos 2 minutos solo comprueba.

```bash
bash instalar.sh
```

Son 194 y no necesitan cámara. Prueban la lógica de las cuatro fases con cuerpos inventados (cada postura, contar flexiones, la calibración, los avisos, la escalera de minutos y la regla de los niveles), los gestos (señalar, la palma que pausa y la que solo pasa por delante, la mano apoyada en la cabeza), la navegación con el teclado y la instalación (los scripts, las versiones fijadas y que los modelos cargan). `tests/test_interfaz.py` abre la aplicación sin ventana con una cámara falsa y juega como un usuario, sin tocar tu progreso. Recorre todas las pantallas en todos sus estados y comprueba que en ningún botón el texto se sale o se pisa con la tecla. Hace el ritual entero (también elegido desde la fila de arriba con el dedo, el ratón y las flechas), cada fase del tutorial al resultado (en las flexiones, una persona de perfil que baja y sube, con la cadera recta o hundida), la pausa con la palma en las cuatro fases (al empezar y a mitad, en el tutorial y en la sesión, y seguir con la palma y el puño), con Espacio y al salir de la cámara, y comprueba que cerrar la ventana a mitad deja guardado el registro. Con `--rapido` comprueba que cada fase acorta sus textos y que las flexiones acaban en segundos sin subir de nivel. `tests/test_arranque.py` comprueba que las opciones de `main.py` (también `--rapido`) llegan a la aplicación y que la demo de `herramientas/crear_demo.py` deja una racha larga, los niveles subidos y hoy sin hacer.

En GitHub se pasan solos en cada push (`.github/workflows/tests.yml`), midiendo con `coverage` qué parte del código prueban. El informe sale en el resumen de cada ejecución en la pestaña Actions. Lo único que no se puede probar sin una persona delante es la cámara y la ventana de verdad (`camara.py`, `vision.py` y `ventana.py`). Además, un Ubuntu y un Mac de GitHub ejecutan `instalar.sh` desde cero, arrancan con `jugar.sh` y lo quitan con `desinstalar.sh`, igual que un usuario nuevo.

## Arquitectura

Tres capas. Los **ojos** ven puntos, el **cerebro** decide qué pasa y la **interfaz** lo enseña y suena. El cerebro no importa Pygame ni OpenCV, así que se prueba con datos inventados.

```
main.py                    arranque y opciones
instalar.sh, jugar.sh      instalación en un equipo limpio, arranque y desinstalar.sh para quitarlo
temple/
  camara.py                ojos     cámara y detección en un hilo aparte, y los avisos si fallan
  vision.py                ojos     Pose (cuerpo, también cadera y tobillo), Hands (mano) y Face (ojos), y qué orificio se tapa
  respiracion.py           cerebro  guion de la respiración
  meditacion.py            cerebro  calibración de la postura, quieto, recto y ojos
  estiramientos.py         cerebro  las siete posturas, qué falta en cada una y su guion
  flexiones.py             cerebro  el ángulo del codo, lo que bajas, la cadera y el contador
  puntero.py               cerebro  señalar, el imán de los botones y la palma que pausa
  navegacion.py            cerebro  moverse por los botones con el teclado
  progreso.py              cerebro  historial, racha y la regla única de niveles, en JSON
  interfaz/
    app.py                 el bucle, las teclas, la pausa, el ritual y el cambio de pantalla
    menus.py               menú, practicar una fase, antes de empezar, progreso, ajustes y salir
    fases/                 una clase por fase (respiración, meditación, estiramientos y flexiones)
    marco.py, botones.py, piezas.py, textos.py, dibujo.py, estilo.py, sonido.py
herramientas/              scripts de los experimentos
tests/
```

La aplicación no sabe nada de respirar ni de estirar. Le pide a la fase activa lo suyo (cómo colocarse, qué cambia en cada nivel, su panel, lo que dibuja sobre la cámara y su resultado). Guardar la sesión con la regla de los niveles es común a todas, en la clase base. Los estiramientos y las flexiones entraron así, con su lógica en `temple/`, su clase en `temple/interfaz/fases/` y una línea en la lista `FASES`, sin tocar las otras fases.

La cámara y los modelos van en un hilo aparte porque tardan de 30 a 50 ms por fotograma. El modelo de cara solo trabaja al meditar.

## Decisiones técnicas

| Decisión | Por qué |
|---|---|
| Detección por reglas, con distancias entre puntos medidas en anchos de hombros | No hace falta entrenar ningún modelo y da igual lo lejos que estés |
| En la respiración vale cualquier dedo pegado a la nariz para el lado izquierdo | Con la mano doblada MediaPipe confunde qué dedo es cuál (experimento con `herramientas/explorar_manos.py`) |
| La espalda se mide por la cabeza, comparada con tu postura recta calibrada al empezar | Sentado cerca la cámara no ve las caderas |
| Ojos cerrados con los *blendshapes* de Face Landmarker, corte en 0,4 | En nuestras pruebas, abiertos daban 0,15-0,25 y cerrados 0,6-0,77 |
| Un fallo solo cuenta si dura más de 1 s en la meditación y en los estiramientos | Un parpadeo o un salto del modelo no deben quitar puntos |
| En los estiramientos el lado sale de dónde está en la pantalla, no de la etiqueta de MediaPipe | Con la imagen en espejo, sus etiquetas de izquierda y derecha se cruzan |
| La cabeza inclinada se mide contra la línea de los hombros | Así da igual que la cámara esté algo torcida |
| Las muñecas se usan aunque MediaPipe no esté seguro de verlas | Con el brazo estirado la muñeca se sale de la imagen y el modelo estima bien dónde está |
| En el tríceps, "sujeta el codo" mira la muñeca más cercana al codo del otro brazo | MediaPipe intercambia a ratos qué muñeca es cuál, así que no se mira cuál es |
| Señalar solo cuenta con el índice estirado, los demás dedos cerrados y apuntando a la pantalla o hacia arriba | Con la mano apoyada en la cabeza se pulsaban botones solos |
| La palma que pausa tiene que estar de frente, quieta y lejos de la nariz | Al bajar la mano después de meditar saltaba la pausa. Una mano que pide pausa está quieta, una que baja no |
| En los estiramientos la palma solo pausa entre postura y postura | En las posturas la mano está abierta en la cabeza, arriba o sujetando el codo, también por encima de los hombros en el tríceps. La mano del codo pausaba. En mitad de una postura se pausa saliendo de la cámara o con Espacio |
| En los estiramientos los puntos del cuerpo se suavizan y salirse menos de 1 s no corta la cuenta | MediaPipe mueve cada punto unos píxeles en cada fotograma, y más la muñeca escondida detrás de la cabeza en el tríceps (la ve con 0,3 a 0,5 de confianza). Las líneas temblaban y la postura entraba y salía |
| El tríceps se reconoce por qué brazo está más doblado. En el brazo cruzado solo cuenta el cruce, sin mirar qué muñeca es cuál ni si sujetas el codo | Con los datos de la tecla D, el brazo que estiras está siempre más doblado que el que sujeta. Con los brazos cruzados MediaPipe intercambia las muñecas a ratos, y la mano que sujeta tapa el codo. Sujetando, la distancia de la mano al codo daba de 0,04 a 1,2, y sin sujetar de 0,7 a 0,85, así que no se podía pedir sin cortar la cuenta haciéndolo bien |
| Cada texto en un hueco fijo que se encoge si no cabe (el título en una línea y el detalle en dos), y el círculo de todas las fases a la misma altura, por debajo | Así nada se pisa, diga lo que diga. Un test recorre los textos de todos los pasos y falla si alguno llegaría al círculo |
| Una clase por fase y la aplicación solo habla con la fase activa | `app.py` había llegado a 1.300 líneas con dos fases mezcladas |
| Instalación con Conda y conda-forge, y tests en GitHub en Ubuntu y Mac | Es lo más parecido al equipo limpio que pide la entrega, y conda-forge no pide aceptar condiciones |
| Sonidos generados con numpy | No hace falta ningún archivo de audio |
| En las flexiones la regla de medir es el largo del tronco (de hombro a cadera) | De lado los hombros quedan uno encima del otro y su ancho sale casi 0 |
| Se mide el brazo que MediaPipe ve mejor | De lado un brazo tapa al otro |
| Una flexión cuenta al bajar de un ángulo y volver a subir de otro distinto | Si fuera el mismo, un temblor del codo contaría dos flexiones |
| 5 s para colocarse y 2 s de plancha antes de contar | En la primera prueba contaba una flexión mientras nos tumbábamos |
| Dos niveles en las flexiones | Con los límites del nivel técnico, alguien que empieza no sumaba casi ninguna |
| En las flexiones, la mediana de los últimos 5 fotogramas, un fallo de menos de 0,3 s no reinicia la plancha y una flexión de menos de 0,4 s no cuenta | En nuestra prueba del 25/11 el ángulo del codo bailaba de 126° a 172° con los brazos estirados, la plancha tardó 18 s en darse por buena y un salto suelto contó una flexión que no existía |
| Una sola regla para subir de nivel en las cuatro fases (5 días con 3 lotos) | Antes cada fase tenía la suya (sesiones, semanas, mejor marca). Con una sola se explica en una frase y es coherente (consistencia, heurística de Nielsen) |
| Menú por pantallas en lugar de un inicio con todo | El inicio tenía once cosas a la vez y con el dedo costaba atinar. Una cosa en cada pantalla (diseño minimalista, heurística de Nielsen) y botones grandes y separados |
| La forma de la mano se mide en la proporción real de la imagen | MediaPipe da los puntos de 0 a 1 en cada eje, y la imagen es más ancha que alta. Medida así, una palma de frente parecía de lado y no pausaba |
| Seguir desde la pausa con la palma abierta y luego el puño | Un gesto en dos tiempos no salta solo, y se ve en la cámara en qué paso vas |
| Los estiramientos no suben de nivel | Son el calentamiento antes de las flexiones. Hacerlos más largos no es un reto que tenga sentido |
| Antes de cada fase, cómo colocarse y una silueta en las flexiones | Al probar las flexiones nos pusimos de frente a la cámara en vez de de perfil |
| Fondo en tonos de piedra y letra más grande en las sesiones | El violeta no recordaba a un templo, y a 1-2 m la letra pequeña no se leía |

## Tecnología

- [MediaPipe](https://ai.google.dev/edge/mediapipe) (Pose Landmarker, Hand Landmarker y Face Landmarker)
- OpenCV para la cámara y Pygame para la interfaz
- Python 3.12 con Conda
- Fuentes Cormorant Garamond y Nunito, con licencia SIL Open Font License (en `assets/fuentes/`)

## Lo que aprendimos y lo que haríamos distinto

- **Que pase los tests no significa que funcione.** Una primera versión de la meditación pasaba todos los tests y la borramos entera porque no la habíamos probado con la cámara. Rehecha y probada, salieron fallos que ningún test veía.
- **Medir antes de ajustar.** El juego apunta lo que mide en un CSV. Con él vimos que los fallos de recto venían de los hombros y no de encorvarse, y que el brazo cruzado fallaba porque la muñeca se salía de la imagen.
- **Los gestos chocan con los movimientos normales.** La palma que pausa saltaba al estirar con la mano en la cabeza o sujetando el codo y al bajar la mano después de meditar, y señalar se activaba con la mano apoyada. Lo que funcionó fue pensar qué distingue el gesto de verdad (una mano que pide pausa está quieta y de frente, un dedo que señala apunta a la pantalla). Ahora empezaríamos probando cada gesto con lo que el cuerpo hace sin querer.
- **Los dedos de MediaPipe no son fiables con la mano doblada ni con los brazos cruzados.** Funciona mejor medir algo que no dependa de qué dedo o qué muñeca es cuál.
- **Si no se ve la palma, no hay mano.** Muy cerca de la cámara solo salía el dedo y MediaPipe no detectaba la mano. Ahora el juego avisa con "No veo tu mano, aléjate un poco".
- **Manejar menús con la mano es más difícil de lo que parece.** Fueron cuatro intentos (cursor fino, imán largo, gesto de señalar e imán corto) antes de que no se pulsara nada sin querer.
- **Reorganizar sin cambiar nada, y demostrarlo.** Antes de partir `app.py` grabamos 385 capturas de un recorrido automático por todas las pantallas, y después del cambio salieron idénticas píxel a píxel.
- **Los límites se ajustan con datos.** En la primera prueba de las flexiones casi todas salían "poco profundas". Mirando el CSV vimos que en el fondo de una flexión normal el hombro quedaba más alto de lo que habíamos supuesto, y cambiamos el límite.
- **Las coordenadas normalizadas engañan.** Los puntos de MediaPipe van de 0 a 1 tanto a lo ancho como a lo alto. Comparando un ancho con un alto en esas unidades, la palma de frente parecía estrecha. Lo vimos pasando una captura de la prueba por el mismo detector del juego.
- **Lo que la cámara no ve no se puede exigir.** En el brazo cruzado pedíamos sujetar el codo, pero la propia mano lo tapa y MediaPipe lo coloca donde puede. La postura se cortaba haciéndola bien. Pasando por las reglas nuevas las sesiones guardadas con la tecla D vimos que sujetar y no sujetar daban distancias que se solapan, y dejamos de comprobarlo. Ahora, antes de pedir algo, miraríamos en los datos si la cámara lo distingue.
- **Suavizar antes de decidir.** Las líneas del cuerpo temblaban aunque estuvieras quieto y la postura entraba y salía. Con una media entre fotogramas y un segundo de margen, las mismas sesiones pasaron de un 26 % del tiempo fuera a un 0 %.
- **Decir qué hacer, no qué fallaste.** "Lo que más te ha costado, abrir los ojos" se entendía al revés. Ahora dice "Para mejorar, mantén los ojos cerrados", y en los estiramientos, lo que falta para estar en la postura.

## Autores

- Rares Andrei Mocanu
- Nikolas Kaplan
