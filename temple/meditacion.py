"""Logica de la meditacion, sin camara ni ventanas.

Se medita sentado, quieto, con la espalda recta y los ojos cerrados. La camara
solo ve de la cabeza al pecho, asi que la espalda se mide por la cabeza. Al
empezar se calibra la postura recta (lo alta que queda la nariz sobre la linea
de los hombros) y despues se compara con ella.

  - quieto  la nariz apenas se mueve en el ultimo segundo y medio
  - recto   la cabeza no baja de ENCORVADO veces su altura calibrada y los
            hombros no se inclinan a un lado mas que en la postura calibrada
            (nadie tiene los hombros perfectamente a nivel)
  - ojos    el modelo de cara (Face Landmarker) dice que estan cerrados

Un fallo solo cuenta si dura al menos TOLERANCIA_S, para que un parpadeo o un
salto del modelo no quiten puntos. Si dura AVISO_S suena un aviso suave, porque
con los ojos cerrados no se ve la pantalla.

Como en la respiracion, todo es un guion de pasos.
  - mensaje   ensena un texto unos segundos (y puede sonar algo al empezar)
  - esperar   no avanza hasta que la camara ve lo que se pide un momento seguido
  - calibrar  mide la postura recta unos segundos
  - meditar   el tiempo de meditacion, con una campana cada minuto. Con
              duracion 0 es el modo libre, sin cuenta atras, que acaba cuando
              el jugador elige Terminar (campana cada CAMPANA_LIBRE_MIN minutos)
Las distancias van en anchos de hombros, para que no importe lo lejos que estes.
"""

from __future__ import annotations

import csv
from collections import deque
from dataclasses import dataclass, field
from pathlib import Path

ENCORVADO = 0.85  # la cabeza por debajo de esta parte de su altura recta
INCLINADO = 0.15  # cuanto mas se inclinan los hombros que en la postura calibrada
MOVIDO = 0.10  # recorrido de la nariz en VENTANA_S
# Parpadeo medio del modelo de cara (0 abiertos, 1 cerrados). Con Rares (18/11)
# abiertos daba 0,15-0,25 y cerrados 0,6-0,77, asi que el corte va en medio
OJOS_CERRADOS = 0.4
VENTANA_S = 1.5
SUAVE_S = 0.2  # suavizado de la nariz contra el temblor del modelo
TOLERANCIA_S = 1.0
AVISO_S = 3.0
REPETIR_AVISO_S = 10.0
SOSTENER_S = 0.8
CALIBRAR_S = 3.0
ESPERA_OJOS_S = 12.0  # si no ve los ojos cerrados (gafas, poca luz), sigue igual
CAMPANA_LIBRE_MIN = 5  # en el modo libre la campana suena cada 5 minutos
PALMA_MEDITAR_S = 1.5  # la palma para pausar al meditar, algo mas larga
SEGUIR_OJOS_S = 2.0  # en la pausa, cerrar los ojos este rato sigue meditando
REGISTRO = Path(__file__).resolve().parent.parent / "datos" / "ultima_meditacion.csv"
REGISTRO_CADA_S = 0.25

CRITERIOS = ("quieto", "recto", "ojos")


@dataclass(frozen=True)
class Cuerpo:
    """Lo que hace falta de un fotograma, en coordenadas normalizadas de 0 a 1."""

    nariz: tuple[float, float]
    hombro_a: tuple[float, float]
    hombro_b: tuple[float, float]
    ojos: float | None = None  # 0 abiertos, 1 cerrados, None si no se ve la cara

    @property
    def escala(self) -> float:
        dx = self.hombro_a[0] - self.hombro_b[0]
        dy = self.hombro_a[1] - self.hombro_b[1]
        return (dx * dx + dy * dy) ** 0.5

    @property
    def centro_hombros(self) -> tuple[float, float]:
        return ((self.hombro_a[0] + self.hombro_b[0]) / 2,
                (self.hombro_a[1] + self.hombro_b[1]) / 2)


@dataclass
class Medida:
    """Como estas ahora mismo. None en un criterio es que no se puede saber."""

    cuerpo: bool
    quieto: bool | None = None
    recto: bool | None = None
    ojos: bool | None = None
    movimiento: float | None = None  # recorrido de la nariz, en anchos de hombros
    altura: float | None = None  # altura de la cabeza, 1 = la de la calibracion
    inclinacion: float | None = None
    parpadeo: float | None = None

    def bien(self, criterio: str) -> bool | None:
        return getattr(self, criterio)


class Evaluador:
    """Guarda la postura recta calibrada y mide cada fotograma contra ella."""

    def __init__(self):
        self.base_altura: float | None = None
        self.base_escala: float | None = None
        self.base_inclinacion = 0.0
        self._muestras: list[tuple[float, float, float]] = []
        self._suave: tuple[float, float] | None = None
        self._t: float | None = None
        self._ventana: deque[tuple[float, float, float]] = deque()

    @property
    def calibrado(self) -> bool:
        return self.base_altura is not None

    # ---- calibracion ----

    def muestra_calibracion(self, c: Cuerpo) -> None:
        if c.escala > 1e-3:
            self._muestras.append((c.centro_hombros[1] - c.nariz[1], c.escala,
                                   (c.hombro_a[1] - c.hombro_b[1]) / c.escala))

    def cancelar_calibracion(self) -> None:
        self._muestras.clear()

    def fijar_calibracion(self) -> bool:
        if not self._muestras:
            return False
        alturas = sorted(m[0] for m in self._muestras)
        escalas = sorted(m[1] for m in self._muestras)
        inclinaciones = sorted(m[2] for m in self._muestras)
        self.base_inclinacion = inclinaciones[len(inclinaciones) // 2]
        # La mediana aguanta mejor un fotograma raro que la media
        self.base_escala = escalas[len(escalas) // 2]
        self.base_altura = alturas[len(alturas) // 2] / self.base_escala
        self._muestras.clear()
        return self.base_altura > 0

    # ---- medida ----

    def medir(self, t: float, c: Cuerpo | None) -> Medida:
        if c is None or c.escala < 1e-3:
            self._suave, self._t = None, None
            self._ventana.clear()
            return Medida(cuerpo=False)

        # Nariz suavizada y su recorrido en la ventana
        if self._suave is None or self._t is None:
            self._suave = c.nariz
        else:
            dt = max(t - self._t, 0.0)
            k = min(1.0, dt / SUAVE_S) if SUAVE_S > 0 else 1.0
            self._suave = (self._suave[0] + (c.nariz[0] - self._suave[0]) * k,
                           self._suave[1] + (c.nariz[1] - self._suave[1]) * k)
        self._t = t
        self._ventana.append((t, *self._suave))
        while self._ventana and t - self._ventana[0][0] > VENTANA_S:
            self._ventana.popleft()
        xs = [x for _, x, _ in self._ventana]
        ys = [y for _, _, y in self._ventana]
        escala = self.base_escala or c.escala
        movimiento = max(max(xs) - min(xs), max(ys) - min(ys)) / escala
        # Hasta llenar media ventana no se sabe si estas quieto
        lleno = t - self._ventana[0][0] >= VENTANA_S / 2
        quieto = (movimiento < MOVIDO) if lleno else None

        inclinacion = abs((c.hombro_a[1] - c.hombro_b[1]) / escala - self.base_inclinacion)
        altura = recto = None
        if self.calibrado:
            # Con la escala calibrada, porque al encorvarte los hombros se
            # cierran y parecen mas estrechos
            altura = (c.centro_hombros[1] - c.nariz[1]) / self.base_escala / self.base_altura
            recto = altura >= ENCORVADO and inclinacion < INCLINADO

        ojos = None if c.ojos is None else c.ojos >= OJOS_CERRADOS
        return Medida(True, quieto, recto, ojos, movimiento, altura, inclinacion, c.ojos)


# ================= guion =================


@dataclass(frozen=True)
class Paso:
    tipo: str  # mensaje, esperar, calibrar, meditar
    texto: str
    detalle: str = ""
    objetivo: str | None = None  # esperar: cuerpo, ojos, encorvado, recto, movido, quieto
    duracion: float = 0.0  # mensaje, calibrar y meditar
    sonido: str | None = None  # suena al empezar el paso
    espera_max: float | None = None  # esperar: pasado este rato sigue igual


def guion_sesion(minutos: float) -> list[Paso]:
    """minutos 0 es el modo libre."""
    return [
        Paso("esperar", "Siéntate recto", "Espalda recta y hombros relajados",
             objetivo="cuerpo"),
        Paso("calibrar", "Quédate así", "Estoy midiendo tu postura", duracion=CALIBRAR_S),
        Paso("esperar", "Cierra los ojos", "Empezamos cuando los cierres", objetivo="ojos",
             espera_max=ESPERA_OJOS_S),
        Paso("meditar", "Respira tranquilo",
             "Si te mueves o te encorvas, oirás un aviso" if minutos
             else "Para terminar, abre la mano por encima de los hombros",
             duracion=minutos * 60),
        Paso("mensaje", "Abre los ojos despacio", "Has terminado", duracion=6),
    ]


def guion_tutorial() -> list[Paso]:
    return [
        Paso("mensaje", "Meditación", "Quieto, recto y con los ojos cerrados", duracion=5),
        Paso("esperar", "Siéntate recto", "Que se te vean la cabeza y los hombros",
             objetivo="cuerpo"),
        Paso("calibrar", "Quédate así", "Así sé cómo es tu espalda recta", duracion=CALIBRAR_S),
        Paso("esperar", "Ahora encórvate", "Deja caer la cabeza y los hombros",
             objetivo="encorvado"),
        Paso("esperar", "Vuelve a ponerte recto", "Como antes", objetivo="recto"),
        Paso("esperar", "Mueve la cabeza", "De un lado a otro", objetivo="movido"),
        Paso("esperar", "Ahora quieto", "Sin moverte", objetivo="quieto"),
        Paso("mensaje", "Si te mueves", "o te encorvas, oirás este aviso", duracion=4,
             sonido="aviso"),
        Paso("mensaje", "Cada minuto", "sonará esta campana", duracion=5, sonido="campana"),
        Paso("mensaje", "Para parar", "abre la mano por encima de los hombros", duracion=5),
        Paso("esperar", "Cierra los ojos", "Cuando suene la campanita, ábrelos",
             objetivo="ojos", espera_max=ESPERA_OJOS_S),
        Paso("mensaje", "Gana lotos", "Hasta tres, cuanto más rato lo hagas bien", duracion=5),
        Paso("mensaje", "Tu meta", "5 días con 3 lotos te suben de nivel",
             duracion=6),
    ]


def _cumple(objetivo: str, m: Medida) -> bool:
    if not m.cuerpo:
        return False
    return {
        "cuerpo": True,
        "ojos": m.ojos is True,
        "encorvado": m.recto is False,
        "recto": m.recto is True,
        "movido": m.quieto is False,
        "quieto": m.quieto is True,
    }[objetivo]


@dataclass
class Estado:
    """Lo que la interfaz necesita pintar en un instante."""

    paso: Paso
    indice: int
    total: int
    hecho: float  # 0 a 1, lo que llevas del paso
    medida: Medida
    faltas: frozenset[str]  # criterios que ahora mismo cuentan como fallo
    restante_s: float = 0.0  # meditar
    transcurrido_s: float = 0.0  # meditar
    aviso: str | None = None  # suena el aviso en este instante (el criterio que falla)
    minuto: bool = False  # suena la campana del minuto en este instante
    nuevo_paso: bool = False
    terminado: bool = False


@dataclass
class Practica:
    pasos: list[Paso]
    evaluador: Evaluador = field(default_factory=Evaluador)
    sostener_s: float = SOSTENER_S
    _indice: int = 0
    _inicio: float | None = None
    _sosteniendo: float | None = None
    _t: float | None = None
    _mal_desde: dict[str, float] = field(default_factory=dict)
    _aviso_en: float | None = None
    _anunciado: int = -1
    bien_s: float = 0.0
    meditado_s: float = 0.0
    contado_s: float = 0.0
    mal_s: dict[str, float] = field(default_factory=lambda: {c: 0.0 for c in CRITERIOS})

    @property
    def libre(self) -> bool:
        return any(p.tipo == "meditar" and p.duracion == 0 for p in self.pasos)

    @property
    def minutos(self) -> float:
        """Los minutos de la sesion. En el modo libre, los que llevas meditados."""
        if self.libre:
            return self.meditado_s / 60
        return sum(p.duracion for p in self.pasos if p.tipo == "meditar") / 60

    def terminar(self, t: float) -> None:
        """Acaba el modo libre y pasa al mensaje final."""
        if self._indice < len(self.pasos) and self.pasos[self._indice].tipo == "meditar":
            self._avanzar(t)

    @property
    def precision(self) -> float:
        return self.bien_s / self.contado_s if self.contado_s else 0.0

    def _avanzar(self, t: float) -> None:
        self._indice += 1
        self._inicio = t
        self._sosteniendo = None
        self._mal_desde.clear()
        self._aviso_en = None

    def _faltas(self, t: float, m: Medida) -> frozenset[str]:
        """Criterios que fallan desde hace al menos TOLERANCIA_S."""
        faltas = set()
        for c in CRITERIOS:
            if m.bien(c) is False:
                self._mal_desde.setdefault(c, t)
                if t - self._mal_desde[c] >= TOLERANCIA_S:
                    faltas.add(c)
            else:
                self._mal_desde.pop(c, None)
        return frozenset(faltas)

    def actualizar(self, t: float, cuerpo: Cuerpo | None) -> Estado:
        if self._inicio is None:
            self._inicio = t
        dt = 0.0 if self._t is None else max(t - self._t, 0.0)
        self._t = t
        m = self.evaluador.medir(t, cuerpo)
        if self._indice >= len(self.pasos):
            return Estado(self.pasos[-1], len(self.pasos), len(self.pasos), 1.0, m,
                          frozenset(), terminado=True)
        nuevo = self._anunciado != self._indice
        self._anunciado = indice = self._indice
        paso = self.pasos[indice]
        transcurrido = t - self._inicio
        faltas = self._faltas(t, m) if self.evaluador.calibrado else frozenset()

        def estado(hecho, **extra):
            return Estado(paso, indice, len(self.pasos), hecho, m, faltas,
                          nuevo_paso=nuevo, **extra)

        if paso.tipo == "mensaje":
            hecho = min(transcurrido / paso.duracion, 1.0) if paso.duracion else 1.0
            if transcurrido >= paso.duracion:
                self._avanzar(t)
            return estado(hecho)

        if paso.tipo == "esperar":
            if _cumple(paso.objetivo, m):
                if self._sosteniendo is None:
                    self._sosteniendo = t
                hecho = min((t - self._sosteniendo) / self.sostener_s, 1.0) \
                    if self.sostener_s > 0 else 1.0
            else:
                self._sosteniendo = None
                hecho = 0.0
            if hecho >= 1.0 or (paso.espera_max is not None and transcurrido >= paso.espera_max):
                self._avanzar(t)
            return estado(hecho)

        if paso.tipo == "calibrar":
            if not m.cuerpo:
                # Si te vas, se vuelve a empezar la medida
                self.evaluador.cancelar_calibracion()
                self._inicio = t
                return estado(0.0)
            self.evaluador.muestra_calibracion(cuerpo)
            hecho = min(transcurrido / paso.duracion, 1.0)
            if transcurrido >= paso.duracion and self.evaluador.fijar_calibracion():
                self._avanzar(t)
            return estado(hecho)

        # meditar
        aviso = None
        minuto = False
        if m.cuerpo and dt > 0:
            self.contado_s += dt
            if faltas:
                for c in faltas:
                    self.mal_s[c] += dt
            else:
                self.bien_s += dt
        # Aviso si un fallo dura AVISO_S, y se repite cada REPETIR_AVISO_S
        largos = [c for c, desde in self._mal_desde.items() if t - desde >= AVISO_S]
        if largos:
            if self._aviso_en is None or t - self._aviso_en >= REPETIR_AVISO_S:
                self._aviso_en = t
                aviso = min(largos, key=lambda c: self._mal_desde[c])
        else:
            self._aviso_en = None
        self.meditado_s = transcurrido
        antes = max(transcurrido - dt, 0)
        cada = 60 * (CAMPANA_LIBRE_MIN if paso.duracion == 0 else 1)
        if int(transcurrido // cada) > int(antes // cada) and (
                paso.duracion == 0 or transcurrido < paso.duracion):
            minuto = True
        if paso.duracion == 0:  # libre, el aro da una vuelta cada 5 minutos
            return estado((transcurrido % cada) / cada, transcurrido_s=transcurrido,
                          aviso=aviso, minuto=minuto)
        hecho = min(transcurrido / paso.duracion, 1.0)
        restante = max(paso.duracion - transcurrido, 0.0)
        if transcurrido >= paso.duracion:
            self._avanzar(t)
        return estado(hecho, restante_s=restante, transcurrido_s=transcurrido,
                      aviso=aviso, minuto=minuto)


def lotos(precision: float) -> int:
    """De 0 a 3 lotos, con los mismos cortes que la respiracion."""
    if precision >= 0.85:
        return 3
    if precision >= 0.65:
        return 2
    if precision >= 0.40:
        return 1
    return 0


class Registro:
    """Apunta en un CSV lo que mide la camara, para ajustar los umbrales sin capturas.

    Se reescribe en cada meditacion (datos/ultima_meditacion.csv). Cada fila es
    un instante con el paso del guion, asi se sabe que estabas haciendo (por
    ejemplo, en el tutorial, cuando te pide que te encorves).
    """

    CAMPOS = ("t", "paso", "objetivo", "cuerpo", "movimiento", "altura", "inclinacion",
              "ojos", "faltas")

    def __init__(self, ruta: Path = REGISTRO):
        self._ultimo = -REGISTRO_CADA_S
        try:
            ruta.parent.mkdir(parents=True, exist_ok=True)
            self._archivo = open(ruta, "w", newline="", encoding="utf-8")
            self._csv = csv.writer(self._archivo)
            self._csv.writerow(self.CAMPOS)
        except OSError:
            self._archivo = None  # sin registro, el juego sigue

    def apuntar(self, t: float, e: Estado) -> None:
        if self._archivo is None or t - self._ultimo < REGISTRO_CADA_S:
            return
        self._ultimo = t
        m = e.medida

        def r(v):
            return "" if v is None else f"{v:.3f}"

        self._csv.writerow([f"{t:.2f}", e.paso.tipo, e.paso.objetivo or e.paso.texto,
                            int(m.cuerpo), r(m.movimiento), r(m.altura), r(m.inclinacion),
                            r(m.parpadeo), " ".join(sorted(e.faltas))])

    def cerrar(self) -> None:
        if self._archivo is not None:
            self._archivo.close()
            self._archivo = None
