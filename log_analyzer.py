# ==========================================================
# LOG ANALYZER
# Standalone Log Analysis Engine
# ==========================================================

import os
from log_parser import analyze_incident_logs


# ==========================================================
# BUILD EVIDENCE SUMMARY
# ==========================================================

def build_evidence_summary(evidence):

    if not evidence:
        return "No significant log findings detected."

    findings = []

    for error_type, count in evidence.items():

        findings.append(
            f"- {error_type} detected ({count} occurrence(s))"
        )

    return "\n".join(findings)


# ==========================================================
# BUILD ANALYSIS PROMPT
# ==========================================================

def build_log_prompt(
    incident,
    evidence
):

    evidence_summary = build_evidence_summary(
        evidence
    )

    prompt = f"""

You are a senior production support engineer.

Analyze the uploaded log evidence.

INCIDENT

{incident}

LOG FINDINGS

{evidence_summary}

Return analysis in the following format:

SUMMARY:
Brief summary

ROOT CAUSE:
Most probable root cause

EVIDENCE:
Evidence supporting the conclusion

RECOMMENDED ACTIONS:
Provide 4-5 actionable troubleshooting steps

CONFIDENCE:
High / Medium / Low

"""

    return prompt


# ==========================================================
# ANALYZE LOGS
# ==========================================================

def analyze_logs(
    incident,
    kb_id,
    db_name,
    llm
):

    evidence = analyze_incident_logs(
        kb_id,
        db_name
    )

    prompt = build_log_prompt(
        incident,
        evidence
    )

    response = llm.invoke(
        prompt
    )

    return {

        "evidence": evidence,

        "analysis": str(
            response.content
            if hasattr(response, "content")
            else response
        )

    }