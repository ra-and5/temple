"""Textos y formatos que comparten varias pantallas.

Estan juntos para que cambiar una frase o un formato se haga en un solo sitio.
"""

from __future__ import annotations

from temple.progreso import LIBRE

DIAS = "LMXJVSD"  # iniciales de la semana, de lunes a domingo
CORTES = (40, 65, 85)  # % para 1, 2 y 3 lotos (respiracion.estrellas y meditacion.lotos)

# Fases que todavia no existen. Salen apagadas en la fila del ritual
PROXIMAS = ("Flexiones",)

# Ayuda de la linea de abajo en cada pantalla
AYUDAS = {
    "inicio": ("Señala un botón con el índice y espera",
               "Flechas y Enter, o el ratón  ·  F pantalla completa  ·  M sonido  ·  Esc salir"),
    "tutorial": ("Palma abierta y quieta para pausar",
                 "Espacio pausar  ·  D datos de la cámara  ·  M sonido  ·  Esc volver al inicio"),
    "sesion": ("Palma abierta y quieta para pausar",
               "Espacio pausar  ·  D datos de la cámara  ·  M sonido  ·  Esc volver al inicio"),
    "resultado": ("Señala un botón con el índice y espera",
                  "Enter continuar  ·  Esc volver al inicio"),
}
AYUDA_PROGRESO = ("Señala Volver con el índice y espera",
                  "Esc o Enter volver")
AYUDA_SALIR = ("Señala Sí o No con el índice y espera",
               "Enter salir  ·  Esc seguir aquí")
AYUDA_PAUSA = ("Señala Seguir o Salir con el índice y espera",
               "Espacio seguir  ·  Esc volver al inicio")


def minutos(m: float) -> str:
    """5 -> "5 min", 0.5 -> "0,5 min", LIBRE -> "sin límite"."""
    if m == LIBRE:
        return "sin límite"
    return f"{m:g} min".replace(".", ",")


def premio(m: int) -> str:
    """Lo que se desbloquea, dicho para cualquiera."""
    return "meditar sin límite" if m == LIBRE else minutos(m)
