"""Lo que ve la camara en cada fotograma, con MediaPipe Pose, Hands y Face.

La parte principal es saber que orificio de la nariz tapa la mano.

Pose da la nariz y el ancho de los hombros, que sirve de regla para medir
distancias sin que importe lo lejos que este la persona. Hands da las puntas
de los dedos. Face (solo al meditar, con usar_cara) dice si los ojos estan
cerrados. Las orejas, los codos y las munecas de Pose sirven para los
estiramientos.

  - derecho    la punta del pulgar esta pegada a la nariz
  - izquierdo  la punta de otro dedo esta pegada a la nariz (con la mano
               doblada el modelo confunde que dedo es cual, asi que vale cualquiera)
  - ambos      pulgar y otro dedo pegados a la vez (pinza de la retencion)
  - ninguno    nada cerca de la nariz

Umbrales comprobados en el experimento del 11/11 (herramientas/explorar_manos.py).
Pulgar tapando entre 0.07 y 0.10, indice tapando entre 0.03 y 0.05, y el dedo
que no tapa entre 0.31 y 0.39.
"""

from __future__ import annotations

import math
import time
from collections import Counter, deque
from dataclasses import dataclass
from pathlib import Path

import cv2
import mediapipe as mp

RAIZ = Path(__file__).resolve().parent.parent
MODELO_POSE = RAIZ / "models" / "pose_landmarker_full.task"
MODELO_MANOS = RAIZ / "models" / "hand_landmarker.task"
MODELO_CARA = RAIZ / "models" / "face_landmarker.task"

NARIZ = 0
OREJA_IZQ, OREJA_DER = 7, 8
HOMBRO_IZQ, HOMBRO_DER = 11, 12
CODO_IZQ, CODO_DER = 13, 14
MUNECA_IZQ, MUNECA_DER = 15, 16
PULGAR_PUNTA = 4
OTRAS_PUNTAS = {8: "indice", 12: "corazon", 16: "anular", 20: "menique"}

UMBRAL = 0.25  # un dedo tapa si esta a menos de esto (en anchos de hombros)
UMBRAL_AMBOS = 0.15  # para "ambos" los dos dedos tienen que estar muy pegados


@dataclass
class Lectura:
    """Lo que ve la camara en un fotograma."""

    tapado: str | None  # derecho, izquierdo, ambos, ninguno, o None si no se ve a nadie
    d_pulgar: float | None = None
    d_otro: float | None = None
    dedo_otro: str | None = None
    nariz: tuple[float, float] | None = None  # coordenadas normalizadas 0 a 1
    escala: float | None = None  # ancho de hombros, en las mismas unidades
    mano: list[tuple[float, float]] | None = None  # los 21 puntos de la mano
    mano_3d: list[tuple[float, float, float]] | None = None  # en metros, con profundidad
    perdida_s: float = 0.0  # segundos sin ver la mano
    hombros: tuple[tuple[float, float], tuple[float, float]] | None = None
    ojos: float | None = None  # 0 abiertos, 1 cerrados (solo con el modelo de cara)
    # Para los estiramientos. Cada par va en el mismo orden que los hombros
    orejas: tuple[tuple[float, float], tuple[float, float]] | None = None
    codos: tuple[tuple[float, float], tuple[float, float]] | None = None
    munecas: tuple[tuple[float, float], tuple[float, float]] | None = None
    vis_munecas: tuple[float, float] | None = None  # 0 a 1, lo seguro que esta el modelo

    @property
    def cuerpo(self) -> bool:
        """Si la camara ve a alguien (nariz y hombros)."""
        return self.tapado is not None


def clasificar(d_pulgar: float, d_otro: float,
               umbral: float = UMBRAL, umbral_ambos: float = UMBRAL_AMBOS) -> str:
    """Decide que orificio se tapa a partir de las distancias normalizadas."""
    if d_pulgar < umbral_ambos and d_otro < umbral_ambos:
        return "ambos"
    if d_pulgar >= umbral and d_otro >= umbral:
        return "ninguno"
    # Si los dos estan cerca pero no pegados, manda el mas cercano
    return "derecho" if d_pulgar <= d_otro else "izquierdo"


def _distancia(a, b) -> float:
    return math.hypot(a.x - b.x, a.y - b.y)


class Detector:
    """Junta los dos modelos y suaviza el resultado entre fotogramas.

    El lado tapado que devuelve es el mas repetido en los ultimos n_suavizado
    fotogramas. Si la mano desaparece menos de memoria_s segundos se mantiene
    el ultimo, porque delante de la cara el modelo la pierde a ratos.
    """

    def __init__(self, n_suavizado: int = 8, memoria_s: float = 0.6):
        vision = mp.tasks.vision
        base = mp.tasks.BaseOptions
        self._pose = vision.PoseLandmarker.create_from_options(
            vision.PoseLandmarkerOptions(
                base_options=base(model_asset_path=str(MODELO_POSE)),
                running_mode=vision.RunningMode.VIDEO,
                num_poses=1,
            )
        )
        self._manos = vision.HandLandmarker.create_from_options(
            vision.HandLandmarkerOptions(
                base_options=base(model_asset_path=str(MODELO_MANOS)),
                running_mode=vision.RunningMode.VIDEO,
                num_hands=1,
                min_hand_detection_confidence=0.3,
                min_hand_presence_confidence=0.3,
                min_tracking_confidence=0.3,
            )
        )
        # El de cara solo se usa al meditar. Si falta el archivo, el juego sigue
        # sin saber si cierras los ojos
        self._cara = None
        if MODELO_CARA.exists():
            self._cara = vision.FaceLandmarker.create_from_options(
                vision.FaceLandmarkerOptions(
                    base_options=base(model_asset_path=str(MODELO_CARA)),
                    running_mode=vision.RunningMode.VIDEO,
                    num_faces=1,
                    output_face_blendshapes=True,
                )
            )
        self.usar_cara = False
        self._memoria_s = memoria_s
        self._historial: deque[str] = deque(maxlen=n_suavizado)
        self._estable = "ninguno"
        self._visto_mano = float("-inf")
        self._ultimo_ts = 0

    def procesar(self, frame_bgr) -> Lectura:
        """Analiza un fotograma de OpenCV (BGR, ya en espejo si se quiere)."""
        rgb = cv2.cvtColor(frame_bgr, cv2.COLOR_BGR2RGB)
        imagen = mp.Image(image_format=mp.ImageFormat.SRGB, data=rgb)
        # En modo video la marca de tiempo tiene que crecer siempre
        ts = max(int(time.monotonic() * 1000), self._ultimo_ts + 1)
        self._ultimo_ts = ts
        res_pose = self._pose.detect_for_video(imagen, ts)
        res_manos = self._manos.detect_for_video(imagen, ts)
        ojos = None
        if self.usar_cara and self._cara is not None:
            res_cara = self._cara.detect_for_video(imagen, ts)
            if res_cara.face_blendshapes:
                valores = {b.category_name: b.score for b in res_cara.face_blendshapes[0]}
                ojos = (valores.get("eyeBlinkLeft", 0) + valores.get("eyeBlinkRight", 0)) / 2
        ahora = time.monotonic()

        # La mano se devuelve aunque no haya cuerpo, porque los menus se
        # manejan con el dedo y ahi da igual que no se vean los hombros
        puntos_mano = ([(q.x, q.y) for q in res_manos.hand_landmarks[0]]
                       if res_manos.hand_landmarks else None)
        # Los puntos en 3D reales sirven para saber si un dedo esta estirado
        # aunque apunte a la camara (en la imagen plana parece corto)
        puntos_3d = ([(q.x, q.y, q.z) for q in res_manos.hand_world_landmarks[0]]
                     if res_manos.hand_world_landmarks else None)
        if not res_pose.pose_landmarks:
            return Lectura(tapado=None, mano=puntos_mano, mano_3d=puntos_3d, ojos=ojos)
        p = res_pose.pose_landmarks[0]
        nariz = p[NARIZ]
        escala = _distancia(p[HOMBRO_IZQ], p[HOMBRO_DER])
        if escala < 1e-3:
            return Lectura(tapado=None, mano=puntos_mano, mano_3d=puntos_3d, ojos=ojos)
        pos_nariz = (nariz.x, nariz.y)
        hombros = ((p[HOMBRO_IZQ].x, p[HOMBRO_IZQ].y), (p[HOMBRO_DER].x, p[HOMBRO_DER].y))

        def par(i, j):
            return (p[i].x, p[i].y), (p[j].x, p[j].y)

        cuerpo = dict(orejas=par(OREJA_IZQ, OREJA_DER), codos=par(CODO_IZQ, CODO_DER),
                      munecas=par(MUNECA_IZQ, MUNECA_DER),
                      vis_munecas=(p[MUNECA_IZQ].visibility, p[MUNECA_DER].visibility))

        if not res_manos.hand_landmarks:
            perdida = ahora - self._visto_mano
            if perdida > self._memoria_s:
                self._estable = "ninguno"
                self._historial.clear()
            return Lectura(tapado=self._estable, nariz=pos_nariz, escala=escala,
                           perdida_s=perdida, hombros=hombros, ojos=ojos, **cuerpo)

        self._visto_mano = ahora
        mano = res_manos.hand_landmarks[0]
        d_pul = _distancia(mano[PULGAR_PUNTA], nariz) / escala
        i_otro = min(OTRAS_PUNTAS, key=lambda i: _distancia(mano[i], nariz))
        d_otro = _distancia(mano[i_otro], nariz) / escala

        self._historial.append(clasificar(d_pul, d_otro))
        self._estable = Counter(self._historial).most_common(1)[0][0]
        return Lectura(
            tapado=self._estable,
            d_pulgar=d_pul,
            d_otro=d_otro,
            dedo_otro=OTRAS_PUNTAS[i_otro],
            nariz=pos_nariz,
            escala=escala,
            mano=puntos_mano,
            mano_3d=puntos_3d,
            hombros=hombros,
            ojos=ojos,
            **cuerpo,
        )

    def cerrar(self) -> None:
        self._pose.close()
        self._manos.close()
        if self._cara is not None:
            self._cara.close()

    def __enter__(self):
        return self

    def __exit__(self, *_):
        self.cerrar()


def dibujar_lectura(frame, lectura: Lectura) -> None:
    """Dibuja la nariz y la mano sobre el fotograma."""
    h, w = frame.shape[:2]

    def px(punto):
        return int(punto[0] * w), int(punto[1] * h)

    if lectura.nariz:
        cv2.circle(frame, px(lectura.nariz), 6, (0, 0, 255), -1, cv2.LINE_AA)
    if lectura.mano:
        for ini, fin in mp.solutions.hands.HAND_CONNECTIONS:
            cv2.line(frame, px(lectura.mano[ini]), px(lectura.mano[fin]),
                     (255, 0, 0), 2, cv2.LINE_AA)
        cv2.circle(frame, px(lectura.mano[PULGAR_PUNTA]), 9, (0, 200, 0), 2, cv2.LINE_AA)
        for i in OTRAS_PUNTAS:
            cv2.circle(frame, px(lectura.mano[i]), 7, (255, 0, 255), 2, cv2.LINE_AA)
