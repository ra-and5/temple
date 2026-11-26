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

# Las vueltas de respiracion se eligen en Ajustes, pero solo las sesiones de al
# menos VUELTAS_NIVEL cuentan para subir. Asi un dia con prisa vale para la
# racha sin abaratar el reto
VUELTAS_MIN, VUELTAS_MAX, VUELTAS_NIVEL = 1, 9, 5

# La meditacion sube por esta escalera de minutos y al final llega el modo
# libre, sin cuenta atras
ESCALERA = (5, 8, 12, 17, 23, 30, 40)
LIBRE = 0

# Una sola regla para subir de nivel en todas las fases. 5 dias distintos con
# 3 lotos jugando tu nivel mas alto te suben al siguiente. Nunca baja
DIAS_PARA_SUBIR = 5
LOTOS_PARA_SUBIR = 3

# Los niveles de cada fase, del primero al ultimo. Los estiramientos tienen uno
# solo, porque son el calentamiento antes de las flexiones y no un reto
NIVELES = {
    "respiracion": ("principiante", "avanzada"),
    "meditacion": ESCALERA + (LIBRE,),
    "estiramientos": (20,),  # segundos en cada postura
    "flexiones": (("facil", 5), ("tecnico", 5), ("tecnico", 10)),  # tipo y repeticiones
}


def nivel_de_sesion(s: dict) -> int | None:
    """El nivel al que se jugo una sesion, o None si no cuenta para subir.

    Las sesiones nuevas lo guardan. Las de antes del 25/11 no, y se deduce de
    lo que guardaban (variante, vueltas o minutos).
    """
    if s["fase"] == "respiracion" and s.get("vueltas", VUELTAS_NIVEL) < VUELTAS_NIVEL:
        return None
    if "nivel" in s:
        return s["nivel"]
    if s["fase"] == "respiracion":
        return 1 if s["variante"] == "avanzada" else 0
    if s["fase"] == "meditacion":
        cumplidos = [i for i, m in enumerate(ESCALERA) if m <= s.get("minutos", 0) + 1e-6]
        return cumplidos[-1] if cumplidos else None
    if s["fase"] == "flexiones":
        return 1 if s["variante"] == "tecnico" else 0
    return 0


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
                  minutos: float | None = None, nivel=...) -> None:
        """Guarda una sesion. nivel es al que se ha jugado, o None si no cuenta para subir
        (opciones de prueba como --minutos). Sin darlo, se deduce como en las antiguas."""
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
        if nivel is not ...:
            sesion["nivel"] = nivel
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

    def mejor(self, fase: str, variante: str) -> float | None:
        precisiones = [s["precision"] for s in self.sesiones
                       if s["fase"] == fase and s["variante"] == variante]
        return max(precisiones) if precisiones else None

    def hecha_hoy(self, fase: str, hoy: date | None = None) -> bool:
        hoy = (hoy or date.today()).isoformat()
        return any(s["fecha"] == hoy and s["fase"] == fase for s in self.sesiones)

    # ---- niveles ----

    def _subida(self, fase: str) -> tuple[int, int]:
        """(nivel desbloqueado, dias que ya cuentan para el siguiente).

        Recorre las sesiones en orden. Cuenta los dias con 3 lotos jugando al
        nivel mas alto que tenias ese dia, y con 5 sube y empieza de cero.
        """
        maximo = len(NIVELES[fase]) - 1
        n, dias = 0, set()
        for s in sorted(self.sesiones, key=lambda s: s["fecha"]):
            if s["fase"] != fase or s["estrellas"] < LOTOS_PARA_SUBIR or n >= maximo:
                continue
            jugado = nivel_de_sesion(s)
            if jugado is None or jugado < n:
                continue
            dias.add(s["fecha"])
            if len(dias) >= DIAS_PARA_SUBIR:
                n, dias = n + 1, set()
        return n, len(dias)

    def nivel(self, fase: str) -> int:
        """El nivel mas alto desbloqueado, empezando en 0."""
        return self._subida(fase)[0]

    def dias_para_subir(self, fase: str) -> int:
        """Dias que ya cuentan para el siguiente nivel, de 0 a DIAS_PARA_SUBIR - 1."""
        return self._subida(fase)[1]

    def nivel_maximo(self, fase: str) -> bool:
        return self.nivel(fase) >= len(NIVELES[fase]) - 1

    def nivel_elegido(self, fase: str) -> int:
        """El que se juega. El mas alto, salvo que hayas elegido uno mas bajo."""
        elegido = self.ajustes.get("niveles", {}).get(fase)
        alto = self.nivel(fase)
        return alto if elegido is None else min(elegido, alto)

    def elegir_nivel(self, fase: str, paso: int) -> int:
        alto = self.nivel(fase)
        n = min(max(self.nivel_elegido(fase) + paso, 0), alto)
        niveles = self.ajustes.setdefault("niveles", {})
        if n == alto:
            niveles.pop(fase, None)  # sin guardar, asi sube solo al desbloquear otro
        else:
            niveles[fase] = n
        self.guardar()
        return n
