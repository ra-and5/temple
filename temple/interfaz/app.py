"""La aplicacion de Temple en Pygame. El bucle, las teclas, la pausa y el cambio de pantalla.

Pantallas (self.modo), como el menu de un videojuego, una cosa en cada una
  menu        Ritual de hoy, Practicar una fase, Tu progreso, Ajustes, Salir  (menus.py)
  fases       elegir una fase para practicarla suelta                         (menus.py)
  previa      antes de empezar una fase. Como colocarse, nivel y Empezar     (menus.py)
  progreso    racha, semana y nivel de cada fase                              (menus.py)
  ajustes     sonido, pantalla completa y vueltas de respiracion              (menus.py)
  salir       ¿Salir de Temple?                                               (menus.py)
  tutorial    ensena la fase paso a paso                                      (la fase)
  sesion      la fase completa                                                (la fase)
  resultado   lotos ganados y la frase del nivel                              (la fase)

El Ritual de hoy encadena las cuatro fases en orden. Tras cada resultado se
pasa a la previa de la siguiente, para colocarse antes de empezar.

La camara va siempre a la izquierda, como un espejo, y el panel a la derecha
cambia segun la pantalla. Todo lo propio de cada fase (respirar, meditar) esta
en temple/interfaz/fases/, y aqui solo se le pide a la fase activa lo suyo.
Lo que rodea al panel esta en marco.py, los botones en botones.py y las piezas
del panel que se repiten en piezas.py.

Cada fotograma (paso)
  1. eventos      teclado y raton
  2. actualizar   el dedo pulsa botones y la fase avanza con lo que ve la camara
  3. dibujar      fondo, marco, camara y el panel de la pantalla actual
"""

from __future__ import annotations

import pygame

from temple.camara import CamaraHilo
from temple.interfaz import dibujo as D
from temple.interfaz import estilo as E
from temple.interfaz import marco, menus
from temple.interfaz.botones import Botonera
from temple.interfaz.fases import FASES
from temple.interfaz.opciones import MENSAJE_RAPIDO_S, Opciones
from temple.interfaz.sonido import Sonidos
from temple.interfaz.ventana import Ventana
from temple.progreso import RUTA, Progreso
from temple.puntero import GestoPuno

PAUSA_SIN_CUERPO_S = 1.2  # si no te ve este rato mientras practicas, se pausa sola
PRACTICA = ("tutorial", "sesion")
MENUS = ("menu", "fases", "previa", "progreso", "ajustes", "salir")


class App:
    def __init__(self, opciones: Opciones | None = None, camara=None):
        opciones = opciones or Opciones()
        pygame.mixer.pre_init(44100, -16, 2, 512)
        pygame.init()
        icono = pygame.Surface((64, 64), pygame.SRCALPHA)
        D.loto(icono, (32, 50), 36)
        self.ventana = Ventana("Temple", icono)
        self.pantalla = pygame.Surface((E.ANCHO, E.ALTO))
        self.reloj = pygame.time.Clock()
        self.t = 0.0

        self.progreso = Progreso.cargar(opciones.datos / RUTA.name)
        self.sonido = Sonidos()
        # La camara se puede pasar hecha, para probar la app sin webcam
        self.camara = camara or CamaraHilo(opciones.camara)
        self.camara.start()

        self.fondo = D.crear_fondo()
        self.mascara_cam = D.mascara_redondeada(E.CAMARA.size, E.RADIO)
        self.brasas = D.Brasas()
        self.botonera = Botonera(E.PANEL, self.sonido, self.ventana.raton)

        self.fases = {F.clave: F(self, opciones) for F in FASES}
        self.fase = self.fases[FASES[0].clave]  # la abierta, la que se hace o la ultima
        self.modo = "menu"
        self.ritual = False  # si se esta haciendo el ritual de hoy, fase tras fase
        self.prueba = opciones.prueba  # opciones de prueba, no se sube de nivel
        self.rapido = opciones.rapido
        self.pausa_manual = False
        self.puno = GestoPuno()  # en la pausa, palma abierta y luego puno para seguir
        self.sin_cuerpo_desde: float | None = None
        self.ver_datos = False  # D, numeros de la camara para ajustar umbrales
        self.aviso: tuple[str, float] | None = None
        self.cerrar = False

    # ================= bucle =================

    def ejecutar(self) -> None:
        try:
            while True:
                dt = self.reloj.tick(E.FPS) / 1000
                if not self.paso(dt):
                    break
                self.ventana.mostrar(self.pantalla)
        finally:
            # Si se cierra a mitad de una fase, que su registro quede guardado y cerrado
            self._dejar_practica()
            # Esperar a que el hilo cierre la camara y MediaPipe antes de salir
            self.camara.parar()
            self.camara.join(timeout=3)
            pygame.quit()

    def paso(self, dt: float) -> bool:
        """Un fotograma. Devuelve False si hay que salir."""
        self.t += dt
        if not self._eventos() or self.cerrar:
            return False
        frame, lectura = self.camara.ultimo()
        self._actualizar(dt, lectura)
        self._dibujar(dt, frame, lectura)
        return True

    # ================= cambiar de pantalla =================

    def faltan_hoy(self) -> list[str]:
        """Las fases del ritual que aun no has hecho hoy, en orden."""
        return [c for c in self.fases if not self.progreso.hecha_hoy(c)]

    def ir(self, modo: str) -> None:
        self.modo = modo

    def ir_menu(self) -> None:
        self._dejar_practica()
        self.ritual = False
        self.modo = "menu"

    def practicar(self) -> None:
        """Practicar una fase suelta, fuera del ritual."""
        self.ritual = False
        self.modo = "fases"

    def empezar_ritual(self) -> None:
        """Desde la primera fase que falta hoy. Si ya esta todo, otra vez desde el principio."""
        self.ritual = True
        faltan = self.faltan_hoy()
        self.abrir_fase(faltan[0] if faltan else next(iter(self.fases)))

    def empezar_ritual_en(self, clave: str) -> None:
        """El ritual desde la fase elegida en la fila del menu."""
        self.ritual = True
        self.abrir_fase(clave)

    def abrir_fase(self, clave: str) -> None:
        """La previa de una fase. Como colocarse, el nivel y Empezar."""
        self._dejar_practica()
        self.fase = self.fases[clave]
        self.modo = "previa"

    def cambiar_nivel(self, paso: int) -> None:
        if self.fase.con_niveles:
            self.progreso.elegir_nivel(self.fase.clave, paso)

    def accion_principal(self) -> None:
        """Empezar en la previa. El tutorial la primera vez y despues la sesion."""
        self.empezar("sesion" if self.progreso.tutorial_hecho(self.fase.clave) else "tutorial")

    def empezar(self, modo: str) -> None:
        self.modo = modo
        self.fase.nivel = self.progreso.nivel_elegido(self.fase.clave)
        self.fase.prueba = self.prueba
        self.camara.cara = self.fase.usa_cara  # el modelo de cara solo trabaja si hace falta
        self.fase.empezar(modo)
        if self.rapido:
            self.fase.acortar_mensajes(MENSAJE_RAPIDO_S)
        self.pausa_manual = False
        self.sin_cuerpo_desde = None
        self.sonido("cuenco")

    def fin_tutorial(self, texto: str) -> None:
        """Al acabar un tutorial se vuelve a la previa, lista para la sesion."""
        self.camara.cara = False
        self.modo = "previa"
        self.avisar(texto, 5)

    def volver_previa(self) -> None:
        """Salir a mitad de una fase (Esc o Salir en la pausa)."""
        self._dejar_practica()
        self.modo = "previa"

    def _dejar_practica(self) -> None:
        if self.modo in PRACTICA or self.modo == "resultado":
            self.fase.salir()
        self.fase.palma.actualizar(0, None)  # que no quede el aro de pausa a medias
        self.puno.reiniciar()
        self.camara.cara = False
        self.pausa_manual = False
        self.sin_cuerpo_desde = None

    def siguiente_del_ritual(self):
        """La fase que va despues de la actual en el ritual, o None."""
        if not self.ritual:
            return None
        claves = list(self.fases)
        i = claves.index(self.fase.clave) + 1
        return self.fases[claves[i]] if i < len(claves) else None

    def tras_resultado(self) -> None:
        """El boton principal del resultado."""
        siguiente = self.siguiente_del_ritual()
        if siguiente is not None:
            self.abrir_fase(siguiente.clave)
        elif self.ritual:
            self.ir_menu()
        else:
            self.abrir_fase(self.fase.clave)

    def atras(self) -> None:
        """Esc en los menus. Cada pantalla vuelve a la de antes."""
        if self.modo == "previa":
            self.modo = "menu" if self.ritual else "fases"
            self.ritual = False
        elif self.modo == "menu":
            self.modo = "salir"
        else:
            self.modo = "menu"

    def pedir_salir(self) -> None:
        self.modo = "salir"

    def salir(self) -> None:
        self.cerrar = True

    # ================= pausa y avisos =================

    def seguir(self) -> None:
        self.pausa_manual = False
        self.puno.reiniciar()

    def vigilar(self, ausente: bool) -> None:
        """La fase dice si no te ve cuando deberia. Si dura, se pausa sola."""
        if ausente:
            if self.sin_cuerpo_desde is None:
                self.sin_cuerpo_desde = self.t
        else:
            self.sin_cuerpo_desde = None

    def pausado(self) -> bool:
        return self.pausa_manual or (
            self.sin_cuerpo_desde is not None
            and self.t - self.sin_cuerpo_desde > PAUSA_SIN_CUERPO_S)

    def menu_activo(self) -> bool:
        """Pantallas donde el dedo mueve el cursor. Mientras se practica, solo en la pausa."""
        return self.modo in MENUS or self.modo == "resultado" or self.pausa_manual

    def avisar(self, texto: str, segundos: float = 3.5) -> None:
        self.aviso = (texto, self.t + segundos)

    def alternar_sonido(self) -> None:
        self.avisar("Sonido activado" if self.sonido.alternar() else "Sonido apagado")

    # ================= eventos =================

    def _eventos(self) -> bool:
        for ev in pygame.event.get():
            if ev.type == pygame.QUIT:
                return False
            if ev.type == pygame.MOUSEMOTION:
                self.botonera.mover_raton()
            if ev.type == pygame.MOUSEBUTTONDOWN and ev.button == 1:
                self.botonera.clic(self.ventana.a_juego(ev.pos))
            if ev.type == pygame.KEYDOWN and not self._tecla(ev):
                return False
        return True

    def _tecla(self, ev) -> bool:
        """Una tecla. Devuelve False si hay que salir."""
        k = ev.key
        if self.modo == "salir" and k in (pygame.K_RETURN, pygame.K_KP_ENTER):
            return False
        if self.botonera.tecla(ev, self.modo in ("previa", "ajustes")):
            return True
        if k in (pygame.K_f, pygame.K_F11):
            self.ventana.alternar_pantalla_completa()
        elif k == pygame.K_m:
            self.alternar_sonido()
        elif k == pygame.K_d:
            self.ver_datos = not self.ver_datos
        elif self.modo in MENUS:
            self._tecla_menu(k)
        elif self.modo in PRACTICA:
            if k == pygame.K_ESCAPE:
                self.volver_previa()
            elif k in (pygame.K_p, pygame.K_SPACE):
                if self.pausa_manual:
                    self.seguir()
                else:
                    self.pausa_manual = True
            else:
                self.fase.tecla_practica(k)
        elif self.modo == "resultado":
            if k in (pygame.K_SPACE, pygame.K_RETURN):
                self.tras_resultado()
            elif k == pygame.K_ESCAPE:
                self.ir_menu()
        return True

    def _tecla_menu(self, k) -> None:
        """Teclas de los menus. Las flechas y Enter sobre los botones van en la botonera."""
        aceptar = k in (pygame.K_SPACE, pygame.K_RETURN, pygame.K_KP_ENTER)
        if k == pygame.K_ESCAPE:
            self.atras()
        elif self.modo == "previa":
            if aceptar:
                self.accion_principal()
            elif k == pygame.K_t:
                self.empezar("tutorial")
            elif k == pygame.K_s:
                self.empezar("sesion")
            elif k in (pygame.K_LEFT, pygame.K_MINUS, pygame.K_KP_MINUS):
                self.cambiar_nivel(-1)
            elif k in (pygame.K_RIGHT, pygame.K_PLUS, pygame.K_KP_PLUS, pygame.K_EQUALS):
                self.cambiar_nivel(1)
        elif self.modo == "ajustes":
            if k in (pygame.K_LEFT, pygame.K_MINUS, pygame.K_KP_MINUS):
                self.cambiar_vueltas(-1)
            elif k in (pygame.K_RIGHT, pygame.K_PLUS, pygame.K_KP_PLUS, pygame.K_EQUALS):
                self.cambiar_vueltas(1)
            elif aceptar:
                self.atras()
        elif self.modo == "menu" and aceptar:
            self.empezar_ritual()
        elif self.modo in ("progreso",) and aceptar:
            self.atras()
        elif self.modo in ("menu", "fases"):
            for fase in self.fases.values():
                if k == fase.tecla:
                    self.ritual = False
                    self.abrir_fase(fase.clave)

    def cambiar_vueltas(self, paso: int) -> None:
        self.fases["respiracion"].cambiar_vueltas(paso)

    # ================= actualizar y dibujar =================

    def _actualizar(self, dt, lectura) -> None:
        # En la pausa, abrir la palma y cerrar el puno sigue
        if self.pausa_manual and self.modo in PRACTICA:
            if self.puno.actualizar(dt, lectura.mano, lectura.aspecto):
                self.sonido("toque")
                self.seguir()
                return
        else:
            self.puno.reiniciar()
        # El dedo usa los botones del ultimo fotograma dibujado
        if self.menu_activo():
            boton = self.botonera.actualizar_dedo(dt, lectura)
            if boton is not None:
                self.sonido("toque")
                boton.accion()
                return
        else:
            self.botonera.ocultar_dedo()
        self.fase.actualizar(dt, lectura)

    def _dibujar(self, dt, frame, lectura) -> None:
        pantalla = (self.modo, self.pausa_manual, self.fase.clave)
        self.botonera.empezar_fotograma(pantalla, self.menu_activo())
        self.pantalla.blit(self.fondo, (0, 0))
        self.brasas.dibujar(self.pantalla, dt, self.t)
        marco.barra_superior(self)
        marco.camara(self, frame, lectura)
        D.tarjeta(self.pantalla, E.PANEL)
        if self.modo in MENUS:
            menus.dibujar(self)
        elif self.modo in PRACTICA:
            self.fase.panel(lectura)
        else:
            self.fase.panel_resultado()
        marco.pie(self)
        marco.aviso(self)
        marco.gestos(self, lectura)
        self.botonera.terminar_fotograma()
