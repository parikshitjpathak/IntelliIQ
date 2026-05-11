from flask import render_template
from collections import Counter


# ==========================================================
# CATEGORY NORMALIZATION
# ==========================================================

CATEGORY_MAPPING = {

    # APPLICATION
    "ui error": "Application",
    "frontend": "Application",
    "app issue": "Application",
    "application issue": "Application",
    "api": "Application",
    "middleware": "Application",

    # DATABASE
    "oracle": "Database",
    "db": "Database",
    "db failure": "Database",
    "database issue": "Database",

    # INFRA
    "infra": "Infrastructure",
    "server": "Infrastructure",
    "vm": "Infrastructure",
    "network": "Infrastructure",

    # MONITORING
    "dynatrace": "Monitoring",
    "newrelic": "Monitoring",
    "alert": "Monitoring"
}


# ==========================================================
# NORMALIZE CATEGORY
# ==========================================================

def normalize_category(category):

    if not category:
        return "Unknown"

    category_clean = category.strip().lower()

    return CATEGORY_MAPPING.get(
        category_clean,
        category.title()
    )


# ==========================================================
# ANALYST DETAIL METRICS
# ==========================================================

def compute_analyst_detail(tickets, analyst_name):

    filtered = []

    for t in tickets:

        if (t.get("assigned_to") or "Unassigned") == analyst_name:
            filtered.append(t)

    summary = {
        "total": 0,
        "closed": 0,
        "open": 0,
        "closed_met": 0,
        "closed_breach": 0,
        "open_breach": 0,
        "at_risk": 0,
        "problem_tickets": 0
    }

    category_count = Counter()
    priority_count = Counter()
    breach_category = Counter()

    p1_count = 0
    p2_count = 0

    for t in filtered:

        summary["total"] += 1

        status = (t.get("status") or "").lower()
        sla = (t.get("sla_status") or "").lower()

        raw_category = (t.get("category") or "Unknown")
        category = normalize_category(raw_category)

        priority = (t.get("priority") or "Unknown").strip()

        category_count[category] += 1
        priority_count[priority] += 1

        if priority == "P1":
            p1_count += 1

        if priority == "P2":
            p2_count += 1

        if t.get("problem_ticket_id"):
            summary["problem_tickets"] += 1

        # CLOSED

        if status == "done":

            summary["closed"] += 1

            if sla == "completed":

                summary["closed_met"] += 1

            elif sla == "breached":

                summary["closed_breach"] += 1
                breach_category[category] += 1

        # OPEN

        else:

            summary["open"] += 1

            if sla == "breached":

                summary["open_breach"] += 1
                breach_category[category] += 1

            elif sla == "at risk":

                summary["at_risk"] += 1

    # ======================================================
    # SORTING
    # ======================================================

    category_sorted = sorted(
        category_count.items(),
        key=lambda x: x[1],
        reverse=True
    )

    def priority_key(p):

        try:
            return int(p[0].replace("P", ""))
        except:
            return 99

    priority_sorted = sorted(
        priority_count.items(),
        key=lambda x: priority_key(x[0])
    )

    breach_sorted = sorted(
        breach_category.items(),
        key=lambda x: x[1],
        reverse=True
    )

    workload = {
        "p1": p1_count,
        "p2": p2_count
    }

    return (
        summary,
        category_sorted,
        priority_sorted,
        breach_sorted,
        filtered,
        workload
    )


# ==========================================================
# CAPABILITY INTELLIGENCE
# ==========================================================

def compute_analyst_capability(category, breach, workload):

    strengths = []
    weaknesses = []

    recommendations = []
    expertise_areas = []
    risk_areas = []

    operational_benefits = []
    productivity_impacts = []

    capability_notes = []
    mttr_suggestions = []
    sla_risk_insights = []

    category_dict = dict(category)
    breach_dict = dict(breach)

    # ======================================================
    # CATEGORY ANALYSIS
    # ======================================================

    for cat, total in category_dict.items():

        breaches = breach_dict.get(cat, 0)

        sla_percent = (
            ((total - breaches) / total) * 100
            if total > 0 else 0
        )

        # STRONG AREA

        if total >= 5 and sla_percent >= 90:

            strengths.append(
                f"{cat} ({round(sla_percent,1)}% SLA)"
            )

            expertise_areas.append(cat)

        # EMERGING STRONG AREA

        elif total < 5 and sla_percent >= 90:

            expertise_areas.append(
                f"{cat} (Emerging capability)"
            )

        # WEAK AREA

        if total >= 5 and sla_percent < 75:

            weaknesses.append(
                f"{cat} ({round(sla_percent,1)}% SLA)"
            )

            risk_areas.append(cat)

            sla_risk_insights.append(
                f"Repeated SLA breaches observed in {cat} incidents."
            )

            mttr_suggestions.append(
                f"Improve troubleshooting workflow for {cat} incidents to reduce MTTR."
            )

            # TRAINING

            if cat == "Application":

                recommendations.extend([
                    "Application log analysis",
                    "API troubleshooting",
                    "Middleware diagnostics"
                ])

            elif cat == "Database":

                recommendations.extend([
                    "SQL troubleshooting",
                    "Database diagnostics",
                    "Connection pool analysis"
                ])

            elif cat == "Infrastructure":

                recommendations.extend([
                    "Server diagnostics",
                    "Infra monitoring",
                    "Capacity troubleshooting"
                ])

            else:

                recommendations.append(
                    f"Improve troubleshooting capability for {cat}"
                )

        # EMERGING RISK

        elif total < 5 and sla_percent < 75:

            risk_areas.append(
                f"{cat} (Emerging concern)"
            )

            sla_risk_insights.append(
                f"Early SLA concerns observed in {cat} incidents."
            )

    # ======================================================
    # WORKLOAD ANALYSIS
    # ======================================================

    if workload["p1"] >= 5:

        capability_notes.append(
            "High critical incident ownership observed (P1 handling)."
        )

        operational_benefits.append(
            "Can support critical incident management workflows."
        )

    if workload["p2"] >= 10:

        capability_notes.append(
            "High operational workload handling capability observed."
        )

    # ======================================================
    # GENERAL PRODUCTIVITY INSIGHTS
    # ======================================================

    if weaknesses:

        productivity_impacts.append(
            "Improving troubleshooting consistency may reduce escalations and improve analyst productivity."
        )

        operational_benefits.append(
            "Improved SLA handling may reduce operational delays and improve service quality."
        )

    if not weaknesses and strengths:

        operational_benefits.append(
            "Strong operational consistency observed across major incident categories."
        )

    # ======================================================
    # NO DATA CONDITIONS
    # ======================================================

    if not strengths and not expertise_areas:

        capability_notes.append(
            "No strong expertise patterns identified yet."
        )

    if not weaknesses and not risk_areas:

        capability_notes.append(
            "No major operational risk trends currently identified."
        )

    # ======================================================
    # REMOVE DUPLICATES
    # ======================================================

    recommendations = list(dict.fromkeys(recommendations))
    operational_benefits = list(dict.fromkeys(operational_benefits))
    productivity_impacts = list(dict.fromkeys(productivity_impacts))
    capability_notes = list(dict.fromkeys(capability_notes))
    mttr_suggestions = list(dict.fromkeys(mttr_suggestions))
    sla_risk_insights = list(dict.fromkeys(sla_risk_insights))

    return (
        strengths,
        weaknesses,
        recommendations,
        expertise_areas,
        risk_areas,
        operational_benefits,
        productivity_impacts,
        capability_notes,
        mttr_suggestions,
        sla_risk_insights
    )


# ==========================================================
# AI SUMMARY
# ==========================================================

def generate_detail_insight(llm, summary, analyst_name):

    prompt = f"""
Analyze this analyst:

Name: {analyst_name}

Total: {summary['total']}
Closed: {summary['closed']}
Open: {summary['open']}
Open Breach: {summary['open_breach']}

Rules:
- Talk only about this analyst
- Keep it short
"""

    try:

        response = llm.invoke(prompt)

        return getattr(response, "content", str(response))

    except:

        return "Insight unavailable"


# ==========================================================
# ROUTE
# ==========================================================

def register_analyst_detail(app, llm):

    from analyst_data import get_analyst_tickets

    @app.route("/analyst/<analyst_name>")
    def analyst_detail(analyst_name):

        tickets = get_analyst_tickets()

        (
            summary,
            category,
            priority,
            breach,
            filtered,
            workload
        ) = compute_analyst_detail(
            tickets,
            analyst_name
        )

        (
            strengths,
            weaknesses,
            recommendations,
            expertise_areas,
            risk_areas,
            operational_benefits,
            productivity_impacts,
            capability_notes,
            mttr_suggestions,
            sla_risk_insights
        ) = compute_analyst_capability(
            category,
            breach,
            workload
        )

        insight = generate_detail_insight(
            llm,
            summary,
            analyst_name
        )

        return render_template(
            "analyst_detail.html",
            analyst=analyst_name.title(),
            summary=summary,
            category=category,
            priority=priority,
            breach=breach,
            tickets=filtered,
            strengths=strengths,
            weaknesses=weaknesses,
            recommendations=recommendations,
            expertise_areas=expertise_areas,
            risk_areas=risk_areas,
            operational_benefits=operational_benefits,
            productivity_impacts=productivity_impacts,
            capability_notes=capability_notes,
            mttr_suggestions=mttr_suggestions,
            sla_risk_insights=sla_risk_insights,
            insight=insight
        )