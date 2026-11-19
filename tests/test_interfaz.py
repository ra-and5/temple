"""Prueba de humo de la interfaz, sin webcam ni ventana.

Abre la app con una camara falsa y una carpeta de datos temporal, la maneja con
el teclado y comprueba que se puede ir del inicio a una sesion y al resultado
en las tres fases sin que nada falle. No mira como se ve, solo que funciona.
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
from tests import test_estiramientos as T  # noqa: E402
from tests import test_puntero as P  # noqa: E402

DT = 1 / 30


def palma_en(cx, cy):
    """Mano abierta de frente con el centro de la palma en (cx, cy). Dedos rectos hacia arriba."""
    return [(cx, cy + 0.04)] + [(cx + (i // 4 - 2) * 0.03, cy + 0.04 - 0.04 * (i % 4 + 1))
                                for i in range(20)]


def senalando_de_lado():
    """Mano con la forma de senalar pero el indice hacia un lado, como apoyada en la cabeza."""
    return [(0.5 + (0.7 - y), 0.5 + 0.02 * (x - 0.5)) for x, y in P.mano_en(0.5, 0.5)]


class CamaraFalsa:
    """Una persona sentada recta, con los ojos cerrados, que va tapando cada lado."""

    cara = False
    error = None

    def __init__(self):
        self.t = 0.0
        self.postura = None  # en los estiramientos, el cuerpo de tests/test_estiramientos
        self.mano = None  # 21 puntos, o una funcion del tiempo que los da

    def start(self):
        pass

    def parar(self):
        pass

    def join(self, timeout=None):
        pass

    def ultimo(self):
        lado = ("derecho", "izquierdo")[int(self.t / 2) % 2]
        lectura = Lectura(tapado=lado, nariz=(0.5, 0.38), escala=0.3,
                          hombros=((0.35, 0.62), (0.65, 0.62)), ojos=0.9)
        if self.postura is not None:
            c = self.postura
            lectura = Lectura(tapado=lado, nariz=c.nariz, escala=c.escala,
                              hombros=(c.hombro_a, c.hombro_b), orejas=(c.oreja_a, c.oreja_b),
                              codos=(c.codo_a, c.codo_b), munecas=(c.muneca_a, c.muneca_b),
                              vis_munecas=(c.vis_muneca_a, c.vis_muneca_b))
        mano = self.mano(self.t) if callable(self.mano) else self.mano
        if mano is not None:
            lectura.mano = mano
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
        # Lo siguiente del ritual es estirar, y la primera vez con su tutorial
        self.tecla(app, pygame.K_RETURN)
        self.assertEqual((app.modo, app.fase.clave), ("tutorial", "estiramientos"))

    POSTURAS = {"cuerpo": T.NEUTRO, "neutro": T.NEUTRO, "cuello_der": T.CUELLO_DER,
                "cuello_izq": T.CUELLO_IZQ, "arriba": T.ARRIBA, "cruzado_der": T.CRUZADO_DER,
                "cruzado_izq": T.CRUZADO_IZQ, "triceps_der": T.TRICEPS_DER,
                "triceps_izq": T.TRICEPS_IZQ}

    def estirar(self, app, modo, segundos=90):
        """Hace cada postura que pide el guion hasta salir del modo."""
        for _ in range(int(segundos / DT)):
            if app.modo != modo:
                return
            pr = app.fase.practica
            if pr._indice < len(pr.pasos):
                self.camara.postura = self.POSTURAS.get(pr.pasos[pr._indice].objetivo, T.NEUTRO)
            self.correr(app, DT)

    def test_estiramientos_tutorial_y_despues_la_sesion(self):
        app = self.abrir()
        self.camara.postura = T.NEUTRO
        self.tecla(app, pygame.K_i)
        self.tecla(app, pygame.K_SPACE)  # la primera vez, el tutorial
        self.assertEqual((app.modo, app.fase.clave), ("tutorial", "estiramientos"))
        self.estirar(app, "tutorial")
        self.assertEqual(app.modo, "inicio")
        self.assertTrue(self.progreso().tutorial_hecho("estiramientos"))
        self.assertEqual(self.progreso().sesiones, [])  # el tutorial no cuenta como sesion

    def test_estiramientos_espacio_pausa_y_sigue(self):
        app = self.abrir(segundos=2)
        self.camara.postura = T.NEUTRO
        self.tecla(app, pygame.K_i)
        self.tecla(app, pygame.K_s)
        self.correr(app, 1)
        self.tecla(app, pygame.K_SPACE)
        self.assertTrue(app.pausado())
        indice = app.fase.practica._indice
        self.camara.postura = T.CUELLO_DER
        self.correr(app, 3)  # en la pausa el guion no avanza
        self.assertEqual(app.fase.practica._indice, indice)
        self.tecla(app, pygame.K_SPACE)
        self.assertFalse(app.pausado())

    def test_ritual_completo_en_un_dia(self):
        """Respiracion, meditacion y estiramientos seguidos, como un usuario que ya
        ha hecho los tutoriales (la primera vez, el boton de meditar lleva al suyo)."""
        ya = self.progreso()
        for fase in ("respiracion", "meditacion", "estiramientos"):
            ya.marcar_tutorial(fase)
        app = self.abrir(vueltas=1, tiempo_s=0.1, minutos=0.1, segundos=1)
        self.tecla(app, pygame.K_s)
        self.correr(app, 40)
        self.assertEqual((app.modo, app.fase.clave), ("resultado", "respiracion"))
        self.tecla(app, pygame.K_RETURN)  # el boton lleva directo a meditar
        self.assertEqual(app.fase.clave, "meditacion")
        self.correr(app, 25)
        self.assertEqual((app.modo, app.fase.clave), ("resultado", "meditacion"))
        self.camara.postura = T.NEUTRO
        self.tecla(app, pygame.K_RETURN)  # y el de meditar lleva directo a estirar
        self.assertEqual((app.modo, app.fase.clave), ("sesion", "estiramientos"))
        self.estirar(app, "sesion")
        self.assertEqual(app.modo, "resultado")
        progreso = self.progreso()
        for fase in ("respiracion", "meditacion", "estiramientos"):
            self.assertTrue(progreso.hecha_hoy(fase), fase)
        self.assertEqual(progreso.racha(), 1)

    def test_palma_quieta_pausa_la_respiracion(self):
        app = self.abrir(vueltas=1)
        self.tecla(app, pygame.K_s)
        self.correr(app, 1)
        self.camara.mano = palma_en(0.8, 0.4)
        self.correr(app, 1.3)
        self.assertTrue(app.pausado())

    def test_palma_quieta_pausa_la_meditacion_y_bajando_no(self):
        app = self.abrir(minutos=1)
        self.tecla(app, pygame.K_e)
        self.tecla(app, pygame.K_s)
        self.correr(app, 5)
        # La mano abierta bajando desde arriba no pausa
        self.camara.mano = lambda t: palma_en(0.8, 0.1 + 0.25 * (t % 2))
        self.correr(app, 4)
        self.assertFalse(app.pausado())
        # Quieta por encima de los hombros, si (1,5 s)
        self.camara.mano = palma_en(0.8, 0.3)
        self.correr(app, 1.8)
        self.assertTrue(app.pausa_manual)

    def test_mano_apoyada_no_pulsa_nada_en_el_inicio(self):
        app = self.abrir()
        elegida = app.elegida
        self.camara.mano = senalando_de_lado()
        self.correr(app, 5)
        self.assertEqual((app.modo, app.elegida), ("inicio", elegida))
        self.assertIsNone(app.botonera.puntero.objetivo)

    def test_estiramientos_hasta_el_resultado(self):
        posturas = {"cuerpo": T.NEUTRO, "neutro": T.NEUTRO, "cuello_der": T.CUELLO_DER,
                    "cuello_izq": T.CUELLO_IZQ, "arriba": T.ARRIBA,
                    "cruzado_der": T.CRUZADO_DER, "cruzado_izq": T.CRUZADO_IZQ,
                    "triceps_der": T.TRICEPS_DER, "triceps_izq": T.TRICEPS_IZQ}
        app = self.abrir(segundos=1)
        self.camara.postura = T.NEUTRO
        self.tecla(app, pygame.K_i)
        self.assertEqual(app.elegida, "estiramientos")
        self.tecla(app, pygame.K_s)
        for _ in range(int(60 / DT)):
            if app.modo != "sesion":
                break
            pr = app.fase.practica
            if pr._indice < len(pr.pasos):
                self.camara.postura = posturas.get(pr.pasos[pr._indice].objetivo, T.NEUTRO)
            self.correr(app, DT)
        self.assertEqual(app.modo, "resultado")
        sesion = self.progreso().sesiones[0]
        self.assertEqual((sesion["fase"], sesion["estrellas"]), ("estiramientos", 3))
        self.assertTrue((Path(self.dir.name) / "ultimos_estiramientos.csv").exists())
        self.tecla(app, pygame.K_RETURN)
        self.assertEqual(app.modo, "inicio")

    def test_al_estirar_la_palma_no_pausa(self):
        """Con la mano abierta sobre la cabeza no se pausa (prueba de Rares del 19/11)."""
        app = self.abrir(segundos=1)
        self.camara.postura = T.NEUTRO
        self.tecla(app, pygame.K_i)
        self.tecla(app, pygame.K_s)
        app.fase.palma.segundos = 0.01  # si la palma contara, pausaria enseguida
        # Mano abierta encima de la cabeza. Muneca abajo y cada dedo recto hacia arriba
        palma = [(0.5, 0.2)] + [(0.5 + (i // 4 - 2) * 0.03, 0.2 - 0.04 * (i % 4 + 1))
                                for i in range(20)]
        ultimo = self.camara.ultimo
        self.camara.ultimo = lambda: (ultimo()[0], Lectura(**{**ultimo()[1].__dict__,
                                                               "mano": palma}))
        self.correr(app, 2)
        self.assertFalse(app.pausado())
        self.assertEqual(app.fase.palma.llenado, 0)

    def test_escape_vuelve_al_inicio_y_sale(self):
        app = self.abrir()
        self.tecla(app, pygame.K_t)
        self.assertEqual(app.modo, "tutorial")
        self.tecla(app, pygame.K_ESCAPE)
        self.assertEqual(app.modo, "inicio")
        self.tecla(app, pygame.K_ESCAPE)
        self.assertTrue(app.preguntando_salir)
        pygame.event.post(pygame.event.Event(pygame.KEYDOWN, key=pygame.K_RETURN, mod=0))
        self.assertFalse(app.paso(DT))

    def test_salir_pregunta_y_se_puede_volver(self):
        app = self.abrir()
        self.tecla(app, pygame.K_ESCAPE)
        self.assertTrue(app.preguntando_salir)
        self.tecla(app, pygame.K_ESCAPE)
        self.assertFalse(app.preguntando_salir)
        self.assertEqual(app.modo, "inicio")

    def test_salir_con_el_dedo(self):
        app = self.abrir()
        self.correr(app, DT)
        salir = next(b for b in app.botonera.lista if b.accion == app.pedir_salir)
        salir.accion()
        self.correr(app, DT)
        self.assertTrue(app.preguntando_salir)
        si = next(b for b in app.botonera.lista if b.accion == app.salir)
        si.accion()
        self.assertFalse(app.paso(DT))


if __name__ == "__main__":
    unittest.main()
