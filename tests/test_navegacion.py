"""Pruebas de moverse entre los botones con las flechas y el tabulador."""

import unittest

from temple.navegacion import fila_de, lateral, mover, paradas

# Pantalla de inicio: principal, segundo, avanzada, menos, mas, sonido
INICIO = [None, None, None, "vueltas", "vueltas", None]
# Pausa: Seguir y Salir en la misma fila
PAUSA = ["pausa", "pausa"]


class TestParadas(unittest.TestCase):
    def test_agrupa_los_seguidos_del_mismo_grupo(self):
        self.assertEqual(paradas(INICIO), [[0], [1], [2], [3, 4], [5]])

    def test_sin_grupo_cada_boton_es_una_fila(self):
        self.assertEqual(paradas([None, None]), [[0], [1]])

    def test_vacio(self):
        self.assertEqual(paradas([]), [])


class TestMover(unittest.TestCase):
    def test_primera_vez_bajando_marca_el_primero(self):
        self.assertEqual(mover(None, INICIO, 1), 0)

    def test_primera_vez_subiendo_marca_el_ultimo(self):
        self.assertEqual(mover(None, INICIO, -1), 5)

    def test_baja_una_fila(self):
        self.assertEqual(mover(0, INICIO, 1), 1)

    def test_la_fila_de_vueltas_es_una_sola_parada(self):
        self.assertEqual(mover(2, INICIO, 1), 3)
        self.assertEqual(mover(3, INICIO, 1), 5)
        self.assertEqual(mover(4, INICIO, 1), 5)  # desde el mas, tambien
        self.assertEqual(mover(5, INICIO, -1), 3)

    def test_las_flechas_no_dan_la_vuelta(self):
        self.assertEqual(mover(5, INICIO, 1), 5)
        self.assertEqual(mover(0, INICIO, -1), 0)

    def test_tab_da_la_vuelta(self):
        self.assertEqual(mover(5, INICIO, 1, rodear=True), 0)
        self.assertEqual(mover(0, INICIO, -1, rodear=True), 5)

    def test_sin_botones(self):
        self.assertIsNone(mover(None, [], 1))

    def test_foco_fuera_de_rango_vuelve_a_empezar(self):
        self.assertEqual(mover(9, [None], 1), 0)


class TestLateral(unittest.TestCase):
    def test_de_seguir_a_salir_y_vuelta(self):
        self.assertEqual(lateral(0, PAUSA, 1), 1)
        self.assertEqual(lateral(1, PAUSA, -1), 0)

    def test_no_se_sale_de_la_fila(self):
        self.assertIsNone(lateral(1, PAUSA, 1))
        self.assertIsNone(lateral(0, PAUSA, -1))

    def test_boton_solo_en_su_fila(self):
        self.assertIsNone(lateral(0, INICIO, 1))

    def test_fila_de(self):
        self.assertEqual(fila_de(3, INICIO), [3, 4])
        self.assertEqual(fila_de(None, INICIO), [])


if __name__ == "__main__":
    unittest.main()
