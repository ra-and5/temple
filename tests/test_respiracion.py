"""Pruebas de la logica de la respiracion. Se ejecutan con
    python -m unittest discover tests
"""

import unittest

from temple.respiracion import Guion, estrellas, guion_sesion, guion_tutorial


def contar(pasos):
    """Los pasos de contar como tuplas fáciles de comparar."""
    return [(p.accion, p.abierto, p.tapado, p.tiempos) for p in pasos if p.tipo == "contar"]


class TestGuiones(unittest.TestCase):
    def test_sesion_sigue_el_video(self):
        pasos = guion_sesion(vueltas=5)
        c = contar(pasos)
        self.assertEqual(len(c), 1 + 4 * 5)
        self.assertEqual(c[1:5], [
            ("inhala", "izquierdo", "derecho", 4),
            ("exhala", "derecho", "izquierdo", 8),
            ("inhala", "derecho", "izquierdo", 4),
            ("exhala", "izquierdo", "derecho", 8),
        ])
        self.assertEqual(pasos[-1].tipo, "mensaje")

    def test_espera_antes_de_cada_cambio_de_lado(self):
        pasos = guion_sesion(vueltas=1)
        for i, p in enumerate(pasos):
            if p.tipo == "contar":
                anterior = next(q for q in reversed(pasos[:i]) if q.tapado)
                self.assertEqual(anterior.tapado, p.tapado)
        self.assertEqual(pasos[0].tipo, "esperar")

    def test_avanzado_retiene_con_las_dos_tapadas(self):
        c = contar(guion_sesion(vueltas=1, avanzado=True))
        ret = [x for x in c if x[0] == "retiene"]
        self.assertEqual(len(ret), 2)
        self.assertTrue(all(x[2] == "ambos" and x[3] == 16 for x in ret))

    def test_tutorial_ensena_el_cambio(self):
        objetivos = [p.objetivo for p in guion_tutorial() if p.tipo == "esperar"]
        self.assertEqual(objetivos[:5], ["cuerpo", "mano", "derecho", "izquierdo", "derecho"])


class TestMotor(unittest.TestCase):
    def test_esperar_no_avanza_hasta_sostener(self):
        g = Guion(guion_sesion(vueltas=1), sostener_s=1.0)
        g.actualizar(0.0, "ninguno", False)
        self.assertEqual(g.actualizar(5.0, "ninguno", False).indice, 0)  # te espera
        g.actualizar(5.1, "derecho", True)
        self.assertEqual(g.actualizar(5.5, "derecho", True).indice, 0)
        g.actualizar(6.2, "derecho", True)
        self.assertEqual(g.actualizar(6.3, "derecho", True).paso.tipo, "contar")

    def test_soltar_reinicia_la_espera(self):
        g = Guion(guion_sesion(vueltas=1), sostener_s=1.0)
        g.actualizar(0.0, "derecho", True)
        g.actualizar(0.8, "ninguno", True)
        self.assertEqual(g.actualizar(1.2, "derecho", True).indice, 0)

    def test_cuenta_y_aire(self):
        g = Guion(guion_sesion(vueltas=1), tiempo_s=1.0, sostener_s=0.0)
        g.actualizar(0.0, "derecho", True)  # pasa la espera
        e = g.actualizar(0.0, "derecho", True)  # vaciar 4
        self.assertEqual((e.paso.accion, e.cuenta), ("exhala", 1))
        g.actualizar(4.0, "derecho", True)  # termina de vaciar
        e = g.actualizar(4.0, "derecho", True)
        self.assertEqual((e.paso.accion, e.cuenta), ("inhala", 1))
        self.assertAlmostEqual(e.llenado, 0.0)
        e = g.actualizar(7.5, "derecho", True)
        self.assertEqual(e.cuenta, 4)
        self.assertGreater(e.llenado, 0.8)
        self.assertTrue(e.correcto)

    def test_precision(self):
        g = Guion(guion_sesion(vueltas=1), sostener_s=0.0)
        g.actualizar(0.0, "derecho", True)
        g.actualizar(0.1, "derecho", True)
        g.actualizar(0.2, "izquierdo", True)
        self.assertAlmostEqual(g.precision, 0.5)


class TestEstrellas(unittest.TestCase):
    def test_umbrales(self):
        self.assertEqual([estrellas(p) for p in (0.9, 0.7, 0.5, 0.1)], [3, 2, 1, 0])


if __name__ == "__main__":
    unittest.main()
