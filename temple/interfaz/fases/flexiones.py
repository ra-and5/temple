"""La fase de flexiones en la interfaz. Panel, silueta de perfil y resultado."""

import pygame

from temple import flexiones as F
from temple.interfaz import dibujo as D
from temple.interfaz import estilo as E
from temple.interfaz import marco
from temple.interfaz import piezas as Z
from temple.interfaz.fases.base import Fase
from temple.progreso import NIVELES
from temple.puntero import PALMA_S

P = E.PANEL

NOMBRES = {"facil": "Fácil", "tecnico": "Técnico"}

CONSEJOS = {
    "poco profunda": "Para mejorar, baja hasta el suelo",
    "cadera": "Para mejorar, mantén la cadera recta",
}


class Flexiones(Fase):
    """La fase de flexiones. En el suelo, de lado a la cámara."""
    clave = "flexiones"
    nombre = "Flexiones"
    verbo = "Empezar"
    tecla = pygame.K_x
    colocacion = "Portátil en el suelo, a 2 m. Ponte de perfil, que te vea de la cabeza a los pies"
    ayuda = "Palma abierta y quieta, o sal de la cámara, para pausar"

    def __init__(self, app, opciones):
        super().__init__(app, PALMA_S)
        self.practica = None
        self.estado = None
        self.registro = None
        self.reloj = 0.0
        self.ultimo = ""
        self.ruta_registro = opciones.datos / F.REGISTRO.name
        self.flexiones_fijas = opciones.flexiones  # --flexiones para probar

    @property
    def variante(self):
        """Fácil o técnico, según el nivel."""
        return NIVELES[self.clave][self.nivel][0]

    def nombre_nivel(self, n):
        """Cómo se llama ese nivel en el menú."""
        tipo, repeticiones = NIVELES[self.clave][n]
        return f"{NOMBRES[tipo]}, {repeticiones} flexiones"

    def guia(self, img):
        """Una silueta de perfil en plancha, para ver como ponerse."""
        w, h = img.get_size()
        capa = pygame.Surface((w, h), pygame.SRCALPHA)
        col = (*E.ORO, 200)
        suelo = int(h * 0.86)
        cabeza = (int(w * 0.265), int(h * 0.605))
        hombro = (int(w * 0.30), int(h * 0.64))
        cadera = (int(w * 0.56), int(h * 0.72))
        tobillo = (int(w * 0.80), int(h * 0.80))
        mano = (int(w * 0.30), suelo)
        pygame.draw.line(capa, (*E.ORO_SUAVE, 120), (int(w * 0.08), suelo),
                         (int(w * 0.92), suelo), 2)
        pygame.draw.circle(capa, col, cabeza, int(h * 0.04), 4)
        for a, b in ((hombro, cadera), (cadera, tobillo), (hombro, mano)):
            pygame.draw.line(capa, col, a, b, 6)
        pygame.draw.line(capa, col, tobillo, (tobillo[0] + 6, suelo), 6)
        D.texto(capa, E.fuente("negrita", 24), "Ponte así, de perfil", E.CREMA, w // 2,
                int(h * 0.12))
        D.texto(capa, E.fuente("texto", 18), "con el portátil en el suelo, a unos 2 metros",
                E.APAGADO, w // 2, int(h * 0.12) + 34)
        img.blit(capa, (0, 0))

    def empezar(self, modo):
        """Prepara el guion y el registro con las flexiones del nivel."""
        tipo, repeticiones = NIVELES[self.clave][self.nivel]
        if modo == "tutorial":
            pasos = F.guion_tutorial()
        else:
            pasos = F.guion_sesion(self.flexiones_fijas or repeticiones)
        self.practica = F.Practica(pasos, tipo)
        self.cerrar_registro()
        self.registro = F.Registro(self.ruta_registro)
        self.estado = None
        self.reloj = 0.0
        self.ultimo = ""

    def cerrar_registro(self):
        """Cierra el CSV si estaba abierto."""
        if self.registro is not None:
            self.registro.cerrar()
            self.registro = None

    def salir(self):
        """Al dejar la fase, cierra el registro."""
        self.cerrar_registro()
        self.estado = None

    def actualizar(self, dt, lectura):
        """Cada fotograma. Mira la pausa, avanza el guion y suena al contar."""
        app = self.app
        if app.modo not in ("tutorial", "sesion"):
            return
        contando = self.estado is not None and self.estado.paso.tipo == "contar"
        app.vigilar(not lectura.cuerpo and contando)
        if app.pausado():
            self.palma.actualizar(0, None)
            return
        if self.pausa_con_palma(dt, lectura):
            return

        self.reloj += dt
        antes = self.estado
        e = self.practica.actualizar(self.reloj, cuerpo_de(lectura))
        self.estado = e
        if self.registro is not None:
            self.registro.apuntar(self.reloj, e)
        if e.terminado:
            self.terminar()
            return
        if antes is not None and e.indice != antes.indice and antes.paso.tipo != "mensaje":
            app.sonido("toque")
        if e.flexion:
            if e.fallo:
                self.ultimo = e.fallo
                app.sonido("aviso")
            else:
                self.ultimo = "bien"
                app.sonido("tic")

    def terminar(self):
        """Al acabar, guarda la sesión o marca el tutorial como visto."""
        app = self.app
        app.sonido("cuenco")
        self.cerrar_registro()
        self.estado = None
        if app.modo == "tutorial":
            app.progreso.marcar_tutorial(self.clave)
            app.fin_tutorial("Ya sabes hacer flexiones. Ahora, la sesión completa")
            return
        precision = self.practica.precision()
        self.guardar(precision, F.lotos(precision))
        self.resultado["peor"] = self.practica.peor()
        app.modo = "resultado"

    def lineas_datos(self):
        """Los números que se ven con la tecla D."""
        if self.estado is None:
            return []
        m = self.estado.medida
        u = F.NIVELES[self.variante]
        return [f"nivel {NOMBRES[self.variante]}",
                f"codo {m.codo:.0f}  (abajo <= {u['abajo']}, arriba >= {u['arriba']})",
                f"profundidad {m.profundidad:.2f}  (suelo <= {u['profundo']})",
                f"cadera {m.cadera:.2f}  (recta entre -{u['cadera']} y {u['cadera']})"]

    def pistas(self, img, lectura):
        """Las líneas del brazo y del cuerpo sobre la cámara, en verde si van bien."""
        c = cuerpo_de(lectura)
        if c is None or self.estado is None:
            return
        if c.vis_brazos[0] >= c.vis_brazos[1]:
            lado = 0
        else:
            lado = 1
        m = self.estado.medida
        if abs(m.cadera) <= F.NIVELES[self.variante]["cadera"]:
            color = E.JADE
        else:
            color = E.ORO
        capa = pygame.Surface(img.get_size(), pygame.SRCALPHA)
        r, g, b = color
        hombro = marco.px(img, c.hombros[lado])
        codo = marco.px(img, c.codos[lado])
        muneca = marco.px(img, c.munecas[lado])
        cadera = marco.px(img, c.caderas[lado])
        tobillo = marco.px(img, c.tobillos[lado])
        pygame.draw.line(capa, (r, g, b, 200), muneca, codo, 3)
        pygame.draw.line(capa, (r, g, b, 200), codo, hombro, 3)
        pygame.draw.line(capa, (r, g, b, 200), hombro, cadera, 3)
        pygame.draw.line(capa, (r, g, b, 200), cadera, tobillo, 3)
        for punto in (muneca, codo, hombro, cadera, tobillo):
            pygame.draw.circle(capa, (r, g, b, 220), punto, 7)
        img.blit(capa, (0, 0))

    def panel(self, lectura):
        """El panel con la cuenta de flexiones y lo que falta."""
        app = self.app
        p = app.pantalla
        e = self.estado
        if e is None:
            return
        paso = e.paso
        if app.modo == "tutorial":
            Z.cabecera(p, f"TUTORIAL   {e.indice + 1} DE {e.total}")
        else:
            Z.cabecera(p, "FLEXIONES")
        Z.instruccion(p, paso)

        if app.pausa_manual:
            Z.botones_pausa(app, P.top + 250)
            return

        centro, radio = Z.CENTRO, Z.RADIO
        if paso.tipo == "contar":
            D.enso(p, centro, radio, 1, E.ORO_SUAVE, 12, 45)
            D.enso(p, centro, radio, e.hecho, E.JADE, 14)
            hechas = round(e.hecho * paso.repeticiones)
            Z.numero(p, str(hechas), 80, centro, 12)
            d = E.fuente("texto", 20).render(f"de {paso.repeticiones}", True, E.APAGADO)
            p.blit(d, d.get_rect(midtop=(centro[0], centro[1] + 30)))
        elif paso.tipo == "esperar":
            Z.esperando(p, centro, radio, e.hecho, app.t)
        else:
            Z.mensaje(p, centro, app.t)

        if not e.medida.cuerpo:
            Z.chip(app, "No te veo entero", E.APAGADO, suave=True)
        elif paso.tipo == "contar":
            if self.ultimo == "bien":
                Z.chip(app, "Bien", E.JADE)
            elif self.ultimo == "poco profunda":
                Z.chip(app, "Baja más", E.TERRACOTA)
            elif self.ultimo == "cadera":
                Z.chip(app, "Cadera recta", E.TERRACOTA)
        elif paso.tipo == "esperar":
            falta = F.falta(paso.objetivo, e.medida, self.variante)
            if falta and e.hecho == 0:
                Z.chip(app, falta, E.CREMA, suave=True)
        else:
            Z.barra_mensaje(p, e.hecho)

    def dibujar_resultado(self):
        """El resultado, con un consejo para el fallo que más se repitió."""
        app = self.app
        r = self.resultado
        Z.resultado(app, r, "Flexiones completadas", "de las flexiones fueron buenas")
        if r["estrellas"] < 3 and r["peor"]:
            Z.linea(app.pantalla, CONSEJOS[r["peor"]], "texto", 15, E.APAGADO, P.top + 326)


def cuerpo_de(lectura):
    """Saca de la lectura de la cámara los puntos que hacen falta, o None si falta alguno."""
    if (not lectura.cuerpo or not lectura.hombros or not lectura.codos or not lectura.munecas
            or not lectura.caderas or not lectura.tobillos):
        return None
    vis = lectura.vis_brazos or (1.0, 1.0)
    return F.Cuerpo(lectura.hombros, lectura.codos, lectura.munecas, lectura.caderas,
                    lectura.tobillos, vis)
