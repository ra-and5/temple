"""Textos y formatos que comparten varias pantallas.

Estan juntos para que cambiar una frase o un formato se haga en un solo sitio.
"""

from __future__ import annotations

from temple.progreso import LIBRE  # noqa: F401

DIAS = "LMXJVSD"  # iniciales de la semana, de lunes a domingo
CORTES = (40, 65, 85)  # % para 1, 2 y 3 lotos (respiracion.estrellas y meditacion.lotos)

# Ayuda de abajo, en dos lineas. Con la mano, para manejarlo de lejos, y con el
# teclado solo los atajos que sirven en esa pantalla, para quien este cerca
SENALA = "Señala un botón con el índice y espera"
VOLVER = "Flechas y Enter  ·  Esc volver"
PRACTICA = "Espacio pausar  ·  D datos de la cámara  ·  Esc salir"
AYUDAS = {
    "menu": (SENALA, "Flechas y Enter  ·  F pantalla completa  ·  M sonido  ·  Esc salir"),
    "fases": (SENALA, VOLVER),
    "progreso": (SENALA, VOLVER),
    "ajustes": (SENALA, "Flechas y Enter  ·  Izquierda y derecha vueltas  ·  Esc volver"),
    "salir": ("Señala Sí o No con el índice y espera", "Enter salir  ·  Esc seguir aquí"),
    "previa": (SENALA, "Espacio empezar  ·  Izquierda y derecha nivel  ·  T tutorial  ·  Esc volver"),
    "practica": ("Palma abierta y quieta para pausar", PRACTICA),
    "resultado": (SENALA, "Espacio seguir  ·  Esc menú"),
}
AYUDA_PAUSA = ("Abre la palma y ciérrala en un puño para seguir, o señala un botón",
               "Espacio seguir  ·  Esc salir")


def minutos(m: float) -> str:
    """5 -> "5 min", 0.5 -> "0,5 min", LIBRE -> "sin límite"."""
    if m == LIBRE:
        return "sin límite"
    return f"{m:g} min".replace(".", ",")


def premio(m: int) -> str:
    """Lo que se desbloquea, dicho para cualquiera."""
    return "meditar sin límite" if m == LIBRE else minutos(m)
