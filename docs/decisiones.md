# Decisiones

Todas las decisiones importantes del proyecto, agrupadas por tema y en el orden en que las tomamos. Cada una cuenta qué problema había, qué hicimos y por qué. Cuando descartamos otras opciones, también lo decimos.

Cómo funciona cada pieza está en [como-funciona.md](como-funciona.md).

## La idea

| Fecha | Qué decidimos | Por qué |
|---|---|---|
| 05/11 | Un juego serio de **meditación y flexiones** con progresión, aprobado por el profesor | Es algo que queríamos hacer de verdad y nunca empezábamos. El profesor pidió niveles y que no fuera demasiado fácil |
| 05/11 | **Un solo jugador** y la competición entre los dos fuera | Dos personas en el suelo delante de una webcam se tapan una a otra. El ritual diario ya es un juego completo |
| 05/11 | Un **ritual diario** de la calma al cuerpo | Respirar prepara para meditar, y estirar prepara para las flexiones |
| 05/11 | Se llama **Temple** | En español es la calma y también el valor para un reto, que son la meditación y las flexiones. En inglés es templo, el sitio al que vuelves cada día |
| 11/11 | Añadir la **respiración alterna** antes de meditar | Prepara para meditar y es salud. Además suma visión, porque usa dos modelos a la vez (manos y pose) |
| 12/11 | **Terminar una fase entera antes de empezar otra** | Mejor una fase pulida que enseñar cuatro a medias |

## Visión y detección

| Problema | Qué decidimos | Por qué |
|---|---|---|
| Hay que saber si lo haces bien sin entrenar nada | **Reglas** con distancias y ángulos entre los puntos de MediaPipe | Se entienden, se ajustan con números y el profesor dijo que vale |
| Si te acercas o te alejas, todas las distancias cambian | Medir en **anchos de hombros**, y en las flexiones en **largos de tronco** | Así da igual la distancia. De lado los hombros se solapan y su ancho sale casi 0 |
| Cada modelo gasta tiempo | **Tres modelos**, pero el de cara solo trabaja al meditar | La cara añade unos 13 ms por foto y solo hace falta para los ojos |
| Los modelos tardan de 30 a 50 ms y la pantalla iría a saltos | La cámara y los modelos en un **hilo aparte** | La pantalla coge la última lectura sin esperar |
| Con la imagen en espejo, la izquierda y la derecha de MediaPipe se cruzan | El lado sale de **dónde está en la pantalla**, no de su etiqueta | Es lo que ve el jugador |
| Con el brazo estirado la muñeca se sale de la imagen y MediaPipe la marca con poca confianza | Usar las muñecas **aunque el modelo no esté seguro** | Estima bien dónde está por el resto del brazo. Antes, el brazo cruzado solo salía bien 19 de 36 veces porque la muñeca se descartaba |
| MediaPipe da x e y de 0 a 1, y la imagen es más ancha que alta | Medir la mano en la **proporción real** de la imagen | Medida en 0 a 1, una palma de frente daba 0,54 y parecía de lado. En proporción real daba 0,70 |

## Respiración

| Problema | Qué decidimos | Por qué |
|---|---|---|
| Qué técnica seguir | El vídeo de **Anabel Otero**. Inhala 4 y exhala 8 por cada lado, 5 vueltas, y la avanzada con retención de 16 | Es una técnica de principiante, clara y pensada para antes de meditar |
| La cámara no ve el aire | El juego **marca el ritmo** y la cámara mira **qué lado tapas** | Es lo que sí se puede ver. Lo decimos en el tutorial y en el README |
| Con la mano doblada MediaPipe confunde qué dedo es cuál | Derecho tapado = la punta del pulgar cerca de la nariz. Izquierdo = **cualquier otro dedo** cerca | Lo vimos en el experimento con `herramientas/explorar_manos.py`. Así vale cualquier forma de colocar la mano |
| La mano tapa la cara y el modelo pierde la mano a ratos | Votar entre las **8 últimas fotos** y aguantar 0,6 s si se pierde | Un fallo suelto del modelo no cambia el veredicto |
| Un día con prisa | Vueltas de **1 a 9** en Ajustes. Con menos de 5 cuenta para la racha, no para subir | Así el reto no se abarata |

## Meditación

| Problema | Qué decidimos | Por qué |
|---|---|---|
| Qué comprobar | **Quieto, recto y ojos cerrados** | Solo quieto era demasiado fácil y no sabía si mirabas la pantalla. Así suma un tercer modelo |
| Sentado cerca no se ven las caderas | La espalda se mide por **la altura de la cabeza** sobre los hombros | Al encorvarte la cabeza baja |
| Cada cuerpo es distinto | **Calibrar tu postura recta** 3 s al empezar, con la mediana | Comparar con una postura ideal daba fallos falsos. La mediana aguanta una foto rara |
| Con los ojos cerrados no ves la pantalla | **Sonidos suaves**. Dos golpes si algo falla 3 s y una campana cada minuto | Descartamos solo pantalla (no te enteras) y voz (hay que instalar algo y suena menos a meditación) |
| Un parpadeo o un salto del modelo quitaban puntos | Un fallo solo cuenta si dura **más de 1 s** | Lo vimos en la primera prueba |
| Con gafas o poca luz a veces no ve los ojos cerrados | Si en 12 s no los ve, **sigue igual** | Mejor seguir que quedarse atascado |
| Cómo subir | Una **escalera de minutos** 5, 8, 12, 17, 23, 30 y 40, y después sin límite | Saltos pequeños al principio, que es cuando más cuesta |
| En el nivel sin límite no hay cuenta atrás | Se acaba con **Terminar** en la pausa | Es meditar lo que quieras |

## Estiramientos

| Problema | Qué decidimos | Por qué |
|---|---|---|
| Cómo estirar delante de la cámara | **Siete posturas sentado**, de 20 s cada una | Sentado y cerca la cámara solo ve de cintura para arriba. Descartamos contar repeticiones (fallan más) y de pie (el dedo ya no llega a los botones) |
| La primera versión se podía hacer a medias | Las posturas **como se hacen de verdad**. Cuello con la mano en la cabeza, brazo cruzado y tríceps | Lo pidió Rares al probarlo. Abajo sale lo que falta ("Pon la mano sobre la cabeza") |
| Faltaba estirar el brazo por detrás | Dos posturas de **tríceps** | Lo propuso Rares con una foto del estiramiento |
| En el brazo cruzado pedíamos sujetar el codo, pero la mano lo tapa | **Dejar de comprobarlo**, solo se pide | Con los CSV, sujetar daba de 0,04 a 1,2 y no sujetar de 0,7 a 0,85. Se solapan, así que la cámara no lo distingue |
| En el tríceps MediaPipe intercambia las muñecas | Reconocer el lado por **el brazo más doblado** | En los datos de la tecla D, el que estiras siempre está más doblado |
| Las líneas temblaban y la postura entraba y salía | **Suavizar los puntos** y 1 s de margen | Con las mismas sesiones guardadas, el tiempo fuera bajó del 26 % al 0 % |
| Subir de nivel no tenía sentido | **Los estiramientos no suben** | Son el calentamiento antes de las flexiones. Alargarlos no es un reto |

## Flexiones

| Problema | Qué decidimos | Por qué |
|---|---|---|
| La cámara tiene que verte entero | En el suelo, **de lado** y a unos 2 m | De frente no se ve si bajas ni si la cadera va recta |
| De lado un brazo tapa al otro | Medir **el brazo que mejor se ve** | MediaPipe da una confianza por cada punto |
| Un temblor del codo contaba dos flexiones | Bajar de un ángulo y **subir de otro distinto** | Con el mismo ángulo, un temblor justo en el límite contaba dos veces |
| Contaba una flexión mientras te tumbabas | **5 s para colocarse** y 2 s de plancha antes de contar | Nos pasó en la primera prueba |
| La plancha tardó 18 s en darse por buena y un salto contó una flexión que no existía | **Mediana de 5 fotos**, un fallo de menos de 0,3 s no reinicia y una flexión de menos de 0,4 s no cuenta | El ángulo del codo bailaba de 126° a 172° con los brazos estirados |
| Con los límites técnicos, quien empieza no sumaba casi ninguna | **Dos niveles**, fácil y técnico | Fácil 5, técnico 5 y técnico 10 |
| Desde el suelo no se ve la pantalla | Un **tono** por cada flexión buena y dos golpes si sale mal | Igual que en la meditación |
| Nos pusimos de frente en vez de de perfil | Una pantalla antes de empezar con **una silueta de perfil** sobre la cámara | Se entiende sin leer |

## Gestos y manejo

| Problema | Qué decidimos | Por qué |
|---|---|---|
| Se medita y se estira lejos del teclado | **Manejar los menús con el dedo** | Es interacción natural, que es de lo que va la asignatura. Descartamos el pellizco (desde lejos confunde los dedos) y contar dedos (hay que aprenderse los gestos) |
| Delante del profesor costaba atinar a los botones | Un **imán** que resalta el botón y 1,5 s quieto lo pulsa | No hace falta precisión. Fueron cuatro intentos hasta llegar aquí |
| Señalar un hueco pulsaba el botón más cercano | **Imán corto**, solo encima del botón o a menos de 28 px | Lo vimos en las capturas de Rares |
| Estando quieto se pulsaban cosas solas | Solo cuenta **el gesto de señalar**, y para volver a pulsar hay que soltar | Una mano relajada no señala |
| Al señalar hacia la cámara el dedo se ve corto | Mirar la mano con los **puntos 3D** | En 2D no lo reconocía y en 3D sí |
| Con la mano apoyada en la cabeza se pulsaban botones | Señalar solo cuenta **hacia la pantalla o hacia arriba** | Esa mano tiene la forma de señalar, pero no la dirección |
| La palma pausaba al bajar la mano o al estirar | La palma tiene que estar **de frente, quieta y lejos de la nariz**. En los estiramientos solo pausa entre postura y postura | Una mano que pide pausa está quieta. Una que baja, no |
| Seguir desde la pausa saltaba solo | **Palma abierta y luego puño** | Un gesto en dos tiempos no se hace sin querer, y se ve en qué paso vas |
| De cerca hay que poder usarlo como cualquier programa | **Teclado y ratón** a la vez que el dedo | Flechas y Enter, clic, y atajos como R, E, I y X |

## Juego y niveles

| Problema | Qué decidimos | Por qué |
|---|---|---|
| Cómo puntuar | De **0 a 3 lotos** por el porcentaje bien hecho, con los cortes 40, 65 y 85 % | Lotos en vez de puntos, que va con la calma del juego |
| Había unas seis reglas distintas para subir | **Una sola regla**. 5 días con 3 lotos en tu nivel más alto | Se explica en una frase. Es la heurística de consistencia de Nielsen |
| Un día flojo | Se puede **bajar de nivel**, pero así no se sube. Nunca se pierde un nivel | Mantener la racha sin abaratar el reto |
| Probar sin estropear el progreso | Las sesiones con `--rapido`, `--minutos` y demás **no cuentan para subir** | Se puede enseñar el juego sin hacer trampa |

## Interfaz y diseño

| Problema | Qué decidimos | Por qué |
|---|---|---|
| Las ventanas de OpenCV son pobres | Interfaz en **Pygame** | Botones, letras y animaciones cuidadas |
| El inicio tenía once cosas a la vez | **Menú por pantallas**, como en un videojuego | Una cosa en cada pantalla. Es la heurística de diseño minimalista |
| El juego entero en un botón | **Ritual de hoy** encadena las cuatro fases | Se entiende solo |
| Los textos se pisaban | Cada texto en un **hueco fijo** que se encoge si no cabe | Un test recorre todos los textos y falla si alguno se pisa |
| "Lo que más te ha costado, abrir los ojos" se entendía al revés | Decir **qué hacer**, no qué fallaste | "Para mejorar, mantén los ojos cerrados" |
| El violeta no recordaba a un templo y a 1-2 m no se leía | Fondo de **piedra** y letra más grande en las sesiones | Lo vimos al probar las flexiones |
| No necesitar archivos de audio | Sonidos **generados con numpy** | Menos archivos y sin licencias |

## Código, tests e instalación

| Problema | Qué decidimos | Por qué |
|---|---|---|
| `app.py` había llegado a 1.300 líneas con las fases mezcladas | **Una clase por fase** con las mismas funciones | Los estiramientos y las flexiones entraron sin tocar lo demás |
| Comprobar que la reorganización no cambiaba nada | **385 capturas** antes y después | Salieron idénticas píxel a píxel |
| Probar sin cámara | El cerebro **no importa Pygame ni OpenCV**, y la app recibe la cámara y la carpeta de datos al crearse | Así los tests usan una cámara falsa y no tocan tu progreso |
| Que funcione en un equipo limpio | **`instalar.sh`** con Conda y conda-forge, versiones fijadas y modelos con su huella sha256 | MediaPipe 0.10.21 necesita Python 3.12. conda-forge no pide aceptar condiciones |
| Que no se rompa nada en cada cambio | **GitHub Actions** pasa los tests e instala desde cero en Ubuntu y Mac | Es lo más parecido al equipo limpio que pide la entrega |
| Ajustar los límites a ojo fallaba | Cada sesión guarda **un CSV** con lo que mide la cámara, y la tecla **D** lo enseña en directo | Casi todos los arreglos de los umbrales salieron de esos números |
| Que la documentación no se quede atrás | Un test que comprueba que **cada archivo sale en la guía** y que **cada función tiene su explicación** | Igual que los tests cubren el código, este cubre la documentación |

## Forma de trabajar

| Qué decidimos | Por qué |
|---|---|
| Código en un **repositorio compartido** entre el Ubuntu de Rares y el Mac de Nikolas | El profesor lo vio bien. Probarlo en los dos sistemas sacó fallos que en uno solo no salían |
| **Nada entra sin probarlo con la cámara** | Una primera versión de la meditación pasaba todos los tests y la borramos porque no la habíamos probado de verdad |
| Las decisiones se explican **en el repositorio** con su porqué | Lo preguntamos al profesor y le pareció bien. No hay memoria aparte |
