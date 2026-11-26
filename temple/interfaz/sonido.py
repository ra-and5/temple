"""Sonidos de Temple, generados con numpy para no depender de archivos de audio.

  cuenco  cuenco tibetano para empezar y acabar
  toque   campanita corta cuando haces bien lo que se pide
  tic     golpecito de madera muy suave en cada tiempo de la cuenta
  aviso   dos golpes graves y bajitos al meditar, si te mueves o te encorvas
  campana campana suave y larga cada minuto de meditacion
Si el equipo no tiene audio, todo sigue funcionando en silencio.
"""

from __future__ import annotations

import numpy as np
import pygame

FRECUENCIA = 44100


def _onda(duracion, parciales, volumen):
    """Suma de senos que se apagan. parciales es una lista de (Hz, amplitud, caida en s)."""
    t = np.linspace(0, duracion, int(FRECUENCIA * duracion), endpoint=False)
    onda = np.zeros_like(t)
    for hz, amp, caida in parciales:
        # Dos senos casi iguales dan el "batido" tipico del cuenco
        onda += amp * np.exp(-t / caida) * (np.sin(2 * np.pi * hz * t)
                                            + 0.6 * np.sin(2 * np.pi * (hz + 0.9) * t))
    ataque = np.minimum(1, t / 0.008)
    onda *= ataque / np.max(np.abs(onda))
    mono = (onda * volumen * 32767).astype(np.int16)
    return np.column_stack([mono, mono])


def _dos_golpes():
    """Aviso grave, dos golpes seguidos de madera hueca. Se nota sin sobresaltar."""
    golpe = _onda(0.35, [(220, 1.0, 0.09), (330, 0.4, 0.05)], 0.30)
    hueco = np.zeros((int(FRECUENCIA * 0.12), 2), dtype=np.int16)
    return np.ascontiguousarray(np.concatenate([golpe, hueco, golpe]))


class Sonidos:
    """Los sonidos del juego, generados con numpy al arrancar. Si no hay audio, el juego sigue mudo."""
    def __init__(self):
        self.activo = True
        self._sonidos = {}
        try:
            if not pygame.mixer.get_init():
                pygame.mixer.init(FRECUENCIA, -16, 2, 512)
            self._sonidos = {
                "cuenco": pygame.sndarray.make_sound(_onda(
                    6.0, [(196, 1.0, 2.6), (196 * 2.71, 0.45, 1.6), (196 * 5.15, 0.2, 0.8)], 0.32)),
                "toque": pygame.sndarray.make_sound(_onda(
                    1.6, [(784, 1.0, 0.55), (784 * 2.76, 0.3, 0.25)], 0.18)),
                "tic": pygame.sndarray.make_sound(_onda(
                    0.12, [(520, 1.0, 0.025), (1310, 0.4, 0.012)], 0.10)),
                "aviso": pygame.sndarray.make_sound(_dos_golpes()),
                "campana": pygame.sndarray.make_sound(_onda(
                    4.0, [(523, 1.0, 1.6), (523 * 2.4, 0.35, 0.9), (523 * 4.1, 0.12, 0.5)], 0.20)),
            }
        except pygame.error:
            self._sonidos = {}  # sin tarjeta de sonido

    def __call__(self, nombre: str) -> None:
        if self.activo and nombre in self._sonidos:
            self._sonidos[nombre].play()

    def alternar(self) -> bool:
        """Pone o quita el sonido. Devuelve cómo queda."""
        self.activo = not self.activo
        if not self.activo:
            pygame.mixer.stop() if pygame.mixer.get_init() else None
        return self.activo
