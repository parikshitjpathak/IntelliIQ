# ==========================================================
# EARLY WARNING ENGINE
# ==========================================================
# Purpose:
# Detect early signals of potential issues by analyzing
# incident trends in the knowledgeBase table.
#
# Logic:
# - Compare last 24 hours vs previous 24 hours
# - Identify:
#     1. New issues (not seen yesterday)
#     2. Increasing issues (spike detection)
#
# Output:
# Returns a list of warning objects:
# [
#   {
#       "incident": "...",
#       "message": "...",
#       "last_count": int,
#       "prev_count": int
#   }
# ]
# ==========================================================
import os
import sqlite3
from datetime import datetime, timedelta

# ==========================================================
# CONFIGURATION
# ==========================================================

#DB_PATH = r"D:\pythonPractice\IntelliIQ.db"
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_NAME = os.path.join(BASE_DIR, "IntelliIQ.db")


# ==========================================================
# MAIN FUNCTION
# ==========================================================

def get_early_warnings():
    """
    Fetch early warning signals based on incident trends.

    Returns:
        List of warning dictionaries
    """

    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()

    # ------------------------------------------------------
    # TIME WINDOWS
    # ------------------------------------------------------
    # last_24  → today
    # prev_24  → yesterday

    today = datetime.now()
    last_24 = (today - timedelta(days=1)).strftime("%Y-%m-%d")
    prev_24 = (today - timedelta(days=2)).strftime("%Y-%m-%d")

    # ------------------------------------------------------
    # FETCH INCIDENT COUNT - LAST 24 HOURS
    # ------------------------------------------------------
    cursor.execute("""
        SELECT Incident, COUNT(*)
        FROM knowledgeBase
        WHERE Date >= ?
        GROUP BY Incident
    """, (last_24,))

    last_data = cursor.fetchall()

    # ------------------------------------------------------
    # FETCH INCIDENT COUNT - PREVIOUS 24 HOURS
    # ------------------------------------------------------
    cursor.execute("""
        SELECT Incident, COUNT(*)
        FROM knowledgeBase
        WHERE Date >= ? AND Date < ?
        GROUP BY Incident
    """, (prev_24, last_24))

    prev_data = dict(cursor.fetchall())

    conn.close()

    # ------------------------------------------------------
    # ANALYZE TRENDS
    # ------------------------------------------------------
    warnings = []

    for incident, count_last in last_data:

        # Get previous count (default = 0)
        count_prev = prev_data.get(incident, 0)

        # --------------------------------------------------
        # DETECTION RULE
        # --------------------------------------------------
        # Trigger warning if:
        # 1. At least 2 occurrences today (basic signal)
        # OR
        # 2. Increasing trend compared to yesterday

        if count_last >= 2 or (count_prev > 0 and count_last > count_prev):

            # --------------------------------------------------
            # MESSAGE FORMATTING (IMPORTANT FOR UX)
            # --------------------------------------------------

            if count_prev == 0:
                message = f"{incident} observed {count_last} time(s) today"
            else:
                message = f"{incident} increased from {count_prev} → {count_last}"

            # --------------------------------------------------
            # BUILD WARNING OBJECT
            # --------------------------------------------------
            warnings.append({
                "incident": incident,
                "message": message,
                "last_count": count_last,
                "prev_count": count_prev
            })

    return warnings