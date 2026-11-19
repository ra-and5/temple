"""Pruebas de lo que hace falta para instalar Temple en un equipo limpio.

Comprueba los scripts, las dependencias y que los modelos de MediaPipe cargan
y analizan una imagen. Lo de los modelos solo se prueba si ya estan
descargados (los descarga instalar.sh), asi que en los tests rapidos de GitHub
se salta y en el de instalacion completa si se hace.
"""

import os
import shutil
import subprocess
import unittest
from pathlib import Path

import numpy as np

from temple import vision

RAIZ = Path(__file__).resolve().parent.parent
MODELOS = (vision.MODELO_POSE, vision.MODELO_MANOS, vision.MODELO_CARA)


class TestScripts(unittest.TestCase):
    @unittest.skipUnless(shutil.which("bash"), "sin bash")
    def test_los_scripts_no_tienen_errores_de_sintaxis(self):
        for script in ("instalar.sh", "jugar.sh", "desinstalar.sh"):
            r = subprocess.run(["bash", "-n", str(RAIZ / script)], capture_output=True, text=True)
            self.assertEqual(r.returncode, 0, f"{script}\n{r.stderr}")

    def test_los_scripts_se_pueden_ejecutar(self):
        for script in ("instalar.sh", "jugar.sh", "desinstalar.sh"):
            self.assertTrue(os.access(RAIZ / script, os.X_OK), script)

    def test_instalar_descarga_los_modelos_que_usa_el_juego(self):
        texto = (RAIZ / "instalar.sh").read_text(encoding="utf-8")
        bloque = texto.split("<<'MODELOS'")[1].split("MODELOS")[0]
        nombres = {linea.split()[0] + ".task" for linea in bloque.strip().splitlines()}
        self.assertEqual(nombres, {m.name for m in MODELOS})

    def test_dependencias_con_version_fija(self):
        lineas = [linea.strip() for linea in (RAIZ / "requirements.txt").read_text().splitlines()
                  if linea.strip() and not linea.startswith("#")]
        self.assertTrue(lineas)
        for linea in lineas:
            self.assertRegex(linea, r"^[A-Za-z0-9_.-]+==[0-9][0-9A-Za-z.]*$")

    def test_nada_de_datos_ni_modelos_en_git(self):
        ignorado = (RAIZ / ".gitignore").read_text(encoding="utf-8")
        for patron in ("models/", "datos/", "__pycache__/"):
            self.assertIn(patron, ignorado)


class TestAvisos(unittest.TestCase):
    def test_sin_modelos_el_juego_dice_que_hacer(self):
        from unittest import mock

        from temple import camara
        with mock.patch.object(camara, "MODELO_POSE", RAIZ / "no_existe.task"):
            hilo = camara.CamaraHilo()
            hilo.run()  # sin hilo, para ver el resultado al momento
        self.assertEqual(hilo.error, camara.SIN_MODELOS)
        self.assertIn("instalar.sh", hilo.error)


@unittest.skipUnless(all(m.exists() for m in MODELOS), "faltan los modelos (bash instalar.sh)")
class TestModelos(unittest.TestCase):
    def test_los_tres_modelos_cargan_y_analizan_una_imagen(self):
        negro = np.zeros((480, 640, 3), np.uint8)
        with vision.Detector() as detector:
            detector.usar_cara = True
            for _ in range(3):  # en modo video, varios fotogramas seguidos
                lectura = detector.procesar(negro)
        # En una imagen negra no hay nadie
        self.assertIsNone(lectura.tapado)
        self.assertIsNone(lectura.mano)
        self.assertIsNone(lectura.ojos)


if __name__ == "__main__":
    unittest.main()
