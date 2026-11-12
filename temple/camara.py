"""Camara y deteccion en un hilo aparte.

Los dos modelos de MediaPipe tardan unos 30-50 ms por fotograma. Si se
ejecutaran en el mismo bucle que la interfaz, las animaciones irian a saltos.
Aqui un hilo lee la camara y detecta sin parar, y la interfaz solo recoge el
ultimo resultado cuando lo necesita.
"""

from __future__ import annotations

import threading
import time

import cv2

from temple.vision import DetectorFosas, Lectura


class CamaraHilo(threading.Thread):
    def __init__(self, indice: int = 0):
        super().__init__(daemon=True)
        self._indice = indice
        self._candado = threading.Lock()
        self._frame_rgb = None
        self._lectura = Lectura(estado=None)
        self._parar = threading.Event()
        self.error: str | None = None
        self.listo = threading.Event()

    def run(self) -> None:
        cap = cv2.VideoCapture(self._indice)
        if not cap.isOpened():
            self.error = "No se puede abrir la cámara"
            self.listo.set()
            return
        try:
            with DetectorFosas() as detector:
                while not self._parar.is_set():
                    ok, frame = cap.read()
                    if not ok:
                        time.sleep(0.01)
                        continue
                    frame = cv2.flip(frame, 1)  # modo espejo
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
