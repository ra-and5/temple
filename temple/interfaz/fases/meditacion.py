"""Pantallas de la meditacion. La logica esta en temple/meditacion.py."""

from __future__ import annotations

import math

import pygame
from mediapipe.python.solutions.hands import HAND_CONNECTIONS

from temple import meditacion as M
from temple.interfaz import dibujo as D
from temple.interfaz import estilo as E
from temple.interfaz import marco
from temple.interfaz import piezas as Z
from temple.interfaz.fases.base import Fase
from temple.interfaz.opciones import Opciones
from temple.interfaz.textos import minutos as texto_minutos
from temple.progreso import NIVELES

P = E.PANEL
INDICADORES = (("quieto", "Quieto"), ("recto", "Recto"), ("ojos", "Ojos cerrados"))
CONSEJOS = {  # dicho como lo que hay que hacer, no como el fallo
    "quieto": "quédate quieto ({} s moviéndote)",
    "recto": "mantén la espalda recta ({} s encorvado)",
    "ojos": "mantén los ojos cerrados ({} s abiertos)",
}


class Meditacion(Fase):
    clave = "meditacion"
    nombre = "Meditación"
    verbo = "Meditar"
    tecla = pygame.K_e
    colocacion = "Sentado y de frente, que se te vea de la cintura para arriba"
    usa_cara = True
    motivo_pausa = "Cierra los ojos 2 s, o abre la palma y ciérrala en un puño, para seguir"
    ayuda = "Palma abierta y quieta, por encima de los hombros, para pausar"

    def __init__(self, app, opciones: Opciones):
        super().__init__(app, M.PALMA_MEDITAR_S)
        self.minutos_fijos = opciones.minutos  # --minutos para probar
        self.ruta_registro = opciones.datos / M.REGISTRO.name
        self.practica: M.Practica | None = None
        self.registro: M.Registro | None = None
        self.reloj = 0.0  # tiempo del guion, se para en la pausa
        self.estado: M.Estado | None = None
        self._ojos_desde: float | None = None  # en la pausa, cerrar los ojos sigue

    @property
    def minutos(self) -> float:
        if self.minutos_fijos is not None:
            return self.minutos_fijos
        return NIVELES[self.clave][self.nivel]

    def _libre(self) -> bool:
        """Meditando sin cuenta atras. Se acaba con Terminar en la pausa."""
        return (self.practica is not None and self.practica.libre
                and self.estado is not None and self.estado.paso.tipo == "meditar")

    def terminar_libre(self) -> None:
        self.app.pausa_manual = False
        self.practica.terminar(self.reloj)

    def nombre_nivel(self, n: int) -> str:
        m = NIVELES[self.clave][n]
        return "Sin límite" if m == 0 else texto_minutos(m)

    # ================= practica =================

    def empezar(self, modo: str) -> None:
        pasos = M.guion_tutorial() if modo == "tutorial" else M.guion_sesion(self.minutos)
        self.practica = M.Practica(pasos)
        self._cerrar_registro()
        self.registro = M.Registro(self.ruta_registro)
        self.reloj = 0.0
        self.estado = None

    def _cerrar_registro(self) -> None:
        if self.registro is not None:
            self.registro.cerrar()
            self.registro = None

    def salir(self) -> None:
        self._cerrar_registro()
        self.estado = None

    def tecla_practica(self, k) -> bool:
        if k in (pygame.K_RETURN, pygame.K_KP_ENTER) and self.app.pausa_manual and self.practica.libre:
            self.terminar_libre()
            return True
        return False

    def actualizar(self, dt: float, lectura) -> None:
        app = self.app
        if app.modo not in ("tutorial", "sesion"):
            return
        # Pausa automatica si te vas mientras se mide la postura o se medita
        vigilando = self.estado is not None and self.estado.paso.tipo in ("calibrar", "meditar")
        app.vigilar(not lectura.cuerpo and vigilando)
        if app.pausado():
            self.palma.actualizar(0, None)
            self._seguir_con_los_ojos(lectura)
            return
        self._ojos_desde = None
        # La palma solo cuenta por encima de los hombros, para que las manos en
        # el regazo no pausen solas
        techo = min(lectura.hombros[0][1], lectura.hombros[1][1]) if lectura.hombros else -1
        if self.pausa_con_palma(dt, lectura, techo):
            return

        self.reloj += dt
        antes = self.estado
        self.estado = e = self.practica.actualizar(self.reloj, _cuerpo(lectura))
        if self.registro is not None:
            self.registro.apuntar(self.reloj, e)
        if e.terminado:
            self._terminar()
            return
        if (antes is not None and e.indice != antes.indice
                and antes.paso.tipo in ("esperar", "calibrar")):
            app.sonido("toque")
        if e.nuevo_paso and e.paso.sonido:
            app.sonido(e.paso.sonido)
        if e.aviso:
            app.sonido("aviso")
        if e.minuto:
            app.sonido("campana")

    def _seguir_con_los_ojos(self, lectura) -> None:
        """En la pausa, cerrar los ojos un momento sigue meditando, sin buscar el boton."""
        app = self.app
        if app.pausa_manual and lectura.ojos is not None and lectura.ojos >= M.OJOS_CERRADOS:
            if self._ojos_desde is None:
                self._ojos_desde = app.t
            elif app.t - self._ojos_desde >= M.SEGUIR_OJOS_S:
                app.pausa_manual = False
                self._ojos_desde = None
                app.sonido("toque")
        else:
            self._ojos_desde = None

    def _terminar(self) -> None:
        app = self.app
        app.sonido("cuenco")
        app.camara.cara = False
        self._cerrar_registro()
        self.estado = None
        if app.modo == "tutorial":
            app.progreso.marcar_tutorial(self.clave)
            app.fin_tutorial("Ya sabes meditar. Ahora, la sesión completa")
            return
        pr = self.practica
        self.guardar(pr.precision, M.lotos(pr.precision), minutos=pr.minutos)
        self.resultado["mal_s"] = dict(pr.mal_s)
        app.modo = "resultado"

    def lineas_datos(self) -> list[str]:
        if self.estado is None:
            return []
        m = self.estado.medida

        def f(v):
            return "-" if v is None else f"{v:.2f}"

        return [f"movimiento {f(m.movimiento)}  (quieto < {M.MOVIDO})",
                f"altura {f(m.altura)}  (recto >= {M.ENCORVADO})",
                f"inclinacion {f(m.inclinacion)}  (recto < {M.INCLINADO})"]

    # ---- camara ----

    def pistas(self, img, lectura) -> None:
        """Hombros y cuello en trazo fino, y la raya por la que no debe bajar la nariz."""
        if not (lectura.hombros and lectura.nariz):
            return
        h = img.get_height()
        ev = self.practica.evaluador if self.practica else None
        faltas = self.estado.faltas if self.estado else frozenset()
        a, b = lectura.hombros
        centro = ((a[0] + b[0]) / 2, (a[1] + b[1]) / 2)
        color = E.TERRACOTA if "recto" in faltas else E.JADE if ev and ev.calibrado else E.ORO
        capa = pygame.Surface(img.get_size(), pygame.SRCALPHA)

        def px(punto):
            return marco.px(img, punto)

        pygame.draw.line(capa, (*color, 200), px(a), px(b), 3)
        pygame.draw.line(capa, (*color, 200), px(centro), px(lectura.nariz), 3)
        for punto in (a, b):
            pygame.draw.circle(capa, (*color, 220), px(punto), 6)
        pygame.draw.circle(capa, (*E.CREMA, 230), px(lectura.nariz), 6)
        if ev and ev.calibrado:
            # Si la nariz cae por debajo de esta raya, estas encorvado
            y = centro[1] - M.ENCORVADO * ev.base_altura * ev.base_escala
            x = centro[0]
            mitad = ev.base_escala * 0.45
            x0, x1 = px((x - mitad, y))[0], px((x + mitad, y))[0]
            yy = int(y * h)
            for xi in range(x0, x1, 14):
                pygame.draw.line(capa, (*E.CREMA, 150), (xi, yy), (min(xi + 7, x1), yy), 2)
        if lectura.mano:
            for i, j in HAND_CONNECTIONS:
                pygame.draw.aaline(capa, (*E.ORO, 120), px(lectura.mano[i]), px(lectura.mano[j]))
        img.blit(capa, (0, 0))

    # ---- panel ----

    def panel(self, lectura) -> None:
        app, p = self.app, self.app.pantalla
        cx = P.centerx
        e = self.estado
        if e is None:
            return
        paso = e.paso
        if app.modo == "tutorial":
            cab = f"TUTORIAL   {e.indice + 1} DE {e.total}"
        else:
            cab = "MEDITACIÓN   ·   " + (
                "SIN LÍMITE" if self.practica.libre else texto_minutos(self.practica.minutos).upper())
        Z.cabecera(p, cab)
        Z.instruccion(p, paso)

        if app.pausa_manual:
            # En el centro, a la altura de los hombros, que es donde llega el dedo
            # estando sentado cerca de la camara
            Z.botones_pausa(app, P.top + 250, self.terminar_libre if self._libre() else None)
            return

        centro, radio = Z.CENTRO, Z.RADIO
        if paso.tipo == "meditar":
            # El halo respira despacio (unas 6 veces por minuto) para acompañar
            D.halo(p, centro, 150, E.JADE, 0.35 + 0.25 * math.sin(app.t * 2 * math.pi / 10))
            D.enso(p, centro, radio, 1, E.ORO_SUAVE, 12, 45)
            D.enso(p, centro, radio, e.hecho, E.ORO, 14)
            libre = self.practica.libre
            resto = int(e.transcurrido_s) if libre else math.ceil(e.restante_s)
            Z.numero(p, f"{resto // 60}:{resto % 60:02d}", 64, centro, 10)
            d = E.fuente("texto", 20).render("llevas" if libre else "quedan", True, E.APAGADO)
            p.blit(d, d.get_rect(midtop=(centro[0], centro[1] + 30)))
        elif paso.tipo == "calibrar":
            D.enso(p, centro, radio, 1, E.ORO_SUAVE, 12, 45)
            D.enso(p, centro, radio, e.hecho, E.ORO, 14)
            D.loto(p, (centro[0], centro[1] + 22), 44, E.ORO)
        elif paso.tipo == "esperar":
            Z.esperando(p, centro, radio, e.hecho, app.t)
        else:
            Z.mensaje(p, centro, app.t)

        if not e.medida.cuerpo:
            Z.chip(app, "No te veo", E.APAGADO, suave=True)
        elif self.practica.evaluador.calibrado and paso.tipo in ("meditar", "esperar"):
            self._indicadores(e)
        elif paso.tipo == "mensaje":
            Z.barra_mensaje(p, e.hecho)

    def _indicadores(self, e) -> None:
        """Quieto, recto y ojos. Bien es un circulo lleno con marca, mal un aro con
        exclamacion, y sin saberlo un aro con interrogacion. Asi no depende solo del color."""
        p = self.app.pantalla
        y = P.bottom - 58
        for i, (clave, nombre) in enumerate(INDICADORES):
            x = P.centerx + (i - 1) * 138
            valor = e.medida.bien(clave)
            if clave in e.faltas:
                pygame.draw.circle(p, E.TERRACOTA, (x, y), 13, 3)
                D.texto(p, E.fuente("negrita", 18), "!", E.TERRACOTA, x, y - 13)
                col = E.TERRACOTA
            elif valor is None:
                pygame.draw.circle(p, E.ORO_SUAVE, (x, y), 13, 1)
                D.texto(p, E.fuente("negrita", 16), "?", E.APAGADO, x, y - 12)
                col = E.APAGADO
            else:
                pygame.draw.circle(p, E.JADE, (x, y), 13)
                pygame.draw.lines(p, E.NOCHE_ARRIBA, False,
                                  [(x - 6, y), (x - 2, y + 5), (x + 6, y - 5)], 3)
                col = E.CREMA
            s = E.fuente("negrita", 15).render(nombre, True, col)
            p.blit(s, s.get_rect(midtop=(x, y + 20)))

    # ================= resultado =================

    def dibujar_resultado(self) -> None:
        p, r = self.app.pantalla, self.resultado
        Z.resultado(self.app, r, "Meditación completada",
                    "del tiempo quieto, recto y con los ojos cerrados")
        # Lo que mas puntos ha quitado, para saber que mejorar
        if r["estrellas"] < 3:
            peor = max(r["mal_s"], key=r["mal_s"].get)
            segundos = round(r["mal_s"][peor])
            if segundos >= 1:
                Z.linea(p, f"Para mejorar, {CONSEJOS[peor].format(segundos)}", "texto", 15,
                        E.APAGADO, P.top + 326)


def _cuerpo(lectura) -> M.Cuerpo | None:
    """Lo que la logica necesita de la lectura de la camara."""
    if not lectura.cuerpo or not lectura.nariz or not lectura.hombros:
        return None
    return M.Cuerpo(lectura.nariz, *lectura.hombros, lectura.ojos)
