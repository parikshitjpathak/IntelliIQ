# ==========================================================
# OPERATIONS INSIGHTS (AGGREGATION LAYER)
# ==========================================================

from flask import render_template


def register_operations_insights(app):

    @app.route("/operations_insights")
    def operations_insights():

        # =====================================================
        # LAZY IMPORT (PREVENT CIRCULAR DEPENDENCY)
        # =====================================================
        from pcAnalyser import (
            get_status_distribution,
            get_priority_distribution,
            get_sla_status_distribution,
            get_sla_health,
            get_weekly_metrics,
            get_weekly_trend,
            get_top_risks,
            get_aging_tickets,
            get_last_synced_time
        )

        import sqlite3
        import os
        from collections import Counter
        from datetime import datetime, timedelta

        BASE_DIR = os.path.dirname(os.path.abspath(__file__))
        DB_NAME = os.path.join(BASE_DIR, "IntelliIQ.db")

        # =====================================================
        # ================= CONTROL TOWER =====================
        # =====================================================
        status_counts = get_status_distribution()
        priority_counts = get_priority_distribution()

        sla_counts = get_sla_status_distribution()
        sla_health = get_sla_health(sla_counts)

        weekly_metrics = get_weekly_metrics()
        weekly_trend = get_weekly_trend(weekly_metrics)

        top_risks = get_top_risks()
        aging_tickets = get_aging_tickets()

        last_synced = get_last_synced_time()

        # =====================================================
        # ================= CRITICAL METRICS ==================
        # (ONLY REUSING LOGIC — NOT REINVENTING)
        # =====================================================
        conn = sqlite3.connect(DB_NAME)
        cursor = conn.cursor()

        today = datetime.now()
        last_7_days = (today - timedelta(days=7)).strftime("%Y-%m-%d")

        # -------- TOP ISSUES (EXACT SAME LOGIC) --------
        cursor.execute("""
            SELECT normalized_incident
            FROM knowledgeBase
            WHERE date >= ?
        """, (last_7_days,))

        rows = cursor.fetchall()
        normalized_list = [r[0] for r in rows if r[0]]

        issue_counts = Counter(normalized_list)
        top_issues = issue_counts.most_common(5)

        # -------- TREND (LAST 10 DAYS) --------
        cursor.execute("""
            SELECT date, COUNT(*)
            FROM knowledgeBase
            GROUP BY date
            ORDER BY date
        """)

        trend_rows = cursor.fetchall()

        trend_labels = [r[0] for r in trend_rows][-10:]
        trend_values = [r[1] for r in trend_rows][-10:]

        conn.close()

        # =====================================================
        # ================= SYSTEM STATUS =====================
        # (LIGHT OVERLAY — SAFE)
        # =====================================================
        open_p1 = priority_counts.get("P1", 0)

        if open_p1 > 0 or sla_health.get("breached", 0) > 5:
            system_status = "Critical"
            system_color = "red"

        elif weekly_metrics["current"]["created"] > 10:
            system_status = "At Risk"
            system_color = "orange"

        else:
            system_status = "Stable"
            system_color = "green"

        # =====================================================
        # ================= RENDER ============================
        # =====================================================
        return render_template(
            "operations_insights.html",

            # CONTROL TOWER DATA
            status_counts=status_counts,
            priority_counts=priority_counts,
            sla_counts=sla_counts,
            sla_health=sla_health,
            weekly_metrics=weekly_metrics,
            weekly_trend=weekly_trend,
            top_risks=top_risks,
            aging_tickets=aging_tickets,

            # CRITICAL METRICS DATA
            top_issues=top_issues,

            # CHART DATA
            trend_labels=trend_labels,
            trend_values=trend_values,

            # META
            last_synced=last_synced,
            system_status=system_status,
            system_color=system_color,

            active_page="insights"
        )