import unittest

from temple.puntero import (GestoPalma, Puntero, a_area, apunta_a_pantalla, distancia_a_rect,
                            palma_abierta, senala, senalando)

AREA = (0, 0, 1280, 720)
ARRIBA = (100, 100, 400, 60)
ABAJO = (100, 400, 400, 60)
DT = 1 / 60


def mano_en(x, y, abierta=False, puno=False):
    """Mano falsa de 21 puntos con la punta del indice en (x, y).

    Por defecto senala (indice estirado y el resto cerrado). abierta estira
    todos los dedos y puno los cierra todos.
    """
    puntos = [(x, y + 0.2)] * 21  # todo en la muneca
    for punta, nudillo in ((8, 6), (12, 10), (16, 14), (20, 18)):
        puntos[nudillo] = (x, y + 0.1)
        puntos[punta] = (x, y) if abierta else (x, y + 0.15)
    puntos[8] = (x, y + 0.15) if puno else (x, y)
    puntos[9] = (x, y + 0.1)
    if abierta:  # de frente, los nudillos del indice y del menique separados
        puntos[5], puntos[17] = (x - 0.04, y + 0.1), (x + 0.04, y + 0.1)
    return puntos


def mano_hacia(px, py, **kw):
    """Mano cuyo indice cae en el pixel (px, py) del AREA."""
    return mano_en(0.25 + px / AREA[2] * 0.65, 0.20 + py / AREA[3] * 0.60, **kw)


def correr(p, segundos, mano, botones):
    return [p.actualizar(DT, mano, botones) for _ in range(int(segundos / DT))]


class TestPuntero(unittest.TestCase):
    def test_zona_central_cubre_el_area(self):
        self.assertEqual(a_area((0.25, 0.20), (792, 92, 448, 540)), (792, 92))
        self.assertEqual(a_area((0.90, 0.80), (792, 92, 448, 540)), (1240, 632))
        self.assertEqual(a_area((0.0, 1.0), AREA), (0, 720))  # se recorta

    def test_distancia_a_rect(self):
        self.assertEqual(distancia_a_rect(ARRIBA, (200, 120)), 0)
        self.assertEqual(distancia_a_rect(ARRIBA, (200, 200)), 40)

    def test_gesto_de_senalar(self):
        self.assertTrue(senalando(mano_en(0.5, 0.5)))
        self.assertFalse(senalando(mano_en(0.5, 0.5, abierta=True)))
        self.assertFalse(senalando(mano_en(0.5, 0.5, puno=True)))

    def test_iman_corto(self):
        p = Puntero(AREA)
        p.actualizar(DT, mano_hacia(300, 175), [ARRIBA, ABAJO])  # 15 px por debajo
        self.assertEqual(p.objetivo, 0)
        p.pos = None
        p.actualizar(DT, mano_hacia(300, 280), [ARRIBA, ABAJO])  # en el hueco
        self.assertIsNone(p.objetivo)

    def test_en_un_hueco_no_pulsa(self):
        p = Puntero(AREA, espera_s=1.0)
        correr(p, 0.5, mano_hacia(300, 280, puno=True), [ARRIBA, ABAJO])
        pulsos = correr(p, 3, mano_hacia(300, 280), [ARRIBA, ABAJO])
        self.assertEqual(pulsos.count(None), len(pulsos))

    def test_senalar_hacia_la_camara_en_3d(self):
        # En la imagen el indice parece corto, pero en 3D esta estirado
        plano = mano_en(0.5, 0.5, puno=True)
        en_3d = [(x, y, 0.0) for x, y in plano]
        en_3d[8] = (0.5, 0.65, -0.2)  # la punta sale hacia la camara
        self.assertFalse(senalando(plano))
        self.assertTrue(senalando(en_3d))

    def test_mano_relajada_no_pulsa_nada(self):
        p = Puntero(AREA)
        for kw in ({"abierta": True}, {"puno": True}):
            pulsos = correr(p, 3, mano_hacia(300, 130, **kw), [ARRIBA])
            self.assertEqual(pulsos.count(0), 0)
            self.assertIsNone(p.objetivo)

    def test_al_aparecer_senalando_hay_que_soltar_antes(self):
        p = Puntero(AREA, espera_s=1.0)
        pulsos = correr(p, 3, mano_hacia(300, 130), [ARRIBA])
        self.assertNotIn(0, pulsos)

    def test_pulsa_tras_soltar_y_senalar(self):
        p = Puntero(AREA, espera_s=1.0)
        correr(p, 0.5, mano_hacia(300, 130, puno=True), [ARRIBA, ABAJO])
        pulsos = correr(p, 1.2, mano_hacia(300, 130), [ARRIBA, ABAJO])
        self.assertEqual(pulsos.count(0), 1)
        self.assertNotIn(1, pulsos)

    def test_no_repite_sin_soltar(self):
        p = Puntero(AREA, espera_s=0.5)
        correr(p, 0.5, mano_hacia(300, 130, puno=True), [ARRIBA])
        pulsos = correr(p, 4, mano_hacia(300, 130), [ARRIBA])
        self.assertEqual(pulsos.count(0), 1)
        correr(p, 0.5, mano_hacia(300, 130, puno=True), [ARRIBA])
        pulsos = correr(p, 0.7, mano_hacia(300, 130), [ARRIBA])
        self.assertEqual(pulsos.count(0), 1)

    def test_parpadeo_corto_no_borra_la_espera(self):
        p = Puntero(AREA, espera_s=1.0)
        correr(p, 0.5, mano_hacia(300, 130, puno=True), [ARRIBA])
        correr(p, 0.6, mano_hacia(300, 130), [ARRIBA])
        correr(p, 0.1, mano_hacia(300, 130, abierta=True), [ARRIBA])  # el modelo falla 0,1 s
        pulsos = correr(p, 0.5, mano_hacia(300, 130), [ARRIBA])
        self.assertEqual(pulsos.count(0), 1)

    def test_sin_mano_desaparece(self):
        p = Puntero(AREA)
        p.actualizar(DT, mano_hacia(300, 130), [ARRIBA])
        correr(p, 0.5, None, [ARRIBA])
        self.assertIsNone(p.pos)
        self.assertIsNone(p.objetivo)

    def test_mano_en_reposo_no_hay_cursor(self):
        p = Puntero(AREA)
        p.actualizar(DT, mano_en(0.6, 0.95, abierta=True), [ARRIBA])
        self.assertIsNone(p.pos)

    def test_senalando_muy_abajo_llega_al_boton_de_abajo(self):
        abajo_del_todo = (100, 660, 400, 54)
        p = Puntero(AREA)
        correr(p, 0.5, None, [abajo_del_todo])
        pulsados = correr(p, 2.0, mano_en(0.4, 0.95), [abajo_del_todo])
        self.assertIn(0, pulsados)


class TestDireccionDelDedo(unittest.TestCase):
    def test_mano_apoyada_en_la_cabeza_no_senala(self):
        """Indice estirado pero caido hacia abajo, con la mano sobre la cabeza (Rares, 19/11)."""
        mano = mano_en(0.5, 0.5)
        caida = [(x, 1.0 - y) for x, y in mano]  # la misma mano boca abajo
        self.assertTrue(senala(mano))
        self.assertFalse(senala(caida))
        boton = (0, 0, 1000, 1000)
        p = Puntero(boton)
        self.assertEqual([r for r in correr(p, 3, caida, [boton]) if r is not None], [])

    def test_hacia_la_camara_si_senala(self):
        """Apuntando a la camara el dedo se ve corto y casi encima del nudillo."""
        mano = mano_en(0.5, 0.5)
        mano[5] = (0.5, 0.49)  # la punta, un poco por debajo del nudillo en la imagen
        self.assertTrue(apunta_a_pantalla(mano))

    def test_de_lado_no_senala(self):
        """Tumbado con la mano en la cabeza y el indice hacia un lado (Rares, 19/11)."""
        for signo in (1, -1):
            mano = mano_en(0.5, 0.5)
            lado = [(0.5 + signo * (0.7 - y), 0.5 + 0.02 * (x - 0.5)) for x, y in mano]
            self.assertTrue(senalando(lado))  # la forma es la de senalar
            self.assertFalse(senala(lado))  # pero no la direccion

    def test_en_diagonal_hacia_arriba_si_senala(self):
        mano = mano_en(0.5, 0.5)
        mano[8] = (0.6, 0.42)  # la punta arriba a la derecha del nudillo (45 grados)
        self.assertTrue(apunta_a_pantalla(mano))


class TestPalma(unittest.TestCase):
    def test_palma_abierta(self):
        self.assertTrue(palma_abierta(mano_en(0.5, 0.5, abierta=True)))
        self.assertFalse(palma_abierta(mano_en(0.5, 0.5, abierta=False)))

    def test_pausa_a_su_tiempo_una_vez(self):
        g = GestoPalma(2.0)
        mano = mano_en(0.7, 0.5, abierta=True)
        r = [g.actualizar(DT, mano, (0.5, 0.2), 0.3) for _ in range(300)]
        self.assertEqual(r.count(True), 1)
        self.assertFalse(any(r[:int(1.9 / DT)]))

    def test_de_lado_no_cuenta(self):
        g = GestoPalma(0.5)
        mano = mano_en(0.7, 0.5, abierta=True)
        mano[5], mano[17] = (0.7, 0.6), (0.71, 0.6)  # la mano se ve estrecha
        self.assertFalse(any(g.actualizar(DT, mano, (0.5, 0.2), 0.3) for _ in range(100)))

    def test_mano_que_baja_no_pausa(self):
        """Al bajar la mano abierta despues de meditar no se pausa (Rares, 19/11)."""
        g = GestoPalma(0.5)
        r = [g.actualizar(DT, mano_en(0.7, 0.2 + 0.004 * i, abierta=True), (0.5, 0.2), 0.3)
             for i in range(100)]
        self.assertFalse(any(r))
        self.assertEqual(g.llenado < 0.3, True)

    def test_cerca_de_la_nariz_no_cuenta(self):
        g = GestoPalma(0.5)
        mano = mano_en(0.5, 0.25, abierta=True)  # centro de la palma en la nariz
        r = [g.actualizar(DT, mano, (0.5, 0.35), 0.3) for _ in range(100)]
        self.assertFalse(any(r))


if __name__ == "__main__":
    unittest.main()


class TestArreglosMeditacion(unittest.TestCase):
    """Menos y mas se repiten sin soltar, y la palma al meditar pide estar arriba."""

    def test_boton_repetible_sin_soltar(self):
        from temple.puntero import ESPERA_S, REPETIR_S
        boton = (0, 0, 1000, 1000)
        p = Puntero((0, 0, 1000, 1000))
        mano = mano_en(0.5, 0.5)
        p.actualizar(0.1, None, [boton])  # quitar la mano cuenta como soltar
        p.actualizar(1.0, None, [boton])
        pulsaciones = 0
        for _ in range(int((ESPERA_S + 2 * REPETIR_S + 0.1) * 30)):
            if p.actualizar(1 / 30, mano, [boton], repetibles={0}) is not None:
                pulsaciones += 1
        self.assertEqual(pulsaciones, 3)

    def test_palma_por_debajo_del_techo_no_pausa(self):
        g = GestoPalma(0.5)
        mano = mano_en(0.5, 0.4, abierta=True)  # centro de la palma en y = 0.5
        self.assertFalse(any(g.actualizar(0.1, mano, techo=0.3) for _ in range(20)))
        self.assertTrue(any(g.actualizar(0.1, mano, techo=0.7) for _ in range(20)))
