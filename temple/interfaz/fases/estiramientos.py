"""Pantallas de los estiramientos. La logica esta en temple/estiramientos.py."""

from __future__ import annotations

import math

import pygame

from temple import estiramientos as S
from temple.interfaz import dibujo as D
from temple.interfaz import estilo as E
from temple.interfaz import marco
from temple.interfaz import piezas as Z
from temple.interfaz.fases.base import Fase
from temple.interfaz.opciones import Opciones
from temple.progreso import NIVELES
from temple.puntero import PALMA_S

P = E.PANEL


class Estiramientos(Fase):
    clave = "estiramientos"
    nombre = "Estiramientos"
    verbo = "Estirar"
    tecla = pygame.K_i
    colocacion = "Sentado y de frente, que se vean tu cabeza y tus brazos"
    con_niveles = False
    sin_niveles = "Calentamiento hecho. Listo para las flexiones"
    # Al estirar las manos van a la cabeza, al codo y arriba con la palma
    # abierta. Por eso la palma pausa siempre menos mientras haces bien una postura
    ayuda = "Palma abierta y quieta para pausar, fuera de la postura"

    def __init__(self, app, opciones: Opciones):
        super().__init__(app, PALMA_S)
        self.segundos_fijos = opciones.segundos  # --segundos para probar
        self.ruta_registro = opciones.datos / S.REGISTRO.name
        self.practica: S.Practica | None = None
        self.registro: S.Registro | None = None
        self.reloj = 0.0  # tiempo del guion, se para en la pausa
        self.estado: S.Estado | None = None

    @property
    def segundos(self) -> float:
        return self.segundos_fijos or NIVELES[self.clave][self.nivel]

    def nombre_nivel(self, n: int) -> str:
        return f"{len(S.POSTURAS)} posturas de {NIVELES[self.clave][n]} s"

    # ================= practica =================

    def empezar(self, modo: str) -> None:
        pasos = S.guion_tutorial() if modo == "tutorial" else S.guion_sesion(self.segundos)
        self.practica = S.Practica(pasos)
        self._cerrar_registro()
        self.registro = S.Registro(self.ruta_registro)
        self.reloj = 0.0
        self.estado = None

    def _cerrar_registro(self) -> None:
        if self.registro is not None:
            self.registro.cerrar()
            self.registro = None

    def estirando(self) -> bool:
        """Si ahora mismo haces bien una de las posturas."""
        e = self.estado
        return (e is not None and e.paso.objetivo in S.NOMBRES
                and S.falta(e.paso.objetivo, e.medida) is None)

    def salir(self) -> None:
        self._cerrar_registro()
        self.estado = None

    def actualizar(self, dt: float, lectura) -> None:
        app = self.app
        if app.modo not in ("tutorial", "sesion"):
            return
        manteniendo = self.estado is not None and self.estado.paso.tipo == "mantener"
        app.vigilar(not lectura.cuerpo and manteniendo)
        if app.pausado():
            self.palma.actualizar(0, None)
            return
        if self.estirando():
            # Con la postura bien hecha, la mano abierta es parte del estiramiento
            # (sobre la cabeza o arriba), asi que no pausa (prueba de Rares del 19/11)
            self.palma.actualizar(0, None)
        elif self.pausa_con_palma(dt, lectura):
            return

        self.reloj += dt
        antes = self.estado
        self.estado = e = self.practica.actualizar(self.reloj, _cuerpo(lectura))
        if self.registro is not None:
            self.registro.apuntar(self.reloj, e)
        if e.terminado:
            self._terminar()
            return
        if antes is not None and e.indice != antes.indice and antes.paso.tipo != "mensaje":
            app.sonido("toque")
        if e.aviso:
            app.sonido("aviso")

    def _terminar(self) -> None:
        app = self.app
        app.sonido("cuenco")
        self._cerrar_registro()
        self.estado = None
        if app.modo == "tutorial":
            app.progreso.marcar_tutorial(self.clave)
            app.fin_tutorial("Ya sabes estirar. Ahora, la sesión completa")
            return
        pr = self.practica
        self.guardar(pr.precision, S.lotos(pr.precision))
        self.resultado["peor"] = pr.peor
        app.modo = "resultado"

    def lineas_datos(self) -> list[str]:
        if self.estado is None:
            return []
        m = self.estado.medida

        def f(v):
            return "-" if v is None else f"{v:.2f}"

        return [f"inclinacion {f(m.inclinacion)}  (a un lado >= {S.INCLINAR_GRADOS:g})",
                f"mano en la cabeza der {f(m.mano_der)}  izq {f(m.mano_izq)}  (>= {S.MANO_CABEZA})",
                f"codos {f(m.codos)}  (arriba > 0)",
                f"cruce der {f(m.cruce_der)}  izq {f(m.cruce_izq)}  (cruzado >= {S.CRUZAR})",
                f"sujeta el codo {f(m.sujeta)}  (<= {S.SUJETAR})",
                f"triceps codo der {f(m.codo_der)} izq {f(m.codo_izq)}  (>= {S.CODO_ARRIBA})",
                f"triceps doblado der {f(m.doblado_der)} izq {f(m.doblado_izq)}  (>= {S.DOBLADO})"]

    # ---- camara ----

    def pistas(self, img, lectura) -> None:
        """Hombros, orejas y el brazo que toca, y una raya discontinua con la meta."""
        c = _cuerpo(lectura)
        if c is None or self.estado is None:
            return
        objetivo = self.estado.paso.objetivo
        bien = objetivo is not None and S.cumple(objetivo, self.estado.medida)
        color = E.JADE if bien else E.ORO
        capa = pygame.Surface(img.get_size(), pygame.SRCALPHA)

        def px(punto):
            return marco.px(img, punto)

        def linea(a, b, col=color):
            pygame.draw.line(capa, (*col, 200), px(a), px(b), 3)

        def raya(a, b):
            """Discontinua, como la de la meditacion. Hasta aqui hay que llegar."""
            (x0, y0), (x1, y1) = px(a), px(b)
            largo = max(math.hypot(x1 - x0, y1 - y0), 1)
            for i in range(0, int(largo), 14):
                f0, f1 = i / largo, min(i + 7, largo) / largo
                pygame.draw.line(capa, (*E.CREMA, 170), (x0 + (x1 - x0) * f0, y0 + (y1 - y0) * f0),
                                 (x0 + (x1 - x0) * f1, y0 + (y1 - y0) * f1), 2)

        linea(c.hombro_a, c.hombro_b, E.ORO_SUAVE)
        e = c.escala
        if objetivo in ("cuello_der", "cuello_izq", "neutro", "cuerpo") or objetivo is None:
            linea(c.oreja_a, c.oreja_b)
            for o in (c.oreja_a, c.oreja_b):
                pygame.draw.circle(capa, (*color, 220), px(o), 6)
        if objetivo in ("cuello_der", "cuello_izq"):
            # La linea de las orejas tiene que inclinarse hasta esta raya
            signo = 1 if objetivo == "cuello_der" else -1
            base = math.radians(_angulo_hombros(c) + signo * S.INCLINAR_GRADOS)
            mx = (c.oreja_a[0] + c.oreja_b[0]) / 2
            my = (c.oreja_a[1] + c.oreja_b[1]) / 2
            r = e * 0.55
            raya((mx - r * math.cos(base), my - r * math.sin(base)),
                 (mx + r * math.cos(base), my + r * math.sin(base)))
            # El brazo de ese lado, con la mano que va sobre la cabeza
            lado = objetivo[-3:]
            codo, muneca, _ = c.brazo(lado)
            linea(_hombro(c, lado), codo)
            linea(codo, muneca)
            pygame.draw.circle(capa, (*color, 220), px(muneca), 8)
        elif objetivo == "arriba":
            for hombro, codo, muneca in ((c.hombro_a, c.codo_a, c.muneca_a),
                                         (c.hombro_b, c.codo_b, c.muneca_b)):
                linea(hombro, codo)
                linea(codo, muneca)
                pygame.draw.circle(capa, (*color, 220), px(codo), 7)
            # Los codos tienen que subir por encima de esta raya (la de la nariz)
            raya((c.centro_x - e, c.nariz[1]), (c.centro_x + e, c.nariz[1]))
        elif objetivo in ("triceps_der", "triceps_izq"):
            lado = objetivo[-3:]
            codo, muneca, _ = c.brazo(lado)
            linea(_hombro(c, lado), codo)
            linea(codo, muneca)
            pygame.draw.circle(capa, (*color, 220), px(codo), 8)
            # El codo tiene que subir por encima de esta raya (la de la nariz)
            raya((c.centro_x - e, c.nariz[1]), (c.centro_x + e, c.nariz[1]))
            otro = "izq" if lado == "der" else "der"
            _, sujeta, _ = c.brazo(otro)
            pygame.draw.circle(capa, (*color, 220), px(sujeta), 8)
        elif objetivo in ("cruzado_der", "cruzado_izq"):
            lado = objetivo[-3:]
            hombro = _hombro(c, lado)
            codo, muneca, _ = c.brazo(lado)
            linea(hombro, codo)
            linea(codo, muneca)
            pygame.draw.circle(capa, (*color, 220), px(muneca), 8)
            # La muneca tiene que pasar esta raya, al otro lado del pecho
            signo = -1 if lado == "der" else 1
            x = c.centro_x + signo * S.CRUZAR * e
            y = (c.hombro_a[1] + c.hombro_b[1]) / 2
            raya((x, y - 0.3 * e), (x, y + 0.7 * e))
            # Donde va la otra mano, un aro alrededor del codo
            otro = "izq" if lado == "der" else "der"
            _, sujeta, _ = c.brazo(otro)
            pygame.draw.circle(capa, (*color, 220), px(sujeta), 8)
            cx_, cy_ = px(codo)
            radio = max(14, int(S.SUJETAR * 0.5 * e * img.get_width()))
            for i in range(0, 360, 20):
                a0, a1 = math.radians(i), math.radians(i + 10)
                pygame.draw.line(capa, (*E.CREMA, 170),
                                 (cx_ + radio * math.cos(a0), cy_ + radio * math.sin(a0)),
                                 (cx_ + radio * math.cos(a1), cy_ + radio * math.sin(a1)), 2)
        img.blit(capa, (0, 0))

    # ---- panel ----

    def panel(self, lectura) -> None:
        app, p = self.app, self.app.pantalla
        cx = P.centerx
        e = self.estado
        if e is None:
            return
        paso = e.paso
        n = len(S.POSTURAS)
        if app.modo == "tutorial":
            cab = f"TUTORIAL   {e.indice + 1} DE {e.total}"
        elif paso.postura == 0:
            cab = "PREPARACIÓN" if e.indice == 0 else "FINAL"
        else:
            cab = f"POSTURA {paso.postura} DE {n}"
        Z.cabecera(p, cab)
        if app.modo == "sesion" and paso.postura:
            for i in range(n):
                x = cx + int((i - (n - 1) / 2) * 18)
                hecho, actual = i + 1 < paso.postura, i + 1 == paso.postura
                pygame.draw.circle(p, E.ORO if (hecho or actual) else E.ORO_SUAVE,
                                   (x, P.top + 56), 4 if actual else 3, 0 if hecho or actual else 1)
        Z.instruccion(p, paso)

        if app.pausa_manual:
            Z.botones_pausa(app, P.top + 250)
            return

        centro, radio = Z.CENTRO, Z.RADIO
        if paso.tipo == "mantener":
            color = E.JADE if e.bien else E.TERRACOTA
            D.halo(p, centro, 150, color, 0.3 if e.bien else 0.2)
            D.enso(p, centro, radio, 1, E.ORO_SUAVE, 12, 45)
            D.enso(p, centro, radio, e.hecho, color, 14)
            Z.numero(p, str(math.ceil(e.restante_s)), 80, centro, 12)
            d = E.fuente("texto", 20).render("segundos", True, E.APAGADO)
            p.blit(d, d.get_rect(midtop=(centro[0], centro[1] + 30)))
        elif paso.tipo == "esperar":
            Z.esperando(p, centro, radio, e.hecho, app.t)
        else:
            Z.mensaje(p, centro, app.t)

        # Abajo, lo que falta para estar en la postura
        falta = S.falta(paso.objetivo, e.medida) if paso.objetivo else None
        if not e.medida.cuerpo:
            Z.chip(app, "No te veo", E.APAGADO, suave=True)
        elif paso.tipo == "mantener":
            if e.bien:
                Z.chip(app, "Bien, sigue así", E.JADE)
            else:
                Z.chip(app, falta or "Vuelve a la postura", E.TERRACOTA)
        elif paso.tipo == "esperar" and falta and e.hecho == 0:
            Z.chip(app, falta, E.CREMA, suave=True)
        elif paso.tipo == "mensaje":
            Z.barra_mensaje(p, e.hecho)

    # ================= resultado =================

    def dibujar_resultado(self) -> None:
        p, r = self.app.pantalla, self.resultado
        Z.resultado(self.app, r, "Estiramientos completados",
                    "del tiempo aguantaste en la postura")
        peor = r.get("peor")
        if r["estrellas"] < 3 and peor and peor[1] >= 1:
            Z.linea(p, f"Para mejorar, aguanta más {S.NOMBRES[peor[0]]} "
                       f"({round(peor[1])} s fuera)", "texto", 15, E.APAGADO, P.top + 326)


def _angulo_hombros(c: S.Cuerpo) -> float:
    return S._angulo(c.hombro_a, c.hombro_b)


def _hombro(c: S.Cuerpo, lado: str):
    a_es_der = c.hombro_a[0] > c.hombro_b[0]
    return c.hombro_a if (lado == "der") == a_es_der else c.hombro_b


def _cuerpo(lectura) -> S.Cuerpo | None:
    """Lo que la logica necesita de la lectura de la camara."""
    if (not lectura.cuerpo or not lectura.nariz or not lectura.hombros
            or not lectura.orejas or not lectura.codos or not lectura.munecas):
        return None
    vis = lectura.vis_munecas or (1.0, 1.0)
    return S.Cuerpo(lectura.nariz, *lectura.hombros, *lectura.orejas, *lectura.codos,
                    *lectura.munecas, *vis)
