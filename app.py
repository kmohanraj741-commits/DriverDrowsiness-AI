from flask import Flask, render_template, Response, jsonify
import cv2
import mediapipe as mp
from scipy.spatial import distance as dist
import pygame
import time
import csv
import atexit
import os

# ============================================================
# AI MODULES
# ============================================================

from ai.baseline import DriverBaseline
from ai.behaviour import BehaviourAnalyzer
from ai.risk_engine import MultiSignalRiskEngine
from ai.event_manager import EventManager


# ============================================================
# FLASK
# ============================================================

app = Flask(__name__)


# ============================================================
# ALARM
# ============================================================

try:
    pygame.mixer.init()

    pygame.mixer.music.load(
        "static/alarm.wav.mp3"
    )

    alarm_ready = True

except Exception as e:

    print("Alarm error:", e)

    alarm_ready = False


# ============================================================
# CAMERA
# ============================================================

camera = cv2.VideoCapture(0)

camera.set(
    cv2.CAP_PROP_FRAME_WIDTH,
    1280
)

camera.set(
    cv2.CAP_PROP_FRAME_HEIGHT,
    720
)


# ============================================================
# MEDIAPIPE FACE MESH
# ============================================================

mp_face_mesh = mp.solutions.face_mesh

face_mesh = mp_face_mesh.FaceMesh(

    max_num_faces=1,

    refine_landmarks=True,

    min_detection_confidence=0.5,

    min_tracking_confidence=0.5
)

mp_draw = (
    mp.solutions.drawing_utils
)


# ============================================================
# EYE LANDMARKS
# ============================================================

LEFT_EYE = [
    33,
    160,
    158,
    133,
    153,
    144
]

RIGHT_EYE = [
    362,
    385,
    387,
    263,
    373,
    380
]


# ============================================================
# DETECTION SETTINGS
# ============================================================

EAR_THRESHOLD = 0.23

# Minimum number of frames eyes must be closed
# before considering it a real eye closure.
MIN_BLINK_FRAMES = 2

# A normal blink should be shorter than this.
MAX_BLINK_DURATION = 0.8

# Drowsiness if eyes remain closed for 3 seconds.
DROWSINESS_DURATION = 3.0

# Distraction warning after 3 seconds.
DISTRACTION_DURATION = 3.0


# ============================================================
# SESSION VARIABLES
# ============================================================

session_start = time.time()

blink_count = 0

drowsiness_events = 0

distraction_count = 0

safety_score = 100


# ============================================================
# EYE STATE VARIABLES
# ============================================================

eye_closed_start = None

eye_closed_frames = 0

eyes_were_closed = False

current_closed_duration = 0.0

last_closed_duration = 0.0


# ============================================================
# DROWSINESS STATE
# ============================================================

drowsiness_active = False

drowsiness_logged = False


# ============================================================
# DISTRACTION STATE
# ============================================================

attention_start = None

attention_warning = False

distraction_logged = False


# ============================================================
# LIVE STATUS
# ============================================================

current_ear = 0.0

current_ear_trend = "STABLE"

current_blink_pattern = "NORMAL"

current_head_direction = "CENTER"

current_risk_score = 0

current_risk_level = "LOW"

current_warning_level = "NONE"

face_detected = False

eye_status = "OPEN"

alarm_status = "OFF"


# ============================================================
# AI MODULE OBJECTS
# ============================================================

driver_baseline = DriverBaseline(
    calibration_duration=10
)

behaviour_analyzer = BehaviourAnalyzer()

risk_engine = MultiSignalRiskEngine()

event_manager = EventManager(
    confirmation_time=1.5
)


# ============================================================
# START DRIVER BASELINE
# ============================================================

driver_baseline.start_calibration()


# ============================================================
# RISK TIMELINE
# ============================================================

risk_timeline = []


# ============================================================
# EAR FUNCTION
# ============================================================

def eye_aspect_ratio(eye):

    A = dist.euclidean(
        eye[1],
        eye[5]
    )

    B = dist.euclidean(
        eye[2],
        eye[4]
    )

    C = dist.euclidean(
        eye[0],
        eye[3]
    )

    if C == 0:

        return 0.0

    return (
        (A + B)
        / (2.0 * C)
    )


# ============================================================
# ADD TIMELINE EVENT
# ============================================================

def add_timeline_event(
    event_type,
    risk_score,
    severity,
    duration
):

    event = {

        "timestamp":
            time.strftime(
                "%Y-%m-%d %H:%M:%S"
            ),

        "event_type":
            event_type,

        "risk_score":
            round(
                risk_score,
                2
            ),

        "severity":
            severity,

        "duration":
            round(
                duration,
                2
            )
    }

    risk_timeline.append(event)

    print(
        "EVENT:",
        event
    )


# ============================================================
# GENERATE VIDEO
# ============================================================

def generate_frames():

    global blink_count

    global drowsiness_events

    global distraction_count

    global safety_score

    global eye_closed_start

    global eye_closed_frames

    global eyes_were_closed

    global current_closed_duration

    global last_closed_duration

    global drowsiness_active

    global drowsiness_logged

    global attention_start

    global attention_warning

    global distraction_logged

    global current_ear

    global current_ear_trend

    global current_blink_pattern

    global current_head_direction

    global current_risk_score

    global current_risk_level

    global current_warning_level

    global face_detected

    global eye_status

    global alarm_status


    while True:

        # ====================================================
        # CAMERA
        # ====================================================

        success, frame = camera.read()

        if not success:

            print(
                "Camera frame could not be read."
            )

            break


        # ====================================================
        # MIRROR IMAGE
        # ====================================================

        frame = cv2.flip(
            frame,
            1
        )


        height, width, _ = (
            frame.shape
        )


        # ====================================================
        # MEDIAPIPE
        # ====================================================

        rgb = cv2.cvtColor(
            frame,
            cv2.COLOR_BGR2RGB
        )

        results = face_mesh.process(
            rgb
        )


        # ====================================================
        # DEFAULT VALUES
        # ====================================================

        face_detected = False


        # ====================================================
        # FACE FOUND
        # ====================================================

        if results.multi_face_landmarks:

            face_detected = True


            for face_landmarks in (
                results.multi_face_landmarks
            ):

                # =================================================
                # DRAW FACE MESH
                # =================================================

                mp_draw.draw_landmarks(

                    frame,

                    face_landmarks,

                    mp_face_mesh.FACEMESH_TESSELATION
                )


                # =================================================
                # HEAD DIRECTION
                # =================================================

                nose = (
                    face_landmarks
                    .landmark[1]
                )

                nose_x = int(
                    nose.x * width
                )

                nose_y = int(
                    nose.y * height
                )


                cv2.circle(

                    frame,

                    (
                        nose_x,
                        nose_y
                    ),

                    5,

                    (255, 0, 0),

                    -1
                )


                # =================================================
                # SIMPLE HEAD DIRECTION
                # =================================================

                if nose_x < width * 0.40:

                    direction = (
                        "LOOKING LEFT"
                    )

                    head_direction = "LEFT"

                    direction_color = (
                        0,
                        0,
                        255
                    )


                elif nose_x > width * 0.60:

                    direction = (
                        "LOOKING RIGHT"
                    )

                    head_direction = "RIGHT"

                    direction_color = (
                        0,
                        0,
                        255
                    )


                elif nose_y > height * 0.60:

                    direction = (
                        "LOOKING DOWN"
                    )

                    head_direction = "DOWN"

                    direction_color = (
                        0,
                        165,
                        255
                    )


                else:

                    direction = (
                        "LOOKING STRAIGHT"
                    )

                    head_direction = "CENTER"

                    direction_color = (
                        0,
                        255,
                        0
                    )


                current_head_direction = (
                    head_direction
                )


                # =================================================
                # DISTRACTION TIMER
                # =================================================

                if head_direction != "CENTER":

                    if attention_start is None:

                        attention_start = (
                            time.time()
                        )


                    distraction_duration = (
                        time.time()
                        - attention_start
                    )


                    if (
                        distraction_duration
                        >= DISTRACTION_DURATION
                    ):

                        attention_warning = True


                        if not distraction_logged:

                            distraction_count += 1

                            distraction_logged = True


                    else:

                        attention_warning = False


                else:

                    attention_start = None

                    attention_warning = False

                    distraction_logged = False


                # =================================================
                # EYE LANDMARKS
                # =================================================

                left_eye = []

                right_eye = []


                for index in LEFT_EYE:

                    x = int(
                        face_landmarks
                        .landmark[index]
                        .x
                        * width
                    )

                    y = int(
                        face_landmarks
                        .landmark[index]
                        .y
                        * height
                    )

                    left_eye.append(
                        (x, y)
                    )


                    cv2.circle(

                        frame,

                        (x, y),

                        3,

                        (0, 255, 0),

                        -1
                    )


                for index in RIGHT_EYE:

                    x = int(
                        face_landmarks
                        .landmark[index]
                        .x
                        * width
                    )

                    y = int(
                        face_landmarks
                        .landmark[index]
                        .y
                        * height
                    )

                    right_eye.append(
                        (x, y)
                    )


                    cv2.circle(

                        frame,

                        (x, y),

                        3,

                        (0, 255, 0),

                        -1
                    )


                # =================================================
                # EAR
                # =================================================

                left_ear = (
                    eye_aspect_ratio(
                        left_eye
                    )
                )

                right_ear = (
                    eye_aspect_ratio(
                        right_eye
                    )
                )

                ear = (
                    left_ear
                    + right_ear
                ) / 2.0


                current_ear = ear


                # =================================================
                # BASELINE
                # =================================================

                driver_baseline.update(
                    ear=ear
                )


                # =================================================
                # EAR TREND
                # =================================================

                ear_result = (
                    behaviour_analyzer
                    .update_ear(
                        ear
                    )
                )


                current_ear_trend = (
                    ear_result["trend"]
                )


                # =================================================
                # EYE CLOSURE
                # =================================================

                if ear < EAR_THRESHOLD:

                    eye_status = "CLOSED"

                    eye_closed_frames += 1


                    # ---------------------------------------------
                    # START CLOSURE
                    # ---------------------------------------------

                    if eye_closed_start is None:

                        eye_closed_start = (
                            time.time()
                        )


                    eyes_were_closed = True


                    current_closed_duration = (
                        time.time()
                        - eye_closed_start
                    )


                    # ---------------------------------------------
                    # DROWSINESS
                    # ---------------------------------------------

                    if (
                        current_closed_duration
                        >= DROWSINESS_DURATION
                    ):

                        drowsiness_active = True

                        alarm_status = "ON"


                        if not drowsiness_logged:

                            drowsiness_events += 1

                            drowsiness_logged = True


                        # Alarm
                        if alarm_ready:

                            if not pygame.mixer.music.get_busy():

                                pygame.mixer.music.play()


                    else:

                        drowsiness_active = False


                # =================================================
                # EYES OPEN
                # =================================================

                else:

                    eye_status = "OPEN"


                    # ---------------------------------------------
                    # BLINK DETECTION
                    # ---------------------------------------------

                    if eyes_were_closed:

                        closed_duration = (
                            current_closed_duration
                        )


                        last_closed_duration = (
                            closed_duration
                        )


                        # A normal blink:
                        #
                        # eyes closed for a short time
                        #
                        # AND
                        #
                        # enough frames were detected
                        #
                        if (

                            eye_closed_frames
                            >= MIN_BLINK_FRAMES

                            and

                            closed_duration
                            <= MAX_BLINK_DURATION

                            and

                            not drowsiness_active

                        ):

                            blink_count += 1


                            # Register blink in behaviour module
                            blink_result = (
                                behaviour_analyzer
                                .register_blink()
                            )


                            current_blink_pattern = (
                                blink_result[
                                    "pattern"
                                ]
                            )


                        # -----------------------------------------
                        # RESET EYE CLOSURE
                        # -----------------------------------------

                        eye_closed_start = None

                        eye_closed_frames = 0

                        eyes_were_closed = False

                        current_closed_duration = 0.0


                        # -----------------------------------------
                        # STOP DROWSINESS
                        # -----------------------------------------

                        drowsiness_active = False

                        drowsiness_logged = False


                        if alarm_ready:

                            pygame.mixer.music.stop()


                        alarm_status = "OFF"


                # =================================================
                # EYE STATE TO BEHAVIOUR MODULE
                # =================================================

                eye_closed = (
                    ear < EAR_THRESHOLD
                )

                behaviour_analyzer.update_eye_state(
                    eye_closed
                )


                # =================================================
                # DISTRACTION ANALYZER
                # =================================================

                distraction_result = (
                    behaviour_analyzer
                    .update_head_direction(
                        head_direction
                    )
                )


                # =================================================
                # TEMPORAL WINDOW
                # =================================================

                temporal_result = (
                    behaviour_analyzer
                    .update_temporal_window()
                )


                # =================================================
                # BLINK RESULT
                # =================================================

                blink_result = (
                    behaviour_analyzer
                    .get_blink_result()
                )


                current_blink_pattern = (
                    blink_result["pattern"]
                )


                # =================================================
                # RISK ENGINE
                # =================================================

                risk_result = (
                    risk_engine.calculate_risk(

                        ear_trend=
                        ear_result["trend"],

                        blink_pattern=
                        blink_result["pattern"],

                        eye_closed=
                        eye_closed,

                        closed_duration=
                        current_closed_duration,

                        is_distracted=
                        distraction_result[
                            "is_distracted"
                        ],

                        distraction_duration=
                        distraction_result[
                            "duration"
                        ],

                        temporal_history=
                        temporal_result[
                            "history"
                        ]
                    )
                )


                current_risk_score = (
                    risk_result["risk_score"]
                )

                current_risk_level = (
                    risk_result["risk_level"]
                )


                # =================================================
                # WARNING LEVEL
                # =================================================

                if drowsiness_active:

                    current_warning_level = (
                        "CRITICAL"
                    )

                elif current_risk_score >= 80:

                    current_warning_level = (
                        "CRITICAL"
                    )

                elif current_risk_score >= 60:

                    current_warning_level = (
                        "HIGH"
                    )

                elif current_risk_score >= 30:

                    current_warning_level = (
                        "MEDIUM"
                    )

                elif attention_warning:

                    current_warning_level = (
                        "MEDIUM"
                    )

                else:

                    current_warning_level = (
                        "NONE"
                    )


                # =================================================
                # EVENT MANAGER
                # =================================================

                event_type = None

                event_duration = 0.0


                if drowsiness_active:

                    event_type = "DROWSINESS"

                    event_duration = (
                        current_closed_duration
                    )


                elif attention_warning:

                    event_type = "DISTRACTION"

                    if attention_start is not None:

                        event_duration = (
                            time.time()
                            - attention_start
                        )


                if event_type is not None:

                    event_result = (
                        event_manager
                        .check_condition(

                            event_type,

                            current_risk_score,

                            event_duration
                        )
                    )


                    if event_result.get(
                        "event_confirmed",
                        False
                    ):

                        add_timeline_event(

                            event_result[
                                "event_type"
                            ],

                            event_result[
                                "risk_score"
                            ],

                            event_result[
                                "severity"
                            ],

                            event_result[
                                "duration"
                            ]
                        )


                # =================================================
                # SAFETY SCORE
                # =================================================

                safety_score = 100


                if attention_warning:

                    safety_score -= 30


                if drowsiness_active:

                    safety_score -= 50


                safety_score = max(
                    0,
                    safety_score
                )


                # =================================================
                # CAMERA DISPLAY
                # =================================================

                cv2.putText(

                    frame,

                    "AI DRIVER MONITORING SYSTEM",

                    (80, 35),

                    cv2.FONT_HERSHEY_SIMPLEX,

                    0.6,

                    (0, 255, 255),

                    2
                )


                # =================================================
                # STATUS
                # =================================================

                if drowsiness_active:

                    status = (
                        "DROWSINESS DETECTED"
                    )

                    status_color = (
                        0,
                        0,
                        255
                    )

                elif attention_warning:

                    status = (
                        "DRIVER DISTRACTED"
                    )

                    status_color = (
                        0,
                        165,
                        255
                    )

                elif eye_closed:

                    status = (
                        "EYES CLOSED"
                    )

                    status_color = (
                        0,
                        165,
                        255
                    )

                else:

                    status = "AWAKE"

                    status_color = (
                        0,
                        255,
                        0
                    )


                cv2.putText(

                    frame,

                    f"STATUS : {status}",

                    (20, 80),

                    cv2.FONT_HERSHEY_SIMPLEX,

                    0.8,

                    status_color,

                    2
                )


                # =================================================
                # EAR
                # =================================================

                cv2.putText(

                    frame,

                    f"EAR : {ear:.2f}",

                    (20, 115),

                    cv2.FONT_HERSHEY_SIMPLEX,

                    0.7,

                    (255, 255, 255),

                    2
                )


                # =================================================
                # BLINK COUNT
                # =================================================

                cv2.putText(

                    frame,

                    f"BLINKS : {blink_count}",

                    (20, 150),

                    cv2.FONT_HERSHEY_SIMPLEX,

                    0.7,

                    (255, 255, 0),

                    2
                )


                # =================================================
                # EYE TIMER
                # =================================================

                display_timer = (
                    current_closed_duration
                )


                cv2.putText(

                    frame,

                    f"EYE CLOSED : {display_timer:.1f} sec",

                    (20, 185),

                    cv2.FONT_HERSHEY_SIMPLEX,

                    0.7,

                    (255, 255, 255),

                    2
                )


                # =================================================
                # CAMERA
                # =================================================

                cv2.putText(

                    frame,

                    "CAMERA : ON",

                    (20, 220),

                    cv2.FONT_HERSHEY_SIMPLEX,

                    0.7,

                    (0, 255, 0),

                    2
                )


                # =================================================
                # AI MODEL
                # =================================================

                cv2.putText(

                    frame,

                    "AI MODEL : RUNNING",

                    (20, 255),

                    cv2.FONT_HERSHEY_SIMPLEX,

                    0.7,

                    (0, 255, 255),

                    2
                )


                # =================================================
                # FACE
                # =================================================

                cv2.putText(

                    frame,

                    "FACE : DETECTED",

                    (20, 290),

                    cv2.FONT_HERSHEY_SIMPLEX,

                    0.7,

                    (0, 255, 0),

                    2
                )


                # =================================================
                # EYES
                # =================================================

                cv2.putText(

                    frame,

                    f"EYES : {eye_status}",

                    (20, 325),

                    cv2.FONT_HERSHEY_SIMPLEX,

                    0.7,

                    (255, 255, 255),

                    2
                )


                # =================================================
                # ALARM
                # =================================================

                cv2.putText(

                    frame,

                    f"ALARM : {alarm_status}",

                    (20, 360),

                    cv2.FONT_HERSHEY_SIMPLEX,

                    0.7,

                    (
                        0,
                        0,
                        255
                    )
                    if alarm_status == "ON"
                    else
                    (
                        0,
                        255,
                        0
                    ),

                    2
                )


                # =================================================
                # HEAD
                # =================================================

                cv2.putText(

                    frame,

                    f"HEAD : {direction}",

                    (20, 395),

                    cv2.FONT_HERSHEY_SIMPLEX,

                    0.7,

                    direction_color,

                    2
                )


                # =================================================
                # SAFETY
                # =================================================

                cv2.putText(

                    frame,

                    f"SAFETY SCORE : {safety_score}%",

                    (20, 430),

                    cv2.FONT_HERSHEY_SIMPLEX,

                    0.7,

                    (0, 255, 0),

                    2
                )


                # =================================================
                # RISK SCORE
                # =================================================

                cv2.putText(

                    frame,

                    f"RISK SCORE : {current_risk_score:.0f}",

                    (20, 465),

                    cv2.FONT_HERSHEY_SIMPLEX,

                    0.7,

                    (255, 100, 255),

                    2
                )


                # =================================================
                # RISK LEVEL
                # =================================================

                cv2.putText(

                    frame,

                    f"RISK LEVEL : {current_risk_level}",

                    (20, 500),

                    cv2.FONT_HERSHEY_SIMPLEX,

                    0.7,

                    (255, 100, 255),

                    2
                )


                # =================================================
                # WARNING
                # =================================================

                cv2.putText(

                    frame,

                    f"WARNING : {current_warning_level}",

                    (20, 535),

                    cv2.FONT_HERSHEY_SIMPLEX,

                    0.7,

                    (0, 200, 255),

                    2
                )


                # =================================================
                # SESSION
                # =================================================

                session_seconds = int(
                    time.time()
                    - session_start
                )


                cv2.putText(

                    frame,

                    f"SESSION : {session_seconds} sec",

                    (20, 570),

                    cv2.FONT_HERSHEY_SIMPLEX,

                    0.65,

                    (255, 255, 255),

                    2
                )


        # ====================================================
        # NO FACE
        # ====================================================

        else:

            face_detected = False

            current_head_direction = (
                "NO FACE"
            )


            cv2.putText(

                frame,

                "FACE : NOT DETECTED",

                (20, 80),

                cv2.FONT_HERSHEY_SIMPLEX,

                0.8,

                (0, 0, 255),

                2
            )


            cv2.putText(

                frame,

                "Please position your face",

                (20, 120),

                cv2.FONT_HERSHEY_SIMPLEX,

                0.7,

                (0, 165, 255),

                2
            )


        # ====================================================
        # ENCODE FRAME
        # ====================================================

        success, buffer = cv2.imencode(
            ".jpg",
            frame
        )


        if not success:

            continue


        frame_bytes = (
            buffer.tobytes()
        )


        yield (

            b"--frame\r\n"

            b"Content-Type: image/jpeg\r\n\r\n"

            + frame_bytes

            + b"\r\n"
        )


# ============================================================
# HOME
# ============================================================

@app.route("/")
def home():

    return render_template(
        "index.html"
    )


# ============================================================
# VIDEO FEED
# ============================================================

@app.route("/video_feed")
def video_feed():

    return Response(

        generate_frames(),

        mimetype=
        "multipart/x-mixed-replace; boundary=frame"
    )


# ============================================================
# LIVE STATUS API
# ============================================================

@app.route("/status")
def status():

    return jsonify({

        "risk_score":
            current_risk_score,

        "risk_level":
            current_risk_level,

        "warning_level":
            current_warning_level,

        "ear":
            round(
                current_ear,
                3
            ),

        "ear_trend":
            current_ear_trend,

        "blink_pattern":
            current_blink_pattern,

        "total_blinks":
            blink_count,

        "head_direction":
            current_head_direction,

        "drowsiness_events":
            drowsiness_events,

        "distraction_events":
            distraction_count,

        "safety_score":
            safety_score,

        "face_detected":
            face_detected,

        "eye_status":
            eye_status,

        "alarm":
            alarm_status,

        "timeline_events":
            len(risk_timeline)
    })


# ============================================================
# SAVE REPORT
# ============================================================

def save_report():

    try:

        elapsed = int(
            time.time()
            - session_start
        )

        minutes = elapsed // 60

        seconds = elapsed % 60


        filename = (
            "driver_report.csv"
        )


        with open(

            filename,

            "w",

            newline=""

        ) as file:

            writer = csv.writer(file)


            writer.writerow([
                "AI DRIVER MONITORING SESSION REPORT"
            ])


            writer.writerow([])


            writer.writerow([
                "Session Duration",
                f"{minutes} min {seconds} sec"
            ])


            writer.writerow([
                "Total Blinks",
                blink_count
            ])


            writer.writerow([
                "Drowsiness Events",
                drowsiness_events
            ])


            writer.writerow([
                "Distraction Events",
                distraction_count
            ])


            writer.writerow([
                "Safety Score",
                f"{safety_score}%"
            ])


            writer.writerow([
                "Risk Score",
                current_risk_score
            ])


            writer.writerow([
                "Risk Level",
                current_risk_level
            ])


            writer.writerow([
                "Warning Level",
                current_warning_level
            ])


            writer.writerow([
                "EAR Trend",
                current_ear_trend
            ])


            writer.writerow([
                "Blink Pattern",
                current_blink_pattern
            ])


            writer.writerow([
                "Head Direction",
                current_head_direction
            ])


            writer.writerow([])


            writer.writerow([
                "RISK TIMELINE"
            ])


            writer.writerow([

                "Timestamp",

                "Event Type",

                "Risk Score",

                "Severity",

                "Duration"

            ])


            for event in risk_timeline:

                writer.writerow([

                    event[
                        "timestamp"
                    ],

                    event[
                        "event_type"
                    ],

                    event[
                        "risk_score"
                    ],

                    event[
                        "severity"
                    ],

                    event[
                        "duration"
                    ]
                ])


        print(
            f"Report saved: {filename}"
        )


    except Exception as e:

        print(
            "Report save error:",
            e
        )


# ============================================================
# CLEANUP
# ============================================================

def cleanup():

    try:

        camera.release()

    except Exception:
        pass


    try:

        face_mesh.close()

    except Exception:
        pass


    try:

        if alarm_ready:

            pygame.mixer.music.stop()

    except Exception:
        pass


    save_report()


atexit.register(
    cleanup
)


# ============================================================
# START FLASK
# ============================================================

if __name__ == "__main__":

    print()
    print(
        "============================================"
    )

    print(
        " AI DRIVER MONITORING SYSTEM"
    )

    print(
        "============================================"
    )

    print(
        "Camera      : READY"
    )

    print(
        "MediaPipe   : READY"
    )

    print(
        "Blink       : READY"
    )

    print(
        "Risk Engine : READY"
    )

    print(
        "Alarm       :",
        "READY"
        if alarm_ready
        else
        "NOT READY"
    )

    print(
        "============================================"
    )

    print()


    app.run(
        debug=True
    )