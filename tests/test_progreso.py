"""Pruebas del progreso. Se ejecutan con
    python -m unittest discover tests
"""

import tempfile
import unittest
from datetime import date, timedelta
from pathlib import Path

from temple.progreso import (DIAS_PARA_SUBIR, ESCALERA, LIBRE, NIVELES, VUELTAS_MAX, VUELTAS_MIN,
                             Progreso)


class TestProgreso(unittest.TestCase):
    def setUp(self):
        self.dir = tempfile.TemporaryDirectory()
        self.ruta = Path(self.dir.name) / "progreso.json"
        self.p = Progreso.cargar(self.ruta)

    def tearDown(self):
        self.dir.cleanup()

    def test_sin_archivo_empieza_vacio(self):
        self.assertFalse(self.p.tutorial_hecho("respiracion"))
        self.assertEqual(self.p.racha(date(2026, 11, 11)), 0)

    def test_guarda_y_carga(self):
        self.p.marcar_tutorial("respiracion")
        self.p.registrar("respiracion", "principiante", 0.94, 3, date(2026, 11, 11))
        otro = Progreso.cargar(self.ruta)
        self.assertTrue(otro.tutorial_hecho("respiracion"))
        self.assertEqual(otro.mejor("respiracion", "principiante"), 0.94)

    def test_racha(self):
        for d in (9, 10, 11):
            self.p.registrar("respiracion", "principiante", 0.9, 3, date(2026, 11, d))
        self.assertEqual(self.p.racha(date(2026, 11, 11)), 3)
        self.assertEqual(self.p.racha(date(2026, 11, 12)), 3)  # hoy aun no, no se pierde
        self.assertEqual(self.p.racha(date(2026, 11, 13)), 0)  # un dia sin practicar la rompe

    def test_semana_de_lunes_a_domingo(self):
        self.p.registrar("respiracion", "principiante", 0.9, 3, date(2026, 11, 9))  # lunes
        self.p.registrar("respiracion", "principiante", 0.9, 3, date(2026, 11, 11))  # miercoles
        self.assertEqual(self.p.semana(date(2026, 11, 11)),
                         [True, False, True, False, False, False, False])

    def test_vueltas_elegidas_se_guardan_y_se_limitan(self):
        self.assertEqual(self.p.vueltas(5), 5)
        self.assertEqual(self.p.elegir_vueltas(7), 7)
        self.assertEqual(Progreso.cargar(self.ruta).vueltas(5), 7)
        self.assertEqual(self.p.elegir_vueltas(0), VUELTAS_MIN)
        self.assertEqual(self.p.elegir_vueltas(20), VUELTAS_MAX)

    def test_pocas_vueltas_no_suben_de_nivel(self):
        for d in range(5):
            self.p.registrar("respiracion", "principiante", 0.95, 3, date(2026, 11, 9 + d),
                             vueltas=3)
        self.assertEqual(self.p.nivel("respiracion"), 0)
        self.assertEqual(self.p.racha(date(2026, 11, 13)), 5)  # para la racha si cuentan
        for d in range(5):
            self.p.registrar("respiracion", "principiante", 0.95, 3, date(2026, 11, 14 + d),
                             vueltas=5)
        self.assertEqual(self.p.nivel("respiracion"), 1)


class TestNiveles(unittest.TestCase):
    """La regla unica. 5 dias con 3 lotos a tu nivel mas alto te suben al siguiente."""

    def setUp(self):
        self.dir = tempfile.TemporaryDirectory()
        self.ruta = Path(self.dir.name) / "progreso.json"
        self.p = Progreso.cargar(self.ruta)
        self.lunes = date(2026, 11, 9)

    def tearDown(self):
        self.dir.cleanup()

    def dias(self, fase, n, desde=0, lotos=3, nivel=None):
        """Apunta n días seguidos de esa fase con esos lotos."""
        for i in range(n):
            nivel_jugado = self.p.nivel(fase) if nivel is None else nivel
            self.p.registrar(fase, "normal", 0.9, lotos, self.lunes + timedelta(days=desde + i),
                             nivel=nivel_jugado)

    def test_los_estiramientos_no_suben(self):
        """Son el calentamiento antes de las flexiones, con un solo nivel (Rares, 25/11)."""
        for i in range(10):
            self.p.registrar("estiramientos", "normal", 0.9, 3, self.lunes + timedelta(days=i),
                             nivel=0)
        self.assertEqual(self.p.nivel("estiramientos"), 0)
        self.assertTrue(self.p.nivel_maximo("estiramientos"))

    def test_empieza_en_el_primero(self):
        for fase in NIVELES:
            self.assertEqual(self.p.nivel(fase), 0)
            self.assertEqual(self.p.dias_para_subir(fase), 0)

    def test_cinco_dias_suben_y_cuatro_no(self):
        self.dias("flexiones", DIAS_PARA_SUBIR - 1)
        self.assertEqual(self.p.nivel("flexiones"), 0)
        self.assertEqual(self.p.dias_para_subir("flexiones"), 4)
        self.dias("flexiones", 1, desde=4)
        self.assertEqual(self.p.nivel("flexiones"), 1)
        self.assertEqual(self.p.dias_para_subir("flexiones"), 0)  # empieza de cero

    def test_dos_lotos_no_cuentan(self):
        self.dias("flexiones", 5, lotos=2)
        self.assertEqual(self.p.nivel("flexiones"), 0)

    def test_el_mismo_dia_cuenta_una_vez(self):
        for _ in range(5):
            self.p.registrar("flexiones", "normal", 0.9, 3, self.lunes, nivel=0)
        self.assertEqual(self.p.dias_para_subir("flexiones"), 1)

    def test_un_nivel_mas_bajo_no_cuenta(self):
        self.dias("flexiones", 5)
        self.dias("flexiones", 5, desde=5, nivel=0)  # ya tenia el 1
        self.assertEqual(self.p.nivel("flexiones"), 1)
        self.assertEqual(self.p.dias_para_subir("flexiones"), 0)

    def test_las_de_prueba_no_cuentan(self):
        for i in range(5):
            self.p.registrar("meditacion", "normal", 0.9, 3, self.lunes + timedelta(days=i),
                             minutos=0.1, nivel=None)
        self.assertEqual(self.p.nivel("meditacion"), 0)

    def test_nunca_pasa_del_ultimo(self):
        self.dias("respiracion", 30)
        self.assertEqual(self.p.nivel("respiracion"), len(NIVELES["respiracion"]) - 1)
        self.assertTrue(self.p.nivel_maximo("respiracion"))

    def test_toda_la_escalera_de_meditacion_y_el_libre(self):
        self.dias("meditacion", 5 * len(ESCALERA))
        self.assertEqual(NIVELES["meditacion"][self.p.nivel("meditacion")], LIBRE)

    def test_las_sesiones_antiguas_sin_nivel_valen(self):
        """Antes del 25/11 no se guardaba el nivel. Se deduce de minutos y variante."""
        for i in range(5):
            dia = self.lunes + timedelta(days=i)
            self.p.registrar("meditacion", "normal", 0.9, 3, dia, minutos=5)
            self.p.registrar("meditacion", "normal", 0.9, 3, dia, minutos=1)  # corta, no
            self.p.registrar("flexiones", "facil", 0.9, 3, dia)
            self.p.registrar("respiracion", "principiante", 0.9, 3, dia, vueltas=5)
        self.assertEqual(self.p.nivel("meditacion"), 1)
        self.assertEqual(self.p.nivel("flexiones"), 1)
        self.assertEqual(self.p.nivel("respiracion"), 1)

    def test_elegir_un_nivel_mas_bajo(self):
        self.dias("flexiones", 10)
        self.assertEqual(self.p.nivel_elegido("flexiones"), 2)
        self.assertEqual(self.p.elegir_nivel("flexiones", -1), 1)
        self.assertEqual(Progreso.cargar(self.ruta).nivel_elegido("flexiones"), 1)
        self.assertEqual(self.p.elegir_nivel("flexiones", 5), 2)  # no pasa del tuyo
        self.assertEqual(self.p.elegir_nivel("flexiones", -9), 0)

    def test_al_subir_se_juega_el_nuevo(self):
        self.dias("flexiones", 5)
        self.assertEqual(self.p.nivel_elegido("flexiones"), 1)


if __name__ == "__main__":
    unittest.main()
