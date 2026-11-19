"""Lo que tiene que saber hacer cada fase del ritual para que la app la muestre.

La app no sabe nada de respirar ni de meditar. Solo lleva el bucle, las
teclas, la pausa y el cambio de pantalla, y le pide a la fase activa lo
propio de ella (sus botones del inicio, su panel, lo que dibuja sobre la
camara y su resultado). Para anadir una fase nueva, como los estiramientos,
se escribe una clase hija de Fase en esta carpeta y se apunta en FASES
(temple/interfaz/fases/__init__.py). La logica de la fase (que comprueba la
camara, cuando pasa de paso) va aparte, en temple/, sin Pygame y con tests.

Lo que la fase puede usar de la app
  app.pantalla, app.botonera, app.progreso, app.sonido, app.camara y app.t
  app.empezar, app.volver_inicio, app.seguir, app.avisar
  app.pausa_manual, app.pausado() y app.vigilar(ausente)
"""

from __future__ import annotations

from temple.puntero import GestoPalma


class Fase:
    clave = ""  # como se guarda en el progreso
    nombre = ""  # como sale en la fila del ritual
    tecla = None  # tecla del inicio que la elige
    usa_cara = False  # si necesita el modelo de cara (gasta unos 13 ms por fotograma)
    motivo_pausa = ""  # que decir en la camara cuando se pausa con la mano
    ayuda: tuple[str, str] | None = None  # ayuda de abajo mientras se practica, si no vale la de siempre

    def __init__(self, app, palma_s: float):
        # Cada fase hija recibe (app, opciones) y llama a esto con su tiempo de palma
        self.app = app
        self.palma = GestoPalma(palma_s)  # palma abierta para pausar
        self.resultado: dict = {}

    # ---- inicio ----

    def panel_inicio(self) -> None:
        """Botones para empezar, la meta y la fila de menos y mas."""
        raise NotImplementedError

    def cambiar(self, paso: int) -> None:
        """Menos y mas del inicio."""

    def resumen(self) -> str:
        return ""

    def tecla_inicio(self, k) -> bool:
        """Teclas propias del inicio. True si la ha usado."""
        return False

    # ---- practica (tutorial o sesion) ----

    def empezar(self, modo: str, variante: str) -> None:
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
        """Al volver al inicio a mitad o al acabar."""

    # ---- resultado ----

    def panel_resultado(self) -> None:
        raise NotImplementedError

    def accion_resultado(self) -> None:
        """Enter o Espacio en el resultado."""
        self.app.volver_inicio()
