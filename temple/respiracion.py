"""Logica de la respiracion alterna (Anuloma Viloma), sin camara ni ventanas.

Sigue la variante para principiantes del video "Pranayama para Principiantes
(Anuloma Viloma)" de Anabel Otero. Una vuelta es
  inhalar por la izquierda 4  (derecha tapada con el pulgar)
  exhalar por la derecha   8  (izquierda tapada con otro dedo)
  inhalar por la derecha   4  (izquierda tapada)
  exhalar por la izquierda 8  (derecha tapada)
y se hacen 5 vueltas. En la variante avanzada se retiene el aire 16 con los
dos lados tapados despues de cada inhalacion.

Todo es un guion de pasos que se ejecutan en orden.
  - esperar  no avanza hasta que la camara ve lo que se pide un momento seguido.
             Asi nadie va con prisa al cambiar de lado.
  - contar   cuenta los tiempos de inhalar, retener o exhalar, uno por segundo.
  - mensaje  ensena un texto unos segundos.
El tutorial y la sesion usan el mismo motor con guiones distintos.
"""

from __future__ import annotations

from dataclasses import dataclass, field

TIEMPO_S = 1.0  # un tiempo de la cuenta = un segundo
VUELTAS = 5
INHALA, RETIENE, EXHALA = 4, 16, 8
SOSTENER_S = 0.8  # cuanto rato seguido hay que hacer lo pedido en un paso esperar

# Lo que hay que tapar segun por donde pasa el aire
TAPADO_SEGUN_ABIERTO = {"izquierdo": "derecho", "derecho": "izquierdo"}

COMO_TAPAR = {
    "derecho": "Tapa la derecha con el pulgar",
    "izquierdo": "Tapa la izquierda con el anular",
    "ambos": "Tapa las dos",
}


@dataclass(frozen=True)
class Paso:
    tipo: str  # esperar, contar, mensaje
    texto: str  # instruccion principal
    detalle: str = ""  # explicacion corta debajo
    objetivo: str | None = None  # esperar: cuerpo, mano, derecho, izquierdo, ambos
    accion: str | None = None  # contar: inhala, retiene, exhala
    abierto: str | None = None  # contar: lado por el que pasa el aire
    tiempos: int = 0  # contar
    duracion: float = 0.0  # mensaje
    vuelta: int = 0

    @property
    def tapado(self) -> str | None:
        """Lo que tiene que ver la camara durante el paso."""
        if self.tipo == "esperar" and self.objetivo in ("derecho", "izquierdo", "ambos"):
            return self.objetivo
        if self.tipo == "contar":
            return "ambos" if self.accion == "retiene" else TAPADO_SEGUN_ABIERTO[self.abierto]
        return None


def _contar(accion, abierto, tiempos, vuelta=0):
    lado = {"izquierdo": "IZQUIERDA", "derecho": "DERECHA"}.get(abierto, "")
    texto, detalle = {"inhala": ("Coge aire", f"por la {lado}"),
                      "exhala": ("Suelta el aire", f"por la {lado}, despacio"),
                      "retiene": ("Aguanta", "con las dos tapadas")}[accion]
    return Paso("contar", texto, detalle, accion=accion, abierto=abierto,
                tiempos=tiempos, vuelta=vuelta)


def _con_cambios(pasos: list[Paso]) -> list[Paso]:
    """Mete un paso esperar delante de cada contar que pida tapar otro lado."""
    resultado, tapado_actual = [], None
    for paso in pasos:
        if paso.tipo == "contar" and paso.tapado != tapado_actual:
            texto = "Cambia" if tapado_actual is not None else "Prepárate"
            resultado.append(Paso("esperar", texto, COMO_TAPAR[paso.tapado],
                                  objetivo=paso.tapado, vuelta=paso.vuelta))
        if paso.tapado is not None:
            tapado_actual = paso.tapado
        resultado.append(paso)
    return resultado


def guion_sesion(vueltas: int = VUELTAS, avanzado: bool = False) -> list[Paso]:
    pasos = [_contar("exhala", "izquierdo", 4, 0)]  # vaciar antes de empezar
    for v in range(1, vueltas + 1):
        for lado, otro in (("izquierdo", "derecho"), ("derecho", "izquierdo")):
            pasos.append(_contar("inhala", lado, INHALA, v))
            if avanzado:
                pasos.append(_contar("retiene", None, RETIENE, v))
            pasos.append(_contar("exhala", otro, EXHALA, v))
    pasos = _con_cambios(pasos)
    pasos.append(Paso("mensaje", "Baja la mano", "Respira tranquilo",
                      duracion=6, vuelta=vueltas + 1))
    return pasos


def guion_tutorial() -> list[Paso]:
    return [
        Paso("mensaje", "Respiración alterna",
             "Coges aire por un lado y lo sueltas por el otro", duracion=5),
        Paso("esperar", "Siéntate recto", "Que se te vean los hombros", objetivo="cuerpo"),
        Paso("esperar", "Levanta la mano derecha", "Dobla el índice y el corazón",
             objetivo="mano"),
        Paso("esperar", "Tapa la derecha", "con el pulgar", objetivo="derecho"),
        Paso("esperar", "Tapa la izquierda", "con el anular, y suelta el pulgar",
             objetivo="izquierdo"),
        Paso("esperar", "Otra vez la derecha", "con el pulgar", objetivo="derecho"),
        Paso("mensaje", "Ahora con aire", "Sigue los números", duracion=3),
        _contar("inhala", "izquierdo", INHALA),
        Paso("esperar", "Cambia", COMO_TAPAR["izquierdo"], objetivo="izquierdo"),
        _contar("exhala", "derecho", EXHALA),
        Paso("mensaje", "Muy bien", "Ya sabes hacerlo", duracion=3),
    ]


@dataclass
class Estado:
    """Lo que la interfaz necesita pintar en un instante."""

    paso: Paso
    indice: int
    total: int
    cuenta: int  # contar: tiempo actual (1..tiempos)
    llenado: float  # contar: 0 pulmones vacios, 1 llenos
    hecho: float  # esperar: cuanto llevas sosteniendo lo pedido (0 a 1)
    correcto: bool | None  # contar: si tapas el lado que toca
    terminado: bool


@dataclass
class Guion:
    pasos: list[Paso]
    tiempo_s: float = TIEMPO_S
    sostener_s: float = SOSTENER_S
    _indice: int = 0
    _inicio_paso: float | None = None
    _sosteniendo_desde: float | None = None
    _llenado: float = 0.0  # pulmones al empezar el paso actual
    _aciertos: dict[int, int] = field(default_factory=dict)
    _muestras: dict[int, int] = field(default_factory=dict)

    @property
    def vueltas(self) -> int:
        return max((p.vuelta for p in self.pasos if p.tipo == "contar"), default=0)

    def _avanzar(self, t: float, llenado: float) -> None:
        self._indice += 1
        self._inicio_paso = t
        self._sosteniendo_desde = None
        self._llenado = llenado

    def actualizar(self, t: float, detectado: str | None, hay_mano: bool) -> Estado:
        """Avanza el guion al instante t con lo que ve la camara.

        detectado es derecho, izquierdo, ambos, ninguno o None si no hay cuerpo.
        """
        if self._inicio_paso is None:
            self._inicio_paso = t
        if self._indice >= len(self.pasos):
            return Estado(self.pasos[-1], len(self.pasos), len(self.pasos),
                          0, 0.0, 1.0, None, True)

        paso = self.pasos[self._indice]
        dt = t - self._inicio_paso

        if paso.tipo == "mensaje":
            if dt >= paso.duracion:
                self._avanzar(t, self._llenado)
            return Estado(paso, self._indice, len(self.pasos), 0, self._llenado,
                          min(dt / paso.duracion, 1.0), None, False)

        if paso.tipo == "esperar":
            cumple = {
                "cuerpo": detectado is not None,
                "mano": detectado is not None and hay_mano,
            }.get(paso.objetivo, detectado == paso.objetivo)
            if not cumple:
                self._sosteniendo_desde = None
                hecho = 0.0
            else:
                if self._sosteniendo_desde is None:
                    self._sosteniendo_desde = t
                sostenido = t - self._sosteniendo_desde
                hecho = min(sostenido / self.sostener_s, 1.0) if self.sostener_s > 0 else 1.0
                if hecho >= 1.0:
                    self._avanzar(t, self._llenado)
            return Estado(paso, self._indice, len(self.pasos), 0, self._llenado,
                          hecho, None, False)

        # contar
        duracion = paso.tiempos * self.tiempo_s
        progreso = min(dt / duracion, 1.0)
        if paso.accion == "inhala":
            llenado = self._llenado + (1.0 - self._llenado) * progreso
        elif paso.accion == "exhala":
            llenado = self._llenado * (1.0 - progreso)
        else:
            llenado = self._llenado
        cuenta = min(paso.tiempos, int(dt / self.tiempo_s) + 1)
        correcto = detectado == paso.tapado
        self._muestras[paso.vuelta] = self._muestras.get(paso.vuelta, 0) + 1
        self._aciertos[paso.vuelta] = self._aciertos.get(paso.vuelta, 0) + int(correcto)
        if dt >= duracion:
            self._avanzar(t, llenado)
        return Estado(paso, self._indice, len(self.pasos), cuenta, llenado,
                      progreso, correcto, False)

    @property
    def precision(self) -> float:
        total = sum(self._muestras.values())
        return sum(self._aciertos.values()) / total if total else 0.0


def estrellas(precision: float) -> int:
    """De 0 a 3 estrellas segun lo bien tapado que estuvo el lado correcto."""
    if precision >= 0.85:
        return 3
    if precision >= 0.65:
        return 2
    if precision >= 0.40:
        return 1
    return 0
