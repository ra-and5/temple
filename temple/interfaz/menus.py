"""Las pantallas de menu, como en un videojuego. Una cosa en cada pantalla.

  menu       Ritual de hoy, Practicar una fase, Tu progreso, Ajustes y Salir
  fases      las cuatro fases para practicar una suelta
  previa     antes de empezar una fase. Como colocarse, el nivel y Empezar
  progreso   racha, semana y el nivel de cada fase
  ajustes    sonido, pantalla completa y vueltas de respiracion
  salir      ¿Salir de Temple?

Lo propio de cada fase (su nombre, como colocarse, que cambia en cada nivel)
lo da la fase. Aqui solo se coloca.
"""

from __future__ import annotations

from datetime import date

import pygame

from temple.interfaz import dibujo as D
from temple.interfaz import estilo as E
from temple.interfaz import marco
from temple.interfaz import piezas as Z
from temple.interfaz.textos import DIAS
from temple.progreso import DIAS_PARA_SUBIR, LOTOS_PARA_SUBIR, NIVELES, VUELTAS_MAX, VUELTAS_MIN, VUELTAS_NIVEL

P = E.PANEL


def dibujar(app) -> None:
    """Dibuja el menú que toque según la pantalla en la que estás."""
    {"menu": _menu, "fases": _fases, "previa": _previa, "progreso": _progreso,
     "ajustes": _ajustes, "salir": _salir}[app.modo](app)


def _subtitulo(p, texto) -> None:
    D.texto(p, E.fuente("cursiva", 22), texto, E.ORO, P.centerx, P.top + 22)


def _check(p, centro) -> None:
    """Circulo jade con una marca, lo hecho hoy."""
    x, y = centro
    pygame.draw.circle(p, E.JADE, (x, y), 10)
    pygame.draw.lines(p, E.NOCHE_ARRIBA, False, [(x - 5, y), (x - 1, y + 4), (x + 5, y - 4)], 2)


def _ritual(app, y) -> None:
    """Las cuatro fases en una fila, con la marca de las hechas hoy.

    Cada una es un boton. Elegir una empieza el ritual desde ella, y despues
    sigue en orden con las demas.
    """
    p = app.pantalla
    fases = list(app.fases.values())
    izq, ancho = P.left + 12, P.w - 24  # algo mas ancha que los botones, para que quepa el recuadro
    paso = ancho // len(fases)
    xs = [izq + int(ancho * (i + 0.5) / len(fases)) for i in range(len(fases))]
    for x, fase in zip(xs, fases):
        app.botonera.casilla(p, pygame.Rect(x - paso // 2, y - 18, paso, 60), fase.nombre,
                             lambda c=fase.clave: app.empezar_ritual_en(c), grupo="ritual")
    pygame.draw.line(p, E.ORO_SUAVE, (xs[0], y), (xs[-1], y), 1)
    for x, fase, boton in zip(xs, fases, app.botonera.lista[-len(fases):]):
        if app.progreso.hecha_hoy(fase.clave):
            _check(p, (x, y))
        else:
            pygame.draw.circle(p, E.TARJETA, (x, y), 10)
            pygame.draw.circle(p, E.CREMA, (x, y), 10, 2)
        s = E.fuente("texto", 14).render(fase.nombre, True, E.CREMA)
        nombre = s.get_rect(midtop=(x, y + 16))
        p.blit(s, nombre)
        boton.piezas = (nombre,)


# ---------- menu principal ----------

def _menu(app) -> None:
    p, b = app.pantalla, app.botonera
    _subtitulo(p, "tu práctica de hoy")
    _ritual(app, P.top + 78)

    hechas = len(app.fases) - len(app.faltan_hoy())
    if hechas == len(app.fases):
        texto, etiqueta = "Repetir el ritual", "hecho hoy"
    else:
        texto, etiqueta = "Ritual de hoy", f"{hechas} de {len(app.fases)}"
    y = P.top + 140
    b.dibujar(p, pygame.Rect(Z.IZQ, y, Z.ANCHO, 58), texto, "Espacio", app.empezar_ritual,
              True, etiqueta)
    b.dibujar(p, pygame.Rect(Z.IZQ, y + 76, Z.ANCHO, 50), "Practicar una fase", None,
              app.practicar)
    rect = pygame.Rect(Z.IZQ, y + 140, Z.ANCHO, 50)
    b.dibujar(p, rect, "Tu progreso", None, lambda: app.ir("progreso"))
    _puntos_semana(app, rect)
    b.dibujar(p, pygame.Rect(Z.IZQ, y + 204, Z.ANCHO, 50), "Ajustes", None,
              lambda: app.ir("ajustes"))
    b.dibujar(p, pygame.Rect(Z.IZQ, y + 268, Z.ANCHO, 50), "Salir", "Esc", app.pedir_salir)


def _puntos_semana(app, rect) -> None:
    """Los siete dias de la semana dentro del boton de Tu progreso."""
    p, hoy_i = app.pantalla, date.today().weekday()
    for i, hecho in enumerate(app.progreso.semana(date.today())):
        x = rect.right - 30 - (6 - i) * 20
        if hecho:
            pygame.draw.circle(p, E.ORO, (x, rect.centery), 6)
        else:
            pygame.draw.circle(p, E.ORO_SUAVE, (x, rect.centery), 6, 1)
        if i == hoy_i:
            pygame.draw.circle(p, E.CREMA, (x, rect.centery), 9, 1)


# ---------- practicar una fase ----------

def _fases(app) -> None:
    p, b = app.pantalla, app.botonera
    _subtitulo(p, "practicar una fase")
    y = P.top + 70
    for fase in app.fases.values():
        n = app.progreso.nivel(fase.clave)
        hecha = app.progreso.hecha_hoy(fase.clave)
        b.dibujar(p, pygame.Rect(Z.IZQ, y, Z.ANCHO, 56), fase.nombre,
                  f"Nivel {n + 1}" if fase.con_niveles else "Calentar",
                  lambda c=fase.clave: app.abrir_fase(c),
                  icono=(lambda c: _check(p, c)) if hecha else None)
        y += 72
    if len(app.faltan_hoy()) < len(app.fases):
        Z.linea(p, "La marca verde es lo que ya has hecho hoy", "texto", 14, E.APAGADO, y + 4)
    Z.boton_atras(app)


# ---------- antes de empezar una fase ----------

def _previa(app) -> None:
    p, fase, pr = app.pantalla, app.fase, app.progreso
    if app.ritual:
        claves = list(app.fases)
        Z.cabecera(p, f"RITUAL DE HOY   {claves.index(fase.clave) + 1} DE {len(claves)}")
    else:
        Z.cabecera(p, "PRACTICAR")
    Z.linea(p, fase.nombre, "titulo", 44, E.CREMA, P.top + 42)
    D.texto(p, E.fuente("texto", 17), fase.colocacion, E.CREMA, P.centerx, P.top + 104,
            P.w - 70)

    # Lo que falta para subir, con la regla de siempre
    alto = pr.nivel(fase.clave)
    y = P.top + 178
    primera = not pr.tutorial_hecho(fase.clave)
    if not fase.con_niveles:
        Z.linea(p, "Calentamiento antes de las flexiones", "negrita", 17, E.ORO, y)
        Z.linea(p, "Prepara cuello, hombros y brazos para no lesionarte", "texto", 15,
                E.APAGADO, y + 30)
        Z.linea(p, fase.nombre_nivel(0), "texto", 15, E.CREMA, y + 82)
        Z.botones_empezar(app, primera, "Aprender con el tutorial", "Empezar", P.top + 316)
        Z.boton_atras(app, "Menú" if app.ritual else "Volver")
        return
    if pr.nivel_maximo(fase.clave):
        Z.linea(p, "Tienes el nivel máximo", "texto", 15, E.ORO, y + 14)
    else:
        Z.linea(p, f"{DIAS_PARA_SUBIR} días con {LOTOS_PARA_SUBIR} lotos te suben al nivel "
                   f"{alto + 2}", "texto", 15, E.APAGADO, y - 4)
        Z.fila_lotos(p, y, pr.dias_para_subir(fase.clave), DIAS_PARA_SUBIR)

    # El nivel que se juega. Se puede bajar, pero asi no se sube
    elegido = pr.nivel_elegido(fase.clave)
    nota = fase.nombre_nivel(elegido)
    if elegido < alto:
        nota += "  ·  más bajo, no sube"
    Z.fila_mas_menos(app, f"Nivel {elegido + 1}", nota, app.cambiar_nivel, "nivel",
                     P.top + 250)
    Z.botones_empezar(app, primera, "Aprender con el tutorial", "Empezar", P.top + 316)
    Z.boton_atras(app, "Menú" if app.ritual else "Volver")


# ---------- tu progreso ----------

def _progreso(app) -> None:
    p, pr, hoy = app.pantalla, app.progreso, date.today()
    _subtitulo(p, "tu progreso")
    racha = pr.racha(hoy)
    if racha == 0:
        titulo, nota = "Empieza tu racha hoy", "Con una sesión al día la mantienes"
    else:
        titulo = "1 día seguido" if racha == 1 else f"{racha} días seguidos"
        nota = "Practica cada día para no perder la racha"
    D.texto(p, E.fuente("titulo", 36), titulo, E.CREMA, P.centerx, P.top + 50)
    Z.linea(p, nota, "texto", 15, E.APAGADO, P.top + 98)

    semana = pr.semana(hoy)
    for i, (letra, hecho) in enumerate(zip(DIAS, semana)):
        x, y = P.centerx + (i - 3) * 46, P.top + 148
        if hecho:
            pygame.draw.circle(p, E.ORO, (x, y), 15)
            col = E.NOCHE_ARRIBA
        else:
            pygame.draw.circle(p, E.ORO_SUAVE, (x, y), 15, 1)
            col = E.APAGADO
        if i == hoy.weekday():
            pygame.draw.circle(p, E.CREMA, (x, y), 19, 1)
        s = E.fuente("negrita", 14).render(letra, True, col)
        p.blit(s, s.get_rect(center=(x, y)))
    Z.linea(p, f"Esta semana, {sum(semana)} de 7 días", "texto", 15, E.APAGADO, P.top + 174)

    y = P.top + 214
    for fase in app.fases.values():
        n = pr.nivel(fase.clave)
        x = Z.IZQ + 10
        if pr.hecha_hoy(fase.clave):
            _check(p, (x, y + 11))
        else:
            pygame.draw.circle(p, E.ORO_SUAVE, (x, y + 11), 9, 1)
        p.blit(E.fuente("negrita", 17).render(fase.nombre, True, E.CREMA), (x + 20, y))
        derecha = (f"Nivel {n + 1} de {len(NIVELES[fase.clave])}" if fase.con_niveles
                   else "Calentamiento")
        s = E.fuente("negrita", 15).render(derecha, True, E.ORO)
        p.blit(s, s.get_rect(topright=(Z.IZQ + Z.ANCHO, y + 2)))
        if not fase.con_niveles:
            detalle = f"{fase.nombre_nivel(0)}  ·  antes de las flexiones"
        elif pr.nivel_maximo(fase.clave):
            detalle = f"{fase.nombre_nivel(n)}  ·  nivel máximo"
        else:
            detalle = (f"{fase.nombre_nivel(n)}  ·  {pr.dias_para_subir(fase.clave)} de "
                       f"{DIAS_PARA_SUBIR} días para subir")
        p.blit(E.fuente("texto", 14).render(detalle, True, E.APAGADO), (x + 20, y + 25))
        y += 56
    Z.boton_atras(app)


# ---------- ajustes ----------

def _ajustes(app) -> None:
    p, b = app.pantalla, app.botonera
    _subtitulo(p, "ajustes")
    activo = app.sonido.activo
    b.dibujar(p, pygame.Rect(Z.IZQ, P.top + 70, Z.ANCHO, 50),
              "Sonido activado" if activo else "Sonido apagado", "M", app.alternar_sonido,
              icono=lambda c: marco.altavoz(p, c, activo, E.CREMA if activo else E.APAGADO))
    completa = app.ventana.completa
    b.dibujar(p, pygame.Rect(Z.IZQ, P.top + 134, Z.ANCHO, 50),
              "Salir de pantalla completa" if completa else "Pantalla completa", "F",
              app.ventana.alternar_pantalla_completa)

    D.texto_espaciado(p, E.fuente("negrita", 13), "VUELTAS DE RESPIRACIÓN", E.ORO,
                      (P.centerx, P.top + 214), espacio=3, centrado=True)
    v = app.fases["respiracion"].vueltas
    if v < VUELTAS_NIVEL:
        nota = f"con menos de {VUELTAS_NIVEL} no se sube de nivel"
    elif v in (VUELTAS_MIN, VUELTAS_MAX):
        nota = "mínimo" if v == VUELTAS_MIN else "máximo"
    else:
        nota = ""
    Z.fila_mas_menos(app, f"{v} {'vuelta' if v == 1 else 'vueltas'}", nota,
                     app.cambiar_vueltas, "vueltas", P.top + 240)
    Z.boton_atras(app)


# ---------- salir ----------

def _salir(app) -> None:
    p, b = app.pantalla, app.botonera
    D.loto(p, (P.centerx, P.top + 150), 56)
    D.texto(p, E.fuente("titulo", 40), "¿Salir de Temple?", E.CREMA, P.centerx, P.top + 190)
    D.texto(p, E.fuente("texto", 19), "Tu progreso ya está guardado", E.APAGADO, P.centerx,
            P.top + 246)
    b.dibujar(p, pygame.Rect(Z.IZQ, P.top + 310, Z.ANCHO, 54), "Sí, salir", "Enter",
              app.salir, True)
    b.dibujar(p, pygame.Rect(Z.IZQ, P.top + 384, Z.ANCHO, 54), "No, seguir aquí", "Esc",
              lambda: app.ir("menu"))
