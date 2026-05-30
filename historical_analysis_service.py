import json

from kb_engine import search_kb_new

from ai_engine import analyze_incident


# ==========================================================
# BUILD HISTORICAL SUMMARY
# ==========================================================

def build_historical_summary(

    incident,
    match,
    frequency

):

    root_cause = match.get(
        "root_cause",
        "Historical root cause unavailable"
    )

    solution = match.get(
        "solution",
        "Historical solution unavailable"
    )

    jira_ticket = match.get(
        "jira_ticket_id",
        "N/A"
    )

    summary_prompt = f"""

You are an operations support expert.

A similar historical incident already exists.

Current Incident:
{incident}

Historical Root Cause:
{root_cause}

Historical Resolution:
{solution}

Historical Jira Ticket:
{jira_ticket}

Occurrence Frequency:
{frequency}

Generate a concise operational summary.

Return ONLY valid JSON.

{{
    "summary": "...",
    "impact": "...",
    "root_cause": "...",
    "recommendations": "...",
    "severity": "...",
    "confidence": "..."
}}

"""

    ai_output = analyze_incident(
        summary_prompt
    )

    return ai_output


# ==========================================================
# MAIN SERVICE
# ==========================================================

def get_incident_analysis(

    incident

):

    result = search_kb_new(
        incident
    )

    # ======================================================
    # HISTORICAL MATCH FOUND
    # ======================================================

    if result:

        match = result.get("match")

        score = result.get(
            "score",
            0
        )

        frequency = result.get(
            "frequency",
            0
        )

        # Strong historical match
        if score >= 2 and match:

            historical_ai = build_historical_summary(

                incident,
                match,
                frequency

            )

            return {

                "analysis": historical_ai,

                "source": "historical",

                "match": match,

                "score": score,

                "frequency": frequency,

                "top_root_cause":
                    result.get(
                        "top_root_cause"
                    ),

                "matches":
                    result.get(
                        "matches",
                        []
                    )
            }

    # ======================================================
    # FULL AI FALLBACK
    # ======================================================

    ai_output = analyze_incident(
        incident
    )

    return {

        "analysis": ai_output,

        "source": "ai",

        "match": None,

        "score": 0,

        "frequency": 0,

        "top_root_cause": "",

        "matches": []
    }