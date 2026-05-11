#===== required imports for performance service =====
import sqlite3
import os
from datetime import datetime
#==== imports end =====
#from pcAnalyser import DB_NAME

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_NAME = os.path.join(BASE_DIR, "IntelliIQ.db")

#===== fetch top performers from DB (Phase 3)=====
def get_top_performers():

    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()

    result = {
        "weekly": [],
        "monthly": [],
        "quarterly": []
    }

    for period in ["weekly", "monthly", "quarterly"]:

        cursor.execute("""
            SELECT analyst_name, resolved_count, sla_met_count, sla_percentage
            FROM top_performers
            WHERE period_type = ?
            ORDER BY sla_percentage DESC, resolved_count DESC
            LIMIT 3
        """, (period,))

        rows = cursor.fetchall()

        result[period] = [
            {
                "name": r[0],
                "resolved": r[1],
                "sla_met": r[2],
                "sla_percent": r[3]
            }
            for r in rows
        ]

    conn.close()
    return result
#==== top performers fetch ends========

#===== fetch full analyst performance (Phase 4A)=====
def get_analyst_performance():

    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()

    cursor.execute("""
        SELECT analyst_name, period_type, resolved_count, sla_met_count, sla_percentage
        FROM analyst_performance_data
        ORDER BY period_type, sla_percentage DESC
    """)

    rows = cursor.fetchall()
    conn.close()

    performance = {
        "weekly": [],
        "monthly": [],
        "quarterly": []
    }

    for r in rows:
        record = {
            "name": r[0],
            "resolved": r[2],
            "sla_met": r[3],
            "sla_percent": r[4]
        }

        if r[1] == "weekly":
            performance["weekly"].append(record)
        elif r[1] == "monthly":
            performance["monthly"].append(record)
        elif r[1] == "quarterly":
            performance["quarterly"].append(record)

    return performance
#==== analyst performance fetch ends========
#===== analyst insights generator (Phase 4B)=====
def generate_analyst_insights():

    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()

    insights = []

    # Get latest WEEKLY data only (for now)
    cursor.execute("""
        SELECT analyst_name, resolved_count, sla_percentage
        FROM analyst_performance_data
        WHERE period_type = 'weekly'
        ORDER BY period_end DESC
    """)

    rows = cursor.fetchall()
    conn.close()

    if not rows:
        return ["No performance data available"]

    # Convert to usable format
    data = [
        {
            "name": r[0],
            "resolved": r[1],
            "sla": r[2]
        }
        for r in rows
    ]

    # ================= INSIGHT 1 — Highest workload =================
    max_resolved = max(data, key=lambda x: x["resolved"])
    insights.append(f"⚠️ {max_resolved['name']} has highest workload ({max_resolved['resolved']} tickets)")

    # ================= INSIGHT 2 — Best quality =================
    best_sla = max(data, key=lambda x: x["sla"])
    insights.append(f"✅ {best_sla['name']} has best SLA performance ({best_sla['sla']}%)")

    # ================= INSIGHT 3 — Risky analyst =================
    worst_sla = min(data, key=lambda x: x["sla"])
    insights.append(f"🚨 {worst_sla['name']} has lowest SLA ({worst_sla['sla']}%)")

    # ================= INSIGHT 4 — Balanced performer =================
    balanced = [
        x for x in data
        if x["resolved"] >= 10 and x["sla"] >= 90
    ]

    if balanced:
        top_balanced = max(balanced, key=lambda x: x["resolved"])
        insights.append(f"🏆 {top_balanced['name']} is a strong balanced performer")

    return insights
#==== analyst insights ends========
