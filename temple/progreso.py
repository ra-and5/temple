"""Progreso del jugador, guardado en datos/progreso.json.

Cada fase del juego registra aqui lo que hace (fecha, fase, variante, precision,
estrellas y vueltas). Tambien se guardan los ajustes, como las vueltas elegidas. De ese registro salen la racha de dias seguidos, los dias de la
semana practicados y los niveles que se desbloquean. Las fechas se pasan como
argumento para poder probarlo sin depender del dia de hoy.
"""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from datetime import date, timedelta
from pathlib import Path

RUTA = Path(__file__).resolve().parent.parent / "datos" / "progreso.json"

# Sesiones de respiracion con 3 estrellas que desbloquean la variante avanzada
PERFECTAS_PARA_AVANZADA = 5
# Las vueltas se eligen en el juego, pero solo las sesiones de al menos estas
# cuentan para subir de nivel. Asi un dia con prisa vale para la racha sin
# abaratar el reto
VUELTAS_MIN, VUELTAS_MAX, VUELTAS_NIVEL = 1, 9, 5

# Meditacion. Una escalera de minutos que se va desbloqueando. Si una semana
# (de lunes a domingo) meditas 5 dias con el escalon mas alto que tienes y
# sacando al menos 2 lotos, la siguiente se desbloquea el de arriba. Despues
# del ultimo llega el modo libre, sin cuenta atras. Nunca baja. Se puede elegir
# menos tiempo (y 1, 2 o 3 minutos para un dia con prisa o para probar), pero
# eso no cuenta para subir
ESCALERA = (5, 8, 12, 17, 23, 30, 40)
CORTOS = (1, 2, 3)
LIBRE = 0  # en los ajustes y en las opciones, el modo sin cuenta atras
DIAS_PARA_SUBIR = 5
LOTOS_PARA_CONTAR = 2  # un dia de meditacion cuenta para subir con 2 lotos o mas


@dataclass
class Progreso:
    ruta: Path = RUTA
    tutoriales: set[str] = field(default_factory=set)
    sesiones: list[dict] = field(default_factory=list)
    ajustes: dict = field(default_factory=dict)

    @classmethod
    def cargar(cls, ruta: Path = RUTA) -> "Progreso":
        try:
            datos = json.loads(ruta.read_text(encoding="utf-8"))
        except (OSError, ValueError):
            return cls(ruta)
        return cls(ruta, set(datos.get("tutoriales", [])), list(datos.get("sesiones", [])),
                   dict(datos.get("ajustes", {})))

    def guardar(self) -> None:
        self.ruta.parent.mkdir(parents=True, exist_ok=True)
        datos = {"tutoriales": sorted(self.tutoriales), "sesiones": self.sesiones,
                 "ajustes": self.ajustes}
        self.ruta.write_text(json.dumps(datos, indent=2, ensure_ascii=False), encoding="utf-8")

    # ---- registrar ----

    def marcar_tutorial(self, fase: str) -> None:
        self.tutoriales.add(fase)
        self.guardar()

    def registrar(self, fase: str, variante: str, precision: float, estrellas: int,
                  dia: date | None = None, vueltas: int | None = None,
                  minutos: float | None = None) -> None:
        sesion = {
            "fecha": (dia or date.today()).isoformat(),
            "fase": fase,
            "variante": variante,
            "precision": round(precision, 3),
            "estrellas": estrellas,
        }
        if vueltas is not None:
            sesion["vueltas"] = vueltas
        if minutos is not None:
            sesion["minutos"] = round(minutos, 2)
        self.sesiones.append(sesion)
        self.guardar()

    def elegir_vueltas(self, n: int) -> int:
        n = min(max(n, VUELTAS_MIN), VUELTAS_MAX)
        self.ajustes["vueltas"] = n
        self.guardar()
        return n

    # ---- consultar ----

    def tutorial_hecho(self, fase: str) -> bool:
        return fase in self.tutoriales

    def dias_practicados(self) -> set[date]:
        return {date.fromisoformat(s["fecha"]) for s in self.sesiones}

    def racha(self, hoy: date | None = None) -> int:
        """Dias seguidos con alguna sesion. Si hoy aun no has practicado, cuenta desde ayer."""
        hoy = hoy or date.today()
        dias = self.dias_practicados()
        dia = hoy if hoy in dias else hoy - timedelta(days=1)
        n = 0
        while dia in dias:
            n += 1
            dia -= timedelta(days=1)
        return n

    def semana(self, hoy: date | None = None) -> list[bool]:
        """Lunes a domingo de esta semana, True si ese dia se practico."""
        hoy = hoy or date.today()
        lunes = hoy - timedelta(days=hoy.weekday())
        dias = self.dias_practicados()
        return [lunes + timedelta(days=i) in dias for i in range(7)]

    def vueltas(self, por_defecto: int) -> int:
        return self.ajustes.get("vueltas", por_defecto)

    def perfectas(self, fase: str, variante: str) -> int:
        """Sesiones con 3 estrellas y vueltas suficientes. Las antiguas sin vueltas valen."""
        return sum(1 for s in self.sesiones
                   if s["fase"] == fase and s["variante"] == variante and s["estrellas"] == 3
                   and s.get("vueltas", VUELTAS_NIVEL) >= VUELTAS_NIVEL)

    def avanzada_desbloqueada(self) -> bool:
        return self.perfectas("respiracion", "principiante") >= PERFECTAS_PARA_AVANZADA

    def mejor(self, fase: str, variante: str) -> float | None:
        precisiones = [s["precision"] for s in self.sesiones
                       if s["fase"] == fase and s["variante"] == variante]
        return max(precisiones) if precisiones else None

    def hecha_hoy(self, fase: str, hoy: date | None = None) -> bool:
        hoy = (hoy or date.today()).isoformat()
        return any(s["fecha"] == hoy and s["fase"] == fase for s in self.sesiones)

    # ---- meditacion ----

    def _dias_meditados(self, lunes: date, minutos: float) -> int:
        """Dias de la semana que empieza en lunes con una sesion de al menos esos minutos."""
        domingo = lunes + timedelta(days=6)
        return len({s["fecha"] for s in self.sesiones
                    if s["fase"] == "meditacion" and s.get("minutos", 0) >= minutos
                    and s["estrellas"] >= LOTOS_PARA_CONTAR
                    and lunes <= date.fromisoformat(s["fecha"]) <= domingo})

    def _escalon(self, hoy: date) -> int:
        """Indice del escalon de esta semana. len(ESCALERA) es el modo libre."""
        fechas = [date.fromisoformat(s["fecha"]) for s in self.sesiones
                  if s["fase"] == "meditacion"]
        n = 0
        if not fechas:
            return n
        lunes_hoy = hoy - timedelta(days=hoy.weekday())
        primera = min(fechas)
        lunes = primera - timedelta(days=primera.weekday())
        while lunes < lunes_hoy and n < len(ESCALERA):
            if self._dias_meditados(lunes, ESCALERA[n]) >= DIAS_PARA_SUBIR:
                n += 1
            lunes += timedelta(days=7)
        return n

    def minutos_meditacion(self, hoy: date | None = None) -> int:
        """El escalon mas alto desbloqueado (el ultimo si ya tienes el libre)."""
        return ESCALERA[min(self._escalon(hoy or date.today()), len(ESCALERA) - 1)]

    def libre_desbloqueado(self, hoy: date | None = None) -> bool:
        return self._escalon(hoy or date.today()) >= len(ESCALERA)

    def siguiente_escalon(self, hoy: date | None = None) -> int | None:
        """Minutos del escalon que se desbloquea, LIBRE para el libre, o None si ya esta todo."""
        n = self._escalon(hoy or date.today())
        if n >= len(ESCALERA):
            return None
        return ESCALERA[n + 1] if n + 1 < len(ESCALERA) else LIBRE

    def opciones_minutos(self, hoy: date | None = None) -> list[int]:
        hoy = hoy or date.today()
        nivel = self.minutos_meditacion(hoy)
        opciones = list(CORTOS) + [m for m in ESCALERA if m <= nivel]
        if self.libre_desbloqueado(hoy):
            opciones.append(LIBRE)
        return opciones

    def minutos_elegidos(self, hoy: date | None = None) -> int:
        """Los que elegiste la ultima vez si siguen disponibles, si no el escalon mas alto."""
        elegido = self.ajustes.get("minutos")
        return elegido if elegido in self.opciones_minutos(hoy) else self.minutos_meditacion(hoy)

    def cambiar_minutos(self, paso: int, hoy: date | None = None) -> int:
        opciones = self.opciones_minutos(hoy)
        i = opciones.index(self.minutos_elegidos(hoy)) + paso
        self.ajustes["minutos"] = opciones[min(max(i, 0), len(opciones) - 1)]
        self.guardar()
        return self.ajustes["minutos"]

    def dias_meditados_semana(self, hoy: date | None = None) -> int:
        hoy = hoy or date.today()
        lunes = hoy - timedelta(days=hoy.weekday())
        return self._dias_meditados(lunes, self.minutos_meditacion(hoy))
