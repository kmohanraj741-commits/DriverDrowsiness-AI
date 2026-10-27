import time


class DriverBaseline:
    def __init__(self, calibration_duration=10):
        self.calibration_duration = calibration_duration

        self.start_time = None
        self.calibrating = False
        self.completed = False

        self.ear_values = []
        self.blink_intervals = []

        self.average_ear = 0.0
        self.average_blink_interval = 0.0

    def start_calibration(self):
        self.start_time = time.time()
        self.calibrating = True
        self.completed = False

        self.ear_values = []
        self.blink_intervals = []

    def update(self, ear=None, blink_interval=None):
        if not self.calibrating:
            return

        # Store EAR values
        if ear is not None and ear > 0:
            self.ear_values.append(ear)

        # Store blink interval
        if blink_interval is not None and blink_interval > 0:
            self.blink_intervals.append(blink_interval)

        # Check calibration time
        elapsed = time.time() - self.start_time

        if elapsed >= self.calibration_duration:
            self.finish_calibration()

    def finish_calibration(self):
        if self.ear_values:
            self.average_ear = sum(self.ear_values) / len(self.ear_values)

        if self.blink_intervals:
            self.average_blink_interval = (
                sum(self.blink_intervals) /
                len(self.blink_intervals)
            )

        self.calibrating = False
        self.completed = True

    def get_status(self):
        if self.calibrating:
            elapsed = time.time() - self.start_time
            remaining = max(
                0,
                self.calibration_duration - elapsed
            )

            return {
                "status": "CALIBRATING",
                "remaining": round(remaining, 1)
            }

        if self.completed:
            return {
                "status": "COMPLETED",
                "average_ear": round(self.average_ear, 3),
                "average_blink_interval": round(
                    self.average_blink_interval,
                    2
                )
            }

        return {
            "status": "NOT_STARTED"
        }