from __future__ import annotations

import os

import pygame
from pygame._sdl2.video import Renderer, Texture, Window

from temple.interfaz import estilo as E


class Ventana:
    def __init__(self, titulo: str, icono: pygame.Surface):
        self.ventana = Window(titulo, size=(E.ANCHO, E.ALTO), allow_highdpi=True)
        self.ventana.set_icon(icono)
        self.render = Renderer(self.ventana)
        self.nitida = self._textura("0")
        self.suave = self._textura("1")
        self.destino = pygame.Rect(0, 0, E.ANCHO, E.ALTO)
        self.completa = False

    def _textura(self, calidad: str) -> Texture:
        os.environ["SDL_RENDER_SCALE_QUALITY"] = calidad
        return Texture(self.render, (E.ANCHO, E.ALTO), streaming=True)

    def mostrar(self, superficie: pygame.Surface) -> None:
        salida = self.render.get_viewport()
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
        self.completa = not self.completa
        if self.completa:
            self.ventana.set_fullscreen(desktop=True)
        else:
            self.ventana.set_windowed()
            self.ventana.size = (E.ANCHO, E.ALTO)

    def a_juego(self, pos) -> tuple[int, int]:
        if self.ventana.size[0] == 0 or self.destino.w == 0:
            return pos
        pixeles = self.render.get_viewport().w / self.ventana.size[0]
        x = (pos[0] * pixeles - self.destino.x) * E.ANCHO / self.destino.w
        y = (pos[1] * pixeles - self.destino.y) * E.ALTO / self.destino.h
        return int(x), int(y)

    def raton(self) -> tuple[int, int]:
        return self.a_juego(pygame.mouse.get_pos())
