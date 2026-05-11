# ==========================================================
# PERFORMANCE ENGINE
# Purpose:
# - Calculate analyst performance
# - Store snapshots (weekly / monthly / quarterly)
# - Identify top performers
# ==========================================================

import sqlite3
from datetime import datetime, timedelta
import os

# ================= DB CONFIG =================
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_NAME = os.path.join(BASE_DIR, "IntelliIQ.db")


# ==========================================================
# MAIN FUNCTION
# ==========================================================
def generate_performance_snapshot():

    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()

    now = datetime.now()

    # ---------------- PERIOD CONFIG ----------------
    periods = [
        ("weekly", 7, 10),
        ("monthly", 30, 40),
        ("quarterly", 90, 100)
    ]

    for period_type, days, min_threshold in periods:

        #start_date = now - timedelta(days=days)
        #end_date = now

        #===== normalize period dates (critical for snapshot locking)=====
        end_date = now.replace(hour=0, minute=0, second=0, microsecond=0)
        start_date = end_date - timedelta(days=days)
        #==== normalization ends========

        #===== snapshot existence check (Phase 3 - locking logic)=====
        cursor.execute("""
            SELECT COUNT(*)
            FROM analyst_performance_data
            WHERE period_type = ?
            AND period_start = ?
            AND period_end = ?
        """, (
            period_type,
            start_date.strftime("%Y-%m-%d"),
            end_date.strftime("%Y-%m-%d")
        ))

        exists = cursor.fetchone()[0]

        if exists > 0:
            print(f"⚠️ Snapshot already exists for {period_type} — skipping")
            continue
    #==== snapshot locking ends========

        # ================= FETCH DATA =================
        cursor.execute("""
            SELECT assigned_to, resolved_date, due_date
            FROM knowledgeBase
            WHERE resolved_date IS NOT NULL
        """)

        rows = cursor.fetchall()

        performance = {}

        for assignee, resolved_date, due_date in rows:

            if not assignee:
                assignee = "Unassigned"

            # -------- Parse resolved date --------
           # try:
            #    resolved_dt = datetime.strptime(resolved_date, "%Y-%m-%d %H:%M:%S")
            #except:
             #   continue

            try:
            # Handle formats like: 2026-04-23T22:33:51.630+0530
                 clean_resolved = resolved_date.split("+")[0].split(".")[0]
                 resolved_dt = datetime.strptime(clean_resolved, "%Y-%m-%dT%H:%M:%S")
            except Exception as e:
                print("RESOLVED DATE ERROR:", resolved_date)
                continue

            # -------- Filter by period --------
            if resolved_dt < start_date:
                continue

            # -------- Init --------
            if assignee not in performance:
                performance[assignee] = {
                    "resolved": 0,
                    "sla_met": 0
                }

            performance[assignee]["resolved"] += 1

            # -------- SLA CHECK --------
            try:
                due_dt = datetime.strptime(due_date, "%Y-%m-%d %H:%M:%S")
                if resolved_dt <= due_dt:
                    performance[assignee]["sla_met"] += 1
            except:
                pass

        # ================= INSERT FULL SNAPSHOT =================
        for analyst, data in performance.items():

            resolved = data["resolved"]
            sla_met = data["sla_met"]

            if resolved == 0:
                continue

            sla_percent = (sla_met / resolved) * 100

            cursor.execute("""
                INSERT INTO analyst_performance_data
                (analyst_name, period_type, period_start, period_end,
                 resolved_count, sla_met_count, sla_percentage)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            """, (
                analyst,
                period_type,
                start_date.strftime("%Y-%m-%d"),
                end_date.strftime("%Y-%m-%d"),
                resolved,
                sla_met,
                round(sla_percent, 2)
            ))

        # ================= IDENTIFY TOP PERFORMERS =================
        #===== DEBUG: print performance data =====
        print("\n--- PERFORMANCE SUMMARY ---")
        for analyst, data in performance.items():
            resolved = data["resolved"]
            sla_met = data["sla_met"]
            sla_percent = (sla_met / resolved) * 100 if resolved > 0 else 0

            print(f"{analyst} | Resolved: {resolved} | SLA Met: {sla_met} | SLA%: {round(sla_percent,2)}")
        #==== DEBUG END =====


        qualified = []

        for analyst, data in performance.items():

            resolved = data["resolved"]
            sla_met = data["sla_met"]

            if resolved == 0:
                continue

            sla_percent = (sla_met / resolved) * 100

            # -------- Qualification Criteria --------
            if resolved >= min_threshold and sla_percent >= 97:
                qualified.append((analyst, resolved, sla_met, sla_percent))

           #===== DEBUG: qualified analysts =====
            print("\n--- QUALIFIED ANALYSTS ---")
            if not qualified:
                print("No one qualified based on criteria")
            else:
                for q in qualified:
                    print(q)
            #==== DEBUG END =====     

        # -------- Sort (SLA % first, then volume) --------
        qualified.sort(key=lambda x: (-x[3], -x[1]))

        top_3 = qualified[:3]

        # ================= INSERT TOP PERFORMERS =================
        for analyst, resolved, sla_met, sla_percent in top_3:

            cursor.execute("""
                INSERT INTO top_performers
                (analyst_name, period_type, period_start, period_end,
                 resolved_count, sla_met_count, sla_percentage)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            """, (
                analyst,
                period_type,
                start_date.strftime("%Y-%m-%d"),
                end_date.strftime("%Y-%m-%d"),
                resolved,
                sla_met,
                round(sla_percent, 2)
            ))

    conn.commit()
    conn.close()


# ==========================================================
# OPTIONAL: SAFE EXECUTION (for testing only)
# ==========================================================
if __name__ == "__main__":
    print("Running performance snapshot...")
    generate_performance_snapshot()
    print("Snapshot completed.")