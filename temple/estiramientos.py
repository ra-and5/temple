"""Logica de los estiramientos, sin camara ni ventanas.

Siete posturas sentado, de cuello, hombros y brazos, que se mantienen un rato cada una.
La camara solo ve de la cabeza al pecho, asi que todo se mide con Pose.

  - cuello_der   la cabeza inclinada hacia el hombro derecho, con la mano
                 derecha sobre la cabeza (la muneca por encima de la nariz)
  - cuello_izq   lo mismo hacia el izquierdo
  - arriba       los dos brazos arriba, con los codos por encima de la nariz
  - cruzado_der  el brazo derecho cruzado por delante del pecho, con la muneca
                 pasada al otro lado del cuerpo y la otra mano sujetando el codo
  - cruzado_izq  lo mismo con el izquierdo
  - triceps_der  el codo derecho por encima de la cabeza y el brazo doblado (la
                 muneca por debajo del codo, la mano a la espalda), con la otra
                 mano sujetando el codo
  - triceps_izq  lo mismo con el izquierdo
  - neutro       cabeza recta y brazos abajo, para volver entre postura y postura

La imagen va en espejo, asi que tu derecha sale a la derecha de la pantalla.
No se usan las etiquetas izquierda y derecha de MediaPipe (con el espejo se
cruzan). El brazo derecho es el que cuelga del hombro que sale mas a la
derecha, y la oreja derecha la que sale mas a la derecha.

La inclinacion de la cabeza es el angulo de la linea entre las orejas menos el
de la linea de los hombros, asi da igual que la camara este algo torcida.
Las distancias van en anchos de hombros, para que no importe lo lejos que estes.
Las munecas se usan aunque MediaPipe no este seguro de verlas (la del brazo
cruzado se sale de la imagen y la que sujeta queda tapada por el brazo). Su
posicion la estima por el resto del brazo y se acerca bastante.

Como en la meditacion, todo es un guion de pasos.
  - mensaje   ensena un texto unos segundos
  - esperar   no avanza hasta que la camara ve lo que se pide un momento seguido
  - mantener  la cuenta de la postura, que solo avanza mientras estas en ella.
              Salirte menos de TOLERANCIA_S no cuenta (un salto del modelo).
              Si en MAX_VECES su duracion no la has completado, sigue igual
"""

from __future__ import annotations

import csv
import math
from dataclasses import dataclass, field
from pathlib import Path

INCLINAR_GRADOS = 20.0  # cabeza inclinada a un lado
RECTA_GRADOS = 10.0  # cabeza recta para volver al centro
CRUZAR = 0.35  # la muneca pasa del centro del pecho al otro lado (en anchos de hombros)
# Con Rares (19/11) la mano sobre la cabeza daba 0,6-0,7 y bajada -2. Sujetando
# el codo 0,33-0,5 y sin sujetarlo 1,3
MANO_CABEZA = 0.3  # la muneca por encima de la nariz, mano sobre la cabeza
SUJETAR = 0.6  # una muneca a menos de esto del codo del otro brazo
CODO_ARRIBA = 0.0  # triceps, el codo por encima de la nariz
DOBLADO = 0.0  # triceps, la muneca por debajo de su codo
SEGUNDOS = 20.0  # lo que se mantiene cada postura
TOLERANCIA_S = 0.5
AVISO_S = 3.0
REPETIR_AVISO_S = 10.0
SOSTENER_S = 0.8
MAX_VECES = 2.0  # una postura que no sale se deja pasada esta vez su duracion
REGISTRO = Path(__file__).resolve().parent.parent / "datos" / "ultimos_estiramientos.csv"
REGISTRO_CADA_S = 0.25

# Las posturas, en orden. (clave, que hacer, detalle, nombre corto)
POSTURAS = (
    ("cuello_der", "Cabeza a la derecha", "Con la mano derecha sobre la cabeza",
     "cuello a la derecha"),
    ("cuello_izq", "Cabeza a la izquierda", "Con la mano izquierda sobre la cabeza",
     "cuello a la izquierda"),
    ("arriba", "Brazos arriba", "Estíralos por encima de la cabeza", "brazos arriba"),
    ("cruzado_der", "Cruza el brazo derecho", "Sujeta el codo con la otra mano",
     "brazo derecho cruzado"),
    ("cruzado_izq", "Cruza el brazo izquierdo", "Sujeta el codo con la otra mano",
     "brazo izquierdo cruzado"),
    ("triceps_der", "Codo derecho arriba", "Mano a la espalda, sujeta el codo",
     "tríceps derecho"),
    ("triceps_izq", "Codo izquierdo arriba", "Mano a la espalda, sujeta el codo",
     "tríceps izquierdo"),
)
NOMBRES = {clave: nombre for clave, _, _, nombre in POSTURAS}

Punto = tuple[float, float]


@dataclass(frozen=True)
class Cuerpo:
    """Lo que hace falta de un fotograma, en coordenadas normalizadas de 0 a 1.

    Los brazos van en el mismo orden que los hombros (hombro_a con codo_a y
    muneca_a), porque asi los da MediaPipe aunque cambie el lado.
    """

    nariz: Punto
    hombro_a: Punto
    hombro_b: Punto
    oreja_a: Punto
    oreja_b: Punto
    codo_a: Punto
    codo_b: Punto
    muneca_a: Punto
    muneca_b: Punto
    vis_muneca_a: float = 1.0
    vis_muneca_b: float = 1.0

    @property
    def escala(self) -> float:
        return math.dist(self.hombro_a, self.hombro_b)

    @property
    def centro_x(self) -> float:
        return (self.hombro_a[0] + self.hombro_b[0]) / 2

    def brazo(self, lado: str) -> tuple[Punto, Punto, float]:
        """Codo, muneca y visibilidad del brazo derecho ("der") o izquierdo ("izq")."""
        a_es_der = self.hombro_a[0] > self.hombro_b[0]
        if (lado == "der") == a_es_der:
            return self.codo_a, self.muneca_a, self.vis_muneca_a
        return self.codo_b, self.muneca_b, self.vis_muneca_b


def _angulo(p: Punto, q: Punto) -> float:
    """Grados de la linea entre dos puntos, de izquierda a derecha de la pantalla.
    Positivo si baja hacia la derecha (y crece hacia abajo)."""
    izq, der = (p, q) if p[0] <= q[0] else (q, p)
    return math.degrees(math.atan2(der[1] - izq[1], der[0] - izq[0]))


@dataclass
class Medida:
    """Como estas ahora mismo. None es que no se puede saber."""

    cuerpo: bool
    inclinacion: float | None = None  # grados, positivo hacia tu derecha
    codos: float | None = None  # lo que sube el codo mas bajo sobre la nariz (anchos)
    cruce_der: float | None = None  # lo que pasa la muneca derecha del centro hacia la izq.
    cruce_izq: float | None = None
    mano_der: float | None = None  # lo que sube la muneca derecha sobre la nariz
    mano_izq: float | None = None
    # De una muneca al codo del otro brazo, la mas corta de las dos. Con los
    # brazos cruzados MediaPipe confunde a ratos que muneca es cual (prueba del
    # 19/11), asi que no se mira cual es, solo que una mano este en el otro codo
    sujeta: float | None = None
    codo_der: float | None = None  # lo que sube el codo derecho sobre la nariz
    codo_izq: float | None = None
    doblado_der: float | None = None  # lo que baja la muneca derecha bajo su codo
    doblado_izq: float | None = None
    vis_der: float | None = None  # lo seguro que esta MediaPipe de ver cada muneca
    vis_izq: float | None = None


def medir(c: Cuerpo | None) -> Medida:
    if c is None or c.escala < 1e-3:
        return Medida(cuerpo=False)
    e = c.escala
    inclinacion = _angulo(c.oreja_a, c.oreja_b) - _angulo(c.hombro_a, c.hombro_b)
    codos = (c.nariz[1] - max(c.codo_a[1], c.codo_b[1])) / e
    c_der, m_der, v_der = c.brazo("der")
    c_izq, m_izq, v_izq = c.brazo("izq")
    # La derecha sale a la derecha, asi que cruzarla es ir hacia x mas pequenas
    return Medida(
        True, inclinacion, codos,
        cruce_der=(c.centro_x - m_der[0]) / e,
        cruce_izq=(m_izq[0] - c.centro_x) / e,
        mano_der=(c.nariz[1] - m_der[1]) / e,
        mano_izq=(c.nariz[1] - m_izq[1]) / e,
        sujeta=min(math.dist(m_izq, c_der), math.dist(m_der, c_izq)) / e,
        codo_der=(c.nariz[1] - c_der[1]) / e,
        codo_izq=(c.nariz[1] - c_izq[1]) / e,
        doblado_der=(m_der[1] - c_der[1]) / e,
        doblado_izq=(m_izq[1] - c_izq[1]) / e,
        vis_der=v_der, vis_izq=v_izq)


def falta(objetivo: str, m: Medida) -> str | None:
    """Lo que falta para estar en la postura, dicho como lo que hay que hacer.
    None si ya estas en ella."""
    if not m.cuerpo:
        return "No te veo"
    if objetivo == "cuerpo":
        return None
    if objetivo in ("cuello_der", "cuello_izq"):
        lado = objetivo[-3:]
        mano = m.mano_der if lado == "der" else m.mano_izq
        if mano < MANO_CABEZA:
            return "Pon la mano sobre la cabeza"
        inclinada = (m.inclinacion >= INCLINAR_GRADOS if lado == "der"
                     else m.inclinacion <= -INCLINAR_GRADOS)
        return None if inclinada else "Inclina más la cabeza"
    if objetivo == "arriba":
        return None if m.codos > 0 else "Sube más los codos"
    if objetivo in ("cruzado_der", "cruzado_izq"):
        der = objetivo == "cruzado_der"
        if (m.cruce_der if der else m.cruce_izq) < CRUZAR:
            return "Cruza más el brazo"
        return None if m.sujeta <= SUJETAR else "Sujeta el codo con la otra mano"
    if objetivo in ("triceps_der", "triceps_izq"):
        der = objetivo == "triceps_der"
        if (m.codo_der if der else m.codo_izq) < CODO_ARRIBA:
            return "Sube el codo por encima de la cabeza"
        if (m.doblado_der if der else m.doblado_izq) < DOBLADO:
            return "Dobla el brazo, la mano a la espalda"
        return None if m.sujeta <= SUJETAR else "Sujeta el codo con la otra mano"
    if objetivo == "neutro":
        if abs(m.inclinacion) >= RECTA_GRADOS:
            return "Pon la cabeza recta"
        if (max(m.codo_der, m.codo_izq) > 0 or m.cruce_der >= CRUZAR
                or m.cruce_izq >= CRUZAR):
            return "Baja los brazos"
        return None
    raise ValueError(objetivo)


def cumple(objetivo: str, m: Medida) -> bool:
    return falta(objetivo, m) is None


# ================= guion =================


@dataclass(frozen=True)
class Paso:
    tipo: str  # mensaje, esperar, mantener
    texto: str
    detalle: str = ""
    objetivo: str | None = None  # esperar y mantener (cuerpo, neutro o una postura)
    duracion: float = 0.0  # mensaje y mantener
    postura: int = 0  # 1 a len(POSTURAS) en la sesion, 0 fuera de las posturas


def guion_sesion(segundos: float = SEGUNDOS) -> list[Paso]:
    pasos = [Paso("esperar", "Siéntate recto", "Que se te vean la cabeza y los codos",
                  objetivo="cuerpo")]
    for i, (clave, texto, detalle, _) in enumerate(POSTURAS, start=1):
        if i > 1:
            pasos.append(Paso("esperar", "Vuelve al centro", "Cabeza recta y brazos abajo",
                              objetivo="neutro", postura=i))
        pasos.append(Paso("esperar", texto, detalle, objetivo=clave, postura=i))
        pasos.append(Paso("mantener", "Aguanta así", texto, objetivo=clave,
                          duracion=segundos, postura=i))
    pasos.append(Paso("mensaje", "Bien hecho", "Suelta los brazos despacio", duracion=4))
    return pasos


def guion_tutorial() -> list[Paso]:
    pasos = [
        Paso("mensaje", "Estiramientos", "Cuello, hombros y brazos, sin levantarte", duracion=5),
        Paso("esperar", "Siéntate recto", "Que se te vean la cabeza y los codos",
             objetivo="cuerpo"),
    ]
    for i, (clave, texto, detalle, _) in enumerate(POSTURAS):
        if i:
            pasos.append(Paso("esperar", "Vuelve al centro", "Cabeza recta y brazos abajo",
                              objetivo="neutro"))
        pasos.append(Paso("esperar", texto, detalle, objetivo=clave))
        if i == 0:
            # Solo la primera se mantiene en el tutorial, para ensenar la cuenta
            pasos.append(Paso("mantener", "Aguanta así", "La cuenta solo avanza si sigues así",
                              objetivo=clave, duracion=5))
    pasos += [
        Paso("esperar", "Vuelve al centro", "Cabeza recta y brazos abajo", objetivo="neutro"),
        Paso("mensaje", "En la sesión", "aguantarás cada postura 20 segundos", duracion=5),
        Paso("mensaje", "Gana lotos", "Hasta tres, si no te sales de la postura",
             duracion=5),
    ]
    return pasos


@dataclass
class Estado:
    """Lo que la interfaz necesita pintar en un instante."""

    paso: Paso
    indice: int
    total: int
    hecho: float  # 0 a 1, lo que llevas del paso
    medida: Medida
    bien: bool = False  # en la postura (mantener, con la tolerancia)
    restante_s: float = 0.0  # mantener
    aviso: bool = False  # suena el aviso en este instante
    nuevo_paso: bool = False
    terminado: bool = False


@dataclass
class Practica:
    pasos: list[Paso]
    sostener_s: float = SOSTENER_S
    _indice: int = 0
    _inicio: float | None = None
    _sosteniendo: float | None = None
    _t: float | None = None
    _mal_desde: float | None = None
    _aviso_en: float | None = None
    _anunciado: int = -1
    _llevas: float = 0.0  # segundos de la postura ya mantenidos
    bien_s: float = 0.0
    contado_s: float = 0.0
    fuera_s: dict[str, float] = field(default_factory=dict)  # por postura

    @property
    def precision(self) -> float:
        return self.bien_s / self.contado_s if self.contado_s else 0.0

    @property
    def peor(self) -> tuple[str, float] | None:
        """La postura de la que mas te has salido, y cuanto."""
        if not self.fuera_s:
            return None
        clave = max(self.fuera_s, key=self.fuera_s.get)
        return clave, self.fuera_s[clave]

    def _avanzar(self, t: float) -> None:
        self._indice += 1
        self._inicio = t
        self._sosteniendo = None
        self._mal_desde = None
        self._aviso_en = None
        self._llevas = 0.0

    def actualizar(self, t: float, cuerpo: Cuerpo | None) -> Estado:
        if self._inicio is None:
            self._inicio = t
        dt = 0.0 if self._t is None else max(t - self._t, 0.0)
        self._t = t
        m = medir(cuerpo)
        if self._indice >= len(self.pasos):
            return Estado(self.pasos[-1], len(self.pasos), len(self.pasos), 1.0, m,
                          terminado=True)
        nuevo = self._anunciado != self._indice
        self._anunciado = indice = self._indice
        paso = self.pasos[indice]
        transcurrido = t - self._inicio

        def estado(hecho, **extra):
            return Estado(paso, indice, len(self.pasos), hecho, m, nuevo_paso=nuevo, **extra)

        if paso.tipo == "mensaje":
            hecho = min(transcurrido / paso.duracion, 1.0) if paso.duracion else 1.0
            if transcurrido >= paso.duracion:
                self._avanzar(t)
            return estado(hecho)

        if paso.tipo == "esperar":
            if cumple(paso.objetivo, m):
                if self._sosteniendo is None:
                    self._sosteniendo = t
                hecho = min((t - self._sosteniendo) / self.sostener_s, 1.0) \
                    if self.sostener_s > 0 else 1.0
            else:
                self._sosteniendo = None
                hecho = 0.0
            if hecho >= 1.0:
                self._avanzar(t)
            return estado(hecho)

        # mantener. Fuera de la postura solo cuenta si dura TOLERANCIA_S
        if cumple(paso.objetivo, m):
            self._mal_desde = None
        elif self._mal_desde is None:
            self._mal_desde = t
        fuera = self._mal_desde is not None and t - self._mal_desde >= TOLERANCIA_S
        if m.cuerpo and dt > 0:
            self.contado_s += dt
            if fuera:
                self.fuera_s[paso.objetivo] = self.fuera_s.get(paso.objetivo, 0.0) + dt
            else:
                self.bien_s += dt
                self._llevas += dt
        aviso = False
        if self._mal_desde is not None and t - self._mal_desde >= AVISO_S:
            if self._aviso_en is None or t - self._aviso_en >= REPETIR_AVISO_S:
                self._aviso_en = t
                aviso = True
        else:
            self._aviso_en = None
        hecho = min(self._llevas / paso.duracion, 1.0)
        restante = max(paso.duracion - self._llevas, 0.0)
        if self._llevas >= paso.duracion or transcurrido >= MAX_VECES * paso.duracion:
            self._avanzar(t)
        return estado(hecho, bien=not fuera, restante_s=restante, aviso=aviso)


def lotos(precision: float) -> int:
    """De 0 a 3 lotos, con los mismos cortes que las otras fases."""
    if precision >= 0.85:
        return 3
    if precision >= 0.65:
        return 2
    if precision >= 0.40:
        return 1
    return 0


class Registro:
    """Apunta en un CSV lo que mide la camara, para ajustar los umbrales sin capturas.

    Se reescribe en cada sesion (datos/ultimos_estiramientos.csv). Cada fila es
    un instante con el paso del guion, asi se sabe que postura se pedia.
    """

    CAMPOS = ("t", "paso", "objetivo", "cuerpo", "inclinacion", "codos", "cruce_der",
              "cruce_izq", "mano_der", "mano_izq", "sujeta", "codo_der", "codo_izq", "doblado_der",
              "doblado_izq", "vis_der",
              "vis_izq", "bien")

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
                            int(m.cuerpo), r(m.inclinacion), r(m.codos), r(m.cruce_der),
                            r(m.cruce_izq), r(m.mano_der), r(m.mano_izq), r(m.sujeta),
                            r(m.codo_der), r(m.codo_izq), r(m.doblado_der),
                            r(m.doblado_izq), r(m.vis_der), r(m.vis_izq), int(e.bien)])

    def cerrar(self) -> None:
        if self._archivo is not None:
            self._archivo.close()
            self._archivo = None
