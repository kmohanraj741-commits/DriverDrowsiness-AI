// ============================================================
// DRIVER RISK MONITOR
// ============================================================

console.log("Driver Risk Monitor Started");


// ============================================================
// UPDATE RISK INFORMATION
// ============================================================

function updateRiskMonitor() {

    fetch("/status")

        .then(response => response.json())

        .then(data => {


            // ================================================
            // RISK SCORE
            // ================================================

            document.getElementById(
                "risk-score"
            ).textContent = data.risk_score;


            // ================================================
            // RISK LEVEL
            // ================================================

            document.getElementById(
                "risk-level"
            ).textContent = data.risk_level;


            // ================================================
            // WARNING LEVEL
            // ================================================

            document.getElementById(
                "warning-level"
            ).textContent = data.warning_level;


            // ================================================
            // EAR TREND
            // ================================================

            document.getElementById(
                "ear-trend"
            ).textContent = data.ear_trend;


            // ================================================
            // BLINK PATTERN
            // ================================================

            document.getElementById(
                "blink-pattern"
            ).textContent = data.blink_pattern;


            // ================================================
            // HEAD DIRECTION
            // ================================================

            document.getElementById(
                "head-direction"
            ).textContent = data.head_direction;


            // ================================================
            // DROWSINESS EVENTS
            // ================================================

            document.getElementById(
                "drowsiness-events"
            ).textContent = data.drowsiness_events;


            // ================================================
            // DISTRACTION EVENTS
            // ================================================

            document.getElementById(
                "distraction-events"
            ).textContent = data.distraction_events;


            // ================================================
            // TOTAL BLINKS
            // ================================================

            document.getElementById(
                "total-blinks"
            ).textContent = data.total_blinks;

        })

        .catch(error => {

            console.log(
                "Status update error:",
                error
            );

        });

}


// ============================================================
// UPDATE EVERY 500 MILLISECONDS
// ============================================================

setInterval(
    updateRiskMonitor,
    500
);


// ============================================================
// FIRST UPDATE
// ============================================================

updateRiskMonitor();