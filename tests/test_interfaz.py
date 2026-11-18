"""Prueba de humo de la interfaz, sin webcam ni ventana.

Abre la app con una camara falsa y una carpeta de datos temporal, la maneja con
el teclado y comprueba que se puede ir del inicio a una sesion y al resultado
en las dos fases sin que nada falle. No mira como se ve, solo que funciona.
"""

import os
import tempfile
import unittest
from pathlib import Path

os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
os.environ.setdefault("SDL_AUDIODRIVER", "dummy")

import numpy as np  # noqa: E402
import pygame  # noqa: E402

from temple.interfaz.app import App  # noqa: E402
from temple.interfaz.opciones import Opciones  # noqa: E402
from temple.progreso import Progreso  # noqa: E402
from temple.vision import Lectura  # noqa: E402

DT = 1 / 30


class CamaraFalsa:
    """Una persona sentada recta, con los ojos cerrados, que va tapando cada lado."""

    cara = False
    error = None

    def __init__(self):
        self.t = 0.0

    def start(self):
        pass

    def parar(self):
        pass

    def join(self, timeout=None):
        pass

    def ultimo(self):
        lado = ("derecho", "izquierdo")[int(self.t / 2) % 2]
        lectura = Lectura(estado=lado, nariz=(0.5, 0.38), escala=0.3,
                          hombros=((0.35, 0.62), (0.65, 0.62)), ojos=0.9)
        return np.zeros((120, 160, 3), np.uint8), lectura


class TestInterfaz(unittest.TestCase):
    def setUp(self):
        self.dir = tempfile.TemporaryDirectory()
        self.camara = CamaraFalsa()

    def tearDown(self):
        # Sin pygame.quit(), que invalidaria las fuentes que guarda estilo.fuente
        pygame.display.quit()
        self.dir.cleanup()

    def abrir(self, **opciones):
        pygame.display.quit()  # cada app abre su ventana
        return App(Opciones(datos=Path(self.dir.name), **opciones), camara=self.camara)

    def correr(self, app, segundos):
        for _ in range(int(segundos / DT)):
            self.camara.t += DT
            self.assertTrue(app.paso(DT))

    def tecla(self, app, k):
        pygame.event.post(pygame.event.Event(pygame.KEYDOWN, key=k, mod=0))
        self.correr(app, DT)

    def progreso(self):
        return Progreso.cargar(Path(self.dir.name) / "progreso.json")

    def test_respiracion_hasta_el_resultado(self):
        app = self.abrir(vueltas=1, tiempo_s=0.1)
        self.correr(app, 0.5)
        self.assertEqual(app.modo, "inicio")
        self.tecla(app, pygame.K_s)
        self.assertEqual((app.modo, app.fase.clave), ("sesion", "respiracion"))
        self.correr(app, 40)
        self.assertEqual(app.modo, "resultado")
        self.assertEqual(len(self.progreso().sesiones), 1)

    def test_meditacion_con_pausa_hasta_el_resultado(self):
        app = self.abrir(minutos=0.1)
        self.tecla(app, pygame.K_e)
        self.assertEqual(app.elegida, "meditacion")
        self.tecla(app, pygame.K_s)
        self.assertTrue(app.camara.cara)  # el modelo de cara solo al meditar
        self.correr(app, 5)
        self.tecla(app, pygame.K_SPACE)
        self.assertTrue(app.pausado())
        self.correr(app, 1)
        self.tecla(app, pygame.K_SPACE)
        self.assertFalse(app.pausado())
        self.correr(app, 20)
        self.assertEqual(app.modo, "resultado")
        self.assertFalse(app.camara.cara)
        sesion = self.progreso().sesiones[0]
        self.assertEqual((sesion["fase"], sesion["estrellas"]), ("meditacion", 3))
        self.assertTrue((Path(self.dir.name) / "ultima_meditacion.csv").exists())
        self.tecla(app, pygame.K_RETURN)
        self.assertEqual(app.modo, "inicio")

    def test_escape_vuelve_al_inicio_y_sale(self):
        app = self.abrir()
        self.tecla(app, pygame.K_t)
        self.assertEqual(app.modo, "tutorial")
        self.tecla(app, pygame.K_ESCAPE)
        self.assertEqual(app.modo, "inicio")
        pygame.event.post(pygame.event.Event(pygame.KEYDOWN, key=pygame.K_ESCAPE, mod=0))
        self.assertFalse(app.paso(DT))


if __name__ == "__main__":
    unittest.main()
