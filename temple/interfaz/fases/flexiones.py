import math

import pygame

from temple import flexiones as F
from temple.interfaz import dibujo as D
from temple.interfaz import estilo as E
from temple.interfaz import marco
from temple.interfaz import piezas as Z
from temple.interfaz.fases.base import Fase
from temple.puntero import PALMA_S

P = E.PANEL

NOMBRES = {"facil": "Fácil", "tecnico": "Técnico"}
NOTAS = {"facil": "cuenta casi todo", "tecnico": "hasta el suelo y con el cuerpo recto"}

CONSEJOS = {
    "poco profunda": "Para mejorar, baja hasta el suelo",
    "cadera": "Para mejorar, mantén la cadera recta",
}


class Flexiones(Fase):
    clave = "flexiones"
    nombre = "Flexiones"
    tecla = pygame.K_x
    motivo_pausa = "Señala Seguir con el índice y espera"
    ayuda = ("Levántate o sal de la cámara para pausar",
             "Espacio pausar  ·  D datos de la cámara  ·  M sonido  ·  Esc volver al inicio")

    def __init__(self, app, opciones):
        super().__init__(app, PALMA_S)
        self.practica = None
        self.estado = None
        self.registro = None
        self.reloj = 0.0
        self.ultimo = ""
        self.nivel = "facil"
        self.ruta_registro = opciones.datos / F.REGISTRO.name

    def cambiar(self, paso):
        if self.nivel == "facil":
            self.nivel = "tecnico"
        else:
            self.nivel = "facil"

    def resumen(self):
        mejor = self.app.progreso.mejor(self.clave, self.nivel)
        if mejor is None:
            return "Todavía sin sesiones"
        return f"Tu mejor marca, {math.floor(mejor * 100)} % de flexiones buenas"

    def panel_inicio(self):
        app = self.app
        p = app.pantalla
        primera = not app.progreso.tutorial_hecho(self.clave)
        Z.botones_empezar(app, primera, "Aprender flexiones", "Empezar flexiones")
        Z.linea(p, self.resumen() if not primera else
                f"{F.REPETICIONES} flexiones en el suelo. Gana hasta 3 lotos",
                "texto", 15, E.APAGADO, P.top + 248)
        Z.linea(p, "Portátil en el suelo, de lado, a unos 2 metros", "texto", 15, E.CREMA,
                P.top + 280)
        Z.fila_mas_menos(app, f"Nivel {NOMBRES[self.nivel]}", NOTAS[self.nivel], self.cambiar,
                         "nivel")

    def empezar(self, modo, variante):
        if modo == "tutorial":
            pasos = F.guion_tutorial()
        else:
            pasos = F.guion_sesion()
        self.practica = F.Practica(pasos, self.nivel)
        self.cerrar_registro()
        self.registro = F.Registro(self.ruta_registro)
        self.estado = None
        self.reloj = 0.0
        self.ultimo = ""

    def cerrar_registro(self):
        if self.registro is not None:
            self.registro.cerrar()
            self.registro = None

    def salir(self):
        self.cerrar_registro()
        self.estado = None

    def actualizar(self, dt, lectura):
        app = self.app
        if app.modo not in ("tutorial", "sesion"):
            return
        contando = self.estado is not None and self.estado.paso.tipo == "contar"
        app.vigilar(not lectura.cuerpo and contando)
        self.palma.actualizar(0, None)
        if app.pausado():
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
        app = self.app
        app.sonido("cuenco")
        self.cerrar_registro()
        if app.modo == "tutorial":
            app.progreso.marcar_tutorial(self.clave)
            app.modo = "inicio"
            app.elegir_fase(self.clave)
            self.estado = None
            app.avisar("Ya sabes hacer flexiones. Ahora, la sesión completa", 5)
            return
        precision = self.practica.precision()
        n = F.lotos(precision)
        mejor_antes = app.progreso.mejor(self.clave, self.nivel)
        app.progreso.registrar(self.clave, self.nivel, precision, n)
        self.resultado = {
            "precision": precision,
            "estrellas": n,
            "record": mejor_antes is not None and precision > mejor_antes,
            "peor": self.practica.peor(),
        }
        app.modo = "resultado"
        self.estado = None

    def lineas_datos(self):
        if self.estado is None:
            return []
        m = self.estado.medida
        u = F.NIVELES[self.nivel]
        return [f"nivel {NOMBRES[self.nivel]}",
                f"codo {m.codo:.0f}  (abajo <= {u['abajo']}, arriba >= {u['arriba']})",
                f"profundidad {m.profundidad:.2f}  (suelo <= {u['profundo']})",
                f"cadera {m.cadera:.2f}  (recta entre -{u['cadera']} y {u['cadera']})"]

    def pistas(self, img, lectura):
        c = cuerpo_de(lectura)
        if c is None or self.estado is None:
            return
        if c.vis_brazos[0] >= c.vis_brazos[1]:
            lado = 0
        else:
            lado = 1
        m = self.estado.medida
        if abs(m.cadera) <= F.NIVELES[self.nivel]["cadera"]:
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

        centro = (P.centerx, P.top + 310)
        radio = 88
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
            falta = F.falta(paso.objetivo, e.medida, self.nivel)
            if falta and e.hecho == 0:
                Z.chip(app, falta, E.CREMA, suave=True)
        else:
            Z.barra_mensaje(p, e.hecho)

    def panel_resultado(self):
        app = self.app
        p = app.pantalla
        r = self.resultado
        Z.resultado(app, r, "Flexiones completadas", "de las flexiones fueron buenas")
        if r["estrellas"] < 3 and r["peor"]:
            Z.linea(p, CONSEJOS[r["peor"]], "texto", 15, E.APAGADO, P.top + 326)

        faltan = [f.nombre.lower() for f in app.fases.values()
                  if not app.progreso.hecha_hoy(f.clave)]
        if not faltan:
            texto, color = "Ritual de hoy completo", E.ORO
        else:
            texto, color = f"Hoy aún te queda {' y '.join(faltan)}", E.APAGADO
        Z.linea(p, texto, "negrita", 16, color, P.top + 384)
        Z.boton_volver(app)


def cuerpo_de(lectura):
    if (not lectura.cuerpo or not lectura.hombros or not lectura.codos or not lectura.munecas
            or not lectura.caderas or not lectura.tobillos):
        return None
    vis = lectura.vis_brazos or (1.0, 1.0)
    return F.Cuerpo(lectura.hombros, lectura.codos, lectura.munecas, lectura.caderas,
                    lectura.tobillos, vis)
