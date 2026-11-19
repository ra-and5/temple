"""Temple. Juego serio de respiracion, meditacion y ejercicio con la webcam.

Uso, desde la raiz del repositorio
    python main.py
    python main.py --vueltas 2      sesion corta para probar (en el juego se eligen con - y +)
    python main.py --avanzada       deja usar la variante avanzada sin desbloquearla
    python main.py --minutos 1      meditacion corta para probar
    python main.py --segundos 5     estiramientos cortos para probar
"""

import argparse

from temple.interfaz.app import App
from temple.interfaz.opciones import Opciones
from temple.respiracion import TIEMPO_S


def main():
    parser = argparse.ArgumentParser(description="Temple, juego serio con la webcam")
    parser.add_argument("--vueltas", type=int, default=None,
                        help="vueltas de respiracion solo para probar (no se guardan)")
    parser.add_argument("--tiempo", type=float, default=TIEMPO_S, help="segundos por tiempo")
    parser.add_argument("--avanzada", action="store_true",
                        help="variante avanzada disponible sin desbloquearla")
    parser.add_argument("--minutos", type=float, default=None,
                        help="minutos de meditacion solo para probar (no cuentan para subir)")
    parser.add_argument("--segundos", type=float, default=None,
                        help="segundos de cada estiramiento solo para probar")
    args = parser.parse_args()
    opciones = Opciones(args.vueltas, args.tiempo, args.avanzada, args.minutos, args.segundos)
    App(opciones).ejecutar()


if __name__ == "__main__":
    main()
