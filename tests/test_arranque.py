"""Pruebas de lo que se usa para arrancar y ensenar Temple.

main.py tiene que pasar bien las opciones de la linea de comandos a la app
(tambien --rapido, que acorta todo para probarlo en pocos minutos), y
herramientas/crear_demo.py tiene que dejar un progreso creible (racha larga,
niveles subidos y hoy sin hacer) para grabar el video sin tocar el de verdad.
"""

import importlib.util
import sys
import tempfile
import unittest
from datetime import date, timedelta
from pathlib import Path
from unittest import mock

import main
from temple.progreso import NIVELES, Progreso

RAIZ = Path(__file__).resolve().parent.parent
HOY = date(2026, 11, 26)  # un jueves, el dia del video


def cargar_demo():
    spec = importlib.util.spec_from_file_location("crear_demo",
                                                  RAIZ / "herramientas" / "crear_demo.py")
    modulo = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(modulo)
    return modulo


class TestMain(unittest.TestCase):
    def arrancar(self, *argumentos):
        with mock.patch.object(sys, "argv", ["main.py", *argumentos]), \
                mock.patch.object(main, "App") as App:
            main.main()
        App.return_value.ejecutar.assert_called_once()
        return App.call_args.args[0]

    def test_sin_opciones_juega_de_verdad(self):
        o = self.arrancar()
        self.assertIsNone(o.vueltas)
        self.assertIsNone(o.minutos)
        self.assertIsNone(o.segundos)
        self.assertFalse(o.avanzada)
        self.assertEqual(o.camara, 0)
        self.assertEqual(o.datos.name, "datos")
        self.assertIsNone(o.flexiones)
        self.assertFalse(o.rapido)
        self.assertFalse(o.prueba)

    def test_las_opciones_llegan_a_la_app(self):
        o = self.arrancar("--vueltas", "2", "--minutos", "1", "--segundos", "5",
                          "--camara", "1", "--avanzada", "--datos", "datos/demo")
        self.assertEqual((o.vueltas, o.minutos, o.segundos, o.camara), (2, 1.0, 5.0, 1))
        self.assertTrue(o.avanzada)
        self.assertEqual(o.datos, Path("datos/demo"))

    def test_rapido_pone_todo_corto_y_no_sube_de_nivel(self):
        o = self.arrancar("--rapido")
        self.assertEqual((o.vueltas, o.minutos, o.segundos, o.flexiones), (1, 1.0, 4.0, 2))
        self.assertTrue(o.rapido)
        self.assertTrue(o.prueba)

    def test_con_rapido_lo_que_se_dice_aparte_manda(self):
        o = self.arrancar("--rapido", "--minutos", "2", "--flexiones", "5")
        self.assertEqual((o.vueltas, o.minutos, o.flexiones), (1, 2.0, 5))

    def test_una_opcion_mal_escrita_no_arranca(self):
        with mock.patch.object(sys, "argv", ["main.py", "--vueltas", "dos"]), \
                mock.patch.object(main, "App") as App, \
                mock.patch("sys.stderr"), self.assertRaises(SystemExit):
            main.main()
        App.assert_not_called()


class TestDemo(unittest.TestCase):
    def setUp(self):
        self.dir = tempfile.TemporaryDirectory()
        self.carpeta = Path(self.dir.name)
        cargar_demo().crear(HOY, self.carpeta)
        self.p = Progreso.cargar(self.carpeta / "progreso.json")

    def tearDown(self):
        self.dir.cleanup()

    def test_hoy_queda_sin_practicar_para_el_ritual(self):
        self.assertTrue(self.p.sesiones)
        self.assertTrue(all(s["fecha"] < HOY.isoformat() for s in self.p.sesiones))
        self.assertFalse(any(self.p.hecha_hoy(f, HOY) for f in NIVELES))

    def test_racha_larga_y_tutoriales_vistos(self):
        self.assertGreaterEqual(self.p.racha(HOY - timedelta(days=1)), 21)
        for fase in NIVELES:
            self.assertTrue(self.p.tutorial_hecho(fase), fase)

    def test_las_flexiones_son_de_los_ultimos_dias(self):
        dias = {s["fecha"] for s in self.p.sesiones if s["fase"] == "flexiones"}
        self.assertTrue(dias)
        self.assertGreaterEqual(min(dias), (HOY - timedelta(days=10)).isoformat())

    def test_se_puede_crear_otra_vez_sin_duplicar(self):
        antes = len(self.p.sesiones)
        cargar_demo().crear(HOY, self.carpeta)
        otra = Progreso.cargar(self.carpeta / "progreso.json")
        self.assertEqual(len(otra.sesiones), antes)

    def test_no_toca_el_progreso_de_verdad(self):
        self.assertEqual(cargar_demo().CARPETA, RAIZ / "datos" / "demo")


if __name__ == "__main__":
    unittest.main()
