import sqlite3
import json
from collections import Counter

from kb_engine import search_kb
from trend_engine import calculate_trends
from decision_engine import get_decision
from suggestions_engine import generate_suggestions
from domain_engine import enhance_with_domain
from normalization_engine import normalize_incident

from ai_engine import analyze_incident


DB_PATH = "IntelliIQ.db"


# ==========================================================
# SAVE ANALYSIS
# ==========================================================

def save_analysis_to_kb(

    incident,
    summary,
    root_cause,
    recommendations,
    category,
    source_type

):

    conn = sqlite3.connect(DB_PATH)

    cursor = conn.cursor()

    cursor.execute("""

        INSERT INTO knowledgeBase (

            Incident,
            Solution,
            Root_Cause,
            Category,
            Keywords,
            Jira_Ticket_Id,
            Date

        )

        VALUES (?, ?, ?, ?, ?, ?, datetime('now'))

    """, (

        incident,
        recommendations,
        root_cause,
        category,
        source_type,
        None

    ))

    conn.commit()

    conn.close()


# ==========================================================
# BUILD CATEGORY DISTRIBUTION
# ==========================================================

def build_category_distribution(matches):

    categories = []

    for row, score in matches:

        category = row.get("Category")

        if category:
            categories.append(category)

    return dict(
        Counter(categories)
    )


# ==========================================================
# HISTORICAL SUMMARY
# ==========================================================

def build_historical_analysis(

    incident,
    kb_result

):

    best_match = kb_result.get("match", {})

    root_cause = best_match.get(
        "root_cause",
        "Historical root cause unavailable"
    )

    solution = best_match.get(
        "solution",
        "Historical solution unavailable"
    )

    summary = f"""
Similar incidents were found in the knowledge base.
Previous operational resolution patterns were identified.
AI summarized the historical incident resolution data.
"""

    return {

        "summary": summary.strip(),

        "impact":
        "Similar operational impact observed historically.",

        "root_cause": root_cause,

        "recommendations": solution,

        "severity": "Medium",

        "confidence": "95%",

        "source": "Historical Knowledge Base"
    }


# ==========================================================
# MAIN INCIDENT ANALYSIS
# ==========================================================

def process_incident_analysis(

    incident,
    product,
    environment,
    users_impacted,
    region_impacted,
    revenue_impact,
    workaround

):

    # ======================================================
    # NORMALIZATION
    # ======================================================

    normalized_category = normalize_incident(
        incident
    )

    # ======================================================
    # KB SEARCH FIRST
    # ======================================================

    kb_result = search_kb(
        incident
    )

    historical_match_found = False

    ai_result = None

    frequency = 0

    matches = []

    top_root_cause = None

    match_score = 0

    kb_solution = None

    source_type = "AI Generated"

    # ======================================================
    # HISTORICAL MATCH FOUND
    # ======================================================

    if kb_result and kb_result.get("score", 0) >= 2:

        historical_match_found = True

        source_type = "Historical KB"

        ai_result = build_historical_analysis(
            incident,
            kb_result
        )

        frequency = kb_result.get(
            "frequency",
            0
        )

        matches = kb_result.get(
            "matches",
            []
        )

        top_root_cause = kb_result.get(
            "top_root_cause"
        )

        match_score = kb_result.get(
            "score",
            0
        )

        kb_solution = kb_result.get(
            "match",
            {}
        ).get(
            "solution"
        )

    # ======================================================
    # NO MATCH -> FULL AI ANALYSIS
    # ======================================================

    else:

        ai_result = analyze_incident(
            incident
        )

    # ======================================================
    # TREND ANALYSIS
    # ======================================================

    if matches:

        (

            count_1d,
            count_3d,
            count_5d,
            count_7d,
            count_older,
            trend_message

        ) = calculate_trends(
            matches,
            frequency
        )

    else:

        count_1d = 0
        count_3d = 0
        count_5d = 0
        count_7d = 0
        count_older = 0

        trend_message = (
            "No historical incident trend found"
        )

    # ======================================================
    # DECISION
    # ======================================================

    decision = get_decision(
        frequency,
        ai_result
    )

    # ======================================================
    # SUGGESTIONS
    # ======================================================

    suggestions = generate_suggestions(
        ai_result,
        matches
    )

    suggestions = enhance_with_domain(
        product,
        suggestions,
        incident
    )

    # ======================================================
    # CATEGORY DISTRIBUTION
    # ======================================================

    category_counts = build_category_distribution(
        matches
    )

    # ======================================================
    # PERSIST ANALYSIS
    # ======================================================

    save_analysis_to_kb(

        incident=incident,

        summary=ai_result.get(
            "summary"
        ),

        root_cause=ai_result.get(
            "root_cause"
        ),

        recommendations=ai_result.get(
            "recommendations"
        ),

        category=normalized_category,

        source_type=source_type

    )

    # ======================================================
    # RESPONSE
    # ======================================================

    return {

        "data": ai_result,

        "incident": incident,

        "priority": None,

        "sla_text": None,

        "due_date": None,

        "decision": decision,

        "frequency": frequency,

        "top_root_cause": top_root_cause,

        "match_score": match_score,

        "kb_solution": kb_solution,

        "matches": matches,

        "suggestions": suggestions,

        "category_counts": category_counts,

        "trend_message": trend_message,

        "count_1d": count_1d,
        "count_3d": count_3d,
        "count_5d": count_5d,
        "count_7d": count_7d,
        "count_older": count_older,

        "pattern_flag":

            "Recurring Incident"
            if frequency >= 3
            else "Low Recurrence",

        "historical_match_found":
            historical_match_found
    }