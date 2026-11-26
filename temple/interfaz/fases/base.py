"""Lo que tiene que saber hacer cada fase del ritual para que la app la muestre.

La app no sabe nada de respirar ni de meditar. Lleva el bucle, las teclas, la
pausa y el cambio de pantalla, y le pide a la fase activa lo propio de ella
(como colocarse, su panel, lo que dibuja sobre la camara y su resultado).
Para anadir una fase nueva se escribe una clase hija de Fase en esta carpeta,
se apunta en FASES (temple/interfaz/fases/__init__.py) y se ponen sus niveles
en temple/progreso.py (NIVELES). La logica de la fase (que comprueba la camara,
cuando pasa de paso) va aparte, en temple/, sin Pygame y con tests.

Lo comun a todas esta aqui. El nivel que se juega (self.nivel, lo pone la app
al empezar), guardar la sesion con la regla unica de subir de nivel y el
final del resultado (la frase del nivel y los botones de seguir).

Lo que la fase puede usar de la app
  app.pantalla, app.botonera, app.progreso, app.sonido, app.camara y app.t
  app.empezar, app.fin_tutorial, app.seguir, app.avisar
  app.pausa_manual, app.pausado() y app.vigilar(ausente)
"""

from __future__ import annotations

from dataclasses import replace

from temple.interfaz import estilo as E
from temple.interfaz import piezas as Z
from temple.progreso import DIAS_PARA_SUBIR, LOTOS_PARA_SUBIR, NIVELES, VUELTAS_NIVEL
from temple.puntero import GestoPalma


class Fase:
    clave = ""  # como se guarda en el progreso
    nombre = ""  # como sale en los menus
    tecla = None  # tecla que la abre desde el menu
    con_niveles = True  # False en el calentamiento, que no sube de nivel
    sin_niveles = ""  # lo que se dice en su lugar (para que sirve la fase)
    verbo = ""  # el boton de empezar (Respirar, Meditar…)
    colocacion = ""  # como ponerse delante de la camara, antes de empezar
    usa_cara = False  # si necesita el modelo de cara (gasta unos 13 ms por fotograma)
    motivo_pausa = "Abre la palma y ciérrala en un puño para seguir"  # en la camara, en la pausa
    ayuda: str | None = None  # como pausar con el cuerpo, si no vale la palma

    def __init__(self, app, palma_s: float):
        # Cada fase hija recibe (app, opciones) y llama a esto con su tiempo de palma
        self.app = app
        self.palma = GestoPalma(palma_s)  # palma abierta para pausar
        self.resultado: dict = {}
        self.nivel = 0  # el que se juega, lo pone la app al empezar
        self.prueba = False  # con opciones de prueba (--minutos…) no se sube de nivel

    # ---- pausa con la palma ----

    def pausa_con_palma(self, dt: float, lectura, techo=None) -> bool:
        """Palma abierta, de frente y quieta, pausa. Vale en todas las fases y en
        cualquier paso. True si acaba de pausar (y el fotograma no sigue)."""
        if self.palma.actualizar(dt, lectura.mano, lectura.nariz, lectura.escala, techo,
                                lectura.aspecto):
            self.app.pausa_manual = True
            self.app.sonido("toque")
            return True
        return False

    # ---- modo rapido ----

    def pasos(self) -> list:
        """Los pasos de la practica en curso."""
        return self.practica.pasos

    def acortar_mensajes(self, maximo_s: float) -> None:
        """Con --rapido, los textos de paso no hacen esperar mas de maximo_s."""
        lista = self.pasos()
        for i, paso in enumerate(lista):
            if paso.tipo == "mensaje" and paso.duracion > maximo_s:
                lista[i] = replace(paso, duracion=maximo_s)

    # ---- niveles ----

    def nombre_nivel(self, n: int) -> str:
        """Lo que cambia en ese nivel, corto (8 min, Avanzada, 30 s por postura…)."""
        return str(NIVELES[self.clave][n])

    @property
    def variante(self) -> str:
        """Como se guarda para la mejor marca."""
        return "normal"

    # ---- antes de empezar ----

    def guia(self, img) -> None:
        """Lo que se dibuja sobre la camara antes de empezar, para colocarse."""

    # ---- practica (tutorial o sesion) ----

    def empezar(self, modo: str) -> None:
        raise NotImplementedError

    def actualizar(self, dt: float, lectura) -> None:
        """Cada fotograma. Avanza el guion con lo que ve la camara."""
        raise NotImplementedError

    def pistas(self, img, lectura) -> None:
        """Lo que se dibuja encima de la camara mientras se practica."""

    def panel(self, lectura) -> None:
        raise NotImplementedError

    def tecla_practica(self, k) -> bool:
        return False

    def lineas_datos(self) -> list[str]:
        """Numeros para la tecla D."""
        return []

    def salir(self) -> None:
        """Al volver a mitad o al acabar."""

    # ---- resultado ----

    def guardar(self, precision: float, estrellas: int, **datos) -> None:
        """Guarda la sesion y prepara lo comun del resultado.

        Una sola regla para todas las fases. Cada dia con 3 lotos a tu nivel
        mas alto cuenta, y con 5 dias subes. La frase de abajo dice por que
        ha contado o no.
        """
        pr = self.app.progreso
        nivel_antes = pr.nivel(self.clave)
        dias_antes = pr.dias_para_subir(self.clave)
        mejor = pr.mejor(self.clave, self.variante)
        pr.registrar(self.clave, self.variante, precision, estrellas,
                     nivel=None if self.prueba else self.nivel, **datos)
        nivel, dias = pr.nivel(self.clave), pr.dias_para_subir(self.clave)

        if not self.con_niveles:
            linea = (self.sin_niveles, E.JADE)
        elif nivel > nivel_antes:
            linea = (f"¡Subes al nivel {nivel + 1}! {self.nombre_nivel(nivel)}", E.AZAFRAN)
        elif nivel_antes >= len(NIVELES[self.clave]) - 1:
            linea = ("Nivel máximo. Cuida tu racha", E.ORO)
        elif self.prueba:
            linea = ("Con las opciones de prueba no se sube de nivel", E.APAGADO)
        elif self.nivel < nivel_antes:
            linea = ("En un nivel más bajo no se sube", E.APAGADO)
        elif datos.get("vueltas", VUELTAS_NIVEL) < VUELTAS_NIVEL:
            linea = (f"Con menos de {VUELTAS_NIVEL} vueltas no se sube", E.APAGADO)
        elif estrellas < LOTOS_PARA_SUBIR:
            linea = (f"Para subir cuentan los días con {LOTOS_PARA_SUBIR} lotos", E.APAGADO)
        elif dias == dias_antes:
            linea = (f"Hoy ya contaba. Llevas {dias} de {DIAS_PARA_SUBIR} días", E.APAGADO)
        else:
            linea = (f"Día contado para subir, {dias} de {DIAS_PARA_SUBIR}", E.JADE)

        self.resultado = {
            "precision": precision,
            "estrellas": estrellas,
            "record": mejor is not None and precision > mejor,
            "linea": linea,
        }

    def dibujar_resultado(self) -> None:
        """Lo propio de la fase en el resultado (titulo, lotos, consejo)."""
        raise NotImplementedError

    def panel_resultado(self) -> None:
        self.dibujar_resultado()
        texto, color = self.resultado["linea"]
        Z.linea(self.app.pantalla, texto, "negrita", 16, color, E.PANEL.top + 384)
        Z.botones_fin(self.app)
