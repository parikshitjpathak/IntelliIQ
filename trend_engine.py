# ==========================================================
# FUNCTION: calculate_trends
# Purpose:
# - Calculate incident trend distribution
# - Generate trend message
# ==========================================================

from datetime import datetime
import os


def calculate_trends(matches, frequency):

    now = datetime.now()

    count_1d = 0
    count_3d = 0
    count_5d = 0
    count_7d = 0
    count_older = 0

    for m in matches:
        try:
            row = m[0]
            date_str = row[5]

            incident_date = datetime.strptime(date_str, "%Y-%m-%d")
            days_diff = (now - incident_date).days

            if days_diff <= 1:
                count_1d += 1

            elif days_diff <= 3:
                count_3d += 1

            elif days_diff <= 5:
                count_5d += 1

            elif days_diff <= 7:
                count_7d += 1

            else:
                count_older += 1

        except Exception as e:
            print("Trend error:", e)
            continue

    # Trend message
    if frequency == 0:
        trend_message = "No historical incidents found — this appears to be a new issue"

    elif count_3d >= 0.8 * frequency:
        trend_message = "⚠️ High concentration of incidents in the last 3 days — possible spike"

    elif count_7d >= 0.9 * frequency:
        trend_message = "⚠️ Majority of incidents are recent — recurring issue"

    elif count_1d >= 3 and count_1d >= 0.5 * frequency:
        trend_message = "⚠️ Multiple incidents in last 24 hours — possible spike"

    else:
        trend_message = "Incident occurrence is distributed over time"

    return count_1d, count_3d, count_5d, count_7d, count_older, trend_message

# ==========================================================
# END FUNCTION
# ==========================================================

# ==========================================================
# PROBLEM TICKET DETECTION ENGINE
# ==========================================================
# PURPOSE:
# - Detect recurring incidents
# - Identify candidates for problem tickets
# ==========================================================

import sqlite3
from datetime import datetime, timedelta

#DB_PATH = r"D:\pythonPractice\IntelliIQ.db"

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_NAME = os.path.join(BASE_DIR, "IntelliIQ.db")


def get_recurring_issues(days=5, threshold=2):
    """
    Detect recurring incidents within a time window

    Args:
        days (int): lookback window
        threshold (int): minimum occurrence count

    Returns:
        list of recurring issues
    """

    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()

    # Calculate date window
    cutoff_date = (datetime.now() - timedelta(days=days)).strftime("%Y-%m-%d")
    print("Recurring Issues Window:", days)
    print("Cutoff Date:", cutoff_date)

    cursor.execute("""
        SELECT Incident, COUNT(*) as count
        FROM knowledgeBase
        WHERE Date >= ?
        GROUP BY Incident
        HAVING count >= ?
        ORDER BY count DESC
    """, (cutoff_date, threshold))

    rows = cursor.fetchall()
    conn.close()

    results = []

    for r in rows:
        results.append({
            "incident": r[0],
            "count": r[1],
            "window_days": days
        })

    return results

