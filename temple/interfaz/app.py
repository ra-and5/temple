"""La aplicacion de Temple en Pygame. El bucle, las teclas, la pausa y el cambio de pantalla.

Pantallas (self.modo)
  inicio      la practica de hoy, con la fase elegida y la semana   (inicio.py)
  tutorial    ensena la fase paso a paso                            (la fase)
  sesion      la fase completa                                      (la fase)
  resultado   lotos ganados y lo que falta para el siguiente nivel  (la fase)

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
from temple.interfaz import inicio, marco
from temple.interfaz.botones import Botonera
from temple.interfaz.fases import FASES
from temple.interfaz.opciones import Opciones
from temple.interfaz.sonido import Sonidos
from temple.progreso import RUTA, Progreso

PAUSA_SIN_CUERPO_S = 1.2  # si no te ve este rato mientras practicas, se pausa sola
PRACTICA = ("tutorial", "sesion")


class App:
    def __init__(self, opciones: Opciones | None = None, camara=None):
        opciones = opciones or Opciones()
        pygame.mixer.pre_init(44100, -16, 2, 512)
        pygame.init()
        pygame.display.set_caption("Temple")
        icono = pygame.Surface((64, 64), pygame.SRCALPHA)
        D.loto(icono, (32, 50), 36)
        pygame.display.set_icon(icono)
        self.pantalla = pygame.display.set_mode((E.ANCHO, E.ALTO), pygame.SCALED)
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
        self.botonera = Botonera(E.PANEL, self.sonido)

        self.fases = {F.clave: F(self, opciones) for F in FASES}
        self.fase = self.fases[FASES[0].clave]  # la que se hace o la ultima que se hizo
        self.elegida = self._fase_sugerida()  # la marcada en el inicio
        self.modo = "inicio"
        self.pausa_manual = False
        self.sin_cuerpo_desde: float | None = None
        self.ver_datos = False  # D, numeros de la camara para ajustar umbrales
        self.aviso: tuple[str, float] | None = None

    # ================= bucle =================

    def ejecutar(self) -> None:
        try:
            while True:
                dt = self.reloj.tick(E.FPS) / 1000
                if not self.paso(dt):
                    break
                pygame.display.flip()
        finally:
            # Esperar a que el hilo cierre la camara y MediaPipe antes de salir
            self.camara.parar()
            self.camara.join(timeout=3)
            pygame.quit()

    def paso(self, dt: float) -> bool:
        """Un fotograma. Devuelve False si hay que salir."""
        self.t += dt
        if not self._eventos():
            return False
        frame, lectura = self.camara.ultimo()
        self._actualizar(dt, lectura)
        self._dibujar(dt, frame, lectura)
        return True

    # ================= cambiar de pantalla =================

    def _fase_sugerida(self) -> str:
        """La primera fase que falta hoy, para que el inicio ya la tenga elegida."""
        for clave in self.fases:
            if not self.progreso.hecha_hoy(clave):
                return clave
        return next(iter(self.fases))

    def elegir_fase(self, clave: str) -> None:
        self.elegida = clave

    def accion_principal(self) -> None:
        """Espacio en el inicio. El tutorial la primera vez y despues la sesion."""
        self.empezar("sesion" if self.progreso.tutorial_hecho(self.elegida) else "tutorial")

    def empezar(self, modo: str, variante: str = "principiante") -> None:
        self.modo = modo
        self.fase = self.fases[self.elegida]
        self.camara.cara = self.fase.usa_cara  # el modelo de cara solo trabaja si hace falta
        self.fase.empezar(modo, variante)
        self.pausa_manual = False
        self.sin_cuerpo_desde = None
        self.sonido("cuenco")

    def volver_inicio(self) -> None:
        self.modo = "inicio"
        self.camara.cara = False
        self.fase.salir()
        self.elegida = self._fase_sugerida()
        self.pausa_manual = False

    # ================= pausa y avisos =================

    def seguir(self) -> None:
        self.pausa_manual = False

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
        return self.modo in ("inicio", "resultado") or self.pausa_manual

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
                self.botonera.clic(ev.pos)
            if ev.type == pygame.KEYDOWN and not self._tecla(ev):
                return False
        return True

    def _tecla(self, ev) -> bool:
        """Una tecla. Devuelve False si hay que salir."""
        k = ev.key
        if self.botonera.tecla(ev, self.modo == "inicio"):
            return True
        if k == pygame.K_F11:
            pygame.display.toggle_fullscreen()
        elif k == pygame.K_m:
            self.alternar_sonido()
        elif k == pygame.K_d:
            self.ver_datos = not self.ver_datos
        elif self.modo == "inicio":
            return self._tecla_inicio(k)
        elif self.modo in PRACTICA:
            if k == pygame.K_ESCAPE:
                self.volver_inicio()
            elif k in (pygame.K_p, pygame.K_SPACE):
                self.pausa_manual = not self.pausa_manual
            else:
                self.fase.tecla_practica(k)
        elif self.modo == "resultado":
            if k in (pygame.K_SPACE, pygame.K_RETURN):
                self.fase.accion_resultado()
            elif k == pygame.K_ESCAPE:
                self.volver_inicio()
        return True

    def _tecla_inicio(self, k) -> bool:
        elegida = self.fases[self.elegida]
        if k == pygame.K_ESCAPE:
            return False
        if k in (pygame.K_SPACE, pygame.K_RETURN):
            self.accion_principal()
        elif k == pygame.K_t:
            self.empezar("tutorial")
        elif k == pygame.K_s:
            self.empezar("sesion")
        elif k in (pygame.K_LEFT, pygame.K_MINUS, pygame.K_KP_MINUS):
            elegida.cambiar(-1)
        elif k in (pygame.K_RIGHT, pygame.K_PLUS, pygame.K_KP_PLUS, pygame.K_EQUALS):
            elegida.cambiar(1)
        elif not elegida.tecla_inicio(k):
            for fase in self.fases.values():
                if k == fase.tecla:
                    self.elegir_fase(fase.clave)
        return True

    # ================= actualizar y dibujar =================

    def _actualizar(self, dt, lectura) -> None:
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
        self.botonera.empezar_fotograma((self.modo, self.pausa_manual), self.menu_activo())
        self.pantalla.blit(self.fondo, (0, 0))
        self.brasas.dibujar(self.pantalla, dt, self.t)
        marco.barra_superior(self)
        marco.camara(self, frame, lectura)
        D.tarjeta(self.pantalla, E.PANEL)
        if self.modo == "inicio":
            inicio.dibujar(self)
        elif self.modo in PRACTICA:
            self.fase.panel(lectura)
        else:
            self.fase.panel_resultado()
        marco.pie(self)
        marco.aviso(self)
        marco.gestos(self, lectura)
        self.botonera.terminar_fotograma()
