"""Piezas de dibujo de Temple. Fondo, tarjetas, texto, loto, enso y particulas."""

from __future__ import annotations

import math
import random

import pygame
import pygame.gfxdraw

from temple.interfaz import estilo as E


# ---------- fondo y tarjetas ----------

def crear_fondo() -> pygame.Surface:
    """Degradado de noche con un halo de lampara detras del panel."""
    fondo = pygame.Surface((E.ANCHO, E.ALTO))
    for y in range(E.ALTO):
        t = y / E.ALTO
        color = [int(a + (b - a) * t) for a, b in zip(E.NOCHE_ARRIBA, E.NOCHE_ABAJO)]
        pygame.draw.line(fondo, color, (0, y), (E.ANCHO, y))
    halo = pygame.Surface((E.ANCHO, E.ALTO), pygame.SRCALPHA)
    cx, cy = E.PANEL.centerx, E.PANEL.top + 120
    for r in range(420, 0, -6):
        a = int(26 * (1 - r / 420) ** 2)
        pygame.draw.circle(halo, (*E.ORO, a), (cx, cy), r)
    fondo.blit(halo, (0, 0))
    return fondo


def tarjeta(destino: pygame.Surface, rect: pygame.Rect, alpha: int = 215) -> None:
    """Tarjeta translucida con sombra y un filo dorado muy fino."""
    sombra = pygame.Surface((rect.w + 30, rect.h + 30), pygame.SRCALPHA)
    pygame.draw.rect(sombra, (0, 0, 0, 70), sombra.get_rect().inflate(-14, -14),
                     border_radius=E.RADIO + 8)
    destino.blit(sombra, (rect.x - 15, rect.y - 6))
    capa = pygame.Surface(rect.size, pygame.SRCALPHA)
    pygame.draw.rect(capa, (*E.TARJETA, alpha), capa.get_rect(), border_radius=E.RADIO)
    pygame.draw.rect(capa, E.BORDE, capa.get_rect(), 1, border_radius=E.RADIO)
    destino.blit(capa, rect.topleft)


def mascara_redondeada(tam: tuple[int, int], radio: int) -> pygame.Surface:
    mascara = pygame.Surface(tam, pygame.SRCALPHA)
    pygame.draw.rect(mascara, (255, 255, 255, 255), mascara.get_rect(), border_radius=radio)
    return mascara


# ---------- texto ----------

def partir(fuente: pygame.font.Font, texto: str, ancho: int) -> list[str]:
    lineas, actual = [], ""
    for palabra in texto.split():
        prueba = f"{actual} {palabra}".strip()
        if fuente.size(prueba)[0] <= ancho:
            actual = prueba
        else:
            if actual:
                lineas.append(actual)
            actual = palabra
    if actual:
        lineas.append(actual)
    return lineas


def texto(destino, fuente, cadena, color, centro_x, y, ancho=None, interlinea=1.15,
          alpha=255) -> int:
    """Texto centrado y partido en lineas. Devuelve la y de debajo."""
    ancho = ancho or destino.get_width()
    alto_linea = int(fuente.get_linesize() * interlinea)
    for linea in partir(fuente, cadena, ancho):
        s = fuente.render(linea, True, color)
        if alpha < 255:
            s.set_alpha(alpha)
        destino.blit(s, s.get_rect(midtop=(centro_x, y)))
        y += alto_linea
    return y


def texto_espaciado(destino, fuente, cadena, color, pos, espacio=4, centrado=False):
    """Texto con letras separadas, para titulos y etiquetas en mayusculas."""
    letras = [fuente.render(c, True, color) for c in cadena]
    total = sum(l.get_width() for l in letras) + espacio * (len(letras) - 1)
    x, y = pos
    if centrado:
        x -= total // 2
    for l in letras:
        destino.blit(l, (x, y))
        x += l.get_width() + espacio
    return total


# ---------- simbolos ----------

def _petalo(cx, cy, largo, ancho, angulo):
    """Puntos de un petalo apuntado que sale de (cx, cy) con el angulo dado."""
    izq, der = [], []
    for i in range(13):
        t = i / 12
        w = ancho * math.sin(math.pi * t) ** 0.85
        izq.append((-w, -t * largo))
        der.append((w, -t * largo))
    puntos = izq + der[::-1]
    c, s = math.cos(math.radians(angulo)), math.sin(math.radians(angulo))
    return [(cx + x * c - y * s, cy + x * s + y * c) for x, y in puntos]


def loto(destino, centro, tam, color=E.ORO, relleno=True, alpha=255):
    """Flor de loto de cinco petalos. tam es el alto del petalo central."""
    cx, cy = centro
    capa = pygame.Surface(destino.get_size(), pygame.SRCALPHA)
    petalos = [(-62, 0.62), (62, 0.62), (-31, 0.84), (31, 0.84), (0, 1.0)]
    for angulo, escala in petalos:
        pts = _petalo(cx, cy, tam * escala, tam * 0.27 * (0.8 + 0.2 * escala), angulo)
        if relleno:
            # Los petalos de detras un poco mas oscuros, para dar volumen
            k = 0.72 + 0.28 * escala
            col = (*[int(v * k) for v in color], alpha)
            pygame.gfxdraw.filled_polygon(capa, pts, col)
            pygame.gfxdraw.aapolygon(capa, pts, col)
        else:
            pygame.gfxdraw.aapolygon(capa, pts, (*color, alpha))
    # Hoja de agua debajo, una linea curva fina
    ancho = tam * 0.62
    curva = [(cx + ancho * (i / 10 * 2 - 1), cy + tam * 0.10 * (1 - (i / 10 * 2 - 1) ** 2))
             for i in range(11)]
    pygame.draw.aalines(capa, (*color, alpha), False, curva)
    destino.blit(capa, (0, 0))


def llama(destino, centro, tam, color=E.AZAFRAN):
    """Llama de lampara de aceite, para la racha."""
    cx, cy = centro
    pts = []
    for i in range(24):
        t = i / 23 * 2 * math.pi
        r = tam * (0.5 + 0.5 * math.cos(t / 2) ** 6) * 0.55
        x = cx + r * math.sin(t) * 0.75
        y = cy - tam * 0.2 + r * math.cos(t) * (1.4 if math.cos(t) < 0 else 0.9)
        pts.append((x, y))
    pygame.gfxdraw.filled_polygon(destino, pts, color)
    pygame.gfxdraw.aapolygon(destino, pts, color)
    nucleo = [(cx + (x - cx) * 0.45, cy + (y - cy) * 0.45 + tam * 0.12) for x, y in pts]
    pygame.gfxdraw.filled_polygon(destino, nucleo, E.CREMA)


# Ruido fijo para que el trazo del enso tenga textura de pincel sin temblar
_RUIDO = [math.sin(i * 0.37) * 0.5 + math.sin(i * 1.13) * 0.3 for i in range(720)]


def enso(destino, centro, radio, fraccion, color, grosor=14, alpha=255, inicio=-100):
    """Circulo zen pintado con pincel. fraccion de 0 a 1 es cuanto esta trazado."""
    if fraccion <= 0:
        return
    cx, cy = centro
    capa = pygame.Surface((radio * 2 + grosor * 4, radio * 2 + grosor * 4), pygame.SRCALPHA)
    ox, oy = capa.get_width() // 2, capa.get_height() // 2
    pasos = max(2, int(360 * fraccion))
    for i in range(pasos):
        t = i / 359
        ang = math.radians(inicio + 360 * t * 0.97)  # el enso nunca se cierra del todo
        r = radio + _RUIDO[i] * 1.6
        # Trazo grueso al empezar y que se afina al final, como un pincel
        g = grosor * (0.55 + 0.45 * math.sin(math.pi * min(1, t * 1.25 + 0.15)))
        if t > 0.85:
            g *= max(0.25, 1 - (t - 0.85) * 4)
        x, y = ox + r * math.cos(ang), oy + r * math.sin(ang)
        pygame.gfxdraw.filled_circle(capa, int(x), int(y), max(1, int(g / 2)), (*color, alpha))
    destino.blit(capa, (cx - ox, cy - oy))


def halo(destino, centro, radio, color, intensidad):
    """Brillo suave alrededor de un punto. intensidad de 0 a 1."""
    if intensidad <= 0.01:
        return
    capa = pygame.Surface((radio * 2, radio * 2), pygame.SRCALPHA)
    for r in range(radio, 0, -4):
        a = int(70 * intensidad * (1 - r / radio) ** 1.6)
        pygame.draw.circle(capa, (*color, a), (radio, radio), r)
    destino.blit(capa, (centro[0] - radio, centro[1] - radio))


# ---------- particulas ----------

class Brasas:
    """Motas de incienso que suben despacio por todo el fondo."""

    def __init__(self, n=46):
        self.motas = [self._nueva(aleatoria=True) for _ in range(n)]

    def _nueva(self, aleatoria=False):
        return [random.uniform(0, E.ANCHO),
                random.uniform(0, E.ALTO) if aleatoria else E.ALTO + 10,
                random.uniform(6, 18),  # velocidad
                random.uniform(0.8, 2.2),  # tamano
                random.uniform(0, math.tau)]  # fase del parpadeo

    def dibujar(self, destino, dt, t):
        capa = pygame.Surface((E.ANCHO, E.ALTO), pygame.SRCALPHA)
        for m in self.motas:
            m[1] -= m[2] * dt
            m[0] += math.sin(t * 0.6 + m[4]) * 4 * dt
            if m[1] < -10:
                m[:] = self._nueva()
            a = int(60 + 50 * math.sin(t * 1.7 + m[4]))
            pygame.gfxdraw.filled_circle(capa, int(m[0]), int(m[1]), int(m[3]), (*E.ORO, a))
        destino.blit(capa, (0, 0))


class Aire:
    """Hilo de motas que entra o sale por el orificio abierto."""

    def __init__(self):
        self.motas: list[list[float]] = []
        self._acumulado = 0.0

    def actualizar(self, dt, activo):
        if activo:
            self._acumulado += dt
            while self._acumulado > 0.06:
                self._acumulado -= 0.06
                self.motas.append([0.0, random.uniform(-5, 5)])
        for m in self.motas:
            m[0] += dt / 1.1
        self.motas = [m for m in self.motas if m[0] < 1]

    def dibujar(self, destino, origen, entrando: bool, largo=80):
        ox, oy = origen
        for t, dx in self.motas:
            # Entrando suben hacia la nariz, saliendo bajan desde ella
            d = (1 - t) if entrando else t
            x = ox + dx * d
            y = oy + 14 + largo * d
            a = int(220 * math.sin(math.pi * t))
            pygame.gfxdraw.filled_circle(destino, int(x), int(y), 3, (*E.CREMA, a))
