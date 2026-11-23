"""Pantalla de inicio. La practica de hoy, la fase elegida, el sonido y la semana.

Lo comun va aqui. Lo de cada fase (sus botones, su meta y su fila de menos y
mas) lo dibuja la propia fase con panel_inicio.
"""

from __future__ import annotations

from datetime import date

import pygame

from temple.interfaz import estilo as E
from temple.interfaz import marco
from temple.interfaz import dibujo as D
from temple.interfaz import piezas as Z
from temple.interfaz import resumen
from temple.interfaz.botones import Boton
from temple.interfaz.textos import PROXIMAS

P = E.PANEL


def dibujar(app) -> None:
    if app.preguntando_salir:
        _pregunta_salir(app)
        return
    if app.viendo_progreso:
        resumen.dibujar(app)
        return
    p = app.pantalla
    D.texto(p, E.fuente("cursiva", 22), "tu práctica de hoy", E.ORO, P.centerx, P.top + 22)
    _ritual(app)
    app.fases[app.elegida].panel_inicio()
    _sonido(app)
    _pantalla_completa(app)
    _progreso(app)
    app.botonera.dibujar(p, pygame.Rect(P.right - 20 - 96, P.top + 14, 96, 40), "Salir", None,
                         app.pedir_salir, centrado=True)


def _ritual(app) -> None:
    """Las fases del dia en una fila. Las que ya existen se eligen como un boton."""
    p, b = app.pantalla, app.botonera
    fases = [(f.nombre, f.clave) for f in app.fases.values()] + [(n, None) for n in PROXIMAS]
    y = P.top + 74
    xs = [Z.IZQ + int(Z.ANCHO * (i + 0.5) / len(fases)) for i in range(len(fases))]
    pygame.draw.line(p, E.ORO_SUAVE, (xs[0], y), (xs[-1], y), 1)
    for x, (nombre, clave) in zip(xs, fases):
        elegida = clave == app.elegida
        hecho = clave is not None and app.progreso.hecha_hoy(clave)
        if clave:
            # Alta, para que el dedo llegue sin tener que subir mucho la mano
            zona = pygame.Rect(0, 0, Z.ANCHO // len(fases) - 4, 66)
            zona.midtop = (x, y - 18)
            indice = len(b.lista)
            marcado = b.marcado(indice)
            encima = marcado or zona.collidepoint(b.raton())
            if elegida or encima:
                capa = pygame.Surface(zona.size, pygame.SRCALPHA)
                r = capa.get_rect()
                pygame.draw.rect(capa, (*E.ORO, 46 if encima else 24), r, border_radius=14)
                if b.por_dedo(indice) and b.puntero.llenado > 0:
                    relleno = pygame.Surface(zona.size, pygame.SRCALPHA)
                    pygame.draw.rect(relleno, (255, 255, 255, 45), r, border_radius=14)
                    lleno = int(zona.w * min(1.0, b.puntero.llenado))
                    capa.blit(relleno, (0, 0), pygame.Rect(0, 0, lleno, zona.h))
                if marcado:
                    pygame.draw.rect(capa, (*E.CREMA, 230), r, 2, border_radius=14)
                p.blit(capa, zona.topleft)
            b.anadir(Boton(zona, lambda c=clave: app.elegir_fase(c), grupo="fases"))
        if hecho:
            pygame.draw.circle(p, E.JADE, (x, y), 10)
            pygame.draw.lines(p, E.NOCHE_ARRIBA, False, [(x - 5, y), (x - 1, y + 4), (x + 5, y - 4)], 2)
        elif clave:
            pygame.draw.circle(p, E.TARJETA, (x, y), 10)
            pygame.draw.circle(p, E.AZAFRAN if elegida else E.CREMA, (x, y), 10, 2)
        else:
            pygame.draw.circle(p, E.TARJETA, (x, y), 7)
            pygame.draw.circle(p, E.ORO_SUAVE, (x, y), 7, 1)
        s = E.fuente("negrita" if elegida else "texto", 14).render(
            nombre, True, E.CREMA if clave else E.APAGADO)
        p.blit(s, s.get_rect(midtop=(x, y + 16)))


def _pregunta_salir(app) -> None:
    p, b = app.pantalla, app.botonera
    D.loto(p, (P.centerx, P.top + 150), 56)
    D.texto(p, E.fuente("titulo", 40), "¿Salir de Temple?", E.CREMA, P.centerx, P.top + 190)
    D.texto(p, E.fuente("texto", 19), "Tu progreso ya está guardado", E.APAGADO, P.centerx,
            P.top + 246)
    b.dibujar(p, pygame.Rect(Z.IZQ, P.top + 310, Z.ANCHO, 54), "Sí, salir", "Enter",
              app.salir, True)
    b.dibujar(p, pygame.Rect(Z.IZQ, P.top + 384, Z.ANCHO, 54), "No, seguir aquí", "Esc",
              app.no_salir)


def _sonido(app) -> None:
    activo = app.sonido.activo
    app.botonera.dibujar(
        app.pantalla, pygame.Rect(Z.IZQ, P.top + 376, Z.ANCHO, 40),
        "Sonido activado" if activo else "Sonido apagado", "M", app.alternar_sonido,
        icono=lambda c: marco.altavoz(app.pantalla, c, activo, E.CREMA if activo else E.APAGADO))


def _pantalla_completa(app) -> None:
    completa = app.ventana.completa
    app.botonera.dibujar(
        app.pantalla, pygame.Rect(Z.IZQ, P.top + 424, Z.ANCHO, 40),
        "Salir de pantalla completa" if completa else "Pantalla completa", "F",
        app.ventana.alternar_pantalla_completa)


def _progreso(app) -> None:
    p = app.pantalla
    rect = pygame.Rect(Z.IZQ, P.top + 472, Z.ANCHO, 40)
    app.botonera.dibujar(p, rect, "Tu progreso", None, app.ver_progreso)
    hoy_i = date.today().weekday()
    for i, hecho in enumerate(app.progreso.semana(date.today())):
        x = rect.right - 30 - (6 - i) * 20
        if hecho:
            pygame.draw.circle(p, E.ORO, (x, rect.centery), 6)
        else:
            pygame.draw.circle(p, E.ORO_SUAVE, (x, rect.centery), 6, 1)
        if i == hoy_i:
            pygame.draw.circle(p, E.CREMA, (x, rect.centery), 9, 1)
