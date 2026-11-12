"""Temple. Juego serio de respiracion, meditacion y ejercicio con la webcam.

Uso, desde la raiz del repositorio
    python main.py
    python main.py --vueltas 2      sesion corta para probar (en el juego se eligen con - y +)
    python main.py --avanzada       deja usar la variante avanzada sin desbloquearla
"""

import argparse

from temple.interfaz.app import App
from temple.respiracion import TIEMPO_S


def main():
    parser = argparse.ArgumentParser(description="Temple, juego serio con la webcam")
    parser.add_argument("--vueltas", type=int, default=None,
                        help="vueltas de respiracion solo para probar (no se guardan)")
    parser.add_argument("--tiempo", type=float, default=TIEMPO_S, help="segundos por tiempo")
    parser.add_argument("--avanzada", action="store_true",
                        help="variante avanzada disponible sin desbloquearla")
    args = parser.parse_args()
    App(args.vueltas, args.tiempo, args.avanzada).ejecutar()


if __name__ == "__main__":
    main()
