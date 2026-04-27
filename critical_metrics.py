from flask import render_template
import sqlite3
from datetime import datetime, timedelta
from collections import Counter


#DB_PATH = r"D:\pythonPractice\IntelliIQ.db"
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_NAME = os.path.join(BASE_DIR, "IntelliIQ.db")

def register_critical_metrics(app):

    @app.route("/critical_metrics")
    def critical_metrics():

        conn = sqlite3.connect(DB_NAME)
        cursor = conn.cursor()

        today = datetime.now()
        last_7_days = (today - timedelta(days=7)).strftime("%Y-%m-%d")
        prev_7_days = (today - timedelta(days=14)).strftime("%Y-%m-%d")

        # ================= CURRENT 7 DAYS =================
        cursor.execute("""
            SELECT priority, revenue_impact, date, due_date
            FROM knowledgeBase
            WHERE date >= ?
        """, (last_7_days,))
        current_rows = cursor.fetchall()

        # ================= PREVIOUS 7 DAYS =================
        cursor.execute("""
            SELECT priority, revenue_impact, date
            FROM knowledgeBase
            WHERE date >= ? AND date < ?
        """, (prev_7_days, last_7_days))
        prev_rows = cursor.fetchall()

        # Fetch normalized incidents
        cursor.execute("""
                       SELECT normalized_incident
                       FROM knowledgeBase
                       WHERE date >= ?
                       """, (last_7_days,))

        rows = cursor.fetchall()

        normalized_list = [r[0] for r in rows if r[0]]

        # Count occurrences
        issue_counts = Counter(normalized_list)

        # Top 5 issues
        top_issues = issue_counts.most_common(5)

        # Reuse normalized incidents (you already fetched earlier OR fetch again safely)
        cursor.execute("""
                       SELECT normalized_incident
                       FROM knowledgeBase
                       WHERE date >= ?
                       """, (last_7_days,))

        rows = cursor.fetchall()

        normalized_list = [r[0] for r in rows if r[0]]

        issue_counts = Counter(normalized_list)

        # Apply threshold (>= 3)
        problem_candidates = [
            (issue, count)
            for issue, count in issue_counts.items()
            if count >= 3
        ]

        # Sort by highest occurrence
        problem_candidates = sorted(problem_candidates, key=lambda x: x[1], reverse=True)

        # Limit to top 5
        problem_candidates = problem_candidates[:5]


        conn.close()

        # ================= METRICS =================
        def compute_metrics(rows):
            total = len(rows)
            p1 = sum(1 for r in rows if r[0] == "P1")
            p2 = sum(1 for r in rows if r[0] == "P2")
            revenue = sum(1 for r in rows if r[1] == "Yes")

            breached = 0
            total_due = 0
            days_open_list = []

            for r in rows:
                priority, revenue_flag, created_date, due_date = r if len(r) == 4 else (*r, None)

                # MTTR proxy
                try:
                    created_dt = datetime.strptime(created_date, "%Y-%m-%d")
                    days_open_list.append((today - created_dt).days)
                except:
                    pass

                # SLA
                try:
                    if due_date:
                        due_dt = datetime.fromisoformat(due_date)
                        now = datetime.now(due_dt.tzinfo)
                        if now > due_dt:
                            breached += 1
                        total_due += 1
                except:
                    pass

            sla_pct = round((breached / total_due) * 100, 1) if total_due else 0
            avg_days = round(sum(days_open_list) / len(days_open_list), 1) if days_open_list else 0

            return total, p1, p2, revenue, sla_pct, avg_days

        curr_total, curr_p1, curr_p2,curr_rev, curr_sla, curr_mttr = compute_metrics(current_rows)
        prev_total, prev_p1, prev_p2,prev_rev, _, _ = compute_metrics(prev_rows)

        # ================= VALUE METRICS =================

        # Estimated hours saved
        hours_saved = round(curr_total * 0.4, 1)

        # MTTR improvement %
        baseline_mttr = 3  # days (assumed baseline)

        if curr_mttr > 0:
            mttr_improvement = round(((baseline_mttr - curr_mttr) / baseline_mttr) * 100, 1)
        else:
            mttr_improvement = 0

        # ================= TREND =================
        def trend(curr, prev):
            if curr > prev:
                return "↑"
            elif curr < prev:
                return "↓"
            return "→"

        # ================= COLOR LOGIC =================
        def color_sla(val):
            if val > 20:
                return "red"
            elif val > 10:
                return "orange"
            return "green"

        def color_mttr(val):
            if val > 3:
                return "red"
            elif val > 1:
                return "orange"
            return "green"



        return render_template(
            "critical_metrics.html",

            total_incidents=curr_total,
            total_trend=trend(curr_total, prev_total),

            p1_count=curr_p1,
            p1_trend=trend(curr_p1, prev_p1),

            p2_count=curr_p2,
            p2_trend=trend(curr_p2, prev_p2),

            revenue_count=curr_rev,
            revenue_trend=trend(curr_rev, prev_rev),

            sla_breach_pct=curr_sla,
            sla_color=color_sla(curr_sla),

            avg_days_open=curr_mttr,
            mttr_color=color_mttr(curr_mttr),

            hours_saved=hours_saved,
            mttr_improvement=mttr_improvement,

            top_issues=top_issues,

            problem_candidates=problem_candidates
        )