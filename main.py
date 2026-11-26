"""Temple. Juego serio de respiracion, meditacion y ejercicio con la webcam.

Uso, desde la raiz del repositorio
    python main.py
    python main.py --vueltas 2      sesion corta para probar (en el juego se eligen con - y +)
    python main.py --avanzada       deja usar la variante avanzada sin desbloquearla
    python main.py --minutos 1      meditacion corta para probar
    python main.py --segundos 5     estiramientos cortos para probar
    python main.py --camara 1       usar otra camara si hay varias
    python main.py --flexiones 2    sesion de flexiones corta para probar
    python main.py --datos datos/demo   jugar con otro progreso (el de herramientas/crear_demo.py)
    python main.py --rapido         todo corto a la vez, para probarlo entero en unos minutos
                                    (1 vuelta, 1 min de meditacion, 4 s por postura, 2 flexiones
                                    y los textos de paso de 1,5 s). Se puede combinar con las otras
"""

import argparse
from pathlib import Path

from temple.interfaz.app import App
from temple.interfaz.opciones import RAPIDO, Opciones
from temple.respiracion import TIEMPO_S


def main():
    """Lee las opciones de la terminal y arranca la aplicación."""
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
    parser.add_argument("--flexiones", type=int, default=None,
                        help="flexiones de la sesion solo para probar")
    parser.add_argument("--rapido", action="store_true",
                        help="todo corto para probar el juego entero en unos minutos "
                             "(no cuenta para subir de nivel)")
    parser.add_argument("--camara", type=int, default=0,
                        help="que camara usar si hay varias (0 la primera, 1 la segunda...)")
    parser.add_argument("--datos", type=Path, default=None,
                        help="carpeta del progreso, para ensenar el juego sin tocar el tuyo")
    args = parser.parse_args()
    if args.rapido:
        for opcion, valor in RAPIDO.items():
            if getattr(args, opcion) is None:  # lo que se diga aparte manda
                setattr(args, opcion, valor)
    extra = {"datos": args.datos} if args.datos else {}
    opciones = Opciones(args.vueltas, args.tiempo, args.avanzada, args.minutos, args.segundos,
                        camara=args.camara, flexiones=args.flexiones, rapido=args.rapido,
                        **extra)
    App(opciones).ejecutar()


if __name__ == "__main__":
    main()
