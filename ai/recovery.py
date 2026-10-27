import time


# ============================================================
# RISK RECOVERY + ADAPTIVE WARNING
# ============================================================

class RiskRecoveryManager:

    def __init__(
        self,
        recovery_rate=5.0,
        recovery_delay=2.0
    ):

        # How quickly risk decreases during normal behaviour
        self.recovery_rate = recovery_rate

        # Driver must remain normal for this duration
        self.recovery_delay = recovery_delay

        self.current_risk = 0.0
        self.recovered_risk = 0.0

        self.normal_start_time = None

        self.warning_level = "NONE"

        self.alarm_active = False

        self.recovery_active = False

    # ========================================================
    # UPDATE RISK
    # ========================================================

    def update(
        self,
        risk_score,
        driver_normal=True
    ):

        current_time = time.time()

        risk_score = max(
            0.0,
            min(
                float(risk_score),
                100.0
            )
        )

        self.current_risk = risk_score

        # ----------------------------------------------------
        # HIGH RISK / ABNORMAL CONDITION
        # ----------------------------------------------------

        if not driver_normal:

            self.normal_start_time = None

            self.recovery_active = False

            self.recovered_risk = risk_score

        # ----------------------------------------------------
        # NORMAL CONDITION
        # ----------------------------------------------------

        else:

            if self.normal_start_time is None:

                self.normal_start_time = current_time

            normal_duration = (
                current_time
                - self.normal_start_time
            )

            # Start recovery only after stable normal behaviour
            if normal_duration >= self.recovery_delay:

                self.recovery_active = True

                self.recovered_risk = max(
                    0.0,
                    self.recovered_risk
                    - self.recovery_rate
                )

        # Update warning
        self.warning_level = (
            self.calculate_warning_level(
                self.recovered_risk
            )
        )

        # Update alarm
        self.update_alarm()

        return self.get_result()

    # ========================================================
    # WARNING LEVEL
    # ========================================================

    def calculate_warning_level(
        self,
        risk_score
    ):

        if risk_score >= 80:

            return "CRITICAL"

        elif risk_score >= 60:

            return "HIGH"

        elif risk_score >= 30:

            return "MEDIUM"

        elif risk_score > 0:

            return "LOW"

        return "NONE"

    # ========================================================
    # ALARM CONTROL
    # ========================================================

    def update_alarm(self):

        if self.warning_level == "CRITICAL":

            self.alarm_active = True

        elif self.warning_level == "HIGH":

            self.alarm_active = True

        elif self.warning_level == "MEDIUM":

            self.alarm_active = False

        else:

            self.alarm_active = False

    # ========================================================
    # RESET
    # ========================================================

    def reset(self):

        self.current_risk = 0.0

        self.recovered_risk = 0.0

        self.normal_start_time = None

        self.warning_level = "NONE"

        self.alarm_active = False

        self.recovery_active = False

    # ========================================================
    # RESULT
    # ========================================================

    def get_result(self):

        normal_duration = 0.0

        if self.normal_start_time is not None:

            normal_duration = (
                time.time()
                - self.normal_start_time
            )

        return {

            "current_risk":
                round(
                    self.current_risk,
                    2
                ),

            "recovered_risk":
                round(
                    self.recovered_risk,
                    2
                ),

            "warning_level":
                self.warning_level,

            "alarm_active":
                self.alarm_active,

            "recovery_active":
                self.recovery_active,

            "normal_duration":
                round(
                    normal_duration,
                    2
                )
        }