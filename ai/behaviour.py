import time
from collections import deque


# ============================================================
# EAR TREND ANALYZER
# ============================================================

class EARTrendAnalyzer:

    def __init__(self, window_size=30):

        self.window_size = window_size

        self.ear_history = deque(
            maxlen=window_size
        )

        self.current_ear = 0.0
        self.average_ear = 0.0
        self.trend = "STABLE"

    def update(self, ear):

        if ear is None or ear <= 0:
            return self.get_result()

        self.current_ear = ear

        self.ear_history.append(ear)

        if len(self.ear_history) > 0:

            self.average_ear = (
                sum(self.ear_history)
                / len(self.ear_history)
            )

        if len(self.ear_history) >= 10:

            recent = list(
                self.ear_history
            )

            middle = len(recent) // 2

            first_half = recent[:middle]

            second_half = recent[middle:]

            first_average = (
                sum(first_half)
                / len(first_half)
            )

            second_average = (
                sum(second_half)
                / len(second_half)
            )

            difference = (
                second_average
                - first_average
            )

            if difference < -0.015:

                self.trend = "DECREASING"

            elif difference > 0.015:

                self.trend = "INCREASING"

            else:

                self.trend = "STABLE"

        return self.get_result()

    def get_result(self):

        return {

            "current_ear":
                round(
                    self.current_ear,
                    3
                ),

            "average_ear":
                round(
                    self.average_ear,
                    3
                ),

            "trend":
                self.trend,

            "samples":
                len(
                    self.ear_history
                )
        }


# ============================================================
# BLINK PATTERN ANALYZER
# ============================================================

class BlinkPatternAnalyzer:

    def __init__(self, window_size=10):

        self.window_size = window_size

        self.blink_times = deque(
            maxlen=window_size
        )

        self.blink_intervals = deque(
            maxlen=window_size
        )

        self.last_blink_time = None

        self.total_blinks = 0

        self.average_interval = 0.0

        self.pattern = "NORMAL"

    def register_blink(self):

        current_time = time.time()

        self.total_blinks += 1

        self.blink_times.append(
            current_time
        )

        if self.last_blink_time is not None:

            interval = (
                current_time
                - self.last_blink_time
            )

            if 0.2 < interval < 60:

                self.blink_intervals.append(
                    interval
                )

        self.last_blink_time = current_time

        self.calculate_pattern()

        return self.get_result()

    def calculate_pattern(self):

        if len(self.blink_intervals) < 3:

            self.pattern = "INSUFFICIENT_DATA"

            return

        intervals = list(
            self.blink_intervals
        )

        self.average_interval = (
            sum(intervals)
            / len(intervals)
        )

        variation = (
            max(intervals)
            - min(intervals)
        )

        if self.average_interval < 1.0:

            self.pattern = "FREQUENT"

        elif self.average_interval > 8.0:

            self.pattern = "INFREQUENT"

        elif variation > 6.0:

            self.pattern = "IRREGULAR"

        else:

            self.pattern = "NORMAL"

    def get_result(self):

        return {

            "total_blinks":
                self.total_blinks,

            "average_interval":
                round(
                    self.average_interval,
                    2
                ),

            "pattern":
                self.pattern,

            "recent_intervals":
                [
                    round(
                        interval,
                        2
                    )
                    for interval
                    in self.blink_intervals
                ]
        }


# ============================================================
# DISTRACTION DURATION ANALYZER
# ============================================================

class DistractionDurationAnalyzer:

    def __init__(
        self,
        warning_duration=2.0
    ):

        self.warning_duration = (
            warning_duration
        )

        self.distraction_start = None

        self.current_duration = 0.0

        self.is_distracted = False

        self.distraction_confirmed = False

        self.direction = "CENTER"

        self.total_distraction_events = 0

    def update(
        self,
        head_direction
    ):

        current_time = time.time()

        if head_direction is None:

            head_direction = "CENTER"

        head_direction = (
            head_direction.upper()
        )

        # ----------------------------------------------------
        # Driver looking away
        # ----------------------------------------------------

        if head_direction != "CENTER":

            if self.distraction_start is None:

                self.distraction_start = (
                    current_time
                )

                self.direction = (
                    head_direction
                )

                self.is_distracted = True

                self.distraction_confirmed = False

            elif (
                head_direction
                != self.direction
            ):

                self.distraction_start = (
                    current_time
                )

                self.direction = (
                    head_direction
                )

                self.distraction_confirmed = False

            self.current_duration = (
                current_time
                - self.distraction_start
            )

            if (
                self.current_duration
                >= self.warning_duration
                and
                not self.distraction_confirmed
            ):

                self.distraction_confirmed = True

                self.total_distraction_events += 1

        # ----------------------------------------------------
        # Driver looking forward
        # ----------------------------------------------------

        else:

            self.distraction_start = None

            self.current_duration = 0.0

            self.is_distracted = False

            self.distraction_confirmed = False

            self.direction = "CENTER"

        return self.get_result()

    def get_result(self):

        return {

            "direction":
                self.direction,

            "is_distracted":
                self.is_distracted,

            "duration":
                round(
                    self.current_duration,
                    2
                ),

            "confirmed":
                self.distraction_confirmed,

            "total_events":
                self.total_distraction_events
        }


# ============================================================
# TEMPORAL BEHAVIOUR WINDOW
# ============================================================

class TemporalBehaviourWindow:

    def __init__(
        self,
        window_seconds=10
    ):

        self.window_seconds = (
            window_seconds
        )

        # Store recent behaviour records
        self.history = deque()

    def add_record(
        self,
        ear_result=None,
        blink_result=None,
        distraction_result=None,
        eye_closed=False
    ):

        current_time = time.time()

        record = {

            "timestamp":
                current_time,

            "ear":
                ear_result,

            "blink":
                blink_result,

            "distraction":
                distraction_result,

            "eye_closed":
                eye_closed
        }

        self.history.append(record)

        self.cleanup()

        return self.get_result()

    def cleanup(self):

        current_time = time.time()

        while self.history:

            oldest_record = self.history[0]

            age = (
                current_time
                - oldest_record["timestamp"]
            )

            if age > self.window_seconds:

                self.history.popleft()

            else:

                break

    def get_recent_records(self):

        self.cleanup()

        return list(
            self.history
        )

    def get_result(self):

        self.cleanup()

        return {

            "window_seconds":
                self.window_seconds,

            "records":
                len(self.history),

            "history":
                list(self.history)
        }


# ============================================================
# COMBINED BEHAVIOUR ANALYZER
# ============================================================

class BehaviourAnalyzer:

    def __init__(self):

        # ----------------------------------------------------
        # EAR Trend
        # ----------------------------------------------------

        self.ear_analyzer = (
            EARTrendAnalyzer(
                window_size=30
            )
        )

        # ----------------------------------------------------
        # Blink Pattern
        # ----------------------------------------------------

        self.blink_analyzer = (
            BlinkPatternAnalyzer(
                window_size=10
            )
        )

        # ----------------------------------------------------
        # Distraction Duration
        # ----------------------------------------------------

        self.distraction_analyzer = (
            DistractionDurationAnalyzer(
                warning_duration=2.0
            )
        )

        # ----------------------------------------------------
        # Temporal Behaviour
        # ----------------------------------------------------

        self.temporal_window = (
            TemporalBehaviourWindow(
                window_seconds=10
            )
        )

        # Current eye state
        self.eye_closed = False

    # ========================================================
    # UPDATE EAR
    # ========================================================

    def update_ear(self, ear):

        return self.ear_analyzer.update(
            ear
        )

    # ========================================================
    # REGISTER BLINK
    # ========================================================

    def register_blink(self):

        return (
            self.blink_analyzer
            .register_blink()
        )

    # ========================================================
    # UPDATE HEAD DIRECTION
    # ========================================================

    def update_head_direction(
        self,
        head_direction
    ):

        return (
            self.distraction_analyzer
            .update(
                head_direction
            )
        )

    # ========================================================
    # UPDATE EYE STATE
    # ========================================================

    def update_eye_state(
        self,
        eye_closed
    ):

        self.eye_closed = bool(
            eye_closed
        )

    # ========================================================
    # UPDATE TEMPORAL WINDOW
    # ========================================================

    def update_temporal_window(self):

        ear_result = (
            self.ear_analyzer
            .get_result()
        )

        blink_result = (
            self.blink_analyzer
            .get_result()
        )

        distraction_result = (
            self.distraction_analyzer
            .get_result()
        )

        return (
            self.temporal_window
            .add_record(
                ear_result=ear_result,
                blink_result=blink_result,
                distraction_result=distraction_result,
                eye_closed=self.eye_closed
            )
        )

    # ========================================================
    # GET EAR RESULT
    # ========================================================

    def get_ear_result(self):

        return (
            self.ear_analyzer
            .get_result()
        )

    # ========================================================
    # GET BLINK RESULT
    # ========================================================

    def get_blink_result(self):

        return (
            self.blink_analyzer
            .get_result()
        )

    # ========================================================
    # GET DISTRACTION RESULT
    # ========================================================

    def get_distraction_result(self):

        return (
            self.distraction_analyzer
            .get_result()
        )

    # ========================================================
    # GET TEMPORAL RESULT
    # ========================================================

    def get_temporal_result(self):

        return (
            self.temporal_window
            .get_result()
        )

    # ========================================================
    # GET ALL RESULTS
    # ========================================================

    def get_result(self):

        return {

            "ear":
                self.get_ear_result(),

            "blink":
                self.get_blink_result(),

            "distraction":
                self.get_distraction_result(),

            "temporal":
                self.get_temporal_result()
        }