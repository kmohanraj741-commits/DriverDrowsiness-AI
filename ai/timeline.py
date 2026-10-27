import time
from datetime import datetime


# ============================================================
# DRIVER RISK TIMELINE
# ============================================================

class RiskTimeline:

    def __init__(self):

        self.events = []

        self.session_start = time.time()

    # ========================================================
    # ADD EVENT
    # ========================================================

    def add_event(
        self,
        event_type,
        risk_score,
        severity,
        duration=0.0
    ):

        current_time = time.time()

        event = {

            "timestamp":
                datetime.now().strftime(
                    "%Y-%m-%d %H:%M:%S"
                ),

            "event_type":
                event_type,

            "risk_score":
                round(
                    float(risk_score),
                    2
                ),

            "severity":
                severity,

            "duration":
                round(
                    float(duration),
                    2
                )
        }

        self.events.append(event)

        return event

    # ========================================================
    # GET ALL EVENTS
    # ========================================================

    def get_events(self):

        return self.events

    # ========================================================
    # TOTAL EVENTS
    # ========================================================

    def get_total_events(self):

        return len(self.events)

    # ========================================================
    # COUNT EVENT TYPE
    # ========================================================

    def count_event_type(
        self,
        event_type
    ):

        count = 0

        for event in self.events:

            if (
                event["event_type"]
                == event_type
            ):

                count += 1

        return count

    # ========================================================
    # AVERAGE RISK
    # ========================================================

    def get_average_risk(self):

        if not self.events:

            return 0.0

        total = sum(
            event["risk_score"]
            for event in self.events
        )

        return round(
            total / len(self.events),
            2
        )

    # ========================================================
    # HIGHEST RISK
    # ========================================================

    def get_highest_risk(self):

        if not self.events:

            return 0.0

        return max(
            event["risk_score"]
            for event in self.events
        )

    # ========================================================
    # SESSION DURATION
    # ========================================================

    def get_session_duration(self):

        duration = (
            time.time()
            - self.session_start
        )

        return round(
            duration,
            2
        )

    # ========================================================
    # COMPLETE RESULT
    # ========================================================

    def get_result(self):

        return {

            "session_duration":
                self.get_session_duration(),

            "total_events":
                self.get_total_events(),

            "drowsiness_events":
                self.count_event_type(
                    "DROWSINESS"
                ),

            "distraction_events":
                self.count_event_type(
                    "DISTRACTION"
                ),

            "average_risk":
                self.get_average_risk(),

            "highest_risk":
                self.get_highest_risk(),

            "events":
                self.get_events()
        }

    # ========================================================
    # RESET SESSION
    # ========================================================

    def reset(self):

        self.events = []

        self.session_start = time.time()