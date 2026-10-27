# ============================================================
# MULTI-SIGNAL DRIVER RISK ENGINE
# ============================================================


class MultiSignalRiskEngine:

    def __init__(self):

        # Current risk score
        self.risk_score = 0.0

        # Current risk level
        self.risk_level = "LOW"

        # Individual signal scores
        self.ear_score = 0.0
        self.blink_score = 0.0
        self.eye_closure_score = 0.0
        self.distraction_score = 0.0
        self.temporal_score = 0.0

    # ========================================================
    # EAR TREND SCORE
    # ========================================================

    def calculate_ear_score(
        self,
        ear_trend
    ):

        if ear_trend == "DECREASING":

            return 20

        elif ear_trend == "STABLE":

            return 0

        elif ear_trend == "INCREASING":

            return 0

        return 0

    # ========================================================
    # BLINK PATTERN SCORE
    # ========================================================

    def calculate_blink_score(
        self,
        blink_pattern
    ):

        if blink_pattern == "FREQUENT":

            return 15

        elif blink_pattern == "INFREQUENT":

            return 15

        elif blink_pattern == "IRREGULAR":

            return 10

        return 0

    # ========================================================
    # EYE CLOSURE SCORE
    # ========================================================

    def calculate_eye_closure_score(
        self,
        eye_closed,
        closed_duration
    ):

        if not eye_closed:

            return 0

        if closed_duration >= 3.0:

            return 35

        elif closed_duration >= 2.0:

            return 25

        elif closed_duration >= 1.0:

            return 10

        return 0

    # ========================================================
    # DISTRACTION SCORE
    # ========================================================

    def calculate_distraction_score(
        self,
        is_distracted,
        distraction_duration
    ):

        if not is_distracted:

            return 0

        if distraction_duration >= 5.0:

            return 25

        elif distraction_duration >= 3.0:

            return 20

        elif distraction_duration >= 2.0:

            return 15

        elif distraction_duration >= 1.0:

            return 5

        return 0

    # ========================================================
    # TEMPORAL SCORE
    # ========================================================

    def calculate_temporal_score(
        self,
        temporal_history
    ):

        if not temporal_history:

            return 0

        # Count recent eye-closure records
        closed_count = 0

        # Count recent distraction records
        distraction_count = 0

        for record in temporal_history:

            if record.get(
                "eye_closed",
                False
            ):

                closed_count += 1

            distraction = record.get(
                "distraction"
            )

            if distraction:

                if distraction.get(
                    "is_distracted",
                    False
                ):

                    distraction_count += 1

        score = 0

        # Repeated eye closure
        if closed_count >= 5:

            score += 15

        elif closed_count >= 3:

            score += 10

        # Repeated distraction
        if distraction_count >= 5:

            score += 10

        elif distraction_count >= 3:

            score += 5

        return min(score, 20)

    # ========================================================
    # CALCULATE TOTAL RISK
    # ========================================================

    def calculate_risk(
        self,
        ear_trend="STABLE",
        blink_pattern="NORMAL",
        eye_closed=False,
        closed_duration=0.0,
        is_distracted=False,
        distraction_duration=0.0,
        temporal_history=None
    ):

        # Calculate individual scores
        self.ear_score = (
            self.calculate_ear_score(
                ear_trend
            )
        )

        self.blink_score = (
            self.calculate_blink_score(
                blink_pattern
            )
        )

        self.eye_closure_score = (
            self.calculate_eye_closure_score(
                eye_closed,
                closed_duration
            )
        )

        self.distraction_score = (
            self.calculate_distraction_score(
                is_distracted,
                distraction_duration
            )
        )

        self.temporal_score = (
            self.calculate_temporal_score(
                temporal_history
            )
        )

        # ----------------------------------------------------
        # Combine all signals
        # ----------------------------------------------------

        total = (
            self.ear_score
            + self.blink_score
            + self.eye_closure_score
            + self.distraction_score
            + self.temporal_score
        )

        # Limit score to 100
        self.risk_score = min(
            max(total, 0),
            100
        )

        # Determine risk level
        self.risk_level = (
            self.get_risk_level(
                self.risk_score
            )
        )

        return self.get_result()

    # ========================================================
    # RISK LEVEL
    # ========================================================

    def get_risk_level(
        self,
        score
    ):

        if score >= 80:

            return "CRITICAL"

        elif score >= 60:

            return "HIGH"

        elif score >= 30:

            return "MEDIUM"

        else:

            return "LOW"

    # ========================================================
    # RESULT
    # ========================================================

    def get_result(self):

        return {

            "risk_score":
                round(
                    self.risk_score,
                    2
                ),

            "risk_level":
                self.risk_level,

            "signals": {

                "ear_trend":
                    self.ear_score,

                "blink_pattern":
                    self.blink_score,

                "eye_closure":
                    self.eye_closure_score,

                "distraction":
                    self.distraction_score,

                "temporal":
                    self.temporal_score
            }
        }