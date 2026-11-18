"""Aplicacion de Temple en Pygame.

Pantallas
  inicio      la practica de hoy, la semana y los botones para empezar
  tutorial    ensena la respiracion alterna paso a paso
  sesion      la respiracion completa
  resultado   lotos ganados, racha y lo que falta para el siguiente nivel

La camara va siempre a la izquierda, como un espejo, y el panel a la derecha
cambia segun la pantalla. La logica esta en temple/respiracion.py y en
temple/progreso.py. Aqui solo se dibuja y se gestionan teclas, raton y el dedo
(temple/puntero.py).

Con el teclado, las flechas arriba y abajo (o Tab) mueven el foco entre los
botones y Enter pulsa el marcado. Izquierda y derecha cambian las vueltas en
el inicio, y en la pausa pasan de Seguir a Salir (temple/navegacion.py).
"""

from __future__ import annotations

import math
import time
from dataclasses import dataclass
from datetime import date
from typing import Callable

import pygame
from mediapipe.python.solutions.hands import HAND_CONNECTIONS

from temple.camara import CamaraHilo
from temple.interfaz import dibujo as D
from temple.interfaz import estilo as E
from temple.interfaz.sonido import Sonidos
from temple import navegacion as N
from temple.progreso import (PERFECTAS_PARA_AVANZADA, VUELTAS_MAX, VUELTAS_MIN, VUELTAS_NIVEL,
                             Progreso)
from temple.puntero import GestoPalma, Puntero
from temple.respiracion import (COMO_TAPAR, TIEMPO_S, VUELTAS, Guion, estrellas,
                                guion_sesion, guion_tutorial)

PAUSA_SIN_CUERPO_S = 1.2  # si no te ve este rato durante la cuenta, se pausa sola
DIAS = "LMXJVSD"
VISTO = {
    "derecho": "derecha tapada",
    "izquierdo": "izquierda tapada",
    "ambos": "las dos tapadas",
    "ninguno": "nada tapado",
    None: "no te veo",
}


@dataclass
class Boton:
    rect: pygame.Rect
    accion: Callable[[], None]
    zona: pygame.Rect | None = None  # donde cuenta el dedo, si es distinta del dibujo
    grupo: str | None = None  # botones de la misma fila para el teclado


class App:
    def __init__(self, vueltas: int | None = None, tiempo_s: float = TIEMPO_S,
                 forzar_avanzada: bool = False):
        pygame.mixer.pre_init(44100, -16, 2, 512)
        pygame.init()
        pygame.display.set_caption("Temple")
        icono = pygame.Surface((64, 64), pygame.SRCALPHA)
        D.loto(icono, (32, 50), 36)
        pygame.display.set_icon(icono)
        self.pantalla = pygame.display.set_mode((E.ANCHO, E.ALTO), pygame.SCALED)
        self.reloj = pygame.time.Clock()

        self.vueltas_fijas = vueltas  # --vueltas para probar, no se guarda
        self.tiempo_s = tiempo_s
        self.forzar_avanzada = forzar_avanzada
        self.progreso = Progreso.cargar()
        self.sonido = Sonidos()
        self.camara = CamaraHilo()
        self.camara.start()

        self.fondo = D.crear_fondo()
        self.mascara_cam = D.mascara_redondeada(E.CAMARA.size, E.RADIO)
        self.brasas = D.Brasas()
        self.aire = D.Aire()

        self.modo = "inicio"
        self.guion: Guion | None = None
        self.variante = "principiante"
        self.reloj_guion = 0.0  # tiempo del guion, se para en la pausa
        self.pausa_manual = False
        self.sin_cuerpo_desde: float | None = None
        self.estado = None
        self.estado_previo = None
        self.resultado: dict = {}
        self.aviso: tuple[str, float] | None = None
        self.botones: list[Boton] = []
        self.puntero = Puntero(E.PANEL)
        self.palma = GestoPalma()
        self.foco: int | None = None  # boton marcado con el teclado
        self._pantalla_foco = None  # para quitar el foco al cambiar de pantalla
        self._cursor = None  # flecha o mano, para no cambiarlo en cada fotograma
        self.t = 0.0

    # ================= bucle =================

    def ejecutar(self) -> None:
        try:
            while True:
                dt = self.reloj.tick(E.FPS) / 1000
                self.t += dt
                if not self._eventos():
                    break
                frame, lectura = self.camara.ultimo()
                self._actualizar(dt, lectura)
                self._dibujar(dt, frame, lectura)
                pygame.display.flip()
        finally:
            # Esperar a que el hilo cierre la camara y MediaPipe antes de salir
            self.camara.parar()
            self.camara.join(timeout=3)
            pygame.quit()

    def _eventos(self) -> bool:
        for ev in pygame.event.get():
            if ev.type == pygame.QUIT:
                return False
            if ev.type == pygame.MOUSEMOTION:
                self.foco = None  # con el raton manda el raton
            if ev.type == pygame.MOUSEBUTTONDOWN and ev.button == 1:
                for b in self.botones:
                    if b.rect.collidepoint(ev.pos):
                        self.foco = None
                        b.accion()
                        break
            if ev.type == pygame.KEYDOWN:
                k = ev.key
                if self._teclas_foco(ev):
                    continue
                if k == pygame.K_F11:
                    pygame.display.toggle_fullscreen()
                elif k == pygame.K_m:
                    self._alternar_sonido()
                elif self.modo == "inicio":
                    if k == pygame.K_ESCAPE:
                        return False
                    if k in (pygame.K_SPACE, pygame.K_RETURN):
                        self._accion_principal()
                    elif k == pygame.K_t:
                        self._empezar("tutorial")
                    elif k == pygame.K_s:
                        self._empezar("sesion")
                    elif k == pygame.K_a and self._avanzada_disponible():
                        self._empezar("sesion", "avanzada")
                    elif k in (pygame.K_LEFT, pygame.K_MINUS, pygame.K_KP_MINUS):
                        self._cambiar_vueltas(-1)
                    elif k in (pygame.K_RIGHT, pygame.K_PLUS, pygame.K_KP_PLUS, pygame.K_EQUALS):
                        self._cambiar_vueltas(1)
                elif self.modo in ("tutorial", "sesion"):
                    if k == pygame.K_ESCAPE:
                        self._volver_inicio()
                    elif k in (pygame.K_p, pygame.K_SPACE):
                        self.pausa_manual = not self.pausa_manual
                elif self.modo == "resultado":
                    if k in (pygame.K_SPACE, pygame.K_RETURN, pygame.K_ESCAPE):
                        self._volver_inicio()
        return True

    def _teclas_foco(self, ev) -> bool:
        """Flechas, Tab y Enter sobre los botones. True si la tecla ya se ha usado."""
        if not self.botones:
            return False
        k = ev.key
        grupos = [b.grupo for b in self.botones]
        if k in (pygame.K_UP, pygame.K_DOWN):
            self.foco = N.mover(self.foco, grupos, 1 if k == pygame.K_DOWN else -1)
            return True
        if k == pygame.K_TAB:
            atras = ev.mod & pygame.KMOD_SHIFT
            self.foco = N.mover(self.foco, grupos, -1 if atras else 1, rodear=True)
            return True
        if k in (pygame.K_LEFT, pygame.K_RIGHT):
            paso = 1 if k == pygame.K_RIGHT else -1
            if self.modo == "inicio":
                return False  # las vueltas, como siempre
            if self.foco is None:
                self.foco = N.mover(None, grupos, 1)
                return True
            lado = N.lateral(self.foco, grupos, paso)
            if lado is not None:
                self.foco = lado
            return True
        if k in (pygame.K_RETURN, pygame.K_KP_ENTER, pygame.K_SPACE) and self.foco is not None:
            if 0 <= self.foco < len(self.botones):
                self.sonido("toque")
                self.botones[self.foco].accion()
                return True
        return False

    # ================= logica =================

    @property
    def vueltas(self) -> int:
        return self.vueltas_fijas or self.progreso.vueltas(VUELTAS)

    def _cambiar_vueltas(self, paso: int) -> None:
        self.vueltas_fijas = None
        self.progreso.elegir_vueltas(self.vueltas + paso)

    def _avanzada_disponible(self) -> bool:
        return self.forzar_avanzada or self.progreso.avanzada_desbloqueada()

    def _accion_principal(self) -> None:
        if self.progreso.tutorial_hecho("respiracion"):
            self._empezar("sesion")
        else:
            self._empezar("tutorial")

    def _empezar(self, modo: str, variante: str = "principiante") -> None:
        self.modo = modo
        self.variante = variante
        if modo == "tutorial":
            self.guion = Guion(guion_tutorial(), tiempo_s=self.tiempo_s)
        else:
            self.guion = Guion(guion_sesion(self.vueltas, variante == "avanzada"),
                               tiempo_s=self.tiempo_s)
        self.reloj_guion = 0.0
        self.pausa_manual = False
        self.sin_cuerpo_desde = None
        self.estado = self.estado_previo = None
        self.sonido("cuenco")

    def _volver_inicio(self) -> None:
        self.modo = "inicio"
        self.estado = self.estado_previo = None
        self.pausa_manual = False

    def _alternar_sonido(self) -> None:
        self._avisar("Sonido activado" if self.sonido.alternar() else "Sonido apagado")

    def _seguir(self) -> None:
        self.pausa_manual = False

    def _avisar(self, texto: str, segundos: float = 3.5) -> None:
        self.aviso = (texto, self.t + segundos)

    def _pausado(self) -> bool:
        return self.pausa_manual or (
            self.sin_cuerpo_desde is not None
            and self.t - self.sin_cuerpo_desde > PAUSA_SIN_CUERPO_S)

    def _menu_activo(self) -> bool:
        """Pantallas donde el dedo mueve el cursor. En la respiracion solo en la pausa."""
        return self.modo in ("inicio", "resultado") or self.pausa_manual

    def _actualizar(self, dt, lectura) -> None:
        # Cursor con el dedo. Usa los botones del ultimo fotograma dibujado
        if self._menu_activo():
            i = self.puntero.actualizar(dt, lectura.mano, [b.zona or b.rect for b in self.botones],
                                        lectura.mano_3d)
            if i is not None:
                self.sonido("toque")
                self.botones[i].accion()
                return
        else:
            self.puntero.ocultar()

        en_cuenta = (self.estado is not None and self.estado.paso.tipo == "contar")
        self.aire.actualizar(dt, en_cuenta and self.estado.paso.abierto is not None
                             and not self._pausado())
        if self.modo not in ("tutorial", "sesion"):
            return

        # Pausa automatica si te vas de la camara en mitad de la cuenta
        if lectura.estado is None and en_cuenta:
            if self.sin_cuerpo_desde is None:
                self.sin_cuerpo_desde = self.t
        else:
            self.sin_cuerpo_desde = None
        if self._pausado():
            self.palma.actualizar(0, None)
            return
        if self.palma.actualizar(dt, lectura.mano, lectura.nariz, lectura.escala):
            self.pausa_manual = True
            self.sonido("toque")
            return

        self.reloj_guion += dt
        self.estado_previo = self.estado
        self.estado = self.guion.actualizar(self.reloj_guion, lectura.estado,
                                            lectura.mano is not None)
        self._sonidos_de_transicion()
        if self.estado.terminado:
            self._terminar()

    def _sonidos_de_transicion(self) -> None:
        antes, ahora = self.estado_previo, self.estado
        if antes is None or ahora.terminado:
            return
        if ahora.indice != antes.indice and antes.paso.tipo == "esperar":
            self.sonido("toque")
        elif ahora.paso.tipo == "contar" and (ahora.indice != antes.indice
                                              or ahora.cuenta != antes.cuenta):
            self.sonido("tic")

    def _terminar(self) -> None:
        self.sonido("cuenco")
        if self.modo == "tutorial":
            self.progreso.marcar_tutorial("respiracion")
            self.modo = "inicio"
            self._avisar("Ya sabes respirar. Ahora, la sesión completa", 5)
            return
        antes = self.progreso.avanzada_desbloqueada()
        precision = self.guion.precision
        n = estrellas(precision)
        mejor_antes = self.progreso.mejor("respiracion", self.variante)
        self.progreso.registrar("respiracion", self.variante, precision, n, vueltas=self.vueltas)
        self.resultado = {
            "pocas_vueltas": self.vueltas < VUELTAS_NIVEL,
            "precision": precision,
            "estrellas": n,
            "record": mejor_antes is not None and precision > mejor_antes,
            "desbloqueada": not antes and self.progreso.avanzada_desbloqueada(),
        }
        self.modo = "resultado"
        self.estado = None

    # ================= dibujo general =================

    def _dibujar(self, dt, frame, lectura) -> None:
        pantalla = (self.modo, self.pausa_manual)
        if pantalla != self._pantalla_foco:
            self._pantalla_foco = pantalla
            self.foco = None  # al entrar en una pantalla no hay nada marcado
        self.botones = []
        self.pantalla.blit(self.fondo, (0, 0))
        self.brasas.dibujar(self.pantalla, dt, self.t)
        self._barra_superior()
        self._camara(frame, lectura)
        D.tarjeta(self.pantalla, E.PANEL)
        {"inicio": self._panel_inicio,
         "tutorial": self._panel_guion,
         "sesion": self._panel_guion,
         "resultado": self._panel_resultado}[self.modo](lectura)
        self._pie()
        self._aviso()
        self._gestos(lectura)
        if self.foco is not None and self.foco >= len(self.botones):
            self.foco = None
        # Mano al pasar el raton por un boton, como en una web
        raton = pygame.mouse.get_pos()
        encima = any(b.rect.collidepoint(raton) for b in self.botones)
        cursor = pygame.SYSTEM_CURSOR_HAND if encima else pygame.SYSTEM_CURSOR_ARROW
        if cursor != self._cursor:
            self._cursor = cursor
            try:
                pygame.mouse.set_cursor(cursor)
            except pygame.error:
                pass  # hay escritorios sin cursores del sistema, se queda la flecha

    def _barra_superior(self) -> None:
        p = self.pantalla
        D.loto(p, (62, 62), 30)
        D.texto_espaciado(p, E.fuente("titulo", 34), "TEMPLE", E.CREMA, (92, 26), espacio=6)
        racha = self.progreso.racha(date.today())
        if racha:
            etiqueta = f"Racha de {racha} {'día' if racha == 1 else 'días'}"
            s = E.fuente("negrita", 18).render(etiqueta, True, E.CREMA)
            x = E.ANCHO - 40 - s.get_width()
            p.blit(s, (x, 40))
            D.llama(p, (x - 18, 50), 22)

    def _altavoz(self, centro, activo, col) -> None:
        p = self.pantalla
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

    def _camara(self, frame, lectura) -> None:
        p = self.pantalla
        D.tarjeta(p, E.CAMARA.inflate(12, 12), alpha=180)
        if frame is None:
            mensaje = self.camara.error or "Encendiendo la cámara"
            centro = E.CAMARA.center
            if not self.camara.error:
                D.enso(p, centro, 46, (self.t * 0.5) % 1, E.ORO_SUAVE, 8, 160,
                       inicio=self.t * 120)
            D.texto(p, E.fuente("texto", 20), mensaje, E.APAGADO, centro[0], centro[1] + 70)
            return

        h, w = frame.shape[:2]
        img = pygame.image.frombuffer(frame.tobytes(), (w, h), "RGB")
        img = pygame.transform.smoothscale(img, E.CAMARA.size).convert_alpha()
        if self.modo == "resultado" or self._pausado():
            velo = pygame.Surface(E.CAMARA.size, pygame.SRCALPHA)
            velo.fill((12, 10, 20, 150))
            img.blit(velo, (0, 0))
        else:
            self._pistas_en_camara(img, lectura)
        img.blit(self.mascara_cam, (0, 0), special_flags=pygame.BLEND_RGBA_MULT)
        p.blit(img, E.CAMARA.topleft)

        if self._pausado() and self.modo in ("tutorial", "sesion"):
            c = E.CAMARA.center
            D.texto(p, E.fuente("titulo", 44), "En pausa", E.CREMA, c[0], c[1] - 40)
            motivo = ("Vuelve a ponerte delante de la cámara" if not self.pausa_manual
                      else "Señala Seguir con el índice y espera")
            D.texto(p, E.fuente("texto", 20), motivo, E.APAGADO, c[0], c[1] + 15)

    def _pistas_en_camara(self, img, lectura) -> None:
        """Mano en trazo fino, circulo donde tapar y el hilo de aire."""
        w, h = img.get_size()

        def px(punto):
            return int(punto[0] * w), int(punto[1] * h)

        if lectura.mano:
            capa = pygame.Surface((w, h), pygame.SRCALPHA)
            for a, b in HAND_CONNECTIONS:
                pygame.draw.aaline(capa, (*E.ORO, 150), px(lectura.mano[a]), px(lectura.mano[b]))
            for punto in lectura.mano:
                x, y = px(punto)
                pygame.draw.circle(capa, (*E.ORO, 170), (x, y), 2)
            img.blit(capa, (0, 0))

        if not (self.estado and lectura.nariz and lectura.escala):
            return
        paso = self.estado.paso
        nx, ny = px(lectura.nariz)
        sep = max(9, int(0.06 * lectura.escala * w))
        y = ny + sep // 2
        lado_x = {"derecho": nx + sep, "izquierdo": nx - sep}  # imagen en espejo

        tapado = paso.tapado
        latido = 0.5 + 0.5 * math.sin(self.t * 4)
        for lado in ("derecho", "izquierdo"):
            if tapado in (lado, "ambos"):
                bien = lectura.estado == tapado
                color = E.JADE if bien else E.AZAFRAN
                r = 13 + int(3 * latido * (not bien))
                pygame.draw.circle(img, color, (lado_x[lado], y), r, 3)

        if paso.tipo == "contar" and paso.abierto:
            capa = pygame.Surface((w, h), pygame.SRCALPHA)
            self.aire.dibujar(capa, (lado_x[paso.abierto], y), paso.accion == "inhala")
            img.blit(capa, (0, 0))
            self._flecha(img, lado_x[paso.abierto], y, paso.accion == "inhala")

    def _flecha(self, img, x, y, entrando):
        """Flecha clara por donde pasa el aire. Sube hacia la nariz o baja desde ella."""
        vaiven = 6 * math.sin(self.t * 5)
        lejos, cerca = y + 78 + vaiven, y + 20 + vaiven
        ini, fin = (lejos, cerca) if entrando else (cerca, lejos)
        punta = -1 if entrando else 1  # hacia donde apunta
        cuerpo = [(x, ini), (x, fin - punta * 12)]
        cabeza = [(x, fin), (x - 11, fin - punta * 16), (x + 11, fin - punta * 16)]
        pygame.draw.line(img, E.NOCHE_ARRIBA, *cuerpo, 9)
        pygame.draw.polygon(img, E.NOCHE_ARRIBA, [(cx, cy + punta * 2) for cx, cy in cabeza])
        pygame.draw.line(img, E.CREMA, *cuerpo, 5)
        pygame.draw.polygon(img, E.CREMA, cabeza)

    def _pie(self) -> None:
        ayudas = {
            "inicio": "Señala con el índice o usa el ratón   ·   Flechas para moverte y Enter para pulsar   ·   M sonido   ·   Esc salir",
            "tutorial": "Palma abierta o Espacio para pausar   ·   M sonido   ·   Esc volver al inicio",
            "sesion": "Palma abierta o Espacio para pausar   ·   M sonido   ·   Esc volver al inicio",
            "resultado": "Señala el botón con el índice o usa el ratón   ·   Enter o Espacio continuar",
        }
        texto = ayudas[self.modo]
        if self.pausa_manual:
            texto = "Señala con el índice o usa el ratón   ·   Flechas para elegir y Enter para pulsar   ·   Esc salir"
        s = E.fuente("texto", 15).render(texto, True, E.APAGADO)
        self.pantalla.blit(s, s.get_rect(midbottom=(E.ANCHO // 2, E.ALTO - 22)))

    def _aviso(self) -> None:
        if not self.aviso:
            return
        texto, fin = self.aviso
        resto = fin - self.t
        if resto <= 0:
            self.aviso = None
            return
        alpha = int(255 * min(1.0, resto / 0.6))
        f = E.fuente("negrita", 18)
        s = f.render(texto, True, E.NOCHE_ARRIBA)
        caja = s.get_rect(midtop=(E.ANCHO // 2, 30)).inflate(36, 18)
        capa = pygame.Surface(caja.size, pygame.SRCALPHA)
        pygame.draw.rect(capa, (*E.ORO, 255), capa.get_rect(), border_radius=caja.h // 2)
        capa.blit(s, s.get_rect(center=(caja.w // 2, caja.h // 2)))
        capa.set_alpha(max(0, alpha))
        self.pantalla.blit(capa, caja.topleft)

    # ================= gestos =================

    def _gestos(self, lectura) -> None:
        """Cursor del dedo con su anillo de espera, y el anillo de la palma."""
        p = self.pantalla
        if self.palma.llenado > 0 and lectura.mano:
            x, y = lectura.mano[9]
            c = (E.CAMARA.x + int(x * E.CAMARA.w), E.CAMARA.y + int(y * E.CAMARA.h))
            D.enso(p, c, 46, 1, E.ORO_SUAVE, 4, 120)
            D.enso(p, c, 46, self.palma.llenado, E.LAVANDA, 7)
            D.texto(p, E.fuente("negrita", 16), "Pausa", E.CREMA, c[0], c[1] + 54)
        if self._menu_activo() and self.puntero.pos is not None:
            # Solo un punto discreto. Lo importante es el boton que resalta el iman
            c = (int(self.puntero.pos[0]), int(self.puntero.pos[1]))
            # Apagado si la mano no senala, para que se note que asi no pulsa
            alfa = 170 if self.puntero.senala else 55
            capa = pygame.Surface((24, 24), pygame.SRCALPHA)
            pygame.draw.circle(capa, (*E.CREMA, alfa), (12, 12), 6)
            pygame.draw.circle(capa, (*E.NOCHE_ARRIBA, alfa), (12, 12), 7, 1)
            p.blit(capa, (c[0] - 12, c[1] - 12))

    # ================= botones =================

    def _boton(self, rect, texto, tecla, accion, principal=False, etiqueta=None, icono=None,
               centrado=False, zona=None, grupo=None):
        p = self.pantalla
        indice = len(self.botones)
        por_dedo = (self._menu_activo() and self.puntero.pos is not None
                    and self.puntero.objetivo == indice)
        # Con el teclado se marca el boton del foco. En las vueltas, el menos y el
        # mas juntos, porque las flechas de los lados ya los manejan
        por_teclado = self.foco == indice or (
            grupo == "vueltas" and self.foco is not None and self.foco < indice
            and self.botones[self.foco].grupo == "vueltas")
        marcado = por_dedo or por_teclado
        encima = marcado or rect.collidepoint(pygame.mouse.get_pos())
        radio = rect.h // 2
        capa = pygame.Surface(rect.size, pygame.SRCALPHA)
        r = capa.get_rect()
        if principal:
            color = tuple(min(255, c + 18) for c in E.AZAFRAN) if encima else E.AZAFRAN
            pygame.draw.rect(capa, color, r, border_radius=radio)
            col_texto, col_tecla = E.NOCHE_ARRIBA, (90, 50, 20)
        else:
            pygame.draw.rect(capa, (*E.ORO, 46 if encima else 18), r, border_radius=radio)
            col_texto, col_tecla = E.CREMA, E.ORO_SUAVE
        if por_dedo and self.puntero.llenado > 0:
            # El boton se va llenando de izquierda a derecha mientras esperas
            relleno = pygame.Surface(rect.size, pygame.SRCALPHA)
            pygame.draw.rect(relleno, (255, 255, 255, 70), r, border_radius=radio)
            ancho = int(rect.w * min(1.0, self.puntero.llenado))
            capa.blit(relleno, (0, 0), pygame.Rect(0, 0, ancho, rect.h))
        borde = (*E.CREMA, 230) if marcado else (*E.ORO, 140)
        if not principal or marcado:
            pygame.draw.rect(capa, borde, r, 2 if marcado else 1, border_radius=radio)
        p.blit(capa, rect.topleft)

        s = E.fuente("negrita", 19).render(texto, True, col_texto)
        if centrado:
            p.blit(s, s.get_rect(center=rect.center))
        else:
            x = rect.x + 26
            if icono:
                icono((x + 10, rect.centery))
                x += 38
            p.blit(s, s.get_rect(midleft=(x, rect.centery)))
        if tecla:
            k = E.fuente("texto", 15).render(tecla, True, col_tecla)
            p.blit(k, k.get_rect(midright=(rect.right - 24, rect.centery)))
        if etiqueta:
            e = E.fuente("negrita", 12).render(etiqueta.upper(), True, E.NOCHE_ARRIBA)
            caja = e.get_rect().inflate(14, 6)
            caja.midright = (rect.right - 96, rect.centery)  # dentro, junto a la tecla
            pygame.draw.rect(p, E.ORO, caja, border_radius=caja.h // 2)
            p.blit(e, e.get_rect(center=caja.center))
        self.botones.append(Boton(rect, accion, zona, grupo))

    # ================= paneles =================

    def _panel_inicio(self, lectura) -> None:
        p, P = self.pantalla, E.PANEL
        cx = P.centerx
        izq, ancho = P.left + 32, P.w - 64
        D.texto(p, E.fuente("cursiva", 22), "tu práctica de hoy", E.ORO, cx, P.top + 22)

        # El ritual diario en una fila. De momento solo esta la respiracion
        hoy = date.today().isoformat()
        hecha = any(s["fecha"] == hoy and s["fase"] == "respiracion"
                    for s in self.progreso.sesiones)
        fases = [("Respiración", True, hecha), ("Meditación", False, False),
                 ("Estiramientos", False, False), ("Flexiones", False, False)]
        y = P.top + 74
        xs = [izq + int(ancho * (i + 0.5) / 4) for i in range(4)]
        pygame.draw.line(p, E.ORO_SUAVE, (xs[0], y), (xs[-1], y), 1)
        for x, (nombre, activa, hecho) in zip(xs, fases):
            if hecho:
                pygame.draw.circle(p, E.JADE, (x, y), 10)
                pygame.draw.lines(p, E.NOCHE_ARRIBA, False,
                                  [(x - 5, y), (x - 1, y + 4), (x + 5, y - 4)], 2)
            elif activa:
                pygame.draw.circle(p, E.TARJETA, (x, y), 10)
                pygame.draw.circle(p, E.AZAFRAN, (x, y), 10, 2)
            else:
                pygame.draw.circle(p, E.TARJETA, (x, y), 7)
                pygame.draw.circle(p, E.ORO_SUAVE, (x, y), 7, 1)
            s = E.fuente("negrita" if activa else "texto", 14).render(
                nombre, True, E.CREMA if activa else E.APAGADO)
            p.blit(s, s.get_rect(midtop=(x, y + 16)))

        # Botones, con aire entre ellos para que el iman no dude
        y = P.top + 128
        primera = not self.progreso.tutorial_hecho("respiracion")
        if primera:
            self._boton(pygame.Rect(izq, y, ancho, 52), "Aprender a respirar", "Espacio",
                        lambda: self._empezar("tutorial"), True, "primera vez")
            self._boton(pygame.Rect(izq, y + 64, ancho, 46), "Ir directo a la sesión", "S",
                        lambda: self._empezar("sesion"))
        else:
            self._boton(pygame.Rect(izq, y, ancho, 52), "Empezar a respirar", "Espacio",
                        lambda: self._empezar("sesion"), True)
            self._boton(pygame.Rect(izq, y + 64, ancho, 46), "Repasar el tutorial", "T",
                        lambda: self._empezar("tutorial"))

        # Nivel siguiente
        y = P.top + 252
        if self._avanzada_disponible():
            self._boton(pygame.Rect(izq, y, ancho, 46), "Respiración avanzada", "A",
                        lambda: self._empezar("sesion", "avanzada"))
        else:
            hechas = min(self.progreso.perfectas("respiracion", "principiante"),
                         PERFECTAS_PARA_AVANZADA)
            s = E.fuente("texto", 15).render(
                f"Nivel avanzado   {hechas} de {PERFECTAS_PARA_AVANZADA} sesiones con tres lotos",
                True, E.APAGADO)
            p.blit(s, s.get_rect(midtop=(cx, y - 2)))
            for i in range(PERFECTAS_PARA_AVANZADA):
                D.loto(p, (cx + (i - 2) * 34, y + 40), 16, E.ORO if i < hechas else E.ORO_SUAVE,
                       relleno=i < hechas, alpha=255 if i < hechas else 210)

        # Vueltas, con menos y mas a los lados para que esten lejos entre si
        y = P.top + 318
        v = self.vueltas
        lado = 92
        # Para el dedo, la fila entera cuenta. Mitad izquierda menos, mitad derecha mas
        mitad = ancho // 2
        self._boton(pygame.Rect(izq, y, lado, 46), "−", None,
                    lambda: self._cambiar_vueltas(-1), centrado=True,
                    zona=pygame.Rect(izq, y, mitad, 46), grupo="vueltas")
        self._boton(pygame.Rect(izq + ancho - lado, y, lado, 46), "+", None,
                    lambda: self._cambiar_vueltas(1), centrado=True,
                    zona=pygame.Rect(izq + mitad, y, ancho - mitad, 46), grupo="vueltas")
        D.texto(p, E.fuente("negrita", 19), f"{v} vueltas", E.CREMA, cx, y + 4)
        nota = ("no suben de nivel" if v < VUELTAS_NIVEL
                else "mínimo" if v == VUELTAS_MIN else "máximo" if v == VUELTAS_MAX else "")
        if nota:
            D.texto(p, E.fuente("texto", 13), nota, E.APAGADO, cx, y + 28)

        # Sonido
        y = P.top + 378
        activo = self.sonido.activo
        self._boton(pygame.Rect(izq, y, ancho, 46),
                    "Sonido activado" if activo else "Sonido apagado", "M",
                    self._alternar_sonido,
                    icono=lambda c: self._altavoz(c, activo, E.CREMA if activo else E.APAGADO))

        # Semana
        y = P.bottom - 40
        semana = self.progreso.semana(date.today())
        hoy_i = date.today().weekday()
        for i, (letra, hecho) in enumerate(zip(DIAS, semana)):
            x = cx + (i - 3) * 46
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

    def _panel_guion(self, lectura) -> None:
        p, P = self.pantalla, E.PANEL
        cx = P.centerx
        e = self.estado
        if e is None:
            return
        paso = e.paso
        tutorial = self.modo == "tutorial"

        # Cabecera
        if tutorial:
            cab = f"TUTORIAL   {e.indice + 1} DE {e.total}"
        elif paso.vuelta == 0:
            cab = "PREPARACIÓN"
        elif paso.vuelta > self.guion.vueltas:
            cab = "FINAL"
        else:
            cab = f"VUELTA {paso.vuelta} DE {self.guion.vueltas}"
        if self.variante == "avanzada" and not tutorial:
            cab += "   ·   AVANZADA"
        D.texto_espaciado(p, E.fuente("negrita", 13), cab, E.ORO, (cx, P.top + 26),
                          espacio=3, centrado=True)
        if not tutorial and 1 <= paso.vuelta <= self.guion.vueltas:
            n = self.guion.vueltas
            for i in range(n):
                x = cx + int((i - (n - 1) / 2) * 18)
                hecho = i + 1 < paso.vuelta
                actual = i + 1 == paso.vuelta
                pygame.draw.circle(p, E.ORO if (hecho or actual) else E.ORO_SUAVE,
                                   (x, P.top + 56), 4 if actual else 3, 0 if hecho or actual else 1)

        # Instruccion en huecos fijos para que nada se pise
        D.texto(p, E.fuente("titulo", 42), paso.texto, E.CREMA, cx, P.top + 84, P.w - 50)
        if paso.detalle:
            D.texto(p, E.fuente("texto", 20), paso.detalle, E.APAGADO, cx, P.top + 140, P.w - 70)

        centro = (cx, P.top + 318)
        radio = 88
        if paso.tipo == "contar":
            color = E.COLOR_ACCION[paso.accion]
            D.halo(p, centro, 150, color, 0.25 + 0.75 * e.llenado)
            D.enso(p, centro, radio, 1, E.ORO_SUAVE, 12, 45)
            D.enso(p, centro, radio, e.hecho, color, 14)
            # La fuente tiene numeros de estilo antiguo (el 3, 4, 5, 7 y 9 bajan
            # de la linea), asi que se centra por la tinta y no por la caja
            n = E.fuente("titulo", 92).render(str(e.cuenta), True, E.CREMA)
            recorte = n.get_bounding_rect()
            tinta = recorte.copy()
            tinta.center = (centro[0], centro[1] - 14)
            p.blit(n, tinta, recorte)
            d = E.fuente("texto", 16).render(f"de {paso.tiempos}", True, E.APAGADO)
            # Fijo para que no baile al cambiar de numero (el mas alto llega a +18)
            p.blit(d, d.get_rect(midtop=(centro[0], centro[1] + 28)))
            if e.correcto:
                self._chip("Bien", E.JADE)
            elif paso.tapado != "ninguno" and lectura.mano is None:
                # Sin mano no se sabe que tapas, y "tapa la izquierda" confunde
                # a quien ya la esta tapando
                self._chip("No veo tu mano, aléjate un poco", E.AZAFRAN)
            else:
                self._chip(COMO_TAPAR[paso.tapado], E.TERRACOTA)
        elif paso.tipo == "esperar":
            D.enso(p, centro, radio, 1, E.ORO_SUAVE, 12, 45)
            if e.hecho > 0:
                D.enso(p, centro, radio, e.hecho, E.JADE, 14)
                D.texto(p, E.fuente("titulo", 36), "Eso es", E.JADE, centro[0], centro[1] - 24)
            else:
                respira = 0.5 + 0.5 * math.sin(self.t * 1.6)
                D.loto(p, (centro[0], centro[1] + 22), 44, E.ORO, alpha=int(150 + 90 * respira))
            if lectura.estado is None:
                self._chip("No te veo", E.APAGADO, suave=True)
        else:  # mensaje
            D.halo(p, centro, 140, E.ORO, 0.5 + 0.3 * math.sin(self.t * 1.4))
            D.loto(p, (centro[0], centro[1] + 30), 70)
        if self.pausa_manual:
            ancho = (P.w - 72 - 12) // 2
            self._boton(pygame.Rect(P.left + 36, P.bottom - 82, ancho, 54), "Seguir", "Espacio",
                        self._seguir, True, grupo="pausa")
            self._boton(pygame.Rect(P.right - 36 - ancho, P.bottom - 82, ancho, 54), "Salir",
                        "Esc", self._volver_inicio, grupo="pausa")
        elif paso.tipo == "mensaje":
            ancho = int((P.w - 160) * e.hecho)
            pygame.draw.line(p, E.ORO_SUAVE, (P.left + 80, P.bottom - 44),
                             (P.right - 80, P.bottom - 44), 1)
            pygame.draw.line(p, E.ORO, (P.left + 80, P.bottom - 44),
                             (P.left + 80 + ancho, P.bottom - 44), 2)

    def _chip(self, texto, color, suave=False):
        if self.pausa_manual:
            return  # en su sitio van los botones de la pausa
        p, P = self.pantalla, E.PANEL
        f = E.fuente("texto" if suave else "negrita", 17)
        s = f.render(texto, True, color if suave else E.NOCHE_ARRIBA)
        caja = s.get_rect(center=(P.centerx, P.bottom - 42)).inflate(30, 14)
        if not suave:
            pygame.draw.rect(p, color, caja, border_radius=caja.h // 2)
        p.blit(s, s.get_rect(center=caja.center))

    def _panel_resultado(self, lectura) -> None:
        p, P = self.pantalla, E.PANEL
        cx = P.centerx
        r = self.resultado
        D.texto(p, E.fuente("cursiva", 22), "has terminado", E.ORO, cx, P.top + 28)
        D.texto(p, E.fuente("titulo", 40), "Sesión completada", E.CREMA, cx, P.top + 58)

        y = P.top + 190
        D.halo(p, (cx, y - 20), 170, E.ORO, 0.5)
        for i in range(3):
            ganado = i < r["estrellas"]
            # Los lotos aparecen uno detras de otro
            D.loto(p, (cx + (i - 1) * 96, y), 54 if i == 1 else 44,
                   E.ORO if ganado else E.ORO_SUAVE, relleno=ganado,
                   alpha=255 if ganado else 210)

        y += 40
        # Hacia abajo, para que un 39,9 no salga como 40 % con cero lotos
        pct = f"{math.floor(r['precision'] * 100)} %"
        D.texto(p, E.fuente("titulo", 52), pct, E.CREMA, cx, y)
        y = D.texto(p, E.fuente("texto", 17), "del tiempo tapaste el lado correcto",
                    E.APAGADO, cx, y + 72)
        if r["record"]:
            y = D.texto(p, E.fuente("negrita", 17), "Nueva mejor marca", E.ORO, cx, y + 6)

        y += 24
        racha = self.progreso.racha(date.today())
        s = E.fuente("negrita", 19).render(
            f"Racha de {racha} {'día' if racha == 1 else 'días'}", True, E.CREMA)
        caja = s.get_rect(midtop=(cx + 14, y))
        p.blit(s, caja)
        D.llama(p, (caja.left - 18, caja.centery + 2), 22)

        # Que el bloque del nivel nunca pise el boton de abajo
        y = min(y + 36, P.bottom - 82 - 56)
        if r["desbloqueada"]:
            D.texto(p, E.fuente("negrita", 18), "Has desbloqueado la respiración avanzada",
                    E.AZAFRAN, cx, y + 14)
        elif not self._avanzada_disponible():
            hechas = min(self.progreso.perfectas("respiracion", "principiante"),
                         PERFECTAS_PARA_AVANZADA)
            if r["estrellas"] < 3:
                D.texto(p, E.fuente("negrita", 16), "Esta no cuenta, hacen falta tres lotos (85 %)",
                        E.TERRACOTA, cx, y)
            elif r.get("pocas_vueltas"):
                D.texto(p, E.fuente("negrita", 16),
                        f"Para subir de nivel hacen falta {VUELTAS_NIVEL} vueltas o más",
                        E.TERRACOTA, cx, y)
            y += 24
            D.texto(p, E.fuente("texto", 16),
                    f"Nivel avanzado   {hechas} de {PERFECTAS_PARA_AVANZADA} sesiones con tres lotos",
                    E.APAGADO, cx, y)

        self._boton(pygame.Rect(P.left + 36, P.bottom - 82, P.w - 72, 54), "Volver al inicio",
                    "Espacio", self._volver_inicio, True)
