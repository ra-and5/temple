"""Opciones de arranque.

Las de probar (python main.py --minutos 1 …) no cuentan para subir de nivel.
--rapido las pone todas cortas a la vez, para probar el juego entero en pocos minutos.
La carpeta de datos se cambia en los tests, para no tocar el progreso de verdad.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from temple.progreso import RUTA
from temple.respiracion import TIEMPO_S

# Lo que pone --rapido si no se dice otra cosa
RAPIDO = {"vueltas": 1, "minutos": 1.0, "segundos": 4.0, "flexiones": 2}
MENSAJE_RAPIDO_S = 1.5  # con --rapido, los textos de paso duran como mucho esto


@dataclass(frozen=True)
class Opciones:
    """Las opciones de la terminal, para probar el juego sin tocar el progreso."""
    vueltas: int | None = None  # vueltas de respiracion, no se guardan
    tiempo_s: float = TIEMPO_S  # segundos por tiempo de la cuenta
    avanzada: bool = False  # respiracion avanzada sin desbloquearla
    minutos: float | None = None  # minutos de meditacion (0 es sin limite)
    segundos: float | None = None  # segundos de cada estiramiento
    camara: int = 0  # que camara usar si hay varias (0 es la primera)
    flexiones: int | None = None  # flexiones de la sesion
    rapido: bool = False  # ademas acorta los textos de paso de los tutoriales y sesiones
    datos: Path = RUTA.parent  # carpeta del progreso y del registro (los tests usan otra)

    @property
    def prueba(self) -> bool:
        """Si se ha arrancado con alguna opcion de probar. Esas sesiones no suben de nivel."""
        return (self.vueltas is not None or self.tiempo_s != TIEMPO_S or self.avanzada
                or self.minutos is not None or self.segundos is not None
                or self.flexiones is not None or self.rapido)
