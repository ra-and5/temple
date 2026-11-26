"""Prueba de humo de la interfaz, sin webcam ni ventana.

Abre la app con una camara falsa y una carpeta de datos temporal, la maneja con
el teclado y comprueba que se puede ir del menu a una sesion y al resultado en
cada fase, hacer el ritual de hoy entero y moverse por los menus sin que nada
falle. No mira como se ve, solo que funciona.
"""

import os
import tempfile
import unittest
from unittest import mock
from datetime import date, timedelta
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
from tests import test_flexiones as TF  # noqa: E402
from tests import test_puntero as P  # noqa: E402
from temple import puntero as PZ  # noqa: E402
from temple.interfaz import estilo as E  # noqa: E402

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
        self.perfil = None  # en las flexiones, el cuerpo de tests/test_flexiones o None si no se ve
        self.flexionando = False

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
        if self.flexionando:
            c = self.perfil
            if c is None:
                lectura = Lectura(tapado=None)
            else:
                lectura = Lectura(tapado="ninguno", nariz=(0.2, 0.55), escala=0.1,
                                  hombros=c.hombros, codos=c.codos, munecas=c.munecas,
                                  caderas=c.caderas, tobillos=c.tobillos, vis_brazos=c.vis_brazos)
        mano = self.mano(self.t) if callable(self.mano) else self.mano
        if mano is not None:
            lectura.mano = mano
        return np.zeros((120, 160, 3), np.uint8), lectura


class ConApp(unittest.TestCase):
    """La app con la camara falsa y una carpeta de datos temporal. Sin tests propios."""

    def setUp(self):
        self.dir = tempfile.TemporaryDirectory()
        self.camara = CamaraFalsa()
        self.app = None

    def tearDown(self):
        if self.app is not None:
            self.app._dejar_practica()  # cierra el registro de la fase que quede a medias
        # Sin pygame.quit(), que invalidaria las fuentes que guarda estilo.fuente
        pygame.display.quit()
        self.dir.cleanup()

    def abrir(self, **opciones):
        pygame.display.quit()  # cada app abre su ventana
        if self.app is not None:
            self.app._dejar_practica()
        self.app = App(Opciones(datos=Path(self.dir.name), **opciones), camara=self.camara)
        return self.app

    def correr(self, app, segundos):
        for _ in range(int(segundos / DT)):
            self.camara.t += DT
            self.assertTrue(app.paso(DT))

    def tecla(self, app, k):
        pygame.event.post(pygame.event.Event(pygame.KEYDOWN, key=k, mod=0))
        self.correr(app, DT)

    def progreso(self):
        return Progreso.cargar(Path(self.dir.name) / "progreso.json")

    def boton(self, app, accion):
        return next(b for b in app.botonera.lista if b.accion == accion)


class TestInterfaz(ConApp):

    def test_los_avisos_no_pisan_la_barra_de_arriba(self):
        """El aviso dorado tapaba el lema (captura del 26/11). Va en el hueco libre."""
        app = self.abrir()
        app.progreso.registrar("meditacion", "normal", 1.0, 3)  # con racha, el hueco es menor
        textos = ["Ya sabes hacer flexiones. Ahora, la sesión completa",
                  "Ya sabes respirar. Ahora, la sesión completa", "Sonido apagado"]
        for texto in textos:
            app.avisar(texto, 5)
            self.correr(app, DT)
            izq, der = app.hueco_aviso
            self.assertGreaterEqual(app.caja_aviso.left, izq, texto)
            self.assertLessEqual(app.caja_aviso.right, der, texto)

    def test_respiracion_hasta_el_resultado(self):
        app = self.abrir(vueltas=1, tiempo_s=0.1)
        self.correr(app, 0.5)
        self.assertEqual(app.modo, "menu")
        self.tecla(app, pygame.K_r)
        self.assertEqual((app.modo, app.fase.clave), ("previa", "respiracion"))
        self.tecla(app, pygame.K_s)
        self.assertEqual((app.modo, app.fase.clave), ("sesion", "respiracion"))
        self.correr(app, 40)
        self.assertEqual(app.modo, "resultado")
        self.assertEqual(len(self.progreso().sesiones), 1)

    def test_meditacion_con_pausa_hasta_el_resultado(self):
        app = self.abrir(minutos=0.1)
        self.tecla(app, pygame.K_e)
        self.assertEqual(app.fase.clave, "meditacion")
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
        self.assertIsNone(sesion["nivel"])  # con --minutos no cuenta para subir
        self.assertTrue((Path(self.dir.name) / "ultima_meditacion.csv").exists())
        # Practicando suelta, el boton principal vuelve a su previa
        self.tecla(app, pygame.K_RETURN)
        self.assertEqual((app.modo, app.fase.clave), ("previa", "meditacion"))

    POSTURAS = {"cuerpo": T.NEUTRO, "neutro": T.NEUTRO, "cuello_der": T.CUELLO_DER,
                "cuello_izq": T.CUELLO_IZQ, "arriba": T.ARRIBA, "cruzado_der": T.CRUZADO_DER,
                "cruzado_izq": T.CRUZADO_IZQ, "triceps_der": T.TRICEPS_DER,
                "triceps_izq": T.TRICEPS_IZQ}

    def estirar_hasta(self, app, objetivo, segundos=30):
        """Hace las posturas del guion hasta llegar a mantener la del objetivo."""
        for _ in range(int(segundos / DT)):
            pr = app.fase.practica
            paso = pr.pasos[pr._indice]
            self.camara.postura = self.POSTURAS.get(paso.objetivo, T.NEUTRO)
            if paso.tipo == "mantener" and paso.objetivo == objetivo:
                self.correr(app, 0.3)
                return
            self.correr(app, DT)
        self.fail(f"no llega a {objetivo}")

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
        self.assertEqual((app.modo, app.fase.clave), ("previa", "estiramientos"))
        self.assertTrue(self.progreso().tutorial_hecho("estiramientos"))
        self.assertEqual(self.progreso().sesiones, [])  # el tutorial no cuenta como sesion
        self.tecla(app, pygame.K_SPACE)  # y ahora Espacio ya es la sesion
        self.assertEqual(app.modo, "sesion")

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

    def test_ritual_de_hoy_fase_tras_fase(self):
        """El boton Ritual de hoy encadena las fases. Tras cada resultado, la previa de la
        siguiente para colocarse."""
        ya = self.progreso()
        for fase in ("respiracion", "meditacion", "estiramientos", "flexiones"):
            ya.marcar_tutorial(fase)
        app = self.abrir(vueltas=1, tiempo_s=0.1, minutos=0.1, segundos=1)
        self.tecla(app, pygame.K_SPACE)  # en el menu, Espacio es el ritual
        self.assertEqual((app.modo, app.fase.clave, app.ritual), ("previa", "respiracion", True))
        self.tecla(app, pygame.K_SPACE)
        self.correr(app, 40)
        self.assertEqual((app.modo, app.fase.clave), ("resultado", "respiracion"))
        self.tecla(app, pygame.K_RETURN)
        self.assertEqual((app.modo, app.fase.clave), ("previa", "meditacion"))
        self.tecla(app, pygame.K_SPACE)
        self.correr(app, 25)
        self.assertEqual((app.modo, app.fase.clave), ("resultado", "meditacion"))
        self.camara.postura = T.NEUTRO
        self.tecla(app, pygame.K_RETURN)
        self.assertEqual((app.modo, app.fase.clave), ("previa", "estiramientos"))
        self.tecla(app, pygame.K_SPACE)
        self.estirar(app, "sesion")
        self.assertEqual(app.modo, "resultado")
        self.assertEqual(app.siguiente_del_ritual().clave, "flexiones")
        self.tecla(app, pygame.K_RETURN)
        self.assertEqual((app.modo, app.fase.clave), ("previa", "flexiones"))
        progreso = self.progreso()
        for fase in ("respiracion", "meditacion", "estiramientos"):
            self.assertTrue(progreso.hecha_hoy(fase), fase)
        self.assertEqual(progreso.racha(), 1)
        # Volver al menu y el ritual sigue por lo que falta
        self.tecla(app, pygame.K_ESCAPE)
        self.assertEqual(app.modo, "menu")
        self.assertEqual(app.faltan_hoy(), ["flexiones"])
        app.empezar_ritual()
        self.assertEqual(app.fase.clave, "flexiones")

    def test_al_acabar_el_ritual_vuelve_al_menu(self):
        app = self.abrir()
        app.ritual = True
        app.abrir_fase("flexiones")
        self.assertIsNone(app.siguiente_del_ritual())
        app.tras_resultado()
        self.assertEqual((app.modo, app.ritual), ("menu", False))

    def test_subir_de_nivel_se_dice_en_el_resultado(self):
        ya = self.progreso()
        for d in range(1, 5):  # 4 dias antes, con 3 lotos
            ya.registrar("flexiones", "facil", 0.9, 3, date.today() - timedelta(days=d), nivel=0)
        app = self.abrir()
        fase = app.fases["flexiones"]
        fase.nivel = 0
        fase.guardar(0.95, 3)
        self.assertIn("Subes al nivel 2", fase.resultado["linea"][0])
        self.assertEqual(app.progreso.nivel("flexiones"), 1)
        fase.guardar(0.95, 3)
        self.assertIn("nivel más bajo", fase.resultado["linea"][0])
        fase.nivel = 1
        fase.guardar(0.95, 3)
        self.assertIn("Día contado para subir, 1 de 5", fase.resultado["linea"][0])
        fase.guardar(0.95, 3)  # otra el mismo dia ya no cuenta
        self.assertIn("Hoy ya contaba", fase.resultado["linea"][0])
        fase.guardar(0.6, 1)
        self.assertIn("3 lotos", fase.resultado["linea"][0])

    def test_los_estiramientos_son_calentamiento(self):
        app = self.abrir()
        fase = app.fases["estiramientos"]
        fase.guardar(0.95, 3)
        self.assertIn("Listo para las flexiones", fase.resultado["linea"][0])
        self.tecla(app, pygame.K_i)
        self.tecla(app, pygame.K_RIGHT)  # no hay niveles que cambiar
        self.assertEqual(app.progreso.nivel_elegido("estiramientos"), 0)

    def test_elegir_nivel_en_la_previa(self):
        ya = self.progreso()
        for d in range(5):
            ya.registrar("flexiones", "facil", 0.9, 3, date.today() - timedelta(days=d), nivel=0)
        app = self.abrir()
        self.tecla(app, pygame.K_x)
        self.assertEqual(app.progreso.nivel_elegido("flexiones"), 1)
        self.tecla(app, pygame.K_LEFT)
        self.assertEqual(app.progreso.nivel_elegido("flexiones"), 0)
        self.tecla(app, pygame.K_s)
        self.assertEqual((app.fase.nivel, app.fase.variante), (0, "facil"))

    def test_en_la_pausa_palma_y_puno_siguen(self):
        app = self.abrir(vueltas=1)
        self.tecla(app, pygame.K_r)
        self.tecla(app, pygame.K_s)
        self.correr(app, 1)
        self.tecla(app, pygame.K_SPACE)
        self.assertTrue(app.pausa_manual)
        self.camara.mano = P.mano_en(0.8, 0.4, abierta=True)
        self.correr(app, 0.6)
        self.assertEqual(app.puno.estado, "cierra")
        self.assertTrue(app.pausa_manual)
        self.camara.mano = P.mano_en(0.8, 0.4, puno=True)
        self.correr(app, 0.2)
        self.assertFalse(app.pausa_manual)

    # ---- la palma pausa en las cuatro fases y la palma y el puno siguen ----

    def pausar_y_seguir(self, app, donde):
        """Palma abierta y quieta pausa. Luego palma y puno siguen, y todo avanza otra vez."""
        self.assertFalse(app.pausado(), donde)
        self.camara.mano = palma_en(0.8, 0.4)
        self.correr(app, 1.7)  # 1 s, y 1,5 s al meditar
        self.assertTrue(app.pausa_manual, f"{donde}, la palma no pausa")
        self.camara.mano = None
        self.correr(app, 2)
        self.assertTrue(app.pausa_manual, f"{donde}, sigue solo sin el puno")
        self.camara.mano = P.mano_en(0.8, 0.4, abierta=True)
        self.correr(app, 0.6)
        self.camara.mano = P.mano_en(0.8, 0.4, puno=True)
        self.correr(app, 0.2)
        self.assertFalse(app.pausa_manual, f"{donde}, el puno no sigue")
        self.camara.mano = None

    def test_la_palma_pausa_en_cualquier_paso_de_cada_fase(self):
        """En el tutorial y en la sesion, nada mas empezar y a mitad. En los
        estiramientos va aparte, porque la palma solo pausa entre posturas."""
        for clave, tecla in (("respiracion", pygame.K_r), ("meditacion", pygame.K_e),
                             ("flexiones", pygame.K_x)):
            for modo in (pygame.K_t, pygame.K_s):
                for espera in (0.2, 4):
                    app = self.abrir(minutos=1, segundos=30)
                    self.camara.postura = T.NEUTRO
                    self.camara.flexionando = clave == "flexiones"
                    self.camara.perfil = TF.ARRIBA
                    self.tecla(app, tecla)
                    self.tecla(app, modo)
                    self.correr(app, espera)
                    self.pausar_y_seguir(app, f"{clave}, {pygame.key.name(modo)}, a los {espera} s")
                    self.camara.flexionando = False

    def test_en_la_pausa_nada_avanza(self):
        app = self.abrir(segundos=30)
        self.camara.postura = T.NEUTRO
        self.tecla(app, pygame.K_i)
        self.tecla(app, pygame.K_s)
        self.correr(app, 1)
        self.tecla(app, pygame.K_SPACE)
        self.assertTrue(app.pausa_manual)
        reloj = app.fase.reloj
        self.camara.mano = None
        self.correr(app, 3)
        self.assertEqual(app.fase.reloj, reloj)

    def test_flexiones_la_palma_pausa_contando(self):
        app = self.abrir()
        self.tecla(app, pygame.K_x)
        self.tecla(app, pygame.K_s)
        self.hasta_contar(app)
        self.pausar_y_seguir(app, "flexiones contando")
        self.camara.flexionando = False

    def test_el_aro_de_pausa_no_queda_en_el_menu(self):
        app = self.abrir(vueltas=1)
        self.tecla(app, pygame.K_r)
        self.tecla(app, pygame.K_s)
        self.correr(app, 1)
        self.camara.mano = palma_en(0.8, 0.4)
        self.correr(app, 0.5)  # el aro a medias
        self.assertGreater(app.fase.palma.llenado, 0)
        self.tecla(app, pygame.K_ESCAPE)
        self.assertEqual(app.fase.palma.llenado, 0)

    def test_palma_quieta_pausa_la_respiracion(self):
        app = self.abrir(vueltas=1)
        self.tecla(app, pygame.K_r)
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

    def test_mano_apoyada_no_pulsa_nada_en_el_menu(self):
        app = self.abrir()
        self.camara.mano = senalando_de_lado()
        self.correr(app, 5)
        self.assertEqual(app.modo, "menu")
        self.assertIsNone(app.botonera.puntero.objetivo)

    def test_estiramientos_hasta_el_resultado(self):
        app = self.abrir(segundos=1)
        self.camara.postura = T.NEUTRO
        self.tecla(app, pygame.K_i)
        self.assertEqual(app.fase.clave, "estiramientos")
        self.tecla(app, pygame.K_s)
        self.estirar(app, "sesion", 60)
        self.assertEqual(app.modo, "resultado")
        sesion = self.progreso().sesiones[0]
        self.assertEqual((sesion["fase"], sesion["estrellas"]), ("estiramientos", 3))
        self.assertTrue((Path(self.dir.name) / "ultimos_estiramientos.csv").exists())
        self.tecla(app, pygame.K_ESCAPE)
        self.assertEqual(app.modo, "menu")

    def test_al_estirar_la_palma_no_pausa(self):
        """Con la mano abierta sobre la cabeza haciendo la postura no se pausa (prueba
        de Rares del 19/11). Fuera de la postura la palma si pausa."""
        app = self.abrir(segundos=30)
        self.camara.postura = T.NEUTRO
        self.tecla(app, pygame.K_i)
        self.tecla(app, pygame.K_s)
        self.estirar_hasta(app, "cuello_der")  # mano derecha sobre la cabeza, en la postura
        self.assertTrue(app.fase.estirando())
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

    def _con_palma(self, cx, muneca_y):
        """La camara ve ademas una palma abierta y de frente con la muneca ahi."""
        palma = [(cx, muneca_y)] + [(cx + (i // 4 - 2) * 0.03, muneca_y - 0.04 * (i % 4 + 1))
                                    for i in range(20)]
        ultimo = self.camara.ultimo
        self.camara.ultimo = lambda: (ultimo()[0], Lectura(**{**ultimo()[1].__dict__,
                                                               "mano": palma}))

    def test_al_estirar_la_mano_en_el_codo_no_pausa(self):
        """La mano abierta que sujeta el codo, por debajo de los hombros, no pausa
        aunque la postura falle un momento (prueba de Rares del 26/11)."""
        app = self.abrir(segundos=30)
        self.camara.postura = T.NEUTRO
        self.tecla(app, pygame.K_i)
        self.tecla(app, pygame.K_s)
        self.estirar_hasta(app, "cuello_der")
        self.camara.postura = T.NEUTRO  # la postura se pierde
        self._con_palma(0.8, 0.9)  # palma abierta a la altura del pecho
        self.correr(app, 4)
        self.assertFalse(app.pausado())

    def test_al_estirar_la_palma_no_pausa_en_mitad_de_una_postura(self):
        """Ni colocandote ni manteniendo una postura, aunque este por encima de los
        hombros (la mano en el codo del triceps, prueba de Rares del 26/11)."""
        app = self.abrir(segundos=30)
        self.camara.postura = T.NEUTRO
        self.tecla(app, pygame.K_i)
        self.tecla(app, pygame.K_s)
        self.estirar_hasta(app, "cuello_der")
        self.camara.postura = T.NEUTRO
        self._con_palma(0.85, 0.4)
        self.correr(app, 5)
        self.assertFalse(app.pausado())

    def test_al_estirar_la_palma_pausa_entre_posturas(self):
        app = self.abrir(segundos=1)
        self.camara.postura = T.NEUTRO
        self.tecla(app, pygame.K_i)
        self.tecla(app, pygame.K_s)
        self.estirar_hasta(app, "cuello_der")
        self.correr(app, 1.5)  # acaba la postura y pide volver al centro
        self.assertEqual(app.fase.estado.paso.objetivo, "neutro")
        self.camara.mano = palma_en(0.85, 0.4)  # sigue inclinado, sin volver al centro
        self.correr(app, 1.5)  # dentro del margen despues de la postura, no pausa
        self.assertFalse(app.pausado())
        self.correr(app, 2.5)
        self.assertTrue(app.pausado())
        self.camara.mano = None

    def test_escape_va_hacia_atras_hasta_salir(self):
        app = self.abrir()
        self.tecla(app, pygame.K_r)
        self.tecla(app, pygame.K_t)
        self.assertEqual(app.modo, "tutorial")
        for esperado in ("previa", "fases", "menu", "salir"):
            self.tecla(app, pygame.K_ESCAPE)
            self.assertEqual(app.modo, esperado)
        pygame.event.post(pygame.event.Event(pygame.KEYDOWN, key=pygame.K_RETURN, mod=0))
        self.assertFalse(app.paso(DT))

    def test_salir_pregunta_y_se_puede_volver(self):
        app = self.abrir()
        self.tecla(app, pygame.K_ESCAPE)
        self.assertEqual(app.modo, "salir")
        self.tecla(app, pygame.K_ESCAPE)
        self.assertEqual(app.modo, "menu")

    def test_cada_pantalla_del_menu_se_dibuja(self):
        app = self.abrir()
        for modo in ("menu", "fases", "progreso", "ajustes", "salir"):
            app.ir(modo)
            self.correr(app, DT)
            self.assertTrue(app.botonera.lista, modo)
        for clave in app.fases:
            app.abrir_fase(clave)
            self.correr(app, DT)
            self.assertEqual(app.modo, "previa")

    def test_ajustes_sonido_pantalla_completa_y_vueltas(self):
        app = self.abrir()
        self.tecla(app, pygame.K_f)
        self.assertTrue(app.ventana.completa)
        app.ir("ajustes")
        self.correr(app, DT)
        self.boton(app, app.ventana.alternar_pantalla_completa).accion()
        self.assertFalse(app.ventana.completa)
        activo = app.sonido.activo
        self.boton(app, app.alternar_sonido).accion()
        self.assertNotEqual(app.sonido.activo, activo)
        self.tecla(app, pygame.K_RIGHT)
        self.assertEqual(self.progreso().vueltas(5), 6)

    def test_tu_progreso_se_abre_y_se_cierra(self):
        ya = self.progreso()
        ya.registrar("respiracion", "principiante", 0.9, 3, vueltas=5)
        ya.registrar("meditacion", "normal", 0.8, 2, minutos=5)
        app = self.abrir()
        app.ir("progreso")
        self.correr(app, DT)
        self.assertEqual(app.progreso.dias_para_subir("respiracion"), 1)
        self.assertEqual(app.progreso.dias_para_subir("meditacion"), 0)  # con 2 lotos no
        self.boton(app, app.atras).accion()
        self.assertEqual(app.modo, "menu")

    def apuntar_dedo(self, boton):
        """La mano senalando, colocada para que el cursor caiga en el centro del boton."""
        x, y, w, h = E.PANEL
        fx, fy = (boton.rect.centerx - x) / w, (boton.rect.centery - y) / h
        return P.mano_en(PZ.ZONA_X[0] + fx * (PZ.ZONA_X[1] - PZ.ZONA_X[0]),
                         PZ.ZONA_Y[0] + fy * (PZ.ZONA_Y[1] - PZ.ZONA_Y[0]))

    def casilla(self, app, texto):
        return next(b for b in app.botonera.lista if b.grupo == "ritual" and b.texto == texto)

    def test_fila_del_ritual_con_las_flechas(self):
        app = self.abrir()
        self.correr(app, DT)
        self.tecla(app, pygame.K_DOWN)  # la fila del ritual es lo primero
        self.assertEqual(app.botonera.lista[app.botonera.foco].texto, "Respiración")
        self.tecla(app, pygame.K_RIGHT)
        self.tecla(app, pygame.K_RIGHT)
        self.assertEqual(app.botonera.lista[app.botonera.foco].texto, "Estiramientos")
        self.assertEqual(app.modo, "menu")  # moverse no abre nada
        self.tecla(app, pygame.K_RETURN)
        self.assertEqual((app.modo, app.fase.clave, app.ritual), ("previa", "estiramientos", True))
        self.assertEqual(app.siguiente_del_ritual().clave, "flexiones")  # y sigue en orden
        self.tecla(app, pygame.K_ESCAPE)
        self.assertEqual(app.modo, "menu")
        self.tecla(app, pygame.K_DOWN)
        self.tecla(app, pygame.K_DOWN)  # la fila cuenta como una parada, abajo esta el Ritual
        self.assertEqual(app.botonera.lista[app.botonera.foco].texto, "Ritual de hoy")

    def test_fila_del_ritual_con_el_raton(self):
        app = self.abrir()
        self.correr(app, DT)
        self.assertTrue(app.botonera.clic(self.casilla(app, "Meditación").rect.center))
        self.assertEqual((app.modo, app.fase.clave, app.ritual), ("previa", "meditacion", True))

    def test_fila_del_ritual_con_el_dedo(self):
        app = self.abrir()
        self.correr(app, DT)
        dedo = self.apuntar_dedo(self.casilla(app, "Flexiones"))
        self.camara.mano = dedo
        self.correr(app, 0.5)
        self.camara.mano = None  # al aparecer senalando hay que soltar antes
        self.correr(app, 1)
        self.camara.mano = dedo
        self.correr(app, 2.5)
        self.assertEqual((app.modo, app.fase.clave, app.ritual), ("previa", "flexiones", True))

    def test_salir_con_el_dedo(self):
        app = self.abrir()
        self.correr(app, DT)
        self.boton(app, app.pedir_salir).accion()
        self.correr(app, DT)
        self.assertEqual(app.modo, "salir")
        self.boton(app, app.salir).accion()
        self.assertFalse(app.paso(DT))

    def test_salir_con_el_dedo_sin_bajar_la_mano(self):
        """Senalar Salir y luego el Si sin dejar de senalar (a Rares no le dejaba, 19/11)."""
        app = self.abrir()

        def hacia(accion):
            boton = self.boton(app, accion)
            x, y, w, h = E.PANEL
            fx, fy = (boton.rect.centerx - x) / w, (boton.rect.centery - y) / h
            return P.mano_en(PZ.ZONA_X[0] + fx * (PZ.ZONA_X[1] - PZ.ZONA_X[0]),
                             PZ.ZONA_Y[0] + fy * (PZ.ZONA_Y[1] - PZ.ZONA_Y[0]))

        self.correr(app, DT)
        self.camara.mano = hacia(app.pedir_salir)
        self.correr(app, 0.5)
        self.camara.mano = None  # al aparecer senalando hay que soltar antes
        self.correr(app, 1)
        self.camara.mano = hacia(app.pedir_salir)
        self.correr(app, 2.5)
        self.assertEqual(app.modo, "salir")
        self.camara.mano = hacia(app.salir)
        for _ in range(int(3 / DT)):
            self.camara.t += DT
            if not app.paso(DT):
                break
        self.assertTrue(app.cerrar)

    # ================= flexiones =================

    def flexionar(self, app, abajo=TF.ABAJO, segundos=90):
        """En plancha mientras espera, y bajando y subiendo cada 1,2 s cuando cuenta."""
        self.camara.flexionando = True
        for _ in range(int(segundos / DT)):
            if app.modo not in ("tutorial", "sesion"):
                return
            pr = app.fase.practica
            contando = pr.indice < len(pr.pasos) and pr.pasos[pr.indice].tipo == "contar"
            if contando and self.camara.t % 1.2 < 0.6:
                self.camara.perfil = abajo
            else:
                self.camara.perfil = TF.ARRIBA
            self.correr(app, DT)
        self.fail(f"las flexiones no acaban en {segundos} s")

    def hasta_contar(self, app):
        self.camara.flexionando = True
        self.camara.perfil = TF.ARRIBA
        for _ in range(int(20 / DT)):
            pr = app.fase.practica
            if pr.pasos[pr.indice].tipo == "contar":
                return
            self.correr(app, DT)
        self.fail("no llega a contar flexiones")

    def test_flexiones_tutorial_y_despues_la_sesion(self):
        app = self.abrir()
        self.tecla(app, pygame.K_x)
        self.assertEqual((app.modo, app.fase.clave), ("previa", "flexiones"))
        self.tecla(app, pygame.K_SPACE)  # la primera vez, el tutorial
        self.assertEqual(app.modo, "tutorial")
        self.flexionar(app)
        self.assertEqual((app.modo, app.fase.clave), ("previa", "flexiones"))
        self.assertTrue(self.progreso().tutorial_hecho("flexiones"))
        self.assertEqual(self.progreso().sesiones, [])  # el tutorial no cuenta como sesion
        self.tecla(app, pygame.K_SPACE)
        self.assertEqual(app.modo, "sesion")

    def test_flexiones_hasta_el_resultado(self):
        app = self.abrir()
        self.tecla(app, pygame.K_x)
        self.tecla(app, pygame.K_d)  # con los datos y el esqueleto a la vista, que tambien se dibujan
        self.tecla(app, pygame.K_s)
        self.flexionar(app)
        self.assertEqual(app.modo, "resultado")
        sesion = self.progreso().sesiones[0]
        self.assertEqual((sesion["fase"], sesion["variante"], sesion["estrellas"]),
                         ("flexiones", "facil", 3))
        self.assertEqual(app.fase.practica.hechas, 5)
        self.assertEqual(app.fase.resultado["peor"], "")
        registro = Path(self.dir.name) / "ultimas_flexiones.csv"
        self.assertTrue(registro.exists())
        self.assertGreater(len(registro.read_text(encoding="utf-8").splitlines()), 10)
        self.tecla(app, pygame.K_ESCAPE)
        self.assertEqual(app.modo, "menu")

    def test_flexiones_con_la_cadera_hundida_no_dan_lotos(self):
        app = self.abrir()
        self.tecla(app, pygame.K_x)
        self.tecla(app, pygame.K_s)
        self.hasta_contar(app)
        self.flexionar(app, abajo=TF.HUNDIDA)
        self.assertEqual(app.modo, "resultado")
        self.assertEqual(self.progreso().sesiones[0]["estrellas"], 0)
        self.assertEqual(app.fase.resultado["peor"], "cadera")
        self.correr(app, 0.5)  # el resultado se dibuja con su consejo
        self.assertEqual(app.modo, "resultado")

    def test_flexiones_cada_aviso_sale_en_su_momento(self):
        app = self.abrir()
        self.tecla(app, pygame.K_x)
        self.tecla(app, pygame.K_s)
        self.hasta_contar(app)
        fase = app.fase
        self.camara.perfil = TF.HUNDIDA
        self.correr(app, 0.6)
        self.camara.perfil = TF.ARRIBA
        self.correr(app, 0.6)
        self.assertEqual(fase.ultimo, "cadera")
        self.camara.perfil = TF.ABAJO
        self.correr(app, 0.6)
        self.camara.perfil = TF.ARRIBA
        self.correr(app, 0.6)
        self.assertEqual(fase.ultimo, "bien")
        self.assertEqual((fase.practica.hechas, fase.practica.buenas), (2, 1))

    def test_flexiones_si_te_vas_se_pausa_y_al_volver_sigue(self):
        app = self.abrir()
        self.tecla(app, pygame.K_x)
        self.tecla(app, pygame.K_s)
        self.hasta_contar(app)
        self.camara.perfil = None  # te levantas y sales de la camara
        self.correr(app, 2)
        self.assertTrue(app.pausado())
        self.assertEqual(app.modo, "sesion")
        self.assertEqual(app.fase.practica.hechas, 0)
        self.camara.perfil = TF.ARRIBA
        self.correr(app, DT * 2)
        self.assertFalse(app.pausado())

    def test_flexiones_con_espacio_se_pausa_y_no_cuenta(self):
        app = self.abrir()
        self.tecla(app, pygame.K_x)
        self.tecla(app, pygame.K_s)
        self.hasta_contar(app)
        self.tecla(app, pygame.K_SPACE)
        self.assertTrue(app.pausado())
        for _ in range(2):  # en la pausa las flexiones no cuentan
            self.camara.perfil = TF.ABAJO
            self.correr(app, 0.6)
            self.camara.perfil = TF.ARRIBA
            self.correr(app, 0.6)
        self.assertEqual(app.fase.practica.hechas, 0)
        self.tecla(app, pygame.K_SPACE)
        self.assertFalse(app.pausado())

    def test_flexiones_escape_vuelve_a_la_previa(self):
        app = self.abrir()
        self.tecla(app, pygame.K_x)
        self.tecla(app, pygame.K_s)
        self.hasta_contar(app)
        self.tecla(app, pygame.K_ESCAPE)
        self.assertEqual(app.modo, "previa")
        self.assertIsNone(app.fase.registro)  # el registro se cierra al salir
        self.assertEqual(self.progreso().sesiones, [])

    def test_rapido_acorta_los_textos_de_cada_fase(self):
        from temple.interfaz.opciones import MENSAJE_RAPIDO_S
        app = self.abrir(rapido=True)
        for clave in app.fases:
            for modo in ("tutorial", "sesion"):
                app.abrir_fase(clave)
                app.empezar(modo)
                mensajes = [p for p in app.fase.pasos() if p.tipo == "mensaje"]
                self.assertTrue(mensajes, (clave, modo))
                self.assertTrue(all(p.duracion <= MENSAJE_RAPIDO_S for p in mensajes),
                                (clave, modo))
        app.ir_menu()

    def test_rapido_flexiones_en_segundos_y_sin_subir(self):
        app = self.abrir(rapido=True, flexiones=2)
        self.tecla(app, pygame.K_x)
        self.tecla(app, pygame.K_s)
        inicio = self.camara.t
        self.flexionar(app)
        self.assertEqual(app.modo, "resultado")
        self.assertEqual(app.fase.practica.hechas, 2)
        self.assertLess(self.camara.t - inicio, 12)  # sin --rapido pasa de 20 s
        self.assertIn("opciones de prueba", app.fase.resultado["linea"][0])
        self.assertIsNone(self.progreso().sesiones[0]["nivel"])

    def test_cerrar_la_ventana_a_mitad_guarda_el_registro(self):
        app = self.abrir()
        self.tecla(app, pygame.K_x)
        self.tecla(app, pygame.K_s)
        self.hasta_contar(app)
        archivo = app.fase.registro.archivo
        self.assertFalse(archivo.closed)
        pygame.event.post(pygame.event.Event(pygame.QUIT))
        with mock.patch("pygame.quit"):  # pygame.quit borraria las fuentes de los demas tests
            app.ejecutar()
        self.assertTrue(archivo.closed)
        self.assertIsNone(app.fase.registro)
        lineas = (Path(self.dir.name) / "ultimas_flexiones.csv").read_text(encoding="utf-8")
        self.assertGreater(len(lineas.splitlines()), 10)


class TestTodosLosBotones(ConApp):
    """Recorre todas las pantallas en todos sus estados y mira cada boton por dentro.

    Que el texto, la tecla y la etiqueta quepan en el boton sin pisarse, que la
    letra no baje de lo legible y que ningun boton pise a otro. Sale de la
    captura de Rares del 25/11, con "Seguir: Meditación" encima de "Espacio".
    """

    def setUp(self):
        super().setUp()
        self.vistos = {}  # texto del boton -> pantalla donde se vio

    def mirar(self, app, pantalla):
        self.correr(app, DT)
        lista = app.botonera.lista
        self.assertTrue(lista, f"{pantalla} sin botones")
        ventana = pygame.Rect(0, 0, E.ANCHO, E.ALTO)
        for b in lista:
            donde = f"{pantalla}, boton {b.texto!r}"
            self.assertTrue(ventana.contains(b.rect), f"{donde} se sale de la ventana")
            self.assertGreaterEqual(b.letra, 15, f"{donde} con letra demasiado pequena")
            dentro = b.rect.inflate(-6, -4)
            for pieza in b.piezas:
                self.assertTrue(dentro.contains(pieza), f"{donde} tiene algo fuera del boton")
            for i, a in enumerate(b.piezas):
                for c in b.piezas[i + 1:]:
                    self.assertFalse(a.colliderect(c), f"{donde} se pisa por dentro")
            self.vistos.setdefault(b.texto, pantalla)
        for i, a in enumerate(lista):
            for c in lista[i + 1:]:
                self.assertFalse(a.rect.colliderect(c.rect),
                                 f"{pantalla}, {a.texto!r} pisa {c.texto!r}")

    def test_menus(self):
        app = self.abrir()
        self.mirar(app, "menu sin nada hecho")
        app.ir("fases")
        self.mirar(app, "practicar una fase")
        app.ir("progreso")
        self.mirar(app, "tu progreso")
        app.ir("salir")
        self.mirar(app, "salir")
        app.ir("ajustes")
        for vueltas in range(12):  # de mas a menos, pasando por el minimo y el maximo
            app.cambiar_vueltas(1 if vueltas < 6 else -1)
            self.mirar(app, f"ajustes, paso {vueltas}")
        app.alternar_sonido()
        app.ventana.completa = True  # solo cambia el texto, sin abrir pantalla completa
        self.mirar(app, "ajustes, sin sonido y en pantalla completa")
        app.ventana.completa = False
        for clave in app.fases:
            app.fases[clave].guardar(0.9, 3)
        app.ir_menu()
        self.mirar(app, "menu con todo hecho hoy")
        app.ir("fases")
        self.mirar(app, "practicar una fase con marcas")
        for texto in ("Ritual de hoy", "Repetir el ritual", "Practicar una fase", "Tu progreso",
                      "Ajustes", "Salir", "Sí, salir", "No, seguir aquí", "Sonido activado",
                      "Sonido apagado", "Pantalla completa", "Salir de pantalla completa", "−",
                      "+", "Volver", "Respiración", "Meditación", "Estiramientos", "Flexiones"):
            self.assertIn(texto, self.vistos)

    def test_antes_de_empezar_cada_fase_en_cada_nivel(self):
        app = self.abrir()
        for primera in (True, False):
            for ritual in (False, True):
                for clave in app.fases:
                    if not primera:
                        app.progreso.marcar_tutorial(clave)
                    app.ritual = ritual
                    app.abrir_fase(clave)
                    for n in range(4):  # sube hasta el ultimo nivel y uno mas
                        self.mirar(app, f"previa de {clave}, nivel {n + 1}")
                        app.cambiar_nivel(1)
        for texto in ("Aprender con el tutorial", "Ir directo a la sesión", "Empezar",
                      "Repasar el tutorial", "Menú", "Volver"):
            self.assertIn(texto, self.vistos)

    def test_pausa_de_cada_fase(self):
        app = self.abrir()
        for clave in app.fases:
            for modo in ("tutorial", "sesion"):
                app.abrir_fase(clave)
                app.empezar(modo)
                self.correr(app, 0.5)
                app.pausa_manual = True
                self.mirar(app, f"pausa de {clave} en {modo}")
        app.abrir_fase("meditacion")
        app.empezar("sesion")
        app.fase._libre = lambda: True  # meditar sin limite pausa con Terminar
        self.correr(app, 0.5)
        app.pausa_manual = True
        self.mirar(app, "pausa de la meditacion sin limite")
        for texto in ("Seguir", "Salir", "Terminar"):
            self.assertIn(texto, self.vistos)
        app.ir_menu()

    def test_resultado_de_cada_fase(self):
        app = self.abrir()
        claves = list(app.fases)
        for ritual in (True, False):
            for i, clave in enumerate(claves):
                app.ritual = ritual
                app.fase = app.fases[clave]
                app.fase.guardar(0.9, 3 if i % 2 else 1)  # con y sin consejo
                app.fase.resultado.setdefault("peor", "")
                app.modo = "resultado"
                self.mirar(app, f"resultado de {clave}, ritual {ritual}")
        for clave in claves[1:]:
            self.assertIn(f"Seguir: {app.fases[clave].nombre}", self.vistos)
        for texto in ("Ritual de hoy completo", "Otra vez", "Menú"):
            self.assertIn(texto, self.vistos)
        boton = next(b for b in app.botonera.lista if b.texto == "Otra vez")
        self.assertEqual(len(boton.piezas), 2)  # con sitio, la tecla sale

    def test_el_texto_mas_largo_quita_la_tecla_antes_que_encoger(self):
        app = self.abrir()
        app.ritual = True
        app.fase = app.fases["meditacion"]
        app.fase.guardar(0.9, 3)
        app.modo = "resultado"
        self.mirar(app, "resultado de la meditacion en el ritual")
        seguir = next(b for b in app.botonera.lista if b.texto.startswith("Seguir"))
        self.assertEqual(seguir.texto, "Seguir: Estiramientos")
        self.assertEqual(len(seguir.piezas), 1)  # sin "Espacio", que ya esta en la ayuda
        self.assertGreaterEqual(seguir.letra, 17)


class TestQueNadaSePise(unittest.TestCase):
    """Los textos de todos los pasos caben y el circulo no los tapa (captura de Rares, 25/11)."""

    def test_el_detalle_acaba_antes_del_circulo(self):
        from temple import estiramientos as S
        from temple import flexiones as F
        from temple import meditacion as M
        from temple import respiracion as R
        from temple.interfaz import piezas as Z
        pygame.font.init()
        superficie = pygame.Surface((E.ANCHO, E.ALTO))
        self.assertLess(Z.FIN_TEXTO, Z.CENTRO[1] - Z.RADIO - 7)
        guiones = (R.guion_tutorial() + R.guion_sesion(5, True) + M.guion_tutorial()
                   + M.guion_sesion(5) + S.guion_tutorial() + S.guion_sesion()
                   + F.guion_tutorial() + F.guion_sesion())
        for paso in guiones:
            if paso.detalle:
                fin = Z.parrafo(superficie, paso.detalle, "texto", 24, E.APAGADO, E.PANEL.top + 150)
                self.assertLessEqual(fin, Z.FIN_TEXTO, paso.detalle)


if __name__ == "__main__":
    unittest.main()
