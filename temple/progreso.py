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
                  dia: date | None = None, vueltas: int | None = None) -> None:
        sesion = {
            "fecha": (dia or date.today()).isoformat(),
            "fase": fase,
            "variante": variante,
            "precision": round(precision, 3),
            "estrellas": estrellas,
        }
        if vueltas is not None:
            sesion["vueltas"] = vueltas
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
