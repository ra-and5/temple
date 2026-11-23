import csv
import math
from dataclasses import dataclass, field
from pathlib import Path

NIVELES = {
    "facil": {"abajo": 110, "arriba": 145, "profundo": 0.75, "cadera": 0.25},
    "tecnico": {"abajo": 90, "arriba": 160, "profundo": 0.5, "cadera": 0.12},
}
REPETICIONES = 5
SOSTENER_S = 2.0
REGISTRO = Path(__file__).resolve().parent.parent / "datos" / "ultimas_flexiones.csv"


@dataclass
class Cuerpo:
    hombros: tuple
    codos: tuple
    munecas: tuple
    caderas: tuple
    tobillos: tuple
    vis_brazos: tuple = (1.0, 1.0)


@dataclass
class Medida:
    cuerpo: bool
    codo: float = 0.0
    profundidad: float = 0.0
    cadera: float = 0.0


def angulo_codo(hombro, codo, muneca):
    v1 = (hombro[0] - codo[0], hombro[1] - codo[1])
    v2 = (muneca[0] - codo[0], muneca[1] - codo[1])
    largo1 = math.hypot(v1[0], v1[1])
    largo2 = math.hypot(v2[0], v2[1])
    if largo1 == 0 or largo2 == 0:
        return 0.0
    coseno = (v1[0] * v2[0] + v1[1] * v2[1]) / (largo1 * largo2)
    coseno = max(-1.0, min(1.0, coseno))
    return math.degrees(math.acos(coseno))


def medir(c):
    if c is None:
        return Medida(cuerpo=False)

    if c.vis_brazos[0] >= c.vis_brazos[1]:
        lado = 0
    else:
        lado = 1

    hombro = c.hombros[lado]
    codo = c.codos[lado]
    muneca = c.munecas[lado]
    cadera = c.caderas[lado]
    tobillo = c.tobillos[lado]

    tronco = math.dist(hombro, cadera)
    if tronco < 0.001:
        return Medida(cuerpo=False)

    medio_y = (hombro[1] + tobillo[1]) / 2

    return Medida(
        cuerpo=True,
        codo=angulo_codo(hombro, codo, muneca),
        profundidad=(muneca[1] - hombro[1]) / tronco,
        cadera=(cadera[1] - medio_y) / tronco,
    )


def falta(objetivo, m, nivel="facil"):
    u = NIVELES[nivel]
    if not m.cuerpo:
        return "No te veo entero"
    if objetivo == "plancha":
        if m.codo < u["arriba"]:
            return "Estira los brazos"
        if m.cadera > u["cadera"]:
            return "No hundas la cadera"
        if m.cadera < -u["cadera"]:
            return "Baja la cadera"
    return None


@dataclass
class Paso:
    tipo: str
    texto: str
    detalle: str = ""
    objetivo: str = ""
    duracion: float = 0.0
    repeticiones: int = 0


def guion_sesion(repeticiones=REPETICIONES):
    return [
        Paso("mensaje", "Prepárate", "Tienes 5 segundos para ponerte en el suelo", duracion=5),
        Paso("esperar", "Ponte de lado", "Que se te vea de la cabeza a los pies",
             objetivo="cuerpo"),
        Paso("esperar", "Brazos estirados", "El cuerpo recto, como una tabla",
             objetivo="plancha"),
        Paso("contar", "Baja hasta el suelo", "y sube estirando los brazos",
             repeticiones=repeticiones),
        Paso("mensaje", "Bien hecho", "Ponte de rodillas y descansa", duracion=4),
    ]


def guion_tutorial():
    return [
        Paso("mensaje", "Flexiones", "Pon el portátil en el suelo, a tu lado", duracion=5),
        Paso("mensaje", "Prepárate", "Tienes 5 segundos para ponerte en el suelo", duracion=5),
        Paso("esperar", "Ponte de lado", "Que se te vea de la cabeza a los pies",
             objetivo="cuerpo"),
        Paso("esperar", "Brazos estirados", "El cuerpo recto, como una tabla",
             objetivo="plancha"),
        Paso("contar", "Baja hasta el suelo", "y sube estirando los brazos", repeticiones=2),
        Paso("mensaje", "En la sesión", f"harás {REPETICIONES} flexiones seguidas", duracion=5),
        Paso("mensaje", "Gana lotos", "Bajando hasta el suelo y con el cuerpo recto",
             duracion=5),
    ]


@dataclass
class Estado:
    paso: Paso
    indice: int
    total: int
    hecho: float
    medida: Medida
    hechas: int = 0
    buenas: int = 0
    abajo: bool = False
    flexion: bool = False
    fallo: str = ""
    nuevo_paso: bool = False
    terminado: bool = False


@dataclass
class Practica:
    pasos: list
    nivel: str = "facil"
    sostener_s: float = SOSTENER_S
    indice: int = 0
    inicio: float = -1.0
    desde: float = -1.0
    anunciado: int = -1
    llevas: int = 0
    abajo: bool = False
    profunda: bool = False
    recta: bool = True
    hechas: int = 0
    buenas: int = 0
    fallos: dict = field(default_factory=dict)

    def precision(self):
        if self.hechas == 0:
            return 0.0
        return self.buenas / self.hechas

    def peor(self):
        if not self.fallos:
            return ""
        return max(self.fallos, key=self.fallos.get)

    def siguiente_paso(self, t):
        self.indice += 1
        self.inicio = t
        self.desde = -1.0
        self.llevas = 0
        self.abajo = False

    def contar(self, m):
        u = NIVELES[self.nivel]
        if not m.cuerpo:
            return False, ""

        if not self.abajo:
            if m.codo <= u["abajo"]:
                self.abajo = True
                self.profunda = False
                self.recta = True
            return False, ""

        if m.profundidad <= u["profundo"]:
            self.profunda = True
        if abs(m.cadera) > u["cadera"]:
            self.recta = False

        if m.codo < u["arriba"]:
            return False, ""

        self.abajo = False
        self.llevas += 1
        self.hechas += 1

        if not self.profunda:
            fallo = "poco profunda"
        elif not self.recta:
            fallo = "cadera"
        else:
            self.buenas += 1
            return True, ""

        self.fallos[fallo] = self.fallos.get(fallo, 0) + 1
        return True, fallo

    def actualizar(self, t, cuerpo):
        if self.inicio < 0:
            self.inicio = t
        m = medir(cuerpo)
        total = len(self.pasos)

        if self.indice >= total:
            return Estado(self.pasos[-1], total, total, 1.0, m, self.hechas, self.buenas,
                          terminado=True)

        nuevo = self.anunciado != self.indice
        self.anunciado = self.indice
        indice = self.indice
        paso = self.pasos[indice]

        if paso.tipo == "mensaje":
            hecho = min((t - self.inicio) / paso.duracion, 1.0)
            if t - self.inicio >= paso.duracion:
                self.siguiente_paso(t)
            return Estado(paso, indice, total, hecho, m, self.hechas, self.buenas,
                          nuevo_paso=nuevo)

        if paso.tipo == "esperar":
            if falta(paso.objetivo, m, self.nivel) is None:
                if self.desde < 0:
                    self.desde = t
                hecho = min((t - self.desde) / self.sostener_s, 1.0)
            else:
                self.desde = -1.0
                hecho = 0.0
            if hecho >= 1.0:
                self.siguiente_paso(t)
            return Estado(paso, indice, total, hecho, m, self.hechas, self.buenas,
                          nuevo_paso=nuevo)

        flexion, fallo = self.contar(m)
        abajo = self.abajo
        hecho = min(self.llevas / paso.repeticiones, 1.0)
        if self.llevas >= paso.repeticiones:
            self.siguiente_paso(t)
        return Estado(paso, indice, total, hecho, m, self.hechas, self.buenas, abajo,
                      flexion, fallo, nuevo_paso=nuevo)


def lotos(precision):
    if precision >= 0.85:
        return 3
    if precision >= 0.65:
        return 2
    if precision >= 0.40:
        return 1
    return 0


class Registro:
    CAMPOS = ("t", "paso", "cuerpo", "codo", "profundidad", "cadera", "abajo", "hechas",
              "buenas", "fallo")

    def __init__(self, ruta=REGISTRO):
        self.ultimo = -1.0
        try:
            ruta.parent.mkdir(parents=True, exist_ok=True)
            self.archivo = open(ruta, "w", newline="", encoding="utf-8")
            self.csv = csv.writer(self.archivo)
            self.csv.writerow(self.CAMPOS)
        except OSError:
            self.archivo = None

    def apuntar(self, t, e):
        if self.archivo is None or t - self.ultimo < 0.1:
            return
        self.ultimo = t
        m = e.medida
        self.csv.writerow([f"{t:.2f}", e.paso.texto, int(m.cuerpo), f"{m.codo:.0f}",
                           f"{m.profundidad:.2f}", f"{m.cadera:.2f}", int(e.abajo), e.hechas,
                           e.buenas, e.fallo])

    def cerrar(self):
        if self.archivo is not None:
            self.archivo.close()
            self.archivo = None
