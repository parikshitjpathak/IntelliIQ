from flask import render_template
from collections import defaultdict
import os

#===== importing performance layer =====
from performance_service import get_top_performers, get_analyst_performance, generate_analyst_insights
#==== import ends========


# ============================================================
# ================= CORE METRICS ==============================
# ============================================================

def compute_analyst_metrics(tickets):

    analysts = defaultdict(lambda: {
        "total": 0,
        "closed": 0,
        "open": 0,
        "closed_met": 0,
        "closed_breach": 0,
        "open_breach": 0,
        "at_risk": 0,
        "resolution_times": []
    })

    for t in tickets:

        analyst = t.get("assigned_to") or "Unassigned"
        analysts[analyst]["total"] += 1

        status = (t.get("status") or "").lower()
        sla_status = (t.get("sla_status") or "").lower()
        days_open = t.get("days_open", 0)

        if status == "done":

            analysts[analyst]["closed"] += 1

            if sla_status == "completed":
                analysts[analyst]["closed_met"] += 1
            else:
                if sla_status == "breached":
                    analysts[analyst]["closed_breach"] += 1

            analysts[analyst]["resolution_times"].append(days_open)

        else:

            analysts[analyst]["open"] += 1

            if sla_status == "breached":
                analysts[analyst]["open_breach"] += 1
            else:
                if sla_status == "at risk":
                    analysts[analyst]["at_risk"] += 1

    results = []

    for analyst, data in analysts.items():

        if data["closed"] > 0:
            sla_percent = round((data["closed_met"] / data["closed"]) * 100, 2)
        else:
            sla_percent = 0

        if len(data["resolution_times"]) > 0:
            avg_resolution = round(
                sum(data["resolution_times"]) / len(data["resolution_times"]), 2
            )
        else:
            avg_resolution = 0

        if data["open_breach"] > 5:
            health = "Critical"
            focus = "Needs Attention"
        else:
            if data["open_breach"] > 0:
                health = "Moderate"
                focus = "Monitor"
            else:
                health = "Good"
                focus = "Stable"

        results.append({
            "analyst": analyst,
            "total": data["total"],
            "closed": data["closed"],
            "open": data["open"],
            "sla_percent": sla_percent,
            "closed_breach": data["closed_breach"],
            "open_breach": data["open_breach"],
            "at_risk": data["at_risk"],
            "avg_resolution": avg_resolution,
            "health": health,
            "focus": focus
        })

    return sorted(results, key=lambda x: x["total"], reverse=True)


# ============================================================
# ================= OVERALL METRICS ===========================
# ============================================================

def compute_overall_metrics(tickets):

    total = len(tickets)
    closed = 0
    open_t = 0
    closed_met = 0
    breached = 0
    open_breached = 0

    for t in tickets:

        status = (t.get("status") or "").lower()
        sla_status = (t.get("sla_status") or "").lower()

        if status == "done":

            closed += 1

            if sla_status == "completed":
                closed_met += 1
            else:
                if sla_status == "breached":
                    breached += 1

        else:

            open_t += 1

            if sla_status == "breached":
                breached += 1
                open_breached += 1

    if closed > 0:
        closed_sla = round((closed_met / closed) * 100, 2)
    else:
        closed_sla = 0

    if total > 0:
        breach_rate = round((breached / total) * 100, 2)
    else:
        breach_rate = 0

    return {
        "total": total,
        "closed": closed,
        "open": open_t,
        "closed_sla": closed_sla,
        "open_breached": open_breached,
        "breach_rate": breach_rate
    }


# ============================================================
# ================= AI INSIGHTS ===============================
# ============================================================

def generate_ai_summary(llm, metrics):

    summaries = []

    for m in metrics:

        prompt = f"""
Analyze this analyst:

Name: {m['analyst']}
Total: {m['total']}
Closed: {m['closed']}
Open: {m['open']}
Open Breach: {m['open_breach']}

Rules:
- Talk about the analyst (not team)
- Keep it 2-3 lines
"""

        try:
            response = llm.invoke(prompt)
            content = getattr(response, "content", str(response))
        except:
            content = "Insight unavailable"

        summaries.append({
            "analyst": m["analyst"],
            "summary": content
        })

    return summaries


# ============================================================
# ================= ROUTE ====================================
# ============================================================

def register_analyst_intelligence(app, llm):

    from analyst_data import get_analyst_tickets

    @app.route("/analyst_intelligence")
    def analyst_intelligence():

        tickets = get_analyst_tickets()

        metrics = compute_analyst_metrics(tickets)
        overall = compute_overall_metrics(tickets)
        insights = generate_ai_summary(llm, metrics)
        top_performers = get_top_performers()
        analyst_performance = get_analyst_performance()
        rule_based_insights = generate_analyst_insights()

        return render_template(
            "analyst_intelligence.html",
            metrics=metrics,
            overall=overall,
            insights=insights,
            top_performers=top_performers,
            analyst_performance=analyst_performance,
            rule_based_insights=rule_based_insights,
            active_page="analyst"
        )