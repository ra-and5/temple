"""Pruebas del progreso. Se ejecutan con
    python -m unittest discover tests
"""

import tempfile
import unittest
from datetime import date
from pathlib import Path

from temple.progreso import PERFECTAS_PARA_AVANZADA, VUELTAS_MAX, VUELTAS_MIN, Progreso


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

    def test_desbloqueo_avanzada(self):
        for _ in range(PERFECTAS_PARA_AVANZADA - 1):
            self.p.registrar("respiracion", "principiante", 0.9, 3, date(2026, 11, 11))
        self.p.registrar("respiracion", "principiante", 0.7, 2, date(2026, 11, 11))
        self.assertFalse(self.p.avanzada_desbloqueada())
        self.p.registrar("respiracion", "principiante", 0.9, 3, date(2026, 11, 11))
        self.assertTrue(self.p.avanzada_desbloqueada())

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
        self.assertEqual(self.p.perfectas("respiracion", "principiante"), 0)
        self.assertEqual(self.p.racha(date(2026, 11, 13)), 5)  # para la racha si cuentan
        for d in range(5):
            self.p.registrar("respiracion", "principiante", 0.95, 3, date(2026, 11, 14 + d),
                             vueltas=5)
        self.assertTrue(self.p.avanzada_desbloqueada())

if __name__ == "__main__":
    unittest.main()
