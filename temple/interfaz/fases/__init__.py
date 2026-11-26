"""Las fases del ritual, en el orden en que se hacen.

Para anadir una fase nueva se escribe su clase (ver base.py) y se pone aqui.
Los menus, las teclas y el cambio de pantalla salen solos.
"""

from temple.interfaz.fases.estiramientos import Estiramientos
from temple.interfaz.fases.flexiones import Flexiones
from temple.interfaz.fases.meditacion import Meditacion
from temple.interfaz.fases.respiracion import Respiracion

FASES = (Respiracion, Meditacion, Estiramientos, Flexiones)
