"""Colores, medidas y fuentes de Temple.

Paleta de templo de noche. Fondo indigo casi negro, oro de lampara para lo
importante, azafran para lo que hay que hacer, jade para lo que esta bien y
terracota para avisar, nunca rojo chillon.
"""

from __future__ import annotations

from functools import lru_cache
from pathlib import Path

import pygame

RAIZ = Path(__file__).resolve().parents[2]
FUENTES = RAIZ / "assets" / "fuentes"

ANCHO, ALTO = 1280, 720
FPS = 60

# Zonas de la pantalla
CAMARA = pygame.Rect(40, 92, 720, 540)
PANEL = pygame.Rect(792, 92, 448, 540)
RADIO = 22

# Colores
NOCHE_ARRIBA = (13, 14, 24)
NOCHE_ABAJO = (31, 22, 38)
TARJETA = (24, 22, 35)
ORO = (227, 178, 91)
ORO_SUAVE = (160, 128, 74)
AZAFRAN = (242, 140, 40)
TERRACOTA = (214, 104, 82)
JADE = (102, 190, 160)
LAVANDA = (178, 150, 214)
CREMA = (243, 233, 210)
APAGADO = (150, 140, 132)
BORDE = (227, 178, 91, 46)

# Color de cada momento de la respiracion
COLOR_ACCION = {"inhala": ORO, "exhala": JADE, "retiene": LAVANDA}

_ARCHIVOS = {
    "titulo": "cormorant-garamond-latin-600-normal.ttf",
    "cursiva": "cormorant-garamond-latin-500-italic.ttf",
    "texto": "nunito-latin-400-normal.ttf",
    "negrita": "nunito-latin-700-normal.ttf",
}


@lru_cache(maxsize=None)
def fuente(tipo: str, tam: int) -> pygame.font.Font:
    """Fuente del juego. Si falta el archivo, usa la de Pygame para no romper."""
    ruta = FUENTES / _ARCHIVOS[tipo]
    try:
        return pygame.font.Font(str(ruta), tam)
    except (OSError, FileNotFoundError):
        return pygame.font.Font(None, tam)
