"""Crea un progreso de demostracion, como si llevaras unas semanas jugando.

Sirve para ensenar el juego (y grabar el video) con niveles ya subidos sin
tocar el progreso de verdad. Se guarda en datos/demo/ y las fechas van
respecto a hoy, asi que funciona cualquier dia.

    python herramientas/crear_demo.py
    bash jugar.sh --datos datos/demo

Lo que queda, con la regla de siempre (5 dias con 3 lotos suben de nivel)
    - Tres semanas y media seguidas, de lunes a ayer, asi que la racha es larga.
    - Cada dia las cuatro fases a su nivel mas alto, casi siempre con 3 lotos.
      Las flexiones solo los ultimos 9 dias, como si fueran nuevas, y siempre
      con 3 lotos. Asi quedan en el nivel 2 a 1 dia de subir, sea el dia que
      sea, y en el video se ve la subida al nivel 3 en directo.
    - Hoy sin practicar, para hacer el ritual de hoy en el video.
    - Los cuatro tutoriales vistos.
"""

from __future__ import annotations

import random
import sys
from datetime import date, timedelta
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(RAIZ))

from temple.meditacion import lotos  # noqa: E402
from temple.progreso import NIVELES, RUTA, Progreso  # noqa: E402

CARPETA = RAIZ / "datos" / "demo"
SEMANAS_ATRAS = 3  # semanas completas antes de la actual
DIAS_FLEXIONES = 9  # 5 dias suben al nivel 2 y 4 mas dejan a 1 dia del nivel 3


def crear(hoy: date | None = None, carpeta: Path = CARPETA) -> Progreso:
    hoy = hoy or date.today()
    azar = random.Random(7)
    ruta = carpeta / RUTA.name
    if ruta.exists():
        ruta.unlink()
    p = Progreso(ruta, tutoriales=set(NIVELES), ajustes={"vueltas": 5})

    lunes_hoy = hoy - timedelta(days=hoy.weekday())
    dia = lunes_hoy - timedelta(weeks=SEMANAS_ATRAS)
    while dia < hoy:
        for fase in NIVELES:
            if fase == "flexiones" and (hoy - dia).days > DIAS_FLEXIONES:
                continue
            if fase == "estiramientos" and azar.random() < 0.15:
                continue  # algun dia sin estirar
            # Casi siempre 3 lotos, a veces 2. Las flexiones siempre 3, para que
            # su subida de nivel no dependa del azar ni del dia
            pre = azar.uniform(0.86, 1.0) if azar.random() < 0.8 else azar.uniform(0.66, 0.84)
            if fase == "flexiones":
                pre = azar.uniform(0.86, 1.0)
            nivel = p.nivel(fase)
            minutos = NIVELES["meditacion"][nivel] if fase == "meditacion" else None
            if fase == "respiracion":
                variante = "avanzada" if nivel else "principiante"
            elif fase == "flexiones":
                variante = NIVELES["flexiones"][nivel][0]
            else:
                variante = "normal"
            p.registrar(fase, variante, pre, lotos(pre), dia,
                        vueltas=5 if fase == "respiracion" else None, minutos=minutos,
                        nivel=nivel)
        dia += timedelta(days=1)
    p.guardar()
    return p


def crear_dia5(hoy: date | None = None, carpeta: Path = CARPETA) -> Progreso:
    """El dia 5 del video. Cuatro dias seguidos (de hace 4 dias hasta ayer)
    con 3 lotos en cada fase y a nivel 1. Hoy, con 3 lotos, sube cada
    fase: respiracion avanzada, meditacion de 8 min y flexiones tecnico."""
    hoy = hoy or date.today()
    ruta = carpeta / RUTA.name
    if ruta.exists():
        ruta.unlink()
    p = Progreso(ruta, tutoriales=set(NIVELES), ajustes={"vueltas": 5})
    for atras in range(4, 0, -1):
        dia = hoy - timedelta(days=atras)
        for fase in NIVELES:
            variante = {"respiracion": "principiante", "flexiones": "facil"}.get(fase, "normal")
            p.registrar(fase, variante, 0.95, 3, dia,
                        vueltas=5 if fase == "respiracion" else None,
                        minutos=NIVELES["meditacion"][0] if fase == "meditacion" else None,
                        nivel=0)
    p.guardar()
    return p


if __name__ == "__main__":
    # python herramientas/crear_demo.py --dia5   el dia 5 del guion del video
    p = crear_dia5() if "--dia5" in sys.argv else crear()
    print(f"Progreso de demostracion en {p.ruta.relative_to(RAIZ)}")
    print(f"  racha: {p.racha()} dias")
    for fase in NIVELES:
        print(f"  {fase}: nivel {p.nivel(fase) + 1}, {p.dias_para_subir(fase)} de 5 dias")
    print("Para jugar con el:  bash jugar.sh --datos datos/demo")
