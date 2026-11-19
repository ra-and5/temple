"""Manejar los menus con el dedo, sin teclado ni raton.

  - Puntero      solo cuenta si se SENALA (indice estirado, los demas dedos
                 cerrados y el indice hacia la pantalla o hacia arriba), asi
                 la mano relajada o apoyada en la cabeza no pulsa nada. La punta del
                 indice mueve un cursor por el panel y un iman resalta el boton
                 si esta encima o casi (IMAN px). ESPERA_S segundos senalando
                 el mismo boton lo pulsa. Para volver a pulsar hay que dejar de
                 senalar un momento, y al cambiar de pantalla igual, para que
                 nada se pulse solo (por ejemplo con la mano aun en la nariz).
                 Los botones repetibles (menos y mas) no piden soltar, y seguir
                 senalando vuelve a pulsar cada REPETIR_S segundos.
  - GestoPalma   la palma abierta, de frente a la camara, quieta y lejos de la
                 nariz durante PALMA_S segundos pausa. De frente quiere decir
                 que la mano se ve ancha (de nudillo a nudillo) y quieta que
                 no se mueve mientras se llena el aro, asi una mano que baja o
                 pasa por delante no pausa (le paso a Rares al meditar, 19/11).
                 Lejos de la nariz para no confundirlo con la mano que esta
                 tapando. Al meditar ademas tiene que estar por encima de los
                 hombros (techo), porque las manos en el regazo pueden parecer
                 una palma abierta. En los estiramientos no se usa.

Las manos llegan como 21 puntos (x, y) normalizados de 0 a 1 sobre la imagen
ya en espejo, igual que la pantalla. Los botones son rectangulos (x, y, ancho,
alto) en pixeles. No depende de Pygame, para poder probarlo sin ventana.
"""

from __future__ import annotations

import math

INDICE, MUNECA, CENTRO_PALMA = 8, 0, 9
NUDILLO_INDICE, NUDILLO_MENIQUE = 5, 17
PUNTAS_Y_NUDILLOS = ((8, 6), (12, 10), (16, 14), (20, 18))

# Esta parte de la camara cubre todo el panel de botones, para llegar a todo
# sin estirar el brazo. La mano derecha cae sola en la parte derecha.
ZONA_X = (0.25, 0.90)
ZONA_Y = (0.20, 0.80)
ESPERA_S = 1.5  # tiempo senalando el mismo boton para pulsarlo
IMAN = 28  # pixeles alrededor de un boton que todavia cuentan como encima
SOLTAR_S = 0.25  # sin senalar este rato cuenta como soltar (aguanta parpadeos del modelo)
PALMA_S = 1.0  # tiempo con la palma abierta para pausar
DE_FRENTE = 0.6  # ancho de la palma partido por su largo. De lado se ve estrecha
VISIBLE_LARGO = 0.4  # si el indice se ve mas corto que esto de la palma, apunta a la camara
ARRIBA = 0.5  # el indice apunta arriba si sube mas que esto de su largo (unos 30 grados)
QUIETA = 0.35  # lo que puede moverse el centro de la palma, en largos de palma
REPETIR_S = 0.8  # menos y mas, cada cuanto se repite si sigues senalando
PERDIDA_S = 0.4  # si no se ve la mano este rato, el cursor desaparece
SUAVIDAD = 14.0  # cuanto mas alto, antes alcanza el cursor al dedo
LEJOS_NARIZ = 0.6  # en anchos de hombros
REPOSO = 0.06  # el dedo por debajo de la zona esto o mas es la mano en reposo


def _dist(a, b) -> float:
    return math.dist(a, b)  # vale para puntos en 2D y en 3D


def a_area(punto, area, zona_x=ZONA_X, zona_y=ZONA_Y) -> tuple[float, float]:
    """Pasa un punto de la camara (0 a 1) a pixeles dentro del area (x, y, ancho, alto)."""
    fx = (punto[0] - zona_x[0]) / (zona_x[1] - zona_x[0])
    fy = (punto[1] - zona_y[0]) / (zona_y[1] - zona_y[0])
    fx, fy = min(max(fx, 0.0), 1.0), min(max(fy, 0.0), 1.0)
    return area[0] + fx * area[2], area[1] + fy * area[3]


def distancia_a_rect(rect, pos) -> float:
    """0 si el punto esta dentro, y si no, lo que le falta para llegar al borde."""
    x, y, w, h = rect[0], rect[1], rect[2], rect[3]
    dx = max(x - pos[0], 0, pos[0] - (x + w))
    dy = max(y - pos[1], 0, pos[1] - (y + h))
    return math.hypot(dx, dy)


def senalando(mano) -> bool:
    """Indice estirado y al menos dos de los otros tres dedos cerrados.

    Mejor con los puntos en 3D, porque al senalar hacia la camara el indice
    se ve corto en la imagen aunque este estirado.
    """
    m = mano[MUNECA]
    indice = _dist(mano[8], m) > 1.1 * _dist(mano[6], m)
    cerrados = sum(_dist(mano[t], m) < _dist(mano[n], m) for t, n in PUNTAS_Y_NUDILLOS[1:])
    return indice and cerrados >= 2


def apunta_a_pantalla(mano) -> bool:
    """El indice apunta a la camara (se ve corto en la imagen) o hacia arriba.

    Para mover algo en la pantalla el dedo va hacia ella o hacia arriba. De lado
    o hacia abajo es la mano apoyada, por ejemplo en la cabeza con los dedos
    caidos o tumbados (le paso a Rares el 19/11).
    """
    dx = mano[INDICE][0] - mano[NUDILLO_INDICE][0]
    dy = mano[INDICE][1] - mano[NUDILLO_INDICE][1]  # y crece hacia abajo
    largo = math.hypot(dx, dy)
    # Hacia la camara el dedo se ve tan corto que su direccion es ruido
    if largo < VISIBLE_LARGO * largo_palma(mano):
        return True
    return -dy > ARRIBA * largo


def senala(mano, mano_3d=None) -> bool:
    """El gesto de senalar (en 3D si se tiene) con el dedo hacia la pantalla o arriba."""
    return senalando(mano_3d or mano) and apunta_a_pantalla(mano)


def palma_abierta(mano) -> bool:
    """Los cuatro dedos estirados, cada punta mas lejos de la muneca que su nudillo."""
    m = mano[MUNECA]
    return all(_dist(mano[t], m) > 1.15 * _dist(mano[n], m) for t, n in PUNTAS_Y_NUDILLOS)


def largo_palma(mano) -> float:
    return _dist(mano[MUNECA], mano[CENTRO_PALMA])


def de_frente(mano) -> bool:
    """La palma se ve ancha, o sea que mira a la camara y no esta de lado."""
    largo = largo_palma(mano)
    return largo > 1e-6 and _dist(mano[NUDILLO_INDICE], mano[NUDILLO_MENIQUE]) / largo >= DE_FRENTE


class Puntero:
    def __init__(self, area, espera_s: float = ESPERA_S):
        self.area = tuple(area)  # (x, y, ancho, alto) de la pantalla que cubre la mano
        self.espera_s = espera_s
        self.pos: tuple[float, float] | None = None
        self.senala = False  # si ahora mismo se esta senalando
        self.objetivo: int | None = None  # boton resaltado por el iman
        self.llenado = 0.0  # de 0 a 1, lo que lleva en ese boton
        self._listo = False  # se ha soltado desde la ultima pulsacion o cambio de pantalla
        self._clave = None
        self._sin_mano = 0.0
        self._sin_senalar = 0.0

    def ocultar(self) -> None:
        self.pos = None
        self.senala = False
        self.objetivo = None
        self.llenado = 0.0
        self._listo = False
        self._clave = None

    def _soltar(self) -> None:
        self.senala = False
        self.objetivo = None
        self.llenado = 0.0
        self._clave = None
        self._listo = True

    def actualizar(self, dt: float, mano, botones, mano_3d=None,
                   repetibles=frozenset()) -> int | None:
        """Mueve el cursor. Devuelve el indice del boton pulsado, o None.

        botones son las zonas que se pueden pulsar. mano_3d, si llega, se usa
        para reconocer el gesto de senalar. repetibles son los indices de los
        botones que se repiten sin soltar.
        """
        # Mano apoyada abajo (en la mesa o las piernas), no se esta apuntando.
        # Si senala si cuenta, aunque este muy abajo, porque sentado cerca de la
        # camara el dedo cae ahi al apuntar a los botones de abajo
        if (mano is not None and mano[INDICE][1] > ZONA_Y[1] + REPOSO
                and not senala(mano, mano_3d)):
            mano = None
            self._sin_mano = PERDIDA_S
        if mano is None:
            self._sin_mano += dt
            if self._sin_mano > PERDIDA_S:
                self.ocultar()
                self._listo = True  # quitar la mano tambien es soltar
            return None
        self._sin_mano = 0.0

        destino = a_area(mano[INDICE], self.area)
        if self.pos is None:
            self.pos = destino
        else:
            k = 1 - math.exp(-SUAVIDAD * dt)  # suavizado que no depende de los FPS
            self.pos = (self.pos[0] + (destino[0] - self.pos[0]) * k,
                        self.pos[1] + (destino[1] - self.pos[1]) * k)

        if not senala(mano, mano_3d):
            self._sin_senalar += dt
            if self._sin_senalar >= SOLTAR_S:
                self._soltar()
            return None  # un parpadeo corto no borra lo que llevaba
        self._sin_senalar = 0.0
        self.senala = True

        # Iman corto, el boton mas cercano si esta encima o casi. En un hueco, nada
        cerca = [(distancia_a_rect(r, self.pos), j) for j, r in enumerate(botones)]
        d, i = min(cerca, default=(math.inf, None))
        if d > IMAN:
            self.objetivo, self.llenado, self._clave = None, 0.0, None
            return None
        self.objetivo = i
        if not self._listo:
            return None

        clave = tuple(botones[i][:4])
        if clave != self._clave:
            self._clave, self.llenado = clave, 0.0
        self.llenado += dt / self.espera_s
        if self.llenado >= 1:
            if i in repetibles:
                # Se queda en el boton y vuelve a pulsar en REPETIR_S
                self.llenado = 1 - REPETIR_S / self.espera_s
                return i
            self.llenado, self._clave = 0.0, None
            self._listo = False  # hay que soltar antes de la siguiente
            return i
        return None


class GestoPalma:
    def __init__(self, segundos: float = PALMA_S):
        self.segundos = segundos
        self.llenado = 0.0
        self._armado = True
        self._desde: tuple[float, float] | None = None  # donde empezo a llenarse

    def actualizar(self, dt: float, mano, nariz=None, escala=None, techo=None) -> bool:
        """True en el momento en que se completa el gesto.

        techo, si llega, es la altura (y de 0 a 1) por encima de la que tiene
        que estar el centro de la palma.
        """
        abierta = mano is not None and palma_abierta(mano) and de_frente(mano)
        if abierta and nariz is not None and escala:
            abierta = _dist(mano[CENTRO_PALMA], nariz) / escala > LEJOS_NARIZ
        if abierta and techo is not None:
            abierta = mano[CENTRO_PALMA][1] < techo
        if not abierta:
            self.llenado = 0.0
            self._armado = True
            self._desde = None
            return False
        if not self._armado:
            return False
        # Si la mano se mueve, se vuelve a empezar desde donde esta ahora
        centro = mano[CENTRO_PALMA]
        if self._desde is None or _dist(centro, self._desde) > QUIETA * largo_palma(mano):
            self._desde = centro
            self.llenado = 0.0
        self.llenado += dt / self.segundos
        if self.llenado >= 1:
            self.llenado = 0.0
            self._armado = False  # hay que cerrar la mano antes de repetirlo
            return True
        return False
