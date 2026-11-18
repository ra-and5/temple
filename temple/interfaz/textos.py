"""Textos y formatos que comparten varias pantallas.

Estan juntos para que cambiar una frase o un formato se haga en un solo sitio.
"""

from __future__ import annotations

from temple.progreso import LIBRE

DIAS = "LMXJVSD"  # iniciales de la semana, de lunes a domingo
CORTES = (40, 65, 85)  # % para 1, 2 y 3 lotos (respiracion.estrellas y meditacion.lotos)

# Fases que todavia no existen. Salen apagadas en la fila del ritual
PROXIMAS = ("Estiramientos", "Flexiones")

# Ayuda de la linea de abajo en cada pantalla
AYUDAS = {
    "inicio": "Señala con el índice o usa el ratón   ·   Flechas para moverte y Enter para pulsar   ·   M sonido   ·   Esc salir",
    "tutorial": "Palma abierta o Espacio para pausar   ·   M sonido   ·   Esc volver al inicio",
    "sesion": "Palma abierta o Espacio para pausar   ·   M sonido   ·   Esc volver al inicio",
    "resultado": "Señala el botón con el índice o usa el ratón   ·   Enter o Espacio continuar",
}
AYUDA_PAUSA = "Señala con el índice o usa el ratón   ·   Flechas para elegir y Enter para pulsar   ·   Esc salir"


def minutos(m: float) -> str:
    """5 -> "5 min", 0.5 -> "0,5 min", LIBRE -> "sin límite"."""
    if m == LIBRE:
        return "sin límite"
    return f"{m:g} min".replace(".", ",")


def premio(m: int) -> str:
    """Lo que se desbloquea, dicho para cualquiera."""
    return "meditar sin límite" if m == LIBRE else minutos(m)
