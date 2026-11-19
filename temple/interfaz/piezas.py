"""Piezas del panel de la derecha que se repiten en varias pantallas.

Cada texto va en un hueco fijo y en una sola linea que se encoge si no cabe,
para que nada se pise diga lo que diga. Las alturas (P.top + N) son las
mismas en todas las fases, asi todas las pantallas se parecen.
"""

from __future__ import annotations

import math

import pygame

from temple.interfaz import dibujo as D
from temple.interfaz import estilo as E
from temple.interfaz.textos import CORTES

P = E.PANEL
IZQ, ANCHO = P.left + 32, P.w - 64  # columna de los botones del inicio


# ---------- texto ----------

def linea(p, texto, tipo, tam, color, y, margen=48, minimo=12) -> int:
    """Una linea centrada en el panel que se encoge hasta caber. Nunca salta de linea."""
    ancho = P.w - margen
    while tam > minimo and E.fuente(tipo, tam).size(texto)[0] > ancho:
        tam -= 1
    s = E.fuente(tipo, tam).render(texto, True, color)
    p.blit(s, s.get_rect(midtop=(P.centerx, y)))
    return y + s.get_height()


def cabecera(p, texto) -> None:
    """Rotulo pequeno de arriba (TUTORIAL 3 DE 11, VUELTA 2 DE 5…)."""
    D.texto_espaciado(p, E.fuente("negrita", 13), texto, E.ORO, (P.centerx, P.top + 26),
                      espacio=3, centrado=True)


def instruccion(p, paso) -> None:
    """Lo que hay que hacer ahora, en grande, y debajo el detalle."""
    linea(p, paso.texto, "titulo", 42, E.CREMA, P.top + 84)
    if paso.detalle:
        D.texto(p, E.fuente("texto", 20), paso.detalle, E.APAGADO, P.centerx, P.top + 140,
                P.w - 70)


def chip(app, texto, color, suave=False) -> None:
    """Etiqueta de abajo del panel (Bien, No te veo…)."""
    if app.pausa_manual:
        return  # en su sitio van los botones de la pausa
    p = app.pantalla
    f = E.fuente("texto" if suave else "negrita", 17)
    s = f.render(texto, True, color if suave else E.NOCHE_ARRIBA)
    caja = s.get_rect(center=(P.centerx, P.bottom - 42)).inflate(30, 14)
    if not suave:
        pygame.draw.rect(p, color, caja, border_radius=caja.h // 2)
    p.blit(s, s.get_rect(center=caja.center))


def numero(p, texto, tam, centro, subir) -> None:
    """Numero grande centrado por su tinta.

    La fuente tiene numeros de estilo antiguo (el 3, 4, 5, 7 y 9 bajan de la
    linea), asi que se centra por la tinta y no por la caja.
    """
    n = E.fuente("titulo", tam).render(texto, True, E.CREMA)
    recorte = n.get_bounding_rect()
    tinta = recorte.copy()
    tinta.center = (centro[0], centro[1] - subir)
    p.blit(n, tinta, recorte)


# ---------- el circulo del centro ----------

def esperando(p, centro, radio, hecho, t) -> None:
    """Paso que espera a que hagas algo. Se llena al hacerlo y si no, un loto respira."""
    D.enso(p, centro, radio, 1, E.ORO_SUAVE, 12, 45)
    if hecho > 0:
        D.enso(p, centro, radio, hecho, E.JADE, 14)
        D.texto(p, E.fuente("titulo", 36), "Eso es", E.JADE, centro[0], centro[1] - 24)
    else:
        respira = 0.5 + 0.5 * math.sin(t * 1.6)
        D.loto(p, (centro[0], centro[1] + 22), 44, E.ORO, alpha=int(150 + 90 * respira))


def mensaje(p, centro, t) -> None:
    """Paso que solo ensena un texto. Un loto con un halo que late."""
    D.halo(p, centro, 140, E.ORO, 0.5 + 0.3 * math.sin(t * 1.4))
    D.loto(p, (centro[0], centro[1] + 30), 70)


def barra_mensaje(p, hecho) -> None:
    """Linea de abajo que se llena mientras dura un mensaje."""
    ancho = int((P.w - 160) * hecho)
    pygame.draw.line(p, E.ORO_SUAVE, (P.left + 80, P.bottom - 44), (P.right - 80, P.bottom - 44), 1)
    pygame.draw.line(p, E.ORO, (P.left + 80, P.bottom - 44), (P.left + 80 + ancho, P.bottom - 44), 2)


def fila_lotos(p, y, hechos, total) -> None:
    """Un loto por cada sesion o dia que ya cuenta para la meta."""
    for i in range(total):
        D.loto(p, (P.centerx + (i - 2) * 34, y + 38), 16, E.ORO if i < hechos else E.ORO_SUAVE,
               relleno=i < hechos, alpha=255 if i < hechos else 210)


# ---------- botones que comparten las fases ----------

def botones_empezar(app, primera, aprender, empezar) -> None:
    """La primera vez se ofrece el tutorial, y despues la sesion."""
    b, y = app.botonera, P.top + 128
    if primera:
        b.dibujar(app.pantalla, pygame.Rect(IZQ, y, ANCHO, 52), aprender, "Espacio",
                  lambda: app.empezar("tutorial"), True, "primera vez")
        b.dibujar(app.pantalla, pygame.Rect(IZQ, y + 64, ANCHO, 46), "Ir directo a la sesión", "S",
                  lambda: app.empezar("sesion"))
    else:
        b.dibujar(app.pantalla, pygame.Rect(IZQ, y, ANCHO, 52), empezar, "Espacio",
                  lambda: app.empezar("sesion"), True)
        b.dibujar(app.pantalla, pygame.Rect(IZQ, y + 64, ANCHO, 46), "Repasar el tutorial", "T",
                  lambda: app.empezar("tutorial"))


def fila_mas_menos(app, texto, nota, cambiar, grupo) -> None:
    """Fila de menos y mas (vueltas o minutos).

    Los botones van a los lados para que esten lejos entre si, y para el dedo
    cuenta la fila entera, mitad izquierda menos y mitad derecha mas.
    """
    y, lado, mitad = P.top + 318, 92, ANCHO // 2
    b = app.botonera
    b.dibujar(app.pantalla, pygame.Rect(IZQ, y, lado, 46), "−", None, lambda: cambiar(-1),
              centrado=True, zona=pygame.Rect(IZQ, y, mitad, 46), grupo=grupo)
    b.dibujar(app.pantalla, pygame.Rect(IZQ + ANCHO - lado, y, lado, 46), "+", None,
              lambda: cambiar(1), centrado=True,
              zona=pygame.Rect(IZQ + mitad, y, ANCHO - mitad, 46), grupo=grupo)
    D.texto(app.pantalla, E.fuente("negrita", 19), texto, E.CREMA, P.centerx, y + 4)
    if nota:
        D.texto(app.pantalla, E.fuente("texto", 13), nota, E.APAGADO, P.centerx, y + 28)


def botones_pausa(app, y=None, terminar=None) -> None:
    """Seguir y Salir. Con terminar, Terminar en vez de Salir (y la sesion se guarda)."""
    y = P.bottom - 82 if y is None else y
    ancho = (P.w - 72 - 12) // 2
    b = app.botonera
    b.dibujar(app.pantalla, pygame.Rect(P.left + 36, y, ancho, 54), "Seguir", "Espacio",
              app.seguir, True, grupo="pausa")
    if terminar:
        b.dibujar(app.pantalla, pygame.Rect(P.right - 36 - ancho, y, ancho, 54), "Terminar",
                  "Enter", terminar, grupo="pausa")
    else:
        b.dibujar(app.pantalla, pygame.Rect(P.right - 36 - ancho, y, ancho, 54), "Salir",
                  "Esc", app.volver_inicio, grupo="pausa")


def botones_seguir(app, siguiente, accion) -> None:
    """Lo siguiente del ritual (Meditar, Estirar) y al lado la vuelta al inicio."""
    p, ancho = app.pantalla, (P.w - 72 - 12) // 2
    app.botonera.dibujar(p, pygame.Rect(P.left + 36, P.bottom - 82, ancho + 40, 54),
                         siguiente, "Espacio", accion, True, grupo="fin")
    app.botonera.dibujar(p, pygame.Rect(P.right - 36 - ancho + 40, P.bottom - 82, ancho - 40, 54),
                         "Inicio", "Esc", app.volver_inicio, grupo="fin")


def boton_volver(app) -> None:
    app.botonera.dibujar(app.pantalla, pygame.Rect(P.left + 36, P.bottom - 82, P.w - 72, 54),
                         "Volver al inicio", "Espacio", app.volver_inicio, True)


# ---------- resultado ----------

def resultado(app, r, titulo, que_mide) -> None:
    """Lo que comparten los resultados. Titulo, lotos, porcentaje y el siguiente loto."""
    p, cx = app.pantalla, P.centerx
    linea(p, "nueva mejor marca" if r["record"] else "has terminado", "cursiva", 22, E.ORO,
          P.top + 24)
    linea(p, titulo, "titulo", 40, E.CREMA, P.top + 52)

    y = P.top + 172
    D.halo(p, (cx, y - 20), 170, E.ORO, 0.5)
    for i in range(3):
        ganado = i < r["estrellas"]
        D.loto(p, (cx + (i - 1) * 96, y), 54 if i == 1 else 44,
               E.ORO if ganado else E.ORO_SUAVE, relleno=ganado, alpha=255 if ganado else 210)

    # Hacia abajo, para que un 39,9 no salga como 40 % con cero lotos
    linea(p, f"{math.floor(r['precision'] * 100)} %", "titulo", 52, E.CREMA, P.top + 206)
    linea(p, que_mide, "texto", 16, E.APAGADO, P.top + 272)
    n = r["estrellas"]
    if n >= 3:
        linea(p, "Tres lotos, lo máximo", "texto", 15, E.ORO, P.top + 300)
    else:
        linea(p, f"Llega al {CORTES[n]} % para ganar {n + 1} {'loto' if n == 0 else 'lotos'}",
              "texto", 15, E.APAGADO, P.top + 300)
