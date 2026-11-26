"""Moverse por los botones con el teclado.

Los botones de cada pantalla llegan en orden, de arriba abajo. Cada boton
puede tener un grupo (por ejemplo "vueltas" para el menos y el mas, o "pausa"
para Seguir y Salir). Los botones seguidos del mismo grupo estan en la misma
fila y forman una sola parada para las flechas de arriba y abajo.

  - mover      flecha arriba o abajo, pasa a la fila de antes o de despues
  - lateral    flecha izquierda o derecha, pasa al boton de al lado en la fila
  - fila_de    los botones que estan en la misma fila que el del foco

El foco es el indice del boton marcado, o None si no hay ninguno (al entrar
en una pantalla). No depende de Pygame, para poder probarlo sin ventana.
"""

from __future__ import annotations


def paradas(grupos: list[str | None]) -> list[list[int]]:
    """Agrupa los indices en filas. Ejemplo: [None, "v", "v", None] da [[0], [1, 2], [3]]."""
    filas: list[list[int]] = []
    for i, g in enumerate(grupos):
        if filas and g is not None and grupos[filas[-1][0]] == g:
            filas[-1].append(i)
        else:
            filas.append([i])
    return filas


def _fila(foco: int, filas: list[list[int]]) -> int:
    for n, fila in enumerate(filas):
        if foco in fila:
            return n
    return 0


def fila_de(foco: int | None, grupos: list[str | None]) -> list[int]:
    """Los botones que están en la misma fila que el marcado."""
    if foco is None or not 0 <= foco < len(grupos):
        return []
    filas = paradas(grupos)
    return filas[_fila(foco, filas)]


def mover(foco: int | None, grupos: list[str | None], paso: int, rodear: bool = False) -> int | None:
    """Foco de la fila siguiente (paso 1) o anterior (paso -1).

    Sin foco, la primera vez marca la primera fila (o la ultima si se sube).
    Con rodear, de la ultima se pasa a la primera (como hace Tab).
    """
    filas = paradas(grupos)
    if not filas:
        return None
    if foco is None or not 0 <= foco < len(grupos):
        return filas[0][0] if paso > 0 else filas[-1][0]
    n = _fila(foco, filas) + paso
    if rodear:
        n %= len(filas)
    else:
        n = min(max(n, 0), len(filas) - 1)
    return filas[n][0]


def lateral(foco: int | None, grupos: list[str | None], paso: int) -> int | None:
    """Boton de al lado en la misma fila, o None si no hay otro en esa direccion."""
    fila = fila_de(foco, grupos)
    if len(fila) < 2:
        return None
    j = fila.index(foco) + paso
    return fila[j] if 0 <= j < len(fila) else None
