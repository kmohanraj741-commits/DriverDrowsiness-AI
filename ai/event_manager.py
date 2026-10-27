import time


class EventManager:

    def __init__(self, confirmation_time=1.5):

        self.confirmation_time = confirmation_time

        self.pending_event = None
        self.pending_start = None

        self.total_events = 0

        self.last_event = None
        self.last_event_time = None

    # ========================================================
    # CHECK ABNORMAL CONDITION
    # ========================================================

    def check_condition(
        self,
        event_type,
        risk_score,
        duration=0.0
    ):

        current_time = time.time()

        # ----------------------------------------
        # No abnormal condition
        # ----------------------------------------

        if risk_score < 30:

            self.reset_pending()

            return self.get_result()

        # ----------------------------------------
        # Start a new pending event
        # ----------------------------------------

        if self.pending_event != event_type:

            self.pending_event = event_type

            self.pending_start = current_time

            return self.get_result()

        # ----------------------------------------
        # Calculate confirmation duration
        # ----------------------------------------

        elapsed = (
            current_time
            - self.pending_start
        )

        # ----------------------------------------
        # Confirm event
        # ----------------------------------------

        if elapsed >= self.confirmation_time:

            severity = self.calculate_severity(
                risk_score,
                duration
            )

            # Prevent repeated logging
            if (
                self.last_event != event_type
                or
                self.last_event_time is None
                or
                current_time
                - self.last_event_time > 3
            ):

                self.total_events += 1

                self.last_event = event_type

                self.last_event_time = current_time

                return {
                    "event_confirmed": True,
                    "event_type": event_type,
                    "severity": severity,
                    "risk_score": round(
                        risk_score,
                        2
                    ),
                    "duration": round(
                        duration,
                        2
                    ),
                    "total_events":
                        self.total_events
                }

        return self.get_result()

    # ========================================================
    # SEVERITY
    # ========================================================

    def calculate_severity(
        self,
        risk_score,
        duration
    ):

        if risk_score >= 80 or duration >= 5:

            return "CRITICAL"

        elif risk_score >= 60 or duration >= 3:

            return "HIGH"

        elif risk_score >= 30 or duration >= 1.5:

            return "MEDIUM"

        return "LOW"

    # ========================================================
    # RESET
    # ========================================================

    def reset_pending(self):

        self.pending_event = None

        self.pending_start = None

    # ========================================================
    # RESULT
    # ========================================================

    def get_result(self):

        return {

            "event_confirmed": False,

            "event_type":
                self.pending_event,

            "severity":
                "NONE",

            "risk_score":
                0,

            "duration":
                0,

            "total_events":
                self.total_events
        }