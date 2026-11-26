"""Pruebas de los estiramientos, sin camara. Se ejecutan con
    python -m unittest discover tests
"""

import tempfile
import unittest
from pathlib import Path

from temple import estiramientos as S

FPS = 20

# Sentado recto, con la imagen en espejo. Hombros de 0.3 de ancho. Como hace
# MediaPipe con el espejo, el punto "a" (su izquierda) sale a la derecha
HOMBRO_A, HOMBRO_B = (0.65, 0.6), (0.35, 0.6)  # a es tu hombro derecho


def cuerpo(oreja_a=(0.56, 0.35), oreja_b=(0.44, 0.35), codo_a=(0.7, 0.85), codo_b=(0.3, 0.85),
           muneca_a=(0.68, 1.05), muneca_b=(0.32, 1.05), vis=(1.0, 1.0)):
    """Un cuerpo inventado, sentado recto y con los brazos abajo si no se dice otra cosa."""
    return S.Cuerpo((0.5, 0.38), HOMBRO_A, HOMBRO_B, oreja_a, oreja_b, codo_a, codo_b,
                    muneca_a, muneca_b, *vis)


NEUTRO = cuerpo()
# Cabeza a tu derecha (la oreja de la derecha de la pantalla baja), con la mano
# derecha sobre la cabeza
CUELLO_DER = cuerpo(oreja_a=(0.57, 0.40), oreja_b=(0.45, 0.32), codo_a=(0.66, 0.3),
                    muneca_a=(0.45, 0.22))
CUELLO_IZQ = cuerpo(oreja_a=(0.55, 0.32), oreja_b=(0.43, 0.40), codo_b=(0.34, 0.3),
                    muneca_b=(0.55, 0.22))
ARRIBA = cuerpo(codo_a=(0.66, 0.25), codo_b=(0.34, 0.25), muneca_a=(0.6, 0.0),
                muneca_b=(0.4, 0.0))
# Brazo derecho (el del hombro a) cruzado hasta el hombro izquierdo, y la mano
# izquierda sujetando el codo
CRUZADO_DER = cuerpo(codo_a=(0.48, 0.72), muneca_a=(0.36, 0.66), muneca_b=(0.5, 0.76))
CRUZADO_IZQ = cuerpo(codo_b=(0.52, 0.72), muneca_b=(0.64, 0.66), muneca_a=(0.5, 0.76))
# Triceps derecho. Codo derecho por encima de la cabeza, la mano a la espalda
# (por debajo del codo) y la mano izquierda tirando del codo
TRICEPS_DER = cuerpo(codo_a=(0.55, 0.15), muneca_a=(0.45, 0.30), codo_b=(0.38, 0.20),
                     muneca_b=(0.53, 0.17))
TRICEPS_IZQ = cuerpo(codo_b=(0.45, 0.15), muneca_b=(0.55, 0.30), codo_a=(0.62, 0.20),
                     muneca_a=(0.47, 0.17))


def girar(c):
    """El mismo cuerpo con a y b cambiados, como si MediaPipe llamara al reves los lados."""
    return S.Cuerpo(c.nariz, c.hombro_b, c.hombro_a, c.oreja_b, c.oreja_a, c.codo_b, c.codo_a,
                    c.muneca_b, c.muneca_a, c.vis_muneca_b, c.vis_muneca_a)


def correr(practica, desde, segundos, c):
    """Llama a actualizar a FPS fotogramas por segundo. c puede ser una funcion de t."""
    estados, n = [], int(segundos * FPS)
    for i in range(1, n + 1):
        t = desde + i / FPS
        estados.append(practica.actualizar(t, c(t) if callable(c) else c))
    return estados, desde + n / FPS


class TestMedir(unittest.TestCase):
    def test_cada_postura_se_reconoce_y_solo_ella(self):
        posturas = {"neutro": NEUTRO, "cuello_der": CUELLO_DER, "cuello_izq": CUELLO_IZQ,
                    "arriba": ARRIBA, "cruzado_der": CRUZADO_DER, "cruzado_izq": CRUZADO_IZQ,
                    "triceps_der": TRICEPS_DER, "triceps_izq": TRICEPS_IZQ}
        for nombre, c in posturas.items():
            m = S.medir(c)
            for objetivo in posturas:
                if objetivo == "arriba" and nombre.startswith("triceps"):
                    continue  # en el triceps los dos codos tambien estan arriba
                self.assertEqual(S.cumple(objetivo, m), objetivo == nombre,
                                 f"{objetivo} con el cuerpo en {nombre}")

    def test_triceps_pide_lo_que_falta(self):
        c = cuerpo(codo_a=(0.55, 0.15), muneca_a=(0.5, 0.0))  # codo arriba, brazo estirado
        self.assertEqual(S.falta("triceps_der", S.medir(c)), "Dobla el brazo, la mano a la espalda")
        c = cuerpo(codo_a=(0.55, 0.15), muneca_a=(0.45, 0.30))  # sin sujetar el codo
        self.assertEqual(S.falta("triceps_der", S.medir(c)), "Sujeta el codo con la otra mano")
        self.assertEqual(S.falta("triceps_der", S.medir(NEUTRO)),
                         "Sube el codo por encima de la cabeza")
        self.assertTrue(S.cumple("triceps_der", S.medir(girar(TRICEPS_DER))))

    def test_da_igual_que_lado_llame_izquierdo_mediapipe(self):
        """Si a y b vienen al reves, la derecha sigue siendo la de la pantalla."""
        self.assertTrue(S.cumple("cruzado_der", S.medir(girar(CRUZADO_DER))))
        self.assertTrue(S.cumple("cuello_der", S.medir(girar(CUELLO_DER))))

    def test_camara_torcida_no_cuenta_como_cabeza_inclinada(self):
        """Hombros y orejas inclinados lo mismo, la cabeza esta recta respecto al cuerpo."""
        c = S.Cuerpo((0.5, 0.38), (0.65, 0.66), (0.35, 0.54), (0.56, 0.38), (0.44, 0.33),
                     NEUTRO.codo_a, NEUTRO.codo_b, NEUTRO.muneca_a, NEUTRO.muneca_b)
        self.assertLess(abs(S.medir(c).inclinacion), S.RECTA_GRADOS)

    def test_cuello_sin_la_mano_en_la_cabeza_no_vale(self):
        c = cuerpo(oreja_a=(0.57, 0.40), oreja_b=(0.45, 0.32))
        self.assertEqual(S.falta("cuello_der", S.medir(c)), "Pon la mano sobre la cabeza")
        c = cuerpo(codo_a=(0.66, 0.3), muneca_a=(0.45, 0.22))  # mano puesta, cabeza recta
        self.assertEqual(S.falta("cuello_der", S.medir(c)), "Inclina más la cabeza")

    def test_cruzado_no_depende_de_ver_la_mano_en_el_codo(self):
        """La mano tapa el codo y MediaPipe lo coloca mal, asi que en el cruzado solo
        cuenta el cruce (prueba de Rares del 26/11)."""
        c = cuerpo(codo_a=(0.48, 0.72), muneca_a=(0.36, 0.66))
        self.assertTrue(S.cumple("cruzado_der", S.medir(c)))
        c = cuerpo(codo_a=(0.55, 0.72), muneca_a=(0.48, 0.66), muneca_b=(0.55, 0.76))
        self.assertEqual(S.falta("cruzado_der", S.medir(c)), "Cruza más el brazo")

    def test_sujetar_vale_aunque_mediapipe_cambie_las_munecas(self):
        """Con los brazos cruzados MediaPipe a veces da cada muneca en el otro brazo."""
        c = CRUZADO_DER
        cambiado = S.Cuerpo(c.nariz, c.hombro_a, c.hombro_b, c.oreja_a, c.oreja_b, c.codo_a,
                            c.codo_b, c.muneca_b, c.muneca_a)
        self.assertLessEqual(S.medir(cambiado).sujeta, S.SUJETAR)

    def test_cruzado_vale_aunque_mediapipe_cambie_las_munecas(self):
        """El cruce tampoco depende de cual llama derecha (prueba de Rares del 26/11)."""
        c = CRUZADO_DER
        cambiado = S.Cuerpo(c.nariz, c.hombro_a, c.hombro_b, c.oreja_a, c.oreja_b, c.codo_a,
                            c.codo_b, c.muneca_b, c.muneca_a)
        self.assertTrue(S.cumple("cruzado_der", S.medir(cambiado)))
        self.assertFalse(S.cumple("cruzado_izq", S.medir(cambiado)))

    def test_triceps_con_la_muneca_escondida_tras_la_cabeza(self):
        """MediaPipe pone la muneca escondida a la altura del codo, y un poco por
        encima a ratos. Sigue contando (prueba de Rares del 26/11)."""
        c = cuerpo(codo_a=(0.55, 0.15), muneca_a=(0.5, 0.10), codo_b=(0.38, 0.20),
                   muneca_b=(0.53, 0.05), vis=(0.35, 1.0))
        self.assertTrue(S.cumple("triceps_der", S.medir(c)))
        self.assertFalse(S.cumple("triceps_izq", S.medir(c)))

    def test_el_suavizado_quita_el_temblor(self):
        """Un salto de un fotograma en la muneca apenas mueve el punto suavizado."""
        suave = S.Suavizado()
        for _ in range(30):
            suave.actualizar(CRUZADO_DER, 1 / 30)
        salto = cuerpo(codo_a=(0.48, 0.72), muneca_a=(0.66, 0.66), muneca_b=(0.5, 0.76))
        c = suave.actualizar(salto, 1 / 30)
        self.assertLess(abs(c.muneca_a[0] - CRUZADO_DER.muneca_a[0]), 0.3 / 4)  # salta 0.3
        self.assertIsNone(suave.actualizar(None, 1 / 30))

    def test_muneca_fuera_de_la_imagen_sigue_contando(self):
        """El brazo izquierdo muy estirado saca la muneca por el borde (prueba del 19/11)."""
        c = cuerpo(codo_b=(0.52, 0.72), muneca_b=(1.04, 0.70), muneca_a=(0.5, 0.76),
                   vis=(1.0, 0.05))
        self.assertTrue(S.cumple("cruzado_izq", S.medir(c)))

    def test_sin_cuerpo(self):
        self.assertFalse(S.medir(None).cuerpo)
        self.assertFalse(S.cumple("neutro", S.medir(None)))


class TestPractica(unittest.TestCase):
    def test_sesion_entera_haciendolo_bien(self):
        pr = S.Practica(S.guion_sesion(segundos=2))
        t = 0.0
        estados = []
        while pr._indice < len(pr.pasos):
            paso = pr.pasos[pr._indice]
            c = {"cuerpo": NEUTRO, "neutro": NEUTRO, None: NEUTRO}.get(paso.objetivo)
            c = c or {"cuello_der": CUELLO_DER, "cuello_izq": CUELLO_IZQ, "arriba": ARRIBA,
                      "cruzado_der": CRUZADO_DER, "cruzado_izq": CRUZADO_IZQ,
                      "triceps_der": TRICEPS_DER, "triceps_izq": TRICEPS_IZQ}[paso.objetivo]
            nuevos, t = correr(pr, t, 0.5, c)
            estados += nuevos
            self.assertLess(t, 120, "la sesion no acaba")
        self.assertGreater(pr.precision, 0.95)
        self.assertEqual(S.lotos(pr.precision), 3)
        self.assertEqual({e.paso.postura for e in estados if e.paso.tipo == "mantener"},
                         set(range(1, len(S.POSTURAS) + 1)))

    def test_la_cuenta_solo_avanza_en_la_postura(self):
        pr = S.Practica([S.Paso("mantener", "Aguanta", objetivo="arriba", duracion=4)])
        pr.actualizar(0.0, ARRIBA)
        estados, t = correr(pr, 0.0, 2, ARRIBA)
        self.assertAlmostEqual(estados[-1].restante_s, 2.0, delta=0.1)
        estados, t = correr(pr, t, 3.5, NEUTRO)  # bajo los brazos 3,5 s
        self.assertFalse(estados[-1].bien)
        # La cuenta solo avanzo lo que dura la tolerancia
        self.assertAlmostEqual(estados[-1].restante_s, 2.0 - S.TOLERANCIA_S, delta=0.1)
        self.assertTrue(any(e.aviso for e in estados))
        estados, t = correr(pr, t, 2, ARRIBA)
        self.assertTrue(estados[-1].terminado or estados[-1].restante_s < 0.1)
        self.assertLess(pr.precision, 0.85)
        self.assertEqual(pr.peor[0], "arriba")

    def test_un_salto_corto_no_quita_puntos(self):
        pr = S.Practica([S.Paso("mantener", "Aguanta", objetivo="cuello_der", duracion=5)])
        salto = lambda t: NEUTRO if 2.0 <= t < 2.2 else CUELLO_DER  # noqa: E731
        correr(pr, 0.0, 6, salto)
        self.assertEqual(pr.precision, 1.0)
        self.assertIsNone(pr.peor)

    def test_si_no_sale_la_postura_no_se_queda_atascado(self):
        pr = S.Practica([S.Paso("mantener", "Aguanta", objetivo="cruzado_izq", duracion=3)])
        estados, _ = correr(pr, 0.0, S.MAX_VECES * 3 + 0.5, NEUTRO)
        self.assertTrue(estados[-1].terminado)
        self.assertEqual(S.lotos(pr.precision), 0)

    def test_esperar_pide_aguantar_un_momento(self):
        pr = S.Practica([S.Paso("esperar", "Cabeza", objetivo="cuello_izq"),
                         S.Paso("mensaje", "Fin", duracion=1)])
        estados, t = correr(pr, 0.0, S.SOSTENER_S / 2, CUELLO_IZQ)
        self.assertEqual(estados[-1].indice, 0)
        estados, t = correr(pr, t, S.SOSTENER_S, CUELLO_IZQ)
        self.assertEqual(estados[-1].indice, 1)

    def test_tutorial_ensena_todas(self):
        objetivos = {p.objetivo for p in S.guion_tutorial() if p.tipo == "esperar"}
        self.assertTrue({clave for clave, *_ in S.POSTURAS} <= objetivos)


class TestRegistro(unittest.TestCase):
    def test_apunta_una_fila_por_instante(self):
        with tempfile.TemporaryDirectory() as d:
            ruta = Path(d) / "r.csv"
            reg = S.Registro(ruta)
            pr = S.Practica(S.guion_sesion(segundos=1))
            for i in range(10):
                reg.apuntar(i * 0.3, pr.actualizar(i * 0.3, NEUTRO))
            reg.cerrar()
            filas = ruta.read_text(encoding="utf-8").splitlines()
            self.assertEqual(filas[0].split(","), list(S.Registro.CAMPOS))
            self.assertEqual(len(filas), 11)


if __name__ == "__main__":
    unittest.main()
