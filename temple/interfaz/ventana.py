"""La ventana. Dibuja el juego a 1280×720 y lo escala a la pantalla, también en Retina y en pantalla completa."""
from __future__ import annotations

import os

import pygame
from pygame._sdl2.video import Renderer, Texture, Window

from temple.interfaz import estilo as E


class Ventana:
    """La ventana de verdad, con una textura nítida y otra suavizada para escalar."""
    def __init__(self, titulo: str, icono: pygame.Surface):
        self.ventana = Window(titulo, size=(E.ANCHO, E.ALTO), allow_highdpi=True)
        self.ventana.set_icon(icono)
        self.render = Renderer(self.ventana)
        self.nitida = self._textura("0")
        self.suave = self._textura("1")
        self.destino = pygame.Rect(0, 0, E.ANCHO, E.ALTO)
        self.pixeles = 1.0
        self.completa = False

    def _textura(self, calidad: str) -> Texture:
        os.environ["SDL_RENDER_SCALE_QUALITY"] = calidad
        return Texture(self.render, (E.ANCHO, E.ALTO), streaming=True)

    def mostrar(self, superficie: pygame.Surface) -> None:
        """Pasa lo dibujado a la ventana, escalado y centrado."""
        salida = self.render.get_viewport()
        ancho = self.ventana.size[0]
        if salida.w == 0 or salida.h == 0 or ancho == 0:
            return
        self.pixeles = salida.w / ancho
        escala = min(salida.w / E.ANCHO, salida.h / E.ALTO)
        if escala >= 1 and escala - int(escala) < 0.05:
            escala = int(escala)
            textura = self.nitida
        else:
            textura = self.suave
        self.destino = pygame.Rect(0, 0, int(E.ANCHO * escala), int(E.ALTO * escala))
        self.destino.center = salida.center
        textura.update(superficie)
        self.render.draw_color = (*E.NOCHE_ARRIBA, 255)
        self.render.clear()
        textura.draw(dstrect=self.destino)
        self.render.present()

    def alternar_pantalla_completa(self) -> None:
        """Cambia entre ventana y pantalla completa."""
        self.completa = not self.completa
        if self.completa:
            self.ventana.set_fullscreen(desktop=True)
        else:
            self.ventana.set_windowed()
            self.ventana.size = (E.ANCHO, E.ALTO)

    def a_juego(self, pos) -> tuple[int, int]:
        """Pasa un punto de la ventana a las coordenadas del juego (1280×720)."""
        x = (pos[0] * self.pixeles - self.destino.x) * E.ANCHO / self.destino.w
        y = (pos[1] * self.pixeles - self.destino.y) * E.ALTO / self.destino.h
        return int(x), int(y)

    def raton(self) -> tuple[int, int]:
        """Dónde está el ratón, en coordenadas del juego."""
        return self.a_juego(pygame.mouse.get_pos())
