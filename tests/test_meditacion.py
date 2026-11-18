"""Pruebas de la meditacion, sin camara. Se ejecutan con
    python -m unittest discover tests
"""

import tempfile
import unittest
from datetime import date, timedelta
from pathlib import Path

from temple import meditacion as M
from temple.progreso import CORTOS, ESCALERA, LIBRE, Progreso

FPS = 20


def recto(ojos=0.9, dx=0.0):
    """Sentado recto. La nariz 0.2 por encima de unos hombros de 0.25 de ancho."""
    return M.Cuerpo((0.5 + dx, 0.4), (0.375 + dx, 0.6), (0.625 + dx, 0.6), ojos)


def encorvado(ojos=0.9):
    return M.Cuerpo((0.5, 0.5), (0.375, 0.6), (0.625, 0.6), ojos)


def correr(practica, desde, segundos, cuerpo):
    """Llama a actualizar a FPS fotogramas por segundo. cuerpo puede ser una funcion de t."""
    estados, n = [], int(segundos * FPS)
    for i in range(1, n + 1):
        t = desde + i / FPS
        c = cuerpo(t) if callable(cuerpo) else cuerpo
        estados.append(practica.actualizar(t, c))
    return estados, desde + n / FPS


class TestEvaluador(unittest.TestCase):
    def calibrado(self):
        ev = M.Evaluador()
        for _ in range(10):
            ev.muestra_calibracion(recto())
        self.assertTrue(ev.fijar_calibracion())
        return ev

    def test_recto_y_encorvado(self):
        ev = self.calibrado()
        self.assertTrue(ev.medir(0.0, recto()).recto)
        self.assertFalse(ev.medir(0.1, encorvado()).recto)

    def test_hombros_algo_torcidos_de_siempre_no_cuentan(self):
        torcido = M.Cuerpo((0.5, 0.4), (0.375, 0.57), (0.625, 0.6), 0.9)  # 0.12 de inclinacion
        ev = M.Evaluador()
        for _ in range(10):
            ev.muestra_calibracion(torcido)
        ev.fijar_calibracion()
        self.assertTrue(ev.medir(0.0, torcido).recto)
        self.assertFalse(ev.medir(0.1, M.Cuerpo((0.5, 0.4), (0.375, 0.50), (0.625, 0.6), 0.9)).recto)

    def test_sin_calibrar_no_se_sabe_si_estas_recto(self):
        self.assertIsNone(M.Evaluador().medir(0.0, recto()).recto)

    def test_quieto_y_movido(self):
        ev = self.calibrado()
        for i in range(40):
            m = ev.medir(i / FPS, recto())
        self.assertTrue(m.quieto)
        for i in range(40, 80):
            m = ev.medir(i / FPS, recto(dx=0.05 if (i // 5) % 2 else -0.05))
        self.assertFalse(m.quieto)

    def test_ojos(self):
        ev = self.calibrado()
        self.assertTrue(ev.medir(0.0, recto(ojos=0.8)).ojos)
        self.assertFalse(ev.medir(0.1, recto(ojos=0.1)).ojos)
        self.assertIsNone(ev.medir(0.2, recto(ojos=None)).ojos)

    def test_sin_cuerpo(self):
        self.assertFalse(M.Evaluador().medir(0.0, None).cuerpo)


class TestPractica(unittest.TestCase):
    def sesion_hasta_meditar(self, minutos=1.0):
        pr = M.Practica(M.guion_sesion(minutos))
        _, t = correr(pr, 0, 1.0, recto())  # sentarse
        _, t = correr(pr, t, M.CALIBRAR_S + 0.2, recto())  # calibrar
        _, t = correr(pr, t, 1.0, recto())  # cerrar los ojos
        self.assertEqual(pr.pasos[pr._indice].tipo, "meditar")
        return pr, t

    def test_sesion_perfecta(self):
        pr, t = self.sesion_hasta_meditar(1.0)
        estados, t = correr(pr, t, 60.2, recto())
        self.assertGreater(pr.precision, 0.99)
        self.assertEqual(M.lotos(pr.precision), 3)
        self.assertFalse(any(e.aviso for e in estados))
        _, t = correr(pr, t, 7, recto())  # mensaje final
        self.assertTrue(pr.actualizar(t + 0.1, recto()).terminado)

    def test_un_parpadeo_no_quita_puntos(self):
        pr, t = self.sesion_hasta_meditar(1.0)
        _, t = correr(pr, t, 10, recto())
        _, t = correr(pr, t, 0.5, recto(ojos=0.0))  # parpadeo de medio segundo
        _, t = correr(pr, t, 50.2, recto())
        self.assertGreater(pr.precision, 0.99)

    def test_encorvarse_quita_puntos_y_avisa(self):
        pr, t = self.sesion_hasta_meditar(1.0)
        _, t = correr(pr, t, 30, recto())
        estados, t = correr(pr, t, 30.2, encorvado())
        self.assertLess(pr.precision, 0.6)
        self.assertGreater(pr.mal_s["recto"], 25)
        avisos = [e for e in estados if e.aviso]
        # Primer aviso a los 3 s y luego cada 10 s
        self.assertEqual(len(avisos), 3)
        self.assertEqual(avisos[0].aviso, "recto")

    def test_campana_cada_minuto(self):
        pr, t = self.sesion_hasta_meditar(3.0)
        estados, t = correr(pr, t, 180.2, recto())
        # Suena al cumplir 1 y 2 minutos. Al acabar suena el cuenco, no la campana
        self.assertEqual(sum(e.minuto for e in estados), 2)

    def test_si_no_cierras_los_ojos_sigue_igual(self):
        pr = M.Practica(M.guion_sesion(1.0))
        _, t = correr(pr, 0, 1.0, recto(ojos=None))
        _, t = correr(pr, t, M.CALIBRAR_S + 0.2, recto(ojos=None))
        _, t = correr(pr, t, M.ESPERA_OJOS_S + 0.2, recto(ojos=None))
        self.assertEqual(pr.pasos[pr._indice].tipo, "meditar")

    def test_tutorial_espera_a_que_te_encorves(self):
        pr = M.Practica(M.guion_tutorial())
        _, t = correr(pr, 0, 5.2, recto())  # mensaje
        _, t = correr(pr, t, 1.0, recto())  # sentarse
        _, t = correr(pr, t, M.CALIBRAR_S + 0.2, recto())
        _, t = correr(pr, t, 10, recto())  # sin encorvarse no avanza
        self.assertEqual(pr.pasos[pr._indice].objetivo, "encorvado")
        _, t = correr(pr, t, 1.0, encorvado())
        self.assertEqual(pr.pasos[pr._indice].objetivo, "recto")

    def test_sonido_al_entrar_en_un_paso(self):
        pr = M.Practica([M.Paso("mensaje", "a", duracion=1),
                         M.Paso("mensaje", "b", duracion=1, sonido="campana")])
        estados, _ = correr(pr, 0, 1.5, recto())
        nuevos = [e.paso.texto for e in estados if e.nuevo_paso]
        self.assertEqual(nuevos, ["a", "b"])


class TestLibre(unittest.TestCase):
    def test_sin_cuenta_atras_hasta_terminar(self):
        pr = M.Practica(M.guion_sesion(LIBRE))
        _, t = correr(pr, 0, 1.0, recto())
        _, t = correr(pr, t, M.CALIBRAR_S + 0.2, recto())
        _, t = correr(pr, t, 1.0, recto())
        estados, t = correr(pr, t, 11 * 60, recto())
        self.assertEqual(pr.pasos[pr._indice].tipo, "meditar")  # no se acaba solo
        self.assertEqual(sum(e.minuto for e in estados), 2)  # campana a los 5 y a los 10
        self.assertAlmostEqual(pr.minutos, 11, delta=0.1)
        pr.terminar(t)
        self.assertEqual(pr.pasos[pr._indice].tipo, "mensaje")
        _, t = correr(pr, t, 7, recto())
        self.assertTrue(pr.actualizar(t + 0.1, recto()).terminado)


class TestNivelMeditacion(unittest.TestCase):
    def setUp(self):
        self.dir = tempfile.TemporaryDirectory()
        self.p = Progreso.cargar(Path(self.dir.name) / "progreso.json")
        self.lunes = date(2026, 11, 9)

    def tearDown(self):
        self.dir.cleanup()

    def meditar(self, dia, minutos):
        self.p.registrar("meditacion", "normal", 0.9, 3, dia, minutos=minutos)

    def semana_completa(self, semana, minutos):
        lunes = self.lunes + timedelta(days=7 * semana)
        for i in range(5):
            self.meditar(lunes + timedelta(days=i), minutos)

    def test_empieza_en_el_primer_escalon(self):
        self.assertEqual(self.p.minutos_meditacion(self.lunes), ESCALERA[0])
        self.assertEqual(self.p.siguiente_escalon(self.lunes), ESCALERA[1])

    def test_cinco_dias_desbloquean_el_siguiente(self):
        self.semana_completa(0, 5)
        self.assertEqual(self.p.minutos_meditacion(self.lunes + timedelta(days=6)), 5)
        self.assertEqual(self.p.minutos_meditacion(self.lunes + timedelta(days=7)), ESCALERA[1])

    def test_cuatro_dias_no_suben(self):
        for i in range(4):
            self.meditar(self.lunes + timedelta(days=i), 5)
        self.assertEqual(self.p.minutos_meditacion(self.lunes + timedelta(days=7)), 5)

    def test_sesiones_cortas_no_cuentan(self):
        self.semana_completa(0, 1)
        self.assertEqual(self.p.minutos_meditacion(self.lunes + timedelta(days=7)), 5)
        self.assertEqual(self.p.dias_meditados_semana(self.lunes + timedelta(days=5)), 0)

    def test_hace_falta_meditar_el_escalon_de_esa_semana(self):
        self.semana_completa(0, 5)
        self.semana_completa(1, 5)  # la segunda semana tocaban 8
        self.assertEqual(self.p.minutos_meditacion(self.lunes + timedelta(days=14)), ESCALERA[1])

    def test_toda_la_escalera_y_el_libre(self):
        for n, m in enumerate(ESCALERA):
            self.semana_completa(n, m)
        despues = self.lunes + timedelta(days=7 * len(ESCALERA))
        self.assertEqual(self.p.minutos_meditacion(despues), ESCALERA[-1])
        self.assertTrue(self.p.libre_desbloqueado(despues))
        self.assertIsNone(self.p.siguiente_escalon(despues))
        self.assertEqual(self.p.opciones_minutos(despues)[-1], LIBRE)

    def test_el_ultimo_escalon_desbloquea_el_libre(self):
        for n, m in enumerate(ESCALERA[:-1]):
            self.semana_completa(n, m)
        hoy = self.lunes + timedelta(days=7 * (len(ESCALERA) - 1))
        self.assertEqual(self.p.minutos_meditacion(hoy), ESCALERA[-1])
        self.assertEqual(self.p.siguiente_escalon(hoy), LIBRE)
        self.assertFalse(self.p.libre_desbloqueado(hoy))

    def test_elegir_minutos(self):
        self.assertEqual(self.p.opciones_minutos(self.lunes), list(CORTOS) + [5])
        self.assertEqual(self.p.minutos_elegidos(self.lunes), 5)
        self.assertEqual(self.p.cambiar_minutos(-1, self.lunes), 3)
        self.assertEqual(self.p.cambiar_minutos(-5, self.lunes), 1)
        self.assertEqual(self.p.cambiar_minutos(9, self.lunes), 5)  # no pasa de lo desbloqueado

    def test_un_loto_no_cuenta(self):
        for i in range(5):
            self.p.registrar("meditacion", "normal", 0.5, 1, self.lunes + timedelta(days=i),
                             minutos=5)
        self.assertEqual(self.p.dias_meditados_semana(self.lunes + timedelta(days=5)), 0)
        self.assertEqual(self.p.minutos_meditacion(self.lunes + timedelta(days=7)), 5)

    def test_dos_sesiones_el_mismo_dia_cuentan_uno(self):
        self.meditar(self.lunes, 5)
        self.meditar(self.lunes, 5)
        self.assertEqual(self.p.dias_meditados_semana(self.lunes), 1)


if __name__ == "__main__":
    unittest.main()
