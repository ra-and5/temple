import cv2   #OpenCV, para la camara y para dibujar
import mediapipe as mp  #MediaPipe, el que reconoce el cuerpo
import time # para saver en que milisegundo estamos



#Pieza 1 - Preparar el modelo de pose

BaseOptions = mp.tasks.BaseOptions
PoseLandmarker = mp.tasks.vision.PoseLandmarker
PoseLandmarkerOptions = mp.tasks.vision.PoseLandmarkerOptions
VisionRunningMode = mp.tasks.vision.RunningMode

options = PoseLandmarkerOptions(
    base_options=BaseOptions(model_asset_path="models/pose_landmarker_full.task"),
    running_mode=VisionRunningMode.VIDEO,
    num_poses=1
)

print("Modelo Preparado")

#Pieza 2 - Abrir la camara y enseñar lo que ve

with PoseLandmarker.create_from_options(options) as landmarker:
    cap = cv2.VideoCapture(0)

    while cap.isOpened():
        ret, frame = cap.read()
        if not ret:
            print("NO se peude leer la camara")
            break

        frame = cv2.flip(frame,1)

        #Pieza 3 - detectar el cuerpo

        rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        mp_image = mp.Image(image_format=mp.ImageFormat.SRGB, data=rgb)
        timestamp_ms = int(time.time() * 1000)
        result = landmarker.detect_for_video(mp_image, timestamp_ms)

        # Dibujar el esqueleto si hay alguien

        if result.pose_landmarks:
            puntos = result.pose_landmarks[0]
            h,w, _ = frame.shape

            for inicio, fin in mp.solutions.pose.POSE_CONNECTIONS:
                x1, y1 = int(puntos[inicio].x * w), int(puntos[inicio].y * h)
                x2, y2 = int(puntos[fin].x * w), int(puntos[fin].y * h)
                cv2.line(frame, (x1, y1), (x2, y2), (255, 0, 0), 2)

            for p in puntos:
                cv2.circle(frame, (int(p.x * w), int(p.y * h)), 3, (0, 255, 0), -1)



        cv2.imshow("Explorar pose", frame)



        if cv2.waitKey(1) & 0xFF == 27:
            break

        if cv2.getWindowProperty("Explorar pose", cv2.WND_PROP_VISIBLE) < 1:
            break

    cap.release()
    cv2.destroyAllWindows()


        
    