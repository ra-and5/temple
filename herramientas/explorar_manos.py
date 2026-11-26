"""Experimento de la respiracion alterna (Anuloma Viloma).

Comprueba si la camara distingue que orificio de la nariz se tapa con la mano
derecha. El derecho se tapa con el pulgar y el izquierdo con cualquier otro dedo
(segun la variante se usa el anular, el anular y el menique, o el indice).

Usa dos modelos de MediaPipe a la vez sobre la misma imagen
  - pose, para saber donde esta la nariz y el ancho de los hombros
  - manos, para saber donde estan las puntas de los cinco dedos

En pantalla salen las distancias de cada dedo a la nariz y el veredicto.
En la terminal se escribe una linea cada medio segundo para poder copiarla.

Uso, desde cualquier carpeta
    python herramientas/explorar_manos.py
ESC o la X de la ventana para salir.
"""

import math
import time
from collections import Counter, deque
from pathlib import Path

import cv2
import mediapipe as mp

# Rutas relativas al proyecto, asi funciona se lance desde donde se lance
RAIZ = Path(__file__).resolve().parent.parent
MODELO_POSE = RAIZ / "models" / "pose_landmarker_full.task"
MODELO_MANOS = RAIZ / "models" / "hand_landmarker.task"

# Indices de los puntos que usamos
NARIZ = 0  # pose
HOMBRO_IZQ, HOMBRO_DER = 11, 12  # pose
PULGAR_PUNTA = 4  # mano
# Puntas del resto de dedos. MediaPipe a veces confunde que dedo es cual
# cuando la mano esta doblada, asi que cualquiera de ellos vale para el lado izquierdo
OTRAS_PUNTAS = {8: "indice", 12: "corazon", 16: "anular", 20: "menique"}

# Un dedo "tapa" si su punta esta a menos de UMBRAL anchos de hombros de la nariz.
# Valor de partida, se calibra con el experimento
UMBRAL = 0.25

# Suavizado. El veredicto que se ensena es el mas repetido en los ultimos N frames,
# y si se pierde la mano un momento se mantiene el ultimo durante MEMORIA_S segundos
N_SUAVIZADO = 8
MEMORIA_S = 0.6

VENTANA = "Explorar manos (respiracion alterna)"

# Colores en BGR
AZUL = (255, 0, 0)
VERDE = (0, 200, 0)
ROJO = (0, 0, 255)
AMARILLO = (0, 220, 255)
MAGENTA = (255, 0, 255)
BLANCO = (255, 255, 255)
NEGRO = (0, 0, 0)


def crear_modelos():
    """Prepara los modelos de pose y de manos en modo video."""
    vision = mp.tasks.vision
    base = mp.tasks.BaseOptions

    opciones_pose = vision.PoseLandmarkerOptions(
        base_options=base(model_asset_path=str(MODELO_POSE)),
        running_mode=vision.RunningMode.VIDEO,
        num_poses=1,
    )
    opciones_manos = vision.HandLandmarkerOptions(
        base_options=base(model_asset_path=str(MODELO_MANOS)),
        running_mode=vision.RunningMode.VIDEO,
        num_hands=1,  # solo la mano derecha hace la tecnica
        # Mas permisivo que el 0.5 por defecto, porque la mano delante de la cara
        # se pierde a menudo
        min_hand_detection_confidence=0.3,
        min_hand_presence_confidence=0.3,
        min_tracking_confidence=0.3,
    )
    pose = vision.PoseLandmarker.create_from_options(opciones_pose)
    manos = vision.HandLandmarker.create_from_options(opciones_manos)
    return pose, manos


def distancia(a, b):
    """Distancia entre dos puntos en coordenadas normalizadas (0 a 1)."""
    return math.hypot(a.x - b.x, a.y - b.y)


def texto(frame, msg, fila, color=BLANCO):
    """Escribe una linea con fondo negro para que se lea sobre cualquier imagen."""
    y = 30 + fila * 30
    (ancho, alto), _ = cv2.getTextSize(msg, cv2.FONT_HERSHEY_SIMPLEX, 0.7, 2)
    cv2.rectangle(frame, (5, y - alto - 8), (15 + ancho, y + 8), NEGRO, -1)
    cv2.putText(frame, msg, (10, y), cv2.FONT_HERSHEY_SIMPLEX, 0.7, color, 2)


VEREDICTOS = {
    "ninguno": ("Ninguno tapado", AMARILLO),
    "derecho": ("Tapa DERECHO (pulgar)", VERDE),
    "izquierdo": ("Tapa IZQUIERDO (otro dedo)", MAGENTA),
}


def veredicto(d_pulgar, d_otro):
    """Decide que orificio se tapa a partir de las distancias normalizadas."""
    if d_pulgar >= UMBRAL and d_otro >= UMBRAL:
        return "ninguno"
    # Si los dos estan cerca, manda el que este mas pegado a la nariz
    return "derecho" if d_pulgar <= d_otro else "izquierdo"


def main():
    """Abre la cámara y enseña en directo qué lado de la nariz tapa la mano."""
    pose, manos = crear_modelos()
    print("Modelos preparados")

    cap = cv2.VideoCapture(0)
    if not cap.isOpened():
        print("No se puede abrir la camara")
        return

    ultimo_ts = 0
    ultimo_log = 0.0
    historial = deque(maxlen=N_SUAVIZADO)
    estable = "ninguno"
    visto_mano = 0.0  # ultima vez que se vio la mano

    try:
        while True:
            ok, frame = cap.read()
            if not ok:
                print("No se puede leer la camara")
                break

            frame = cv2.flip(frame, 1)  # modo espejo
            h, w, _ = frame.shape

            rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            imagen = mp.Image(image_format=mp.ImageFormat.SRGB, data=rgb)

            # En modo video el tiempo tiene que crecer siempre
            ts = max(int(time.monotonic() * 1000), ultimo_ts + 1)
            ultimo_ts = ts

            res_pose = pose.detect_for_video(imagen, ts)
            res_manos = manos.detect_for_video(imagen, ts)

            nariz = escala = None
            if res_pose.pose_landmarks:
                p = res_pose.pose_landmarks[0]
                nariz = p[NARIZ]
                escala = distancia(p[HOMBRO_IZQ], p[HOMBRO_DER])
                cv2.circle(frame, (int(nariz.x * w), int(nariz.y * h)), 6, ROJO, -1)

            mano = res_manos.hand_landmarks[0] if res_manos.hand_landmarks else None
            if mano:
                for ini, fin in mp.solutions.hands.HAND_CONNECTIONS:
                    a, b = mano[ini], mano[fin]
                    cv2.line(frame, (int(a.x * w), int(a.y * h)),
                             (int(b.x * w), int(b.y * h)), AZUL, 2)
                for punto in mano:
                    cv2.circle(frame, (int(punto.x * w), int(punto.y * h)), 3, BLANCO, -1)
                pul = mano[PULGAR_PUNTA]
                cv2.circle(frame, (int(pul.x * w), int(pul.y * h)), 9, VERDE, 2)
                for i in OTRAS_PUNTAS:
                    q = mano[i]
                    cv2.circle(frame, (int(q.x * w), int(q.y * h)), 7, MAGENTA, 2)

            # Lo que sale en pantalla y en la terminal
            ahora = time.monotonic()
            if nariz is None or escala is None or escala < 1e-3:
                texto(frame, "Sin cuerpo (no veo la nariz o los hombros)", 0, ROJO)
                linea = "sin cuerpo"
            elif mano is None:
                # Si se pierde la mano un momento, se mantiene el ultimo veredicto
                perdida = ahora - visto_mano
                if perdida > MEMORIA_S:
                    estable = "ninguno"
                    historial.clear()
                msg, color = VEREDICTOS[estable]
                texto(frame, f"Nariz vis={nariz.visibility:.2f}", 0)
                texto(frame, f"Sin mano ({perdida:.1f} s)", 1, ROJO)
                texto(frame, msg, 3, color)
                linea = f"nariz_vis={nariz.visibility:.2f} | sin mano {perdida:.1f}s | {msg}"
            else:
                visto_mano = ahora
                d_pul = distancia(mano[PULGAR_PUNTA], nariz) / escala
                # El dedo (no pulgar) mas cercano a la nariz
                i_otro = min(OTRAS_PUNTAS, key=lambda i: distancia(mano[i], nariz))
                d_otro = distancia(mano[i_otro], nariz) / escala

                historial.append(veredicto(d_pul, d_otro))
                estable = Counter(historial).most_common(1)[0][0]
                msg, color = VEREDICTOS[estable]

                texto(frame, f"Nariz vis={nariz.visibility:.2f}  umbral={UMBRAL}", 0)
                texto(frame, f"Pulgar d={d_pul:.2f}", 1, VERDE)
                texto(frame, f"{OTRAS_PUNTAS[i_otro].capitalize()} d={d_otro:.2f}", 2, MAGENTA)
                texto(frame, msg, 3, color)
                linea = (f"nariz_vis={nariz.visibility:.2f} | pulgar d={d_pul:.2f}"
                         f" | {OTRAS_PUNTAS[i_otro]} d={d_otro:.2f} | {msg}")

            if ahora - ultimo_log >= 0.5:
                print(linea, flush=True)
                ultimo_log = ahora

            cv2.imshow(VENTANA, frame)
            if cv2.waitKey(1) & 0xFF == 27:
                break
            if cv2.getWindowProperty(VENTANA, cv2.WND_PROP_VISIBLE) < 1:
                break
    finally:
        cap.release()
        cv2.destroyAllWindows()
        pose.close()
        manos.close()


if __name__ == "__main__":
    main()
