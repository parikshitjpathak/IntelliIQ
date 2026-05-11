from flask import render_template
import sqlite3
import os
from datetime import datetime, timedelta
from collections import Counter

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_NAME = os.path.join(BASE_DIR, "IntelliIQ.db")


# ==========================================================
# DB
# ==========================================================

def get_connection():
    return sqlite3.connect(DB_NAME)


# ==========================================================
# DATE HELPERS
# ==========================================================

def get_period_start(period):

    today = datetime.now()

    if period == "week":
        return today - timedelta(days=today.weekday())

    elif period == "month":
        return today.replace(day=1)

    elif period == "quarter":

        quarter = (today.month - 1) // 3

        start_month = quarter * 3 + 1

        return today.replace(month=start_month, day=1)

    return today


# ==========================================================
# PERIOD LABELS
# ==========================================================

def get_period_label(period, start, end):

    if period == "week":

        return (
            f"{start.strftime('%d %b')} - "
            f"{(end - timedelta(days=1)).strftime('%d %b')}"
        )

    elif period == "month":

        return start.strftime("%B %Y")

    elif period == "quarter":

        quarter_end = end - timedelta(days=1)

        return (
            f"{start.strftime('%b %y')} - "
            f"{quarter_end.strftime('%b %y')}"
        )

    return ""


# ==========================================================
# OVERALL METRICS
# ==========================================================

def get_overall_metrics():

    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
        SELECT status, due_date, priority, revenue_impact, date
        FROM knowledgeBase
    """)

    rows = cursor.fetchall()

    conn.close()

    total = len(rows)

    breached = 0
    open_count = 0
    inprogress_count = 0
    todo_count = 0

    priority_counts = {
        "P1": 0,
        "P2": 0,
        "P3": 0,
        "P4": 0
    }

    revenue_count = 0

    days_open = []

    now = datetime.now()

    for r in rows:

        status, due_date, priority, revenue, created_date = r

        status_lower = (status or "").lower()

        if status_lower in ["to do", "open"]:
            todo_count += 1

        elif status_lower == "in progress":
            inprogress_count += 1

        if status_lower not in [
            "done",
            "closed",
            "resolved"
        ]:
            open_count += 1

        if priority in priority_counts:
            priority_counts[priority] += 1

        if revenue == "Yes":
            revenue_count += 1

        try:

            due_dt = datetime.fromisoformat(due_date)

            if (
                due_dt < now and
                status_lower not in [
                    "done",
                    "closed",
                    "resolved"
                ]
            ):

                breached += 1

        except:
            pass

        try:

            created_dt = datetime.strptime(
                created_date,
                "%Y-%m-%d"
            )

            days_open.append(
                (now - created_dt).days
            )

        except:
            pass

    sla_pct = round(
        ((total - breached) / total) * 100,
        1
    ) if total else 0

    avg_days = round(
        sum(days_open) / len(days_open),
        1
    ) if days_open else 0

    return {
        "total": total,
        "sla_pct": sla_pct,
        "breached": breached,
        "avg_days": avg_days,
        "open_count": open_count,
        "inprogress_count": inprogress_count,
        "todo_count": todo_count,
        "priority_counts": priority_counts,
        "revenue_count": revenue_count
    }


# ==========================================================
# PERIOD METRICS
# ==========================================================

def get_period_metrics(period, offset=0):

    conn = get_connection()
    cursor = conn.cursor()

    base = get_period_start(period)

    if period == "week":

        start = base - timedelta(days=(7 * offset))
        end = start + timedelta(days=7)

    elif period == "month":

        month = base.month - offset
        year = base.year

        while month <= 0:
            month += 12
            year -= 1

        start = base.replace(
            year=year,
            month=month
        )

        if month == 12:

            end = start.replace(
                year=year + 1,
                month=1
            )

        else:

            end = start.replace(
                month=month + 1
            )

    else:

        start = base - timedelta(days=(90 * offset))
        end = start + timedelta(days=90)

    label = get_period_label(
        period,
        start,
        end
    )

    cursor.execute("""
        SELECT status, due_date, resolved_date, date
        FROM knowledgeBase
        WHERE date >= ? AND date < ?
    """, (
        start.strftime("%Y-%m-%d"),
        end.strftime("%Y-%m-%d")
    ))

    rows = cursor.fetchall()

    conn.close()

    opened = len(rows)

    closed = 0
    breached = 0

    mttr_days = []

    now = datetime.now()

    for r in rows:

        status, due_date, resolved_date, created_date = r

        status_lower = (status or "").lower()

        if status_lower in [
            "done",
            "closed",
            "resolved"
        ]:
            closed += 1

        try:

            due_dt = datetime.fromisoformat(due_date)

            if (
                due_dt < now and
                status_lower not in [
                    "done",
                    "closed",
                    "resolved"
                ]
            ):

                breached += 1

        except:
            pass

        try:

            created_dt = datetime.strptime(
                created_date,
                "%Y-%m-%d"
            )

            mttr_days.append(
                (now - created_dt).days
            )

        except:
            pass

    sla_pct = round(
        ((opened - breached) / opened) * 100,
        1
    ) if opened else 0

    avg_mttr = round(
        sum(mttr_days) / len(mttr_days),
        1
    ) if mttr_days else 0

    baseline = 3

    mttr_improvement = round(
        ((baseline - avg_mttr) / baseline) * 100,
        1
    ) if avg_mttr else 0

    closure_efficiency = round(
        (closed / opened) * 100,
        1
    ) if opened else 0

    return {
        "label": label,
        "opened": opened,
        "closed": closed,
        "breached": breached,
        "sla_pct": sla_pct,
        "mttr_improvement": mttr_improvement,
        "closure_efficiency": closure_efficiency
    }


# ==========================================================
# PRIORITY TRENDS
# ==========================================================

def get_priority_trends():

    conn = get_connection()
    cursor = conn.cursor()

    trends = []

    today = datetime.now()

    for offset in range(0, 3):

        month = today.month - offset
        year = today.year

        while month <= 0:
            month += 12
            year -= 1

        start = datetime(year, month, 1)

        if month == 12:
            end = datetime(year + 1, 1, 1)
        else:
            end = datetime(year, month + 1, 1)

        cursor.execute("""
            SELECT priority, revenue_impact
            FROM knowledgeBase
            WHERE date >= ? AND date < ?
        """, (
            start.strftime("%Y-%m-%d"),
            end.strftime("%Y-%m-%d")
        ))

        rows = cursor.fetchall()

        p1 = 0
        p2 = 0
        p3 = 0
        p4 = 0
        revenue = 0

        for r in rows:

            priority, rev = r

            if priority == "P1":
                p1 += 1

            elif priority == "P2":
                p2 += 1

            elif priority == "P3":
                p3 += 1

            elif priority == "P4":
                p4 += 1

            if rev == "Yes":
                revenue += 1

        trends.append({
            "label": start.strftime("%B %Y"),
            "p1": p1,
            "p2": p2,
            "p3": p3,
            "p4": p4,
            "revenue": revenue
        })

    conn.close()

    return list(reversed(trends))


# ==========================================================
# CATEGORY INSIGHTS
# ==========================================================

def get_category_insights():

    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
        SELECT category, status, due_date
        FROM knowledgeBase
        WHERE category IS NOT NULL
    """)

    rows = cursor.fetchall()

    conn.close()

    now = datetime.now()

    category_stats = {}

    for r in rows:

        category, status, due_date = r

        if category not in category_stats:

            category_stats[category] = {
                "total": 0,
                "breached": 0
            }

        category_stats[category]["total"] += 1

        try:

            due_dt = datetime.fromisoformat(due_date)

            if (
                due_dt < now and
                status.lower() not in [
                    "done",
                    "closed",
                    "resolved"
                ]
            ):

                category_stats[category]["breached"] += 1

        except:
            pass

    best_category = None
    worst_category = None

    best_sla = -1
    worst_sla = 101

    for cat, values in category_stats.items():

        total = values["total"]
        breached = values["breached"]

        if total == 0:
            continue

        sla = round(
            ((total - breached) / total) * 100,
            1
        )

        if sla > best_sla:

            best_sla = sla

            best_category = (
                cat,
                sla
            )

        if sla < worst_sla:

            worst_sla = sla

            worst_category = (
                cat,
                sla
            )

    return {
        "best": best_category,
        "worst": worst_category
    }


# ==========================================================
# TREND INDICATOR
# ==========================================================

def get_trend_indicator(current, previous):

    if current > previous:
        return "🟢 Improving"

    elif current < previous:
        return "🔴 Worsening"

    return "🟡 Stable"


# ==========================================================
# TOP ANALYSTS
# ==========================================================

def get_top_analysts(period):

    conn = get_connection()
    cursor = conn.cursor()

    start = get_period_start(period)

    cursor.execute("""
        SELECT assigned_to, COUNT(*)
        FROM knowledgeBase
        WHERE resolved_date IS NOT NULL
        AND assigned_to IS NOT NULL
        AND resolved_date >= ?
        GROUP BY assigned_to
        ORDER BY COUNT(*) DESC
        LIMIT 3
    """, (
        start.strftime("%Y-%m-%d"),
    ))

    rows = cursor.fetchall()

    conn.close()

    return rows


# ==========================================================
# PERIODIC HIGHLIGHTS
# ==========================================================

def get_top_issues(period):

    conn = get_connection()
    cursor = conn.cursor()

    start = get_period_start(period)

    cursor.execute("""
        SELECT normalized_incident
        FROM knowledgeBase
        WHERE date >= ?
    """, (
        start.strftime("%Y-%m-%d"),
    ))

    rows = cursor.fetchall()

    conn.close()

    incidents = [
        r[0]
        for r in rows
        if r[0]
    ]

    counts = Counter(incidents)

    return counts.most_common(5)


# ==========================================================
# RISKS
# ==========================================================

def get_open_risks():

    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
        SELECT normalized_incident, COUNT(*)
        FROM knowledgeBase
        WHERE status NOT IN ('Done','Closed')
        GROUP BY normalized_incident
        HAVING COUNT(*) >= 2
        ORDER BY COUNT(*) DESC
        LIMIT 5
    """)

    risks = cursor.fetchall()

    conn.close()

    return risks


# ==========================================================
# AGING
# ==========================================================

def get_aging_tickets():

    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
        SELECT incident, priority, date
        FROM knowledgeBase
        WHERE status NOT IN ('Done','Closed')
    """)

    rows = cursor.fetchall()

    conn.close()

    today = datetime.now()

    aging = []

    for r in rows:

        incident, priority, created_date = r

        try:

            created_dt = datetime.strptime(
                created_date,
                "%Y-%m-%d"
            )

            age = (today - created_dt).days

            if age >= 5:

                aging.append({
                    "incident": incident,
                    "priority": priority,
                    "age": age
                })

        except:
            pass

    aging = sorted(
        aging,
        key=lambda x: x["age"],
        reverse=True
    )

    return aging[:5]


# ==========================================================
# ROUTE
# ==========================================================

def register_project_health(app):

    @app.route("/project_health")
    def project_health():

        overall = get_overall_metrics()

        current_week = get_period_metrics("week")

        weekly = [
            get_period_metrics("week", 0),
            get_period_metrics("week", 1),
            get_period_metrics("week", 2)
        ]

        monthly = [
            get_period_metrics("month", 0),
            get_period_metrics("month", 1),
            get_period_metrics("month", 2)
        ]

        quarterly = [
            get_period_metrics("quarter", 0),
            get_period_metrics("quarter", 1),
            get_period_metrics("quarter", 2)
        ]

        priority_trends = get_priority_trends()

        category_insights = get_category_insights()

        weekly_trend = get_trend_indicator(
            weekly[0]["sla_pct"],
            weekly[1]["sla_pct"]
        )

        monthly_trend = get_trend_indicator(
            monthly[0]["sla_pct"],
            monthly[1]["sla_pct"]
        )

        quarterly_trend = get_trend_indicator(
            quarterly[0]["sla_pct"],
            quarterly[1]["sla_pct"]
        )

        top_analysts = {
            "week": get_top_analysts("week"),
            "month": get_top_analysts("month"),
            "quarter": get_top_analysts("quarter")
        }

        highlights = {
            "week": get_top_issues("week"),
            "month": get_top_issues("month"),
            "quarter": get_top_issues("quarter")
        }

        risks = get_open_risks()

        aging = get_aging_tickets()

        return render_template(
            "project_health.html",
            overall=overall,
            current_week=current_week,
            weekly=weekly,
            monthly=monthly,
            quarterly=quarterly,
            priority_trends=priority_trends,
            category_insights=category_insights,
            weekly_trend=weekly_trend,
            monthly_trend=monthly_trend,
            quarterly_trend=quarterly_trend,
            top_analysts=top_analysts,
            highlights=highlights,
            risks=risks,
            aging=aging,
            active_page="project_health"
        )