"""Lo que rodea al panel y es igual en todas las pantallas.

La barra de arriba (nombre y racha), la camara de la izquierda, la ayuda de
abajo, los avisos que aparecen un momento y los gestos de la mano (el punto
del dedo y el anillo de la palma).
"""

from __future__ import annotations

from datetime import date

import pygame
from mediapipe.python.solutions.hands import HAND_CONNECTIONS

from temple import meditacion as M
from temple.interfaz import dibujo as D
from temple.interfaz import estilo as E
from temple.interfaz.textos import AYUDA_PAUSA, AYUDA_PROGRESO, AYUDA_SALIR, AYUDAS


def barra_superior(app) -> None:
    p = app.pantalla
    D.loto(p, (62, 62), 30)
    D.texto_espaciado(p, E.fuente("titulo", 34), "TEMPLE", E.CREMA, (92, 26), espacio=6)
    racha = app.progreso.racha(date.today())
    if racha:
        etiqueta = f"Racha de {racha} {'día' if racha == 1 else 'días'}"
        s = E.fuente("negrita", 18).render(etiqueta, True, E.CREMA)
        x = E.ANCHO - 40 - s.get_width()
        p.blit(s, (x, 40))
        D.llama(p, (x - 18, 50), 22)


def altavoz(p, centro, activo, col) -> None:
    """Icono del boton de sonido, con ondas o con un aspa."""
    cx, cy = centro
    pygame.draw.polygon(p, col, [(cx - 11, cy - 5), (cx - 5, cy - 5), (cx + 2, cy - 11),
                                 (cx + 2, cy + 11), (cx - 5, cy + 5), (cx - 11, cy + 5)])
    if activo:  # ondas
        for radio in (7, 12):
            caja = pygame.Rect(0, 0, radio * 2, radio * 2)
            caja.center = (cx + 2, cy)
            pygame.draw.arc(p, col, caja, -0.85, 0.85, 2)
    else:  # aspa
        pygame.draw.line(p, E.TERRACOTA, (cx + 7, cy - 6), (cx + 17, cy + 6), 3)
        pygame.draw.line(p, E.TERRACOTA, (cx + 7, cy + 6), (cx + 17, cy - 6), 3)


# ---------- camara ----------

def camara(app, frame, lectura) -> None:
    """La imagen en espejo. Encima, lo que dibuje la fase mientras se practica."""
    p = app.pantalla
    D.tarjeta(p, E.CAMARA.inflate(12, 12), alpha=180)
    if frame is None:
        mensaje = app.camara.error or "Encendiendo la cámara"
        centro = E.CAMARA.center
        if not app.camara.error:
            D.enso(p, centro, 46, (app.t * 0.5) % 1, E.ORO_SUAVE, 8, 160, inicio=app.t * 120)
        # El problema en grande y debajo que hacer, partido en lineas si no cabe
        titulo, _, ayuda = mensaje.partition("\n")
        if not app.camara.error:
            D.texto(p, E.fuente("texto", 20), titulo, E.APAGADO, centro[0], centro[1] + 70)
        else:
            y = D.texto(p, E.fuente("negrita", 24), titulo, E.CREMA, centro[0], centro[1] - 50,
                        E.CAMARA.w - 80)
            D.texto(p, E.fuente("texto", 18), ayuda, E.APAGADO, centro[0], y + 12,
                    E.CAMARA.w - 120)
        return

    h, w = frame.shape[:2]
    img = pygame.image.frombuffer(frame.tobytes(), (w, h), "RGB")
    escalada = pygame.transform.smoothscale(img, E.CAMARA.size)
    img = pygame.Surface(E.CAMARA.size, pygame.SRCALPHA)
    img.blit(escalada, (0, 0))
    practicando = app.modo in ("tutorial", "sesion")
    if app.modo == "resultado" or app.pausado():
        velo = pygame.Surface(E.CAMARA.size, pygame.SRCALPHA)
        velo.fill((12, 10, 20, 150))
        img.blit(velo, (0, 0))
    elif practicando:
        app.fase.pistas(img, lectura)
    else:
        mano(img, lectura)
    img.blit(app.mascara_cam, (0, 0), special_flags=pygame.BLEND_RGBA_MULT)
    p.blit(img, E.CAMARA.topleft)
    if app.ver_datos:
        datos(app, lectura)

    if app.pausado() and practicando:
        c = E.CAMARA.center
        D.texto(p, E.fuente("titulo", 44), "En pausa", E.CREMA, c[0], c[1] - 40)
        motivo = (app.fase.motivo_pausa if app.pausa_manual
                  else "Vuelve a ponerte delante de la cámara")
        D.texto(p, E.fuente("texto", 20), motivo, E.APAGADO, c[0], c[1] + 15)


def px(img, punto) -> tuple[int, int]:
    """De coordenadas normalizadas (0 a 1) a pixeles de la imagen."""
    w, h = img.get_size()
    return int(punto[0] * w), int(punto[1] * h)


def mano(img, lectura) -> None:
    """La mano en trazo fino, para ver que la camara la sigue."""
    if not lectura.mano:
        return
    capa = pygame.Surface(img.get_size(), pygame.SRCALPHA)
    for a, b in HAND_CONNECTIONS:
        pygame.draw.aaline(capa, (*E.ORO, 150), px(img, lectura.mano[a]), px(img, lectura.mano[b]))
    for punto in lectura.mano:
        pygame.draw.circle(capa, (*E.ORO, 170), px(img, punto), 2)
    img.blit(capa, (0, 0))


def datos(app, lectura) -> None:
    """Con D, los numeros que mide la camara, para ajustar los umbrales."""
    ojos = "-" if lectura.ojos is None else f"{lectura.ojos:.2f}"
    lineas = [f"ojos {ojos}  (cerrados >= {M.OJOS_CERRADOS})"] + app.fase.lineas_datos()
    fuente = E.fuente("negrita", 15)
    y = E.CAMARA.y + 14
    for texto in lineas:
        s = fuente.render(texto, True, E.CREMA)
        caja = s.get_rect(topleft=(E.CAMARA.x + 16, y)).inflate(12, 6)
        pygame.draw.rect(app.pantalla, E.NOCHE_ARRIBA, caja, border_radius=6)
        app.pantalla.blit(s, (E.CAMARA.x + 16, y))
        y += 26


# ---------- abajo y encima ----------

def pie(app) -> None:
    mano, teclado = AYUDAS[app.modo]
    if app.modo in ("tutorial", "sesion") and app.fase.ayuda:
        mano, teclado = app.fase.ayuda
    if app.pausa_manual:
        mano, teclado = AYUDA_PAUSA
    if app.modo == "inicio" and app.preguntando_salir:
        mano, teclado = AYUDA_SALIR
    if app.modo == "inicio" and app.viendo_progreso:
        mano, teclado = AYUDA_PROGRESO
    filas = [("CON LA MANO", mano, E.CREMA), ("TECLADO", teclado, E.APAGADO)]
    etiquetas = [E.fuente("negrita", 15).render(e, True, E.ORO_SUAVE) for e, _, _ in filas]
    textos = [E.fuente("texto", 18).render(t, True, c) for _, t, c in filas]
    col = max(s.get_width() for s in etiquetas) + 14
    x = (E.ANCHO - col - max(s.get_width() for s in textos)) // 2
    for i, (etiqueta, texto) in enumerate(zip(etiquetas, textos)):
        y = E.ALTO - 52 + i * 28
        app.pantalla.blit(etiqueta, etiqueta.get_rect(midright=(x + col - 14, y)))
        app.pantalla.blit(texto, texto.get_rect(midleft=(x + col, y)))


def aviso(app) -> None:
    """Mensaje dorado arriba que se desvanece (Sonido apagado, Ya sabes respirar…)."""
    if not app.aviso:
        return
    texto, fin = app.aviso
    resto = fin - app.t
    if resto <= 0:
        app.aviso = None
        return
    alpha = int(255 * min(1.0, resto / 0.6))
    s = E.fuente("negrita", 18).render(texto, True, E.NOCHE_ARRIBA)
    caja = s.get_rect(midtop=(E.ANCHO // 2, 30)).inflate(36, 18)
    capa = pygame.Surface(caja.size, pygame.SRCALPHA)
    pygame.draw.rect(capa, (*E.ORO, 255), capa.get_rect(), border_radius=caja.h // 2)
    capa.blit(s, s.get_rect(center=(caja.w // 2, caja.h // 2)))
    capa.set_alpha(max(0, alpha))
    app.pantalla.blit(capa, caja.topleft)


def gestos(app, lectura) -> None:
    """Anillo de la palma mientras se aguanta, y el punto del dedo en los menus."""
    p = app.pantalla
    palma = app.fase.palma
    if palma.llenado > 0 and lectura.mano:
        x, y = lectura.mano[9]
        c = (E.CAMARA.x + int(x * E.CAMARA.w), E.CAMARA.y + int(y * E.CAMARA.h))
        D.enso(p, c, 46, 1, E.ORO_SUAVE, 4, 120)
        D.enso(p, c, 46, palma.llenado, E.LAVANDA, 7)
        D.texto(p, E.fuente("negrita", 16), "Pausa", E.CREMA, c[0], c[1] + 54)
    puntero = app.botonera.puntero
    if app.menu_activo() and puntero.pos is not None:
        # Solo un punto discreto. Lo importante es el boton que resalta el iman
        c = (int(puntero.pos[0]), int(puntero.pos[1]))
        # Apagado si la mano no senala, para que se note que asi no pulsa
        alfa = 170 if puntero.senala else 55
        capa = pygame.Surface((24, 24), pygame.SRCALPHA)
        pygame.draw.circle(capa, (*E.CREMA, alfa), (12, 12), 6)
        pygame.draw.circle(capa, (*E.NOCHE_ARRIBA, alfa), (12, 12), 7, 1)
        p.blit(capa, (c[0] - 12, c[1] - 12))
