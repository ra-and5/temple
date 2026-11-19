"""Camara y deteccion en un hilo aparte.

Los modelos de MediaPipe tardan unos 30-50 ms por fotograma. Si se
ejecutaran en el mismo bucle que la interfaz, las animaciones irian a saltos.
Aqui un hilo lee la camara y detecta sin parar, y la interfaz solo recoge el
ultimo resultado cuando lo necesita.
"""

from __future__ import annotations

import threading
import time

import cv2

from temple.vision import MODELO_MANOS, MODELO_POSE, Detector, Lectura

SIN_IMAGEN_S = 6.0  # si la camara se abre pero no da imagen en este rato, se avisa

# Cada error es el problema y, en la linea de abajo, que hacer
SIN_MODELOS = "Faltan los modelos de MediaPipe\nEjecuta  bash instalar.sh  y vuelve a abrir Temple"
SIN_CAMARA = ("No se puede abrir la cámara {}\n"
              "Comprueba que está conectada y que ningún otro programa la usa. "
              "Si tienes varias, prueba con  bash jugar.sh --camara 1")
SIN_PERMISO = ("La cámara no da imagen\n"
               "En macOS, permite la cámara a la Terminal en Ajustes del Sistema, "
               "Privacidad y seguridad, Cámara, y vuelve a abrir Temple")


class CamaraHilo(threading.Thread):
    def __init__(self, indice: int = 0):
        super().__init__(daemon=True)
        self._indice = indice
        self._candado = threading.Lock()
        self._frame_rgb = None
        self._lectura = Lectura(tapado=None)
        self._parar = threading.Event()
        self.error: str | None = None
        self.listo = threading.Event()
        self.cara = False  # la interfaz lo enciende al meditar

    def run(self) -> None:
        if not (MODELO_POSE.exists() and MODELO_MANOS.exists()):
            self.error = SIN_MODELOS
            self.listo.set()
            return
        cap = cv2.VideoCapture(self._indice)
        if not cap.isOpened():
            self.error = SIN_CAMARA.format(self._indice)
            self.listo.set()
            return
        try:
            with Detector() as detector:
                ultima_imagen = time.monotonic()
                while not self._parar.is_set():
                    ok, frame = cap.read()
                    if not ok:
                        # En macOS, sin permiso la camara se abre pero no da imagen
                        if time.monotonic() - ultima_imagen > SIN_IMAGEN_S and self._frame_rgb is None:
                            self.error = SIN_PERMISO
                            self.listo.set()
                        time.sleep(0.01)
                        continue
                    ultima_imagen = time.monotonic()
                    self.error = None
                    frame = cv2.flip(frame, 1)  # modo espejo
                    detector.usar_cara = self.cara
                    lectura = detector.procesar(frame)
                    rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                    with self._candado:
                        self._frame_rgb = rgb
                        self._lectura = lectura
                    self.listo.set()
        except Exception as e:  # que la interfaz pueda ensenar el fallo
            self.error = f"Fallo en la cámara: {e}"
            self.listo.set()
        finally:
            cap.release()

    def ultimo(self):
        """Devuelve el ultimo fotograma en RGB (o None) y su lectura."""
        with self._candado:
            return self._frame_rgb, self._lectura

    def parar(self) -> None:
        self._parar.set()
