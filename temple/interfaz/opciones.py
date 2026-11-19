"""Opciones de arranque.

Las de probar (python main.py --minutos 1 …) no cuentan para subir de nivel.
La carpeta de datos se cambia en los tests, para no tocar el progreso de verdad.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from temple.progreso import RUTA
from temple.respiracion import TIEMPO_S


@dataclass(frozen=True)
class Opciones:
    vueltas: int | None = None  # vueltas de respiracion, no se guardan
    tiempo_s: float = TIEMPO_S  # segundos por tiempo de la cuenta
    avanzada: bool = False  # respiracion avanzada sin desbloquearla
    minutos: float | None = None  # minutos de meditacion (0 es sin limite)
    segundos: float | None = None  # segundos de cada estiramiento
    camara: int = 0  # que camara usar si hay varias (0 es la primera)
    datos: Path = RUTA.parent  # carpeta del progreso y del registro (los tests usan otra)
