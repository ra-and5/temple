import unittest

from temple import flexiones as F

FPS = 10


def cuerpo(hombro, codo, muneca, cadera=(0.55, 0.55), tobillo=(0.8, 0.6), vis=(1.0, 1.0)):
    return F.Cuerpo((hombro, hombro), (codo, codo), (muneca, muneca), (cadera, cadera),
                    (tobillo, tobillo), vis)


ARRIBA = cuerpo((0.3, 0.5), (0.3, 0.6), (0.3, 0.7))
ABAJO = cuerpo((0.3, 0.66), (0.22, 0.68), (0.3, 0.7), cadera=(0.55, 0.63))
A_MEDIAS = cuerpo((0.3, 0.6), (0.26, 0.65), (0.3, 0.7), cadera=(0.55, 0.6))
POCO_PROFUNDA = cuerpo((0.3, 0.55), (0.22, 0.62), (0.3, 0.7), cadera=(0.55, 0.58))
HUNDIDA = cuerpo((0.3, 0.66), (0.22, 0.68), (0.3, 0.7), cadera=(0.55, 0.75))
TEMBLOR = cuerpo((0.3, 0.55), (0.25, 0.62), (0.3, 0.7))


def correr(practica, lista):
    estados = []
    t = 0.0
    for c in lista:
        t += 1 / FPS
        estados.append(practica.actualizar(t, c))
    return estados


def flexiones(veces, abajo=ABAJO):
    return ([abajo] * 5 + [ARRIBA] * 5) * veces


def sesion(repeticiones=3, nivel="tecnico"):
    p = F.Practica(F.guion_sesion(repeticiones), nivel)
    correr(p, [ARRIBA] * 120)
    return p


class TestMedir(unittest.TestCase):
    def test_angulo_del_codo(self):
        self.assertAlmostEqual(F.angulo_codo((0, 0), (0, 1), (0, 2)), 180)
        self.assertAlmostEqual(F.angulo_codo((0, 0), (0, 1), (1, 1)), 90)

    def test_plancha(self):
        self.assertIsNone(F.falta("plancha", F.medir(ARRIBA)))
        self.assertEqual(F.falta("plancha", F.medir(ABAJO)), "Estira los brazos")
        self.assertEqual(F.falta("plancha", F.medir(ABAJO), "tecnico"), "Estira los brazos")

    def test_cadera_hundida(self):
        hundida = cuerpo((0.3, 0.5), (0.3, 0.6), (0.3, 0.7), cadera=(0.55, 0.68))
        self.assertEqual(F.falta("plancha", F.medir(hundida), "tecnico"), "No hundas la cadera")

    def test_sin_cuerpo(self):
        self.assertFalse(F.medir(None).cuerpo)
        self.assertEqual(F.falta("cuerpo", F.medir(None)), "No te veo entero")

    def test_elige_el_brazo_que_mejor_se_ve(self):
        c = F.Cuerpo(((0.3, 0.5), (0.3, 0.5)), ((0.3, 0.6), (0.22, 0.6)),
                     ((0.3, 0.7), (0.3, 0.7)), ((0.55, 0.55), (0.55, 0.55)),
                     ((0.8, 0.6), (0.8, 0.6)), vis_brazos=(0.3, 0.9))
        self.assertLess(F.medir(c).codo, 145)


class TestContar(unittest.TestCase):
    def test_una_flexion_buena(self):
        p = sesion()
        correr(p, flexiones(1))
        self.assertEqual(p.hechas, 1)
        self.assertEqual(p.buenas, 1)

    def test_poco_profunda(self):
        p = sesion()
        correr(p, flexiones(1, POCO_PROFUNDA))
        self.assertEqual(p.hechas, 1)
        self.assertEqual(p.buenas, 0)
        self.assertEqual(p.peor(), "poco profunda")

    def test_cadera_hundida_no_es_buena(self):
        p = sesion()
        correr(p, flexiones(1, HUNDIDA))
        self.assertEqual(p.hechas, 1)
        self.assertEqual(p.peor(), "cadera")

    def test_un_temblor_no_cuenta(self):
        p = sesion()
        correr(p, [TEMBLOR, ARRIBA] * 10)
        self.assertEqual(p.hechas, 0)

    def test_la_sesion_termina_sola(self):
        p = sesion(3)
        estados = correr(p, flexiones(3) + [ARRIBA] * 50)
        self.assertTrue(estados[-1].terminado)
        self.assertEqual(F.lotos(p.precision()), 3)

    def test_a_medias_cuenta_en_facil(self):
        p = sesion(nivel="facil")
        correr(p, flexiones(1, A_MEDIAS))
        self.assertEqual(p.hechas, 1)
        self.assertEqual(p.buenas, 1)

    def test_a_medias_no_es_buena_en_tecnico(self):
        p = sesion(nivel="tecnico")
        correr(p, flexiones(1, A_MEDIAS))
        self.assertEqual(p.buenas, 0)

    def test_avisa_en_cada_flexion(self):
        p = sesion()
        estados = correr(p, flexiones(2))
        self.assertEqual(sum(1 for e in estados if e.flexion), 2)


if __name__ == "__main__":
    unittest.main()
