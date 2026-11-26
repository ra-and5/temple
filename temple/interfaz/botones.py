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
MARGEN = 24  # hueco entre el borde del boton y lo de dentro
HUECO = 14  # entre el texto y la tecla o la etiqueta
LETRA, LETRA_MIN = 19, 15  # tamano del texto, y lo mas que se reduce si no cabe


@dataclass
class Boton:
    """Un botón de la pantalla, con lo que hace al pulsarlo y dónde cuenta el dedo."""
    rect: pygame.Rect
    accion: Callable[[], None]
    zona: pygame.Rect | None = None  # donde cuenta el dedo, si es distinta del dibujo
    grupo: str | None = None  # botones de la misma fila para el teclado
    texto: str = ""
    piezas: tuple[pygame.Rect, ...] = ()  # donde quedo el texto, la tecla y la etiqueta
    letra: int = LETRA  # tamano con el que cupo el texto


class Botonera:
    """Los botones de la pantalla y las tres formas de pulsarlos, con el dedo, el ratón y el teclado."""
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
        """Vacía la lista al empezar a dibujar. Cada pantalla vuelve a añadir sus botones."""
        if pantalla != self._pantalla:
            self._pantalla = pantalla
            self.foco = None  # al entrar en una pantalla no hay nada marcado
        self.lista = []
        self.dedo = dedo

    def terminar_fotograma(self) -> None:
        """Al acabar de dibujar, ajusta el foco y pone la mano del ratón si está encima de un botón."""
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
        """Añade un botón a la pantalla de ahora."""
        self.lista.append(boton)

    # ---- como se ve cada boton ----

    def por_dedo(self, indice: int) -> bool:
        """Si el dedo está resaltando ese botón."""
        p = self.puntero
        return self.dedo and p.pos is not None and p.objetivo == indice

    def marcado(self, indice: int) -> bool:
        """Si ese botón está marcado, con el teclado o con el dedo."""
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

        # De derecha a izquierda. La tecla, la etiqueta y lo que queda para el texto
        derecha = rect.right - MARGEN
        izquierda = rect.x + MARGEN + (38 if icono and not centrado else 0)
        k = E.fuente("texto", 15).render(tecla, True, col_tecla) if tecla else None
        e = E.fuente("negrita", 12).render(etiqueta.upper(), True, E.NOCHE_ARRIBA) if etiqueta else None
        caja = e.get_rect().inflate(14, 6) if e else None
        ancho = E.fuente("negrita", LETRA).size(texto)[0]

        def sitio(con_tecla: bool) -> int:
            """El ancho que queda para el texto, con o sin la tecla al lado."""
            fin = derecha
            if con_tecla and k:
                fin -= k.get_width() + HUECO
            if caja:
                fin -= caja.w + HUECO
            return fin - izquierda

        if k and ancho > sitio(True):
            k = None  # si no cabe, fuera la tecla. Sigue funcionando y sale en la ayuda de abajo
        letra = LETRA
        if centrado:
            hueco = rect.w - 2 * min(MARGEN, rect.w // 4)
        else:
            hueco = sitio(False)
        while letra > LETRA_MIN and E.fuente("negrita", letra).size(texto)[0] > hueco:
            letra -= 1
        s = E.fuente("negrita", letra).render(texto, True, col_texto)

        piezas = []
        if centrado:
            sr = s.get_rect(center=rect.center)
        else:
            if icono:
                icono((rect.x + MARGEN + 10, rect.centery))
            sr = s.get_rect(midleft=(izquierda, rect.centery))
        destino.blit(s, sr)
        piezas.append(sr)
        if k:
            kr = k.get_rect(midright=(derecha, rect.centery))
            destino.blit(k, kr)
            piezas.append(kr)
            derecha = kr.left - HUECO
        if caja:
            caja.midright = (derecha, rect.centery)  # dentro, junto a la tecla
            pygame.draw.rect(destino, E.ORO, caja, border_radius=caja.h // 2)
            destino.blit(e, e.get_rect(center=caja.center))
            piezas.append(caja)
        self.anadir(Boton(rect, accion, zona, grupo, texto, tuple(piezas), letra))

    def casilla(self, destino, rect, texto, accion, grupo=None) -> Boton:
        """Boton sin forma propia, como los puntos del ritual en el menu.

        Solo dibuja el fondo cuando esta marcado o el raton o el dedo estan
        encima, y lo apunta como cualquier boton. Lo de dentro lo dibuja quien
        lo llama, que puede apuntar en piezas donde lo ha puesto.
        """
        indice = len(self.lista)
        por_dedo = self.por_dedo(indice)
        marcado = por_dedo or self.foco == indice
        encima = marcado or rect.collidepoint(self.raton())
        capa = pygame.Surface(rect.size, pygame.SRCALPHA)
        r, radio = capa.get_rect(), 16
        if encima:
            pygame.draw.rect(capa, (*E.ORO, 46), r, border_radius=radio)
        if por_dedo and self.puntero.llenado > 0:
            relleno = pygame.Surface(rect.size, pygame.SRCALPHA)
            pygame.draw.rect(relleno, (255, 255, 255, 45), r, border_radius=radio)
            capa.blit(relleno, (0, 0), pygame.Rect(0, 0, int(rect.w * min(1.0, self.puntero.llenado)),
                                                   rect.h))
        if marcado:
            pygame.draw.rect(capa, (*E.CREMA, 230), r, 2, border_radius=radio)
        destino.blit(capa, rect.topleft)
        boton = Boton(rect, accion, None, grupo, texto)
        self.anadir(boton)
        return boton

    # ---- pulsar ----

    def actualizar_dedo(self, dt: float, lectura) -> Boton | None:
        """Mueve el cursor del dedo. Devuelve el boton pulsado, o None."""
        repetibles = {j for j, b in enumerate(self.lista) if b.grupo in REPETIBLES}
        i = self.puntero.actualizar(dt, lectura.mano, [b.zona or b.rect for b in self.lista],
                                    lectura.mano_3d, repetibles)
        return None if i is None else self.lista[i]

    def ocultar_dedo(self) -> None:
        """Quita el cursor del dedo."""
        self.puntero.ocultar()

    def mover_raton(self) -> None:
        """Al mover el ratón, el teclado deja de marcar."""
        self.foco = None  # con el raton manda el raton

    def clic(self, pos) -> bool:
        """Pulsa el botón que está debajo del clic. True si había alguno."""
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
