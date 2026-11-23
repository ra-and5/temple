"""Los botones de la pantalla y las tres formas de pulsarlos (dedo, raton y teclado).

Cada fotograma las pantallas vuelven a dibujar sus botones y los apuntan aqui
en orden, de arriba abajo. Asi el dedo (temple/puntero.py), el raton y las
flechas (temple/navegacion.py) siempre trabajan con los botones que se ven.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Callable

import pygame

from temple import navegacion as N
from temple.interfaz import estilo as E
from temple.puntero import Puntero

REPETIBLES = ("vueltas", "minutos")  # grupos cuyo menos y mas se repiten sin soltar el dedo


@dataclass
class Boton:
    rect: pygame.Rect
    accion: Callable[[], None]
    zona: pygame.Rect | None = None  # donde cuenta el dedo, si es distinta del dibujo
    grupo: str | None = None  # botones de la misma fila para el teclado


class Botonera:
    def __init__(self, area: pygame.Rect, sonido: Callable[[str], None],
                 raton: Callable[[], tuple[int, int]] = pygame.mouse.get_pos):
        self.lista: list[Boton] = []
        self.puntero = Puntero(area)
        self.sonido = sonido
        self.raton = raton
        self.foco: int | None = None  # boton marcado con el teclado
        self.dedo = False  # si en esta pantalla el dedo mueve el cursor
        self._pantalla = None  # para quitar el foco al cambiar de pantalla
        self._cursor = None  # flecha o mano, para no cambiarlo en cada fotograma

    # ---- fotograma ----

    def empezar_fotograma(self, pantalla, dedo: bool) -> None:
        if pantalla != self._pantalla:
            self._pantalla = pantalla
            self.foco = None  # al entrar en una pantalla no hay nada marcado
        self.lista = []
        self.dedo = dedo

    def terminar_fotograma(self) -> None:
        if self.foco is not None and self.foco >= len(self.lista):
            self.foco = None
        # Mano al pasar el raton por un boton, como en una web
        raton = self.raton()
        encima = any(b.rect.collidepoint(raton) for b in self.lista)
        cursor = pygame.SYSTEM_CURSOR_HAND if encima else pygame.SYSTEM_CURSOR_ARROW
        if cursor != self._cursor:
            self._cursor = cursor
            try:
                pygame.mouse.set_cursor(cursor)
            except pygame.error:
                pass  # hay escritorios sin cursores del sistema, se queda la flecha

    def anadir(self, boton: Boton) -> None:
        self.lista.append(boton)

    # ---- como se ve cada boton ----

    def por_dedo(self, indice: int) -> bool:
        p = self.puntero
        return self.dedo and p.pos is not None and p.objetivo == indice

    def marcado(self, indice: int) -> bool:
        return self.foco == indice or self.por_dedo(indice)

    def dibujar(self, destino, rect, texto, tecla, accion, principal=False, etiqueta=None,
                icono=None, centrado=False, zona=None, grupo=None) -> None:
        """Dibuja un boton redondeado y lo apunta para que se pueda pulsar."""
        indice = len(self.lista)
        por_dedo = self.por_dedo(indice)
        # Con el teclado se marca el boton del foco. En las vueltas, el menos y el
        # mas juntos, porque las flechas de los lados ya los manejan
        por_teclado = self.foco == indice or (
            grupo in REPETIBLES and self.foco is not None and self.foco < indice
            and self.lista[self.foco].grupo == grupo)
        marcado = por_dedo or por_teclado
        encima = marcado or rect.collidepoint(self.raton())
        radio = rect.h // 2
        capa = pygame.Surface(rect.size, pygame.SRCALPHA)
        r = capa.get_rect()
        if principal:
            color = tuple(min(255, c + 18) for c in E.AZAFRAN) if encima else E.AZAFRAN
            pygame.draw.rect(capa, color, r, border_radius=radio)
            col_texto, col_tecla = E.NOCHE_ARRIBA, (64, 34, 12)
        else:
            pygame.draw.rect(capa, (*E.ORO, 46 if encima else 18), r, border_radius=radio)
            col_texto, col_tecla = E.CREMA, E.ORO_SUAVE
        if por_dedo and self.puntero.llenado > 0:
            # El boton se va llenando de izquierda a derecha mientras esperas
            relleno = pygame.Surface(rect.size, pygame.SRCALPHA)
            pygame.draw.rect(relleno, (255, 255, 255, 45), r, border_radius=radio)
            ancho = int(rect.w * min(1.0, self.puntero.llenado))
            capa.blit(relleno, (0, 0), pygame.Rect(0, 0, ancho, rect.h))
        borde = (*E.CREMA, 230) if marcado else (*E.ORO, 140)
        if not principal or marcado:
            pygame.draw.rect(capa, borde, r, 2 if marcado else 1, border_radius=radio)
        destino.blit(capa, rect.topleft)

        s = E.fuente("negrita", 19).render(texto, True, col_texto)
        if centrado:
            destino.blit(s, s.get_rect(center=rect.center))
        else:
            x = rect.x + 26
            if icono:
                icono((x + 10, rect.centery))
                x += 38
            destino.blit(s, s.get_rect(midleft=(x, rect.centery)))
        if tecla:
            k = E.fuente("texto", 15).render(tecla, True, col_tecla)
            destino.blit(k, k.get_rect(midright=(rect.right - 24, rect.centery)))
        if etiqueta:
            e = E.fuente("negrita", 12).render(etiqueta.upper(), True, E.NOCHE_ARRIBA)
            caja = e.get_rect().inflate(14, 6)
            caja.midright = (rect.right - 88, rect.centery)  # dentro, junto a la tecla
            pygame.draw.rect(destino, E.ORO, caja, border_radius=caja.h // 2)
            destino.blit(e, e.get_rect(center=caja.center))
        self.anadir(Boton(rect, accion, zona, grupo))

    # ---- pulsar ----

    def actualizar_dedo(self, dt: float, lectura) -> Boton | None:
        """Mueve el cursor del dedo. Devuelve el boton pulsado, o None."""
        repetibles = {j for j, b in enumerate(self.lista) if b.grupo in REPETIBLES}
        i = self.puntero.actualizar(dt, lectura.mano, [b.zona or b.rect for b in self.lista],
                                    lectura.mano_3d, repetibles)
        return None if i is None else self.lista[i]

    def ocultar_dedo(self) -> None:
        self.puntero.ocultar()

    def mover_raton(self) -> None:
        self.foco = None  # con el raton manda el raton

    def clic(self, pos) -> bool:
        for b in self.lista:
            if b.rect.collidepoint(pos):
                self.foco = None
                b.accion()
                return True
        return False

    def tecla(self, ev, en_inicio: bool) -> bool:
        """Flechas, Tab y Enter sobre los botones. True si la tecla ya se ha usado."""
        if not self.lista:
            return False
        k = ev.key
        grupos = [b.grupo for b in self.lista]
        if k in (pygame.K_UP, pygame.K_DOWN):
            self.foco = N.mover(self.foco, grupos, 1 if k == pygame.K_DOWN else -1)
            return True
        if k == pygame.K_TAB:
            atras = ev.mod & pygame.KMOD_SHIFT
            self.foco = N.mover(self.foco, grupos, -1 if atras else 1, rodear=True)
            return True
        if k in (pygame.K_LEFT, pygame.K_RIGHT):
            paso = 1 if k == pygame.K_RIGHT else -1
            en_fases = (self.foco is not None and 0 <= self.foco < len(self.lista)
                        and self.lista[self.foco].grupo == "fases")
            if en_inicio and not en_fases:
                return False  # las vueltas o los minutos, como siempre
            if self.foco is None:
                self.foco = N.mover(None, grupos, 1)
                return True
            lado = N.lateral(self.foco, grupos, paso)
            if lado is not None:
                self.foco = lado
                if en_fases:  # en la fila del ritual la flecha ya cambia de fase
                    self.lista[lado].accion()
            return True
        if k in (pygame.K_RETURN, pygame.K_KP_ENTER, pygame.K_SPACE) and self.foco is not None:
            if 0 <= self.foco < len(self.lista):
                self.sonido("toque")
                self.lista[self.foco].accion()
                return True
        return False
