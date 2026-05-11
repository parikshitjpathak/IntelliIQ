# ==========================================================
# SYSTEM ADVISOR MODULE (ENHANCED - STABILITY + REASONING)
# ==========================================================
# Enhancements:
#   - Direct stability answer (Yes / No)
#   - Reasoning included in response
#   - Signal-based intelligence (no fixed fallback days)
#   - Intent-aware responses
# ==========================================================

import os
import re
from collections import Counter
from datetime import datetime, timedelta

from flask import render_template, request
import markdown

from dotenv import load_dotenv

#commenting the below on 11 may load_dotenv(mykeys.env) to test dynamic loading==============

#load_dotenv("mykeys.env")
#============== commenting ends here===============================

#=============== below is the new code on 11 may===============

env=os.getenv("ENV","local")
if env=="local" :
    load_dotenv("mykeys.env")
    
else:
    load_dotenv()    
#load_dotenv()

#============= 11 may code ends========================

from langchain_openai import ChatOpenAI

llm = ChatOpenAI(temperature=0.3)


# ==========================================================
# INTENT DETECTION
# ==========================================================
def detect_intent(query: str) -> str:

    query = query.lower()

    # 🔥 NEW: Direct stability check
    if "stable right now" in query or "is the system stable" in query:
        return "stability_check"

    if any(word in query for word in ["stable", "improve", "optimize", "fix"]):
        return "stability"

    elif any(word in query for word in ["risk", "fail", "trigger", "break"]):
        return "risk"

    elif any(word in query for word in ["why", "analysis", "reason"]):
        return "analysis"

    return "stability"


# ==========================================================
# FETCH RECENT INCIDENTS (LAST 10 DAYS)
# ==========================================================
def get_recent_incidents():

    import sqlite3

    BASE_DIR = os.path.dirname(os.path.abspath(__file__))
    DB_NAME = os.path.join(BASE_DIR, "IntelliIQ.db")

    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()

    ten_days_ago = (datetime.now() - timedelta(days=10)).strftime("%Y-%m-%d")

    cursor.execute("""
        SELECT Incident, Category, Jira_Ticket_Id, Date
        FROM knowledgeBase
        WHERE Date >= ?
    """, (ten_days_ago,))

    rows = cursor.fetchall()
    conn.close()

    return rows


# ==========================================================
# FETCH OPEN HIGH PRIORITY INCIDENTS
# ==========================================================
def get_open_high_priority():

    import sqlite3

    BASE_DIR = os.path.dirname(os.path.abspath(__file__))
    DB_NAME = os.path.join(BASE_DIR, "IntelliIQ.db")

    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()

    cursor.execute("""
        SELECT Incident, Category, Jira_Ticket_Id
        FROM knowledgeBase
        WHERE Priority IN ('P1', 'P2')
          AND Jira_Ticket_Id IS NOT NULL
    """)

    rows = cursor.fetchall()
    conn.close()

    return rows


# ==========================================================
# FETCH RECURRING ISSUES
# ==========================================================
def get_recurring_issues_data():
    try:
        from trend_engine import get_recurring_issues
        return get_recurring_issues()
    except Exception as e:
        print("Trend Engine Error:", e)
        return []


# ==========================================================
# EVALUATE SYSTEM STABILITY (NEW)
# ==========================================================
def evaluate_system_stability():

    recent = get_recent_incidents()
    open_critical = get_open_high_priority()

    reasons = []

    # Rule 1: Open P1/P2
    if open_critical:
        reasons.append(f"{len(open_critical)} open P1/P2 incidents")

    # Rule 2: High recent activity
    if len(recent) > 5:
        reasons.append(f"{len(recent)} incidents in last 10 days")

    if reasons:
        return False, ", ".join(reasons)

    return True, "No significant incidents or risks detected"


# ==========================================================
# BUILD SYSTEM SUMMARY
# ==========================================================
def build_system_summary(issues):

    summary = ""

    # Recurring Issues
    if issues:
        summary += "Recurring issues:\n"
        for i, issue in enumerate(issues[:5], 1):
            summary += f"{i}. {issue['incident']} — {issue['count']} occurrences\n"
    else:
        summary += "No significant recurring issues detected.\n"

    # Category Patterns
    categories = [
        issue.get("category")
        for issue in issues
        if issue.get("category")
    ]

    if categories:
        counts = Counter(categories)
        summary += "\nTop categories:\n"
        for cat, count in counts.most_common(3):
            summary += f"- {cat}: {count}\n"

    # Recent Incidents
    recent = get_recent_incidents()
    if not recent:
        summary += "\nSystem stable in last 10 days.\n"
    else:
        summary += f"\nRecent incidents (last 10 days): {len(recent)}\n"

    # Open Critical
    open_critical = get_open_high_priority()
    if open_critical:
        summary += f"\nOpen P1/P2 incidents: {len(open_critical)}\n"
    else:
        summary += "\nNo open critical incidents.\n"

    return summary


# ==========================================================
# BUILD PROMPT
# ==========================================================
def build_prompt(summary, intent):

    if intent == "stability":
        goal = "Suggest how to improve system stability and prevent incidents."

    elif intent == "risk":
        goal = "Identify what issues are likely to occur again and highlight risks."

    elif intent == "analysis":
        goal = "Explain what is going wrong and why incidents are happening."

    else:
        goal = "Provide system insights."

    prompt = f"""
You are an expert Site Reliability Engineer.

Analyze the system based on the following signals:

{summary}

Goal:
{goal}

Provide structured response:

### 🔍 Overview
### 📊 Key Findings
### 🧠 Observations
### 🛠 Recommendations
### ⚠️ Risks (if applicable)
### 📈 Expected Outcome

Guidelines:
- Be specific
- Avoid generic advice
- Prioritize actionable insights
"""

    return prompt


# ==========================================================
# MAIN INSIGHT FUNCTION
# ==========================================================
def build_system_insight(query: str):

    intent = detect_intent(query)

    issues = get_recurring_issues_data()

    summary = build_system_summary(issues)

    # -------------------------------------------
    # 🔥 NEW: Stability Prefix
    # -------------------------------------------
    prefix = ""

    if intent == "stability_check":

        is_stable, reason = evaluate_system_stability()

        if is_stable:
            prefix = f"✅ Yes. The system is stable. Reason: {reason}.\n\n"
        else:
            prefix = f"❌ No. The system is not stable currently. Reason: {reason}.\n\n"

    # -------------------------------------------
    # LLM
    # -------------------------------------------
    prompt = build_prompt(summary, intent)

    try:
        response = llm.invoke(prompt)
        answer = response.content
    except Exception as e:
        print("Advisor Error:", e)
        answer = "Error generating insights."

    formatted = markdown.markdown(
        answer.replace("\n", "  \n"),
        extensions=["fenced_code", "tables"]
    )

    return prefix + formatted


# ==========================================================
# ROUTE
# ==========================================================
def register_system_advisor(app):

    @app.route("/system_advisor", methods=["GET", "POST"])
    def system_advisor():

        advisor_output = None

        if request.method == "POST":
            query = request.form.get("query", "")
            advisor_output = build_system_insight(query)

        return render_template(
            "system_advisor.html",
            advisor_output=advisor_output,
            active_page="advisor"
        )