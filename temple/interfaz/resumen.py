from __future__ import annotations

from datetime import date

import pygame

from temple.interfaz import dibujo as D
from temple.interfaz import estilo as E
from temple.interfaz import piezas as Z
from temple.interfaz.textos import DIAS

P = E.PANEL


def dibujar(app) -> None:
    p = app.pantalla
    hoy = date.today()
    D.texto(p, E.fuente("cursiva", 22), "tu progreso", E.ORO, P.centerx, P.top + 22)

    racha = app.progreso.racha(hoy)
    if racha == 0:
        titulo = "Empieza tu racha hoy"
        nota = "Con una sesión al día la mantienes"
    else:
        titulo = "1 día seguido" if racha == 1 else f"{racha} días seguidos"
        nota = "Practica cada día para no perder la racha"
    D.texto(p, E.fuente("titulo", 36), titulo, E.CREMA, P.centerx, P.top + 54)
    Z.linea(p, nota, "texto", 15, E.APAGADO, P.top + 104)

    semana = app.progreso.semana(hoy)
    D.texto_espaciado(p, E.fuente("negrita", 13), "ESTA SEMANA", E.ORO,
                      (P.centerx, P.top + 142), espacio=3, centrado=True)
    _semana(p, semana, hoy.weekday(), P.top + 184)
    Z.linea(p, f"Has practicado {sum(semana)} de 7 días", "texto", 15, E.APAGADO, P.top + 212)

    y = P.top + 256
    for fase in app.fases.values():
        _fila(app, fase, y)
        y += 58
    Z.linea(p, "El círculo marcado es lo que ya has hecho hoy", "texto", 13, E.APAGADO, y - 8)

    app.botonera.dibujar(p, pygame.Rect(P.left + 36, P.bottom - 82, P.w - 72, 54), "Volver",
                         "Esc", app.cerrar_progreso, True)


def _semana(p, semana, hoy_i, y) -> None:
    for i, (letra, hecho) in enumerate(zip(DIAS, semana)):
        x = P.centerx + (i - 3) * 46
        if hecho:
            pygame.draw.circle(p, E.ORO, (x, y), 15)
            col = E.NOCHE_ARRIBA
        else:
            pygame.draw.circle(p, E.ORO_SUAVE, (x, y), 15, 1)
            col = E.APAGADO
        if i == hoy_i:
            pygame.draw.circle(p, E.CREMA, (x, y), 19, 1)
        s = E.fuente("negrita", 14).render(letra, True, col)
        p.blit(s, s.get_rect(center=(x, y)))


def _fila(app, fase, y) -> None:
    p = app.pantalla
    x = Z.IZQ + 10
    if app.progreso.hecha_hoy(fase.clave):
        pygame.draw.circle(p, E.JADE, (x, y + 11), 9)
        pygame.draw.lines(p, E.NOCHE_ARRIBA, False,
                          [(x - 4, y + 11), (x - 1, y + 14), (x + 4, y + 7)], 2)
    else:
        pygame.draw.circle(p, E.ORO_SUAVE, (x, y + 11), 9, 1)
    nombre = E.fuente("negrita", 17).render(fase.nombre, True, E.CREMA)
    p.blit(nombre, (x + 20, y))
    n = sum(1 for s in app.progreso.sesiones if s["fase"] == fase.clave)
    cuenta = "1 sesión" if n == 1 else f"{n} sesiones"
    s = E.fuente("texto", 15).render(cuenta, True, E.ORO_SUAVE)
    p.blit(s, s.get_rect(topright=(Z.IZQ + Z.ANCHO, y + 2)))
    detalle = E.fuente("texto", 14).render(fase.resumen(), True, E.APAGADO)
    p.blit(detalle, (x + 20, y + 26))
