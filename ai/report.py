# ============================================================
# DRIVER SESSION REPORT
# ============================================================


class DriverSessionReport:

    def __init__(self, timeline):

        self.timeline = timeline

    # ========================================================
    # GENERATE REPORT
    # ========================================================

    def generate(self):

        data = self.timeline.get_result()

        highest_risk = data["highest_risk"]
        average_risk = data["average_risk"]

        # Determine overall status
        if highest_risk >= 80:
            overall_status = "CRITICAL"

        elif highest_risk >= 60:
            overall_status = "HIGH"

        elif highest_risk >= 30:
            overall_status = "MEDIUM"

        else:
            overall_status = "LOW"

        return {

            "session_duration":
                data["session_duration"],

            "total_events":
                data["total_events"],

            "drowsiness_events":
                data["drowsiness_events"],

            "distraction_events":
                data["distraction_events"],

            "average_risk":
                average_risk,

            "highest_risk":
                highest_risk,

            "overall_status":
                overall_status,

            "events":
                data["events"]
        }

    # ========================================================
    # PRINT REPORT
    # ========================================================

    def print_report(self):

        report = self.generate()

        print()
        print("=" * 50)
        print("          DRIVER SESSION REPORT")
        print("=" * 50)

        print(
            "Session Duration :",
            report["session_duration"],
            "seconds"
        )

        print(
            "Total Events     :",
            report["total_events"]
        )

        print(
            "Drowsiness Events:",
            report["drowsiness_events"]
        )

        print(
            "Distraction Events:",
            report["distraction_events"]
        )

        print(
            "Average Risk     :",
            report["average_risk"]
        )

        print(
            "Highest Risk     :",
            report["highest_risk"]
        )

        print(
            "Overall Status   :",
            report["overall_status"]
        )

        print("=" * 50)

        print()
        print("EVENT TIMELINE")
        print("-" * 50)

        for event in report["events"]:

            print(
                event["timestamp"],
                "|",
                event["event_type"],
                "| Risk:",
                event["risk_score"],
                "|",
                event["severity"],
                "| Duration:",
                event["duration"]
            )

        print("-" * 50)