"""Pantallas de la respiracion alterna. La logica esta en temple/respiracion.py."""

from __future__ import annotations

import math

import pygame

from temple.interfaz import dibujo as D
from temple.interfaz import estilo as E
from temple.interfaz import marco
from temple.interfaz import piezas as Z
from temple.interfaz.fases.base import Fase
from temple.interfaz.opciones import Opciones
from temple.progreso import PERFECTAS_PARA_AVANZADA, VUELTAS_MAX, VUELTAS_MIN, VUELTAS_NIVEL
from temple.puntero import PALMA_S
from temple.respiracion import (COMO_TAPAR, VUELTAS, Guion, estrellas, guion_sesion,
                                guion_tutorial)

P = E.PANEL


class Respiracion(Fase):
    clave = "respiracion"
    nombre = "Respiración"
    tecla = pygame.K_r
    motivo_pausa = "Señala Seguir con el índice y espera"

    def __init__(self, app, opciones: Opciones):
        super().__init__(app, PALMA_S)
        self.vueltas_fijas = opciones.vueltas  # --vueltas para probar, no se guarda
        self.tiempo_s = opciones.tiempo_s
        self.forzar_avanzada = opciones.avanzada
        self.aire = D.Aire()
        self.guion: Guion | None = None
        self.variante = "principiante"
        self.reloj = 0.0  # tiempo del guion, se para en la pausa
        self.estado = None
        self.estado_previo = None
        self.ofrecer_meditar = False  # al acabar, si lo siguiente del ritual es meditar

    @property
    def vueltas(self) -> int:
        return self.vueltas_fijas or self.app.progreso.vueltas(VUELTAS)

    def avanzada_disponible(self) -> bool:
        return self.forzar_avanzada or self.app.progreso.avanzada_desbloqueada()

    # ================= inicio =================

    def cambiar(self, paso: int) -> None:
        self.vueltas_fijas = None
        self.app.progreso.elegir_vueltas(self.vueltas + paso)

    def tecla_inicio(self, k) -> bool:
        if k == pygame.K_a and self.avanzada_disponible():
            self.app.empezar("sesion", "avanzada")
            return True
        return False

    def resumen(self) -> str:
        if self.app.progreso.avanzada_desbloqueada():
            return "Tienes la respiración avanzada"
        hechas = min(self.app.progreso.perfectas(self.clave, "principiante"),
                     PERFECTAS_PARA_AVANZADA)
        return f"{hechas} de {PERFECTAS_PARA_AVANZADA} sesiones con 3 lotos para la avanzada"

    def panel_inicio(self) -> None:
        app, p = self.app, self.app.pantalla
        primera = not app.progreso.tutorial_hecho(self.clave)
        Z.botones_empezar(app, primera, "Aprender a respirar", "Empezar a respirar")

        # Nivel siguiente
        y = P.top + 252
        if self.avanzada_disponible():
            app.botonera.dibujar(p, pygame.Rect(Z.IZQ, y, Z.ANCHO, 46), "Respiración avanzada",
                                 "A", lambda: app.empezar("sesion", "avanzada"))
        else:
            hechas = min(app.progreso.perfectas(self.clave, "principiante"),
                         PERFECTAS_PARA_AVANZADA)
            Z.linea(p, f"{PERFECTAS_PARA_AVANZADA} sesiones con 3 lotos desbloquean la avanzada",
                    "texto", 15, E.APAGADO, y - 4)
            Z.fila_lotos(p, y, hechas, PERFECTAS_PARA_AVANZADA)

        v = self.vueltas
        nota = ("no suben de nivel" if v < VUELTAS_NIVEL
                else "mínimo" if v == VUELTAS_MIN else "máximo" if v == VUELTAS_MAX else "")
        nombre = "vuelta" if v == 1 else "vueltas"
        Z.fila_mas_menos(app, f"{v} {nombre}", nota, self.cambiar, "vueltas")

    # ================= practica =================

    def empezar(self, modo: str, variante: str) -> None:
        self.variante = variante
        if modo == "tutorial":
            self.guion = Guion(guion_tutorial(), tiempo_s=self.tiempo_s)
        else:
            self.guion = Guion(guion_sesion(self.vueltas, variante == "avanzada"),
                               tiempo_s=self.tiempo_s)
        self.reloj = 0.0
        self.estado = self.estado_previo = None

    def salir(self) -> None:
        self.estado = self.estado_previo = None

    def actualizar(self, dt: float, lectura) -> None:
        app = self.app
        en_cuenta = self.estado is not None and self.estado.paso.tipo == "contar"
        # El hilo de aire se mueve aunque estes en el inicio, para que se apague despacio
        self.aire.actualizar(dt, en_cuenta and self.estado.paso.abierto is not None
                             and not app.pausado())
        if app.modo not in ("tutorial", "sesion"):
            return

        # Pausa automatica si te vas de la camara en mitad de la cuenta
        app.vigilar(not lectura.cuerpo and en_cuenta)
        if app.pausado():
            self.palma.actualizar(0, None)
            return
        if self.palma.actualizar(dt, lectura.mano, lectura.nariz, lectura.escala):
            app.pausa_manual = True
            app.sonido("toque")
            return

        self.reloj += dt
        self.estado_previo = self.estado
        self.estado = self.guion.actualizar(self.reloj, lectura.tapado, lectura.mano is not None)
        self._sonidos()
        if self.estado.terminado:
            self._terminar()

    def _sonidos(self) -> None:
        antes, ahora = self.estado_previo, self.estado
        if antes is None or ahora.terminado:
            return
        if ahora.indice != antes.indice and antes.paso.tipo == "esperar":
            self.app.sonido("toque")
        elif ahora.paso.tipo == "contar" and (ahora.indice != antes.indice
                                              or ahora.cuenta != antes.cuenta):
            self.app.sonido("tic")

    def _terminar(self) -> None:
        app = self.app
        app.sonido("cuenco")
        if app.modo == "tutorial":
            app.progreso.marcar_tutorial(self.clave)
            app.modo = "inicio"
            app.avisar("Ya sabes respirar. Ahora, la sesión completa", 5)
            return
        antes = app.progreso.avanzada_desbloqueada()
        precision = self.guion.precision
        n = estrellas(precision)
        mejor_antes = app.progreso.mejor(self.clave, self.variante)
        app.progreso.registrar(self.clave, self.variante, precision, n, vueltas=self.vueltas)
        self.resultado = {
            "pocas_vueltas": self.vueltas < VUELTAS_NIVEL,
            "precision": precision,
            "estrellas": n,
            "record": mejor_antes is not None and precision > mejor_antes,
            "desbloqueada": not antes and app.progreso.avanzada_desbloqueada(),
        }
        # Despues de respirar, lo siguiente del ritual es meditar
        self.ofrecer_meditar = not app.progreso.hecha_hoy("meditacion")
        app.modo = "resultado"
        self.estado = None

    # ---- camara ----

    def pistas(self, img, lectura) -> None:
        """Mano en trazo fino, circulo donde tapar y el hilo de aire."""
        marco.mano(img, lectura)
        if not (self.estado and lectura.nariz and lectura.escala):
            return
        paso = self.estado.paso
        w = img.get_width()
        nx, ny = marco.px(img, lectura.nariz)
        sep = max(9, int(0.06 * lectura.escala * w))
        y = ny + sep // 2
        lado_x = {"derecho": nx + sep, "izquierdo": nx - sep}  # imagen en espejo

        tapado = paso.tapado
        latido = 0.5 + 0.5 * math.sin(self.app.t * 4)
        for lado in ("derecho", "izquierdo"):
            if tapado in (lado, "ambos"):
                bien = lectura.tapado == tapado
                color = E.JADE if bien else E.AZAFRAN
                r = 13 + int(3 * latido * (not bien))
                pygame.draw.circle(img, color, (lado_x[lado], y), r, 3)

        if paso.tipo == "contar" and paso.abierto:
            capa = pygame.Surface(img.get_size(), pygame.SRCALPHA)
            self.aire.dibujar(capa, (lado_x[paso.abierto], y), paso.accion == "inhala")
            img.blit(capa, (0, 0))
            self._flecha(img, lado_x[paso.abierto], y, paso.accion == "inhala")

    def _flecha(self, img, x, y, entrando) -> None:
        """Flecha clara por donde pasa el aire. Sube hacia la nariz o baja desde ella."""
        vaiven = 6 * math.sin(self.app.t * 5)
        lejos, cerca = y + 78 + vaiven, y + 20 + vaiven
        ini, fin = (lejos, cerca) if entrando else (cerca, lejos)
        punta = -1 if entrando else 1  # hacia donde apunta
        cuerpo = [(x, ini), (x, fin - punta * 12)]
        cabeza = [(x, fin), (x - 11, fin - punta * 16), (x + 11, fin - punta * 16)]
        pygame.draw.line(img, E.NOCHE_ARRIBA, *cuerpo, 9)
        pygame.draw.polygon(img, E.NOCHE_ARRIBA, [(cx, cy + punta * 2) for cx, cy in cabeza])
        pygame.draw.line(img, E.CREMA, *cuerpo, 5)
        pygame.draw.polygon(img, E.CREMA, cabeza)

    # ---- panel ----

    def panel(self, lectura) -> None:
        app, p = self.app, self.app.pantalla
        cx = P.centerx
        e = self.estado
        if e is None:
            return
        paso = e.paso
        tutorial = app.modo == "tutorial"
        n = self.guion.vueltas

        if tutorial:
            cab = f"TUTORIAL   {e.indice + 1} DE {e.total}"
        elif paso.vuelta == 0:
            cab = "PREPARACIÓN"
        elif paso.vuelta > n:
            cab = "FINAL"
        else:
            cab = f"VUELTA {paso.vuelta} DE {n}"
        if self.variante == "avanzada" and not tutorial:
            cab += "   ·   AVANZADA"
        Z.cabecera(p, cab)
        if not tutorial and 1 <= paso.vuelta <= n:
            for i in range(n):
                x = cx + int((i - (n - 1) / 2) * 18)
                hecho = i + 1 < paso.vuelta
                actual = i + 1 == paso.vuelta
                pygame.draw.circle(p, E.ORO if (hecho or actual) else E.ORO_SUAVE,
                                   (x, P.top + 56), 4 if actual else 3, 0 if hecho or actual else 1)
        Z.instruccion(p, paso)

        centro, radio = (cx, P.top + 318), 88
        if paso.tipo == "contar":
            color = E.COLOR_ACCION[paso.accion]
            D.halo(p, centro, 150, color, 0.25 + 0.75 * e.llenado)
            D.enso(p, centro, radio, 1, E.ORO_SUAVE, 12, 45)
            D.enso(p, centro, radio, e.hecho, color, 14)
            Z.numero(p, str(e.cuenta), 92, centro, 14)
            d = E.fuente("texto", 20).render(f"de {paso.tiempos}", True, E.APAGADO)
            # Fijo para que no baile al cambiar de numero (el mas alto llega a +18)
            p.blit(d, d.get_rect(midtop=(centro[0], centro[1] + 28)))
            if e.correcto:
                Z.chip(app, "Bien", E.JADE)
            elif paso.tapado != "ninguno" and lectura.mano is None:
                # Sin mano no se sabe que tapas, y "tapa la izquierda" confunde
                # a quien ya la esta tapando
                Z.chip(app, "No veo tu mano, aléjate un poco", E.AZAFRAN)
            else:
                Z.chip(app, COMO_TAPAR[paso.tapado], E.TERRACOTA)
        elif paso.tipo == "esperar":
            Z.esperando(p, centro, radio, e.hecho, app.t)
            if not lectura.cuerpo:
                Z.chip(app, "No te veo", E.APAGADO, suave=True)
        else:
            Z.mensaje(p, centro, app.t)
        if app.pausa_manual:
            Z.botones_pausa(app)
        elif paso.tipo == "mensaje":
            Z.barra_mensaje(p, e.hecho)

    # ================= resultado =================

    def accion_resultado(self) -> None:
        if self.ofrecer_meditar:
            self.app.elegir_fase("meditacion")
            self.app.accion_principal()
        else:
            self.app.volver_inicio()

    def panel_resultado(self) -> None:
        app, p = self.app, self.app.pantalla
        r = self.resultado
        Z.resultado(app, r, "Sesión completada", "del tiempo tapaste el lado correcto")

        hechas = min(app.progreso.perfectas(self.clave, "principiante"), PERFECTAS_PARA_AVANZADA)
        if r["desbloqueada"]:
            texto, color = "Has desbloqueado la respiración avanzada", E.AZAFRAN
        elif self.variante == "avanzada" or self.avanzada_disponible():
            texto, color = "", E.APAGADO
        elif r.get("pocas_vueltas"):
            texto, color = (f"Con menos de {VUELTAS_NIVEL} vueltas no cuenta para la avanzada",
                            E.APAGADO)
        elif r["estrellas"] < 3:
            texto, color = "Para la avanzada cuentan las de 3 lotos", E.APAGADO
        else:
            texto, color = (f"Cuenta para la avanzada, {hechas} de {PERFECTAS_PARA_AVANZADA}",
                            E.JADE)
        if texto:
            Z.linea(p, texto, "negrita", 16, color, P.top + 384)

        if self.ofrecer_meditar:
            Z.botones_seguir(app, "Meditar", self.accion_resultado)
        else:
            Z.boton_volver(app)
