from flask import Flask, render_template, Response
import cv2
import mediapipe as mp
from scipy.spatial import distance as dist
import pygame
import time
from datetime import datetime
import csv
import atexit

app = Flask(__name__)

pygame.mixer.init()
pygame.mixer.music.load("static/alarm.wav.mp3")

camera = cv2.VideoCapture(0)
camera.set(cv2.CAP_PROP_FRAME_WIDTH, 1280)
camera.set(cv2.CAP_PROP_FRAME_HEIGHT, 720)

mp_face_mesh = mp.solutions.face_mesh
face_mesh = mp_face_mesh.FaceMesh(
    max_num_faces=1,
    refine_landmarks=True,
    min_detection_confidence=0.5,
    min_tracking_confidence=0.5
)

mp_draw = mp.solutions.drawing_utils

LEFT_EYE = [33, 160, 158, 133, 153, 144]
RIGHT_EYE = [362, 385, 387, 263, 373, 380]

EAR_THRESHOLD = 0.23

CLOSED_EYES_FRAMES = 30
counter = 0
blink_count = 0
blink_detected = False
eye_closed_start = None
closed_time = 0
last_closed_time = 0
display_start_time = None
attention_start = None
attention_warning = False
safety_score = 100

session_start = time.time()
drowsiness_events = 0
drowsiness_logged = False
distraction_count = 0
distraction_logged = False
last_event = ""

def eye_aspect_ratio(eye):
    A = dist.euclidean(eye[1], eye[5])
    B = dist.euclidean(eye[2], eye[4])
    C = dist.euclidean(eye[0], eye[3])
    return (A + B) / (2.0 * C)

def generate_frames():

    global counter
    global blink_count
    global blink_detected
    global eye_closed_start
    global closed_time
    global last_closed_time
    global display_start_time
    global attention_start
    global attention_warning
    global safety_score
    global session_start
    global drowsiness_events
    global drowsiness_logged
    global distraction_count
    global distraction_logged
    global last_event

    while True:
        success, frame = camera.read()
        if not success:
            break

        frame = cv2.flip(frame, 1)
        overlay = frame.copy()
        cv2.rectangle(overlay, (10,10), (420,620), (25,25,25), -1)
        cv2.putText(frame, "AI DRIVER MONITORING SYSTEM", (80,35), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0,255,255), 2)
        cv2.addWeighted(overlay, 0.45, frame, 0.55, 0, frame)
        cv2.rectangle(frame, (10,10), (430,600), (0,255,255), 2)

        rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        results = face_mesh.process(rgb)
        h, w, _ = frame.shape
        NOSE_TIP = 1

        if results.multi_face_landmarks:
            for face_landmarks in results.multi_face_landmarks:
                nose = face_landmarks.landmark[NOSE_TIP]
                nose_x = int(nose.x * w)
                nose_y = int(nose.y * h)

                cv2.circle(frame,(nose_x, nose_y),6,(255,0,0),-1)
                if nose_x < w * 0.40:
                    direction = "LOOKING LEFT"
                    direction_color = (0, 0, 255)

                elif nose_x > w * 0.60:
                    direction = "LOOKING RIGHT"
                    direction_color = (0, 0, 255)

                elif nose_y > h * 0.60:
                    direction = "LOOKING DOWN"
                    direction_color = (0, 165, 255)

                else:
                    direction = "LOOKING STRAIGHT"
                    direction_color = (0, 255, 0)
                if direction != "LOOKING STRAIGHT":
                    if attention_start is None:
                        attention_start = time.time()
                    if time.time() - attention_start >= 3:
                        attention_warning = True
                    else:
                        attention_warning = False
                else:
                    attention_start = None
                    attention_warning = False
                
                mp_draw.draw_landmarks(
                    frame,
                    face_landmarks,
                    mp_face_mesh.FACEMESH_TESSELATION
                )

                left_eye = []
                right_eye = []

                for idx in LEFT_EYE:
                    x = int(face_landmarks.landmark[idx].x * w)
                    y = int(face_landmarks.landmark[idx].y * h)
                    left_eye.append((x, y))
                    cv2.circle(frame, (x, y), 3, (0,255,0), -1)

                for idx in RIGHT_EYE:
                    x = int(face_landmarks.landmark[idx].x * w)
                    y = int(face_landmarks.landmark[idx].y * h)
                    right_eye.append((x, y))
                    cv2.circle(frame, (x, y), 3, (0,255,0), -1)

                leftEAR = eye_aspect_ratio(left_eye)
                rightEAR = eye_aspect_ratio(right_eye)
                ear = (leftEAR + rightEAR) / 2.0

                cv2.putText(frame, f"EAR : {ear:.2f}", (20,95),
                            cv2.FONT_HERSHEY_SIMPLEX, 0.8, (255,255,255), 2)

                if ear < EAR_THRESHOLD:
                    counter += 1
                    if eye_closed_start is None:
                        eye_closed_start = time.time()
                    closed_time = time.time() - eye_closed_start

                    if not blink_detected:
                        blink_detected = True
                    if counter >= CLOSED_EYES_FRAMES:
                         status = "DROWSINESS DETECTED"
                         color = (0,0,255)
                         if not drowsiness_logged:
                            drowsiness_events += 1
                            drowsiness_logged = True
                         if not pygame.mixer.music.get_busy():
                            pygame.mixer.music.play()
                    else:
                        status = "EYES CLOSED"
                        color = (0,165,255)
                else:
                    if blink_detected:
                        blink_count += 1
                        blink_detected = False
                    counter = 0


                    if eye_closed_start is not None:
                         last_closed_time = closed_time
                         display_start_time = time.time()
                    eye_closed_start = None
                    closed_time = 0

                    status = "AWAKE"

                    color = (0,255,0)

                    pygame.mixer.music.stop()
                    drowsiness_logged = False



                cv2.putText(
                    frame,
                    f"STATUS : {status}",
                    (20,80),
                    cv2.FONT_HERSHEY_SIMPLEX,
                    0.9,
                    color,2)



                cv2.putText(
                    frame,
                    f"BLINKS : {blink_count}",
                    (20,120),
                    cv2.FONT_HERSHEY_SIMPLEX,
                    0.8,(255,255,0),2)


                if closed_time > 0:
                    display_time = closed_time
                elif display_start_time is not None and (time.time() - display_start_time) < 5:
                    display_time = last_closed_time
                else:
                    display_time = 0.0

                cv2.putText(frame,f"TIMER : {display_time:.1f} sec",(20,160),cv2.FONT_HERSHEY_SIMPLEX,0.8,(255,255,255),2)


                cv2.putText(frame,"CAMERA : ON",(20,200),cv2.FONT_HERSHEY_SIMPLEX,0.7,(0,255,0),2)
                cv2.putText(frame,"AI MODEL : RUNNING",(20,230),cv2.FONT_HERSHEY_SIMPLEX,0.7,(255,255,0),2)
                face_status = "DETECTED"

                cv2.putText(
                    frame,f"FACE : {face_status}",(20, 260),cv2.FONT_HERSHEY_SIMPLEX,0.7,(0, 255, 0),2)

                eye_status = "OPEN" if ear >= EAR_THRESHOLD else "CLOSED"

                cv2.putText(frame,f"EYES : {eye_status}",(20, 290),cv2.FONT_HERSHEY_SIMPLEX,0.7,(255, 255, 255),2)


                alarm_status = "ON" if counter >= CLOSED_EYES_FRAMES else "OFF"

                alarm_color = (0, 0, 255) if alarm_status == "ON" else (0, 255, 0)

                cv2.putText(frame,f"ALARM : {alarm_status}",(20, 320),cv2.FONT_HERSHEY_SIMPLEX,0.7,alarm_color,2)
                cv2.putText(frame,f"HEAD : {direction}",(20, 350),cv2.FONT_HERSHEY_SIMPLEX,0.7,direction_color,2)
                if attention_warning:
                    if not distraction_logged:
                        distraction_count += 1
                        distraction_logged = True
                    cv2.putText(frame,"WARNING : DRIVER DISTRACTED",(20,390),cv2.FONT_HERSHEY_SIMPLEX,0.8,(0,0,255),2)
                else:
                    distraction_logged = False

                safety_score = 100
                if attention_warning:
                    safety_score -= 30
                if counter >= CLOSED_EYES_FRAMES:
                    safety_score -= 40
                if safety_score < 0:
                    safety_score = 0


                if safety_score >= 80:
                    score_color = (0,255,0)
                elif safety_score >= 50:
                    score_color = (0,255,255)
                else:
                    score_color = (0,0,255)

                cv2.putText(frame,f"SAFETY SCORE : {safety_score}%",(20,430),cv2.FONT_HERSHEY_SIMPLEX,0.8,score_color,2)

        elapsed = int(time.time() - session_start)
        minutes = elapsed // 60
        seconds = elapsed % 60
        session_time = f"{minutes:02}:{seconds:02}"
        cv2.putText(frame, f"SESSION : {session_time}", (20,470), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255,255,255), 2)
        cv2.putText(frame, f"TOTAL BLINKS : {blink_count}", (20,500), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255,255,0), 2)
        cv2.putText(frame, f"DROWSINESS EVENTS : {drowsiness_events}", (20,530), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0,0,255), 2)
        cv2.putText(frame, f"DISTRACTION WARNINGS : {distraction_count}", (20,560), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0,165,255), 2)

        ret, buffer = cv2.imencode(".jpg", frame)
        frame = buffer.tobytes()

        yield (b'--frame\r\n'
               b'Content-Type: image/jpeg\r\n\r\n' + frame + b'\r\n')

@app.route("/")
def home():
    return render_template("index.html")

@app.route("/video_feed")
def video_feed():
    return Response(generate_frames(),
                    mimetype="multipart/x-mixed-replace; boundary=frame")
def save_report():
    elapsed = int(time.time() - session_start)
    minutes = elapsed // 60
    seconds = elapsed % 60

    with open("driver_report.csv", "w", newline="") as file:
        writer = csv.writer(file)

        writer.writerow(["AI DRIVER DROWSINESS REPORT"])
        writer.writerow([])
        writer.writerow(["Session Time", f"{minutes} min {seconds} sec"])
        writer.writerow(["Total Blinks", blink_count])
        writer.writerow(["Drowsiness Events", drowsiness_events])
        writer.writerow(["Distraction Warnings", distraction_count])
        writer.writerow(["Final Safety Score", f"{safety_score}%"])

atexit.register(save_report)
if __name__ == "__main__":
    app.run(debug=True)