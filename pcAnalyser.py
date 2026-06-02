# ==========================================================
# STEP 1: IMPORTS
# Purpose: Import all required libraries
# ==========================================================
from kb_engine import search_kb as search_kb_new
from suggestions_engine import generate_suggestions
from ticketing_service import (
    create_jira_ticket,
    add_jira_comment,
    create_confluence_page,
)
from decision_engine import get_decision
from trend_engine import calculate_trends
from domain_engine import enhance_with_domain
from flask import Flask, render_template, request, redirect
from project_health import register_project_health
import json
import time
import os
import sqlite3
#from incident_analyser import incident_bp
from log_analyzer_routes import register_log_analyzer_routes
from business_impact import register_business_impact_routes


from ticket_dashboard import register_ticket_dashboard, get_all_tickets
from insurance_copilot import register_insurance_copilot
#from critical_metrics import register_critical_metrics
from system_advisor import register_system_advisor

from performance_service import get_top_performers, get_analyst_performance, generate_analyst_insights
from normalization_engine import normalize_incident
from help_page import register_help_page
from process_doc import register_process_doc
from analyst_intelligence import register_analyst_intelligence
from performance_engine import generate_performance_snapshot

# DB_PATH = r"D:\pythonPractice\IntelliIQ.db"
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_NAME = os.path.join(BASE_DIR, "IntelliIQ.db")

from datetime import datetime, timedelta

from dotenv import load_dotenv
from langchain_openai import ChatOpenAI
from langchain_core.prompts import PromptTemplate
from langchain_core.output_parsers import StrOutputParser

import requests
from requests.auth import HTTPBasicAuth
from datetime import datetime
from analyst_detail import register_analyst_detail
from rca_engine import register_rca_routes
from historical_rca_engine import search_historical_rca
#from db_debug import db_debug_bp

# ============= for telegram config======================

import requests
import os



# ===================== Top Analysts clisuure======================


def get_top_analysts():

    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()

    cursor.execute("""
        SELECT assigned_to, COUNT(*) as total_resolved
        FROM knowledgeBase
        WHERE resolved_date IS NOT NULL
        AND assigned_to IS NOT NULL
        GROUP BY assigned_to
        ORDER BY total_resolved DESC
        LIMIT 3
    """)

    results = cursor.fetchall()
    conn.close()

    analysts = []
    for row in results:
        analysts.append({"name": row[0], "count": row[1]})

    return analysts


# ====================== Analyst clisure ends here=====================


# ================== top risks areas function ==========================
def get_top_risks():

    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()

    from datetime import datetime, timedelta

    seven_days_ago = (datetime.now() - timedelta(days=7)).strftime("%Y-%m-%d")

    cursor.execute(
        """
                   SELECT incident,
                          priority,
                          due_date,
                          COUNT(*) as cnt,
                          GROUP_CONCAT(jira_ticket_id)
                   FROM knowledgeBase
                   WHERE due_date IS NOT NULL
                     AND priority IN ('P1', 'P2')
                     AND status NOT IN ('Done', 'Closed')
                     AND date >= ?
                   GROUP BY LOWER (TRIM (incident))
                   """,
        (seven_days_ago,),
    )

    rows = cursor.fetchall()
    conn.close()

    now = datetime.now()
    risk_dict = {}

    for incident, priority, due_date_str, count, tickets in rows:
        try:
            due_date = datetime.strptime(due_date_str, "%Y-%m-%d %H:%M:%S")

            if due_date < now:
                normalized = incident.strip().lower()

                # 👇 ADD THESE 2 LINES HERE
                ticket_list = tickets.split(",") if tickets else []
                ticket_list = ticket_list[:3]
                status = "BREACHED" if due_date < now else "AT_RISK"

                if normalized not in risk_dict or due_date < risk_dict[normalized][2]:
                    risk_dict[normalized] = (
                        incident,
                        priority,
                        due_date,
                        count,
                        ticket_list,
                        status,
                    )

        except:
            continue

    risks = list(risk_dict.values())
    risks.sort(key=lambda x: x[2])

    return risks[:3]


# ================== top risks areas closed here =============================


# ==================== aging tickets function here=========================
def get_aging_tickets():
    from datetime import datetime

    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()

    cursor.execute("""
        SELECT incident, date, priority
        FROM knowledgeBase
        WHERE status NOT IN ('Done', 'Closed')
    """)

    rows = cursor.fetchall()
    conn.close()

    today = datetime.now().date()
    aging_list = []

    for incident, date_str, priority in rows:
        try:
            created_date = datetime.strptime(date_str, "%Y-%m-%d").date()
            age_days = (today - created_date).days

            if age_days >= 1:
                aging_list.append((incident, priority, age_days))

        except:
            continue

    # Oldest first
    aging_list.sort(key=lambda x: x[2], reverse=True)

    return aging_list[:3]


# ======================= aging tickets funcion ends here========================


# ============== trend for tickets performance===============================


def get_trend_indicator(trend_data):
    created = trend_data.get("created", 0)
    closed = trend_data.get("closed", 0)

    if closed > created:
        return "Improving 📉"
    elif created > closed:
        return "Worsening 📈"
    else:
        return "Stable ➖"


# ====================== trend for tickets performance ends here===================


# ===================== SLA Widget code ===========================


def get_sla_status_distribution():
    import sqlite3
    from datetime import datetime

    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()

    cursor.execute("""
        SELECT due_date 
        FROM knowledgeBase 
        WHERE due_date IS NOT NULL
    """)

    rows = cursor.fetchall()
    conn.close()

    now = datetime.now()

    sla_counts = {"On Track": 0, "At Risk": 0, "Breached": 0}

    for (due_date_str,) in rows:
        try:
            due_date = datetime.strptime(due_date_str, "%Y-%m-%d %H:%M:%S")
            diff_hours = (due_date - now).total_seconds() / 3600

            if diff_hours < 0:
                sla_counts["Breached"] += 1
            elif diff_hours <= 12:
                sla_counts["At Risk"] += 1
            else:
                sla_counts["On Track"] += 1

        except:
            continue

    return sla_counts


# ==================== SLA widget code ends ============================

# ======================= SLA updates ==============================


def get_sla_health(sla_counts):
    total = sum(sla_counts.values())

    if total == 0:
        return {"percentage": 0, "status": "No Data"}

    on_track = sla_counts.get("On Track", 0)
    at_risk = sla_counts.get("At Risk", 0)
    breached = sla_counts.get("Breached", 0)

    # SLA success = not breached
    success = total - breached
    percentage = round((success / total) * 100, 2)

    # Status logic
    if percentage >= 90:
        status = "Good ✅"
    elif percentage >= 75:
        status = "Warning ⚠️"
    else:
        status = "Critical 🔴"

    return {"percentage": percentage, "breached": breached, "status": status}


# ==================== SLA updates end =================================


# ==================== week on week intelligence trned =======================
def get_weekly_metrics():

    from datetime import datetime, timedelta

    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()

    today = datetime.now().date()

    # Date ranges
    current_start = today - timedelta(days=7)
    previous_start = today - timedelta(days=14)
    previous_end = current_start

    # ---------- CURRENT WEEK ----------
    cursor.execute(
        """
        SELECT COUNT(*) FROM knowledgeBase
        WHERE date >= ?
    """,
        (current_start.strftime("%Y-%m-%d"),),
    )
    current_created = cursor.fetchone()[0]

    cursor.execute(
        """
        SELECT COUNT(*) FROM knowledgeBase
        WHERE resolved_date IS NOT NULL
        AND resolved_date >= ?
    """,
        (current_start.strftime("%Y-%m-%d"),),
    )
    current_closed = cursor.fetchone()[0]

    cursor.execute(
        """
        SELECT COUNT(*) FROM knowledgeBase
        WHERE due_date < ?
        AND status NOT IN ('Done', 'Closed')
    """,
        (today.strftime("%Y-%m-%d %H:%M:%S"),),
    )
    current_missed = cursor.fetchone()[0]

    # ---------- PREVIOUS WEEK ----------
    cursor.execute(
        """
        SELECT COUNT(*) FROM knowledgeBase
        WHERE date >= ? AND date < ?
    """,
        (previous_start.strftime("%Y-%m-%d"), previous_end.strftime("%Y-%m-%d")),
    )
    prev_created = cursor.fetchone()[0]

    cursor.execute(
        """
        SELECT COUNT(*) FROM knowledgeBase
        WHERE resolved_date IS NOT NULL
        AND resolved_date >= ? AND resolved_date < ?
    """,
        (previous_start.strftime("%Y-%m-%d"), previous_end.strftime("%Y-%m-%d")),
    )
    prev_closed = cursor.fetchone()[0]

    cursor.execute(
        """
        SELECT COUNT(*) FROM knowledgeBase
        WHERE due_date < ?
        AND status NOT IN ('Done', 'Closed')
    """,
        (previous_end.strftime("%Y-%m-%d %H:%M:%S"),),
    )
    prev_missed = cursor.fetchone()[0]

    conn.close()

    # SLA %
    current_sla = (
        round(((current_closed - current_missed) / current_closed) * 100, 2)
        if current_closed
        else 0
    )
    prev_sla = (
        round(((prev_closed - prev_missed) / prev_closed) * 100, 2)
        if prev_closed
        else 0
    )

    # Labels
    def fmt(d):
        return d.strftime("%d %b")

    return {
        "current": {
            "created": current_created,
            "closed": current_closed,
            "missed": current_missed,
            "sla": current_sla,
            "label": f"{fmt(current_start)} - {fmt(today)}",
        },
        "previous": {
            "created": prev_created,
            "closed": prev_closed,
            "missed": prev_missed,
            "sla": prev_sla,
            "label": f"{fmt(previous_start)} - {fmt(previous_end)}",
        },
    }


# ==================== week on week trned code ends here =======================


# ========================== trend stability indicator =================
def get_weekly_trend(weekly_metrics):
    current = weekly_metrics["current"]
    previous = weekly_metrics["previous"]

    current_backlog = current["created"] - current["closed"]
    prev_backlog = previous["created"] - previous["closed"]

    if current_backlog > prev_backlog:
        return "⚠️ Backlog Increasing"
    elif current_backlog < prev_backlog:
        return "✅ Backlog Reducing"
    else:
        return "➖ Stable"


# ========================== trend stability code ends here ====================


# ============ fetch priority wise distribution of the tickets============
def get_priority_distribution():
    import sqlite3

    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()

    cursor.execute("""
        SELECT priority, COUNT(*) 
        FROM knowledgeBase 
        WHERE priority IS NOT NULL
        GROUP BY priority
    """)

    data = cursor.fetchall()
    conn.close()

    priority_counts = {"P1": 0, "P2": 0, "P3": 0, "P4": 0}

    for priority, count in data:
        if priority in priority_counts:
            priority_counts[priority] += count

    return priority_counts


# =================== pririoty fetching ends here=====================


# ======= fucntion to get db last synced time==============


def get_last_synced_time():
    import sqlite3

    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()

    cursor.execute("""
        SELECT MAX(last_synced) 
        FROM knowledgeBase 
        WHERE last_synced IS NOT NULL
    """)

    result = cursor.fetchone()
    conn.close()

    return result[0] if result and result[0] else "Not Synced Yet"


# =========== last sync function ends here ==============


# ========= Control tower code comes here ===================
def get_status_distribution():

    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()

    cursor.execute("""
        SELECT status, COUNT(*) 
        FROM knowledgeBase 
        WHERE status IS NOT NULL
        GROUP BY status
    """)

    data = cursor.fetchall()
    conn.close()

    status_counts = {"Open": 0, "In Progress": 0, "Closed": 0}

    for status, count in data:
        normalized = status.lower()

        if normalized in ["to do", "open"]:
            status_counts["Open"] += count
        elif normalized in ["in progress"]:
            status_counts["In Progress"] += count
        elif normalized in ["done", "closed", "resolved"]:
            status_counts["Closed"] += count

    return status_counts


# control tower code ends here============================


# ============== priority detemination starts ehre =====
def calculate_priority(env, users, revenue, workaround, region):

    score = 0

    # Environment
    score += 5 if env == "Prod" else 1

    # Users impacted
    if users == ">100":
        score += 5
    elif users == "30-100":
        score += 4
    elif users == "10-30":
        score += 3
    else:
        score += 1

    # Revenue impact
    score += 5 if revenue == "Yes" else 1

    # Workaround
    if workaround == "No":
        score += 5
    elif workaround == "Partial":
        score += 3
    else:  # Yes
        score += 1

    # Region boost
    if region == "Global":
        score += 3

    # Final mapping
    # 🚨 LOW IMPACT OVERRIDE (NEW)
    if (
        revenue == "No"
        and workaround in ["Yes", "Partial"]
        and users in ["<10", "10-30"]
    ):
        priority = "P4"

    # NORMAL LOGIC
    elif score >= 18:
        priority = "P1"
    elif score >= 14:
        priority = "P2"
    elif score >= 9:
        priority = "P3"
    else:
        priority = "P4"

    return priority, score


# ============== priority detemination ends ehre =====

# ======= SLA logic buikidng here============
from datetime import datetime, timedelta, timezone

# from zoneinfo import ZoneInfo


def calculate_due_date(priority):

    # now = datetime.now()
    # IST = pytz.timezone("Asia/Kolkata")
    # now = datetime.now(IST)
    IST = timezone(timedelta(hours=5, minutes=30))
    now = datetime.now(IST)

    if priority == "P1":
        return now + timedelta(hours=4)
    elif priority == "P2":
        return now + timedelta(hours=8)
    elif priority == "P3":
        return now + timedelta(days=2)
    elif priority == "P4":
        return now + timedelta(days=4)
    else:
        return now + timedelta(days=2)


# ======== sla logic ends here =====================


def send_telegram_alert(message, priority=None):
    token = os.getenv("TELEGRAM_BOT_TOKEN")
    chat_id = os.getenv("TELEGRAM_CHAT_ID")
    if priority not in ["P1", "P2"]:
        return

    url = f"https://api.telegram.org/bot{token}/sendMessage"

    payload = {"chat_id": chat_id, "text": message}
    try:
        response = requests.post(url, data=payload)
    except Exception as e:
        print("telegram err:", e)

    #print("Telegram response:", response.text)


# =============== telegram confog ends==================


def categorize_incident(text):
    words = set((text or "").lower().split())
    text_lower = (text or "").lower()

    # Frontend
    if "ajax" in text or "ui" in text or "frontend" in text:
        return "Frontend"

    # Database
    elif (
        "ora" in text
        or "sql" in text
        or "database" in text
        or "db" in text
        or "query" in text
        or "data type" in text
        or "table" in text
        or "table" in text
    ):
        return "Database"

    # API / Gateway
    elif "api" in text or "gateway" in text or ("timeout" in text and "api" in text):
        return "API"

    # Batch
    elif "job" in text or "batch" in text:
        return "Batch"

    # Infrastructure
    elif "memory" in text or "cpu" in text or "server" in text:
        return "Infrastructure"

    # Monitoring
    elif "alert" in text or "monitor" in text:
        return "Monitoring"

    else:
        return "Unclassified"


# def get_global_category_distribution():
# conn = sqlite3.connect(r"D:\pythonPractice\IntelliIQ.db")
# cursor = conn.cursor()

# cursor.execute("SELECT Incident FROM knowledgeBase")
# rows = cursor.fetchall()
# conn.close()

# category_counts = {}

# for row in rows:
#    incident_text = row[0]
#     category = categorize_incident(incident_text)

#      category_counts[category] = category_counts.get(category, 0) + 1

#   return category_counts
#


def get_global_category_distribution():
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()

    cursor.execute("""
        SELECT Category, normalized_incident
        FROM Knowledgebase
    """)

    rows = cursor.fetchall()
    conn.close()

    category_counts = {}

    for row in rows:
        category, normalized_incident = row

        final_category = category

        # Fallback logic (same as UI)
        if not category or category.lower() == "unclassified":
            if normalized_incident:
                final_category = normalized_incident.replace("_", " ").title()

        # Count aggregation
        category_counts[final_category] = category_counts.get(final_category, 0) + 1

    return category_counts


#print("db path: ", os.path.abspath("IntelliIQ.db"))
# ==========================================================
# STEP 2: LOAD ENV VARIABLES
# Purpose: Load API keys and configuration
# ==========================================================

# load_dotenv("mykeys.env")
load_dotenv()

project_key = os.getenv("JIRA_PROJECT_KEY")

# ==========================================================
# STEP 3: INITIALIZE LLM
# Purpose: Setup AI model for incident analysis
# ==========================================================

llm = ChatOpenAI(api_key=os.getenv("OPENAI_API_KEY"), model="gpt-4o-mini")

# ==========================================================
# STEP 4: PROMPT TEMPLATE + CHAIN
# Purpose:
# - Define AI response format
# - Create LangChain pipeline
# ==========================================================

prompt = PromptTemplate(
    input_variables=["incident"],
    template="""
You are an operations expert.

Analyze the incident and return ONLY valid JSON:

{{
  "summary": "1 line summary",
  "impact": "business impact",
  "root_cause": "probable cause",
  "recommendations": "Provide 4-5 clear, actionable troubleshooting steps in bullet style. Each step should be specific and practical. Separate each step using '.'",
  "confidence": "0-100%",
  "severity": "High/Medium/Low"
}}

Rules:
- Confidence should reflect how sure you are
- Severity should reflect business impact
- Do NOT return anything except JSON

Incident:
{incident}
""",
)

chain = prompt | llm | StrOutputParser()

# ==========================================================
# STEP 11: FLASK APP INIT
# ==========================================================

app = Flask(__name__)
app.secret_key = "intelliiq_secret_key_123"
# ==== Registering the apps used ==================
register_insurance_copilot(app, llm)
register_project_health(app)

register_ticket_dashboard(app)
#register_critical_metrics(app)
register_system_advisor(app)
register_business_impact_routes(app)

register_help_page(app)
register_process_doc(app, llm)
register_analyst_intelligence(app, llm)
register_analyst_detail(app, llm)
register_rca_routes(app, llm, DB_NAME)
register_log_analyzer_routes(app,llm,DB_NAME)
#app.register_blueprint(db_debug_bp)
#app.register_blueprint(incident_bp)

# ====== Add all apps registered between these blocks

# =================== route for opertions dashboard ================


@app.route("/operations_dashboard")
def operations_dashboard():

    # INCIDENT DATA
    incidents = get_all_incidents()
    global_category_counts = get_global_category_distribution()
    #top_performers = get_top_performers()
    #analyst_performance = get_analyst_performance()
    #analyst_insights = generate_analyst_insights()

    valid_categories = {
        k: v
        for k, v in global_category_counts.items()
        if k not in ["Unclassified", "Others", None, ""]
    }

    if valid_categories:
        top_category = max(valid_categories, key=valid_categories.get)
        top_count = valid_categories[top_category]
        total = sum(valid_categories.values())
        top_percentage = round((top_count / total) * 100)
    else:
        top_category = None
        top_percentage = 0

    # TICKET DATA
    from early_warning_engine import get_early_warnings
    from trend_engine import get_recurring_issues

    early_warnings = get_early_warnings()
    problem_tickets = get_recurring_issues()
    tickets = get_all_tickets()

    #============operations dashboard route ends=========================

   
    # ===== analyst risk aggregation (Phase 3 FIX - indentation corrected)=====


    analyst_summary = {}

    for t in tickets:

        assignee = t.get("assignee") or "Unassigned"
        #print("ASSIGNEE:", t.get("assignee"))
        risk = t.get("risk_level")

        # moved inside loop (fix)
        if assignee not in analyst_summary:
            analyst_summary[assignee] = {"high": 0, "medium": 0, "total": 0}

        if risk == "High":
            analyst_summary[assignee]["high"] += 1

        if risk == "Medium":
            analyst_summary[assignee]["medium"] += 1

        if risk in ["High", "Medium"]:
            analyst_summary[assignee]["total"] += 1

        # ==== analyst aggregation ends========

    # ===== adding risk summary counts (operations dashboard fix)=====
    summary = {"high": 0, "medium": 0, "safe": 0, "sla_met": 0, "sla_breached": 0}

    for t in tickets:

        risk = t.get("risk_level")
        sla_met = t.get("sla_met")
        status = (t.get("status") or "").lower()
        sla_status = (t.get("sla_status") or "").lower()

        if risk == "High":
            summary["high"] += 1

        if risk == "Medium":
            summary["medium"] += 1

        if risk == "Safe":
            summary["safe"] += 1

        if sla_met == "YES":
            summary["sla_met"] += 1

        if risk == "Closed Breached" or sla_status == "breached":
            summary["sla_breached"] += 1

    # ==== summary logic ends========

    return render_template(
        "operations_dashboard.html",
        early_warnings=early_warnings,
        problem_tickets=problem_tickets,
        tickets=tickets,
        summary=summary,
        analyst_summary=analyst_summary,
        #analyst_performance=analyst_performance,
        #analyst_insights=analyst_insights,
        global_category_counts=global_category_counts,
        top_category=top_category,
        top_percentage=top_percentage,
        #top_performers=top_performers,
        active_page="operations",
    )


# =================== operations DB route ends here===============





# ==========================================================
# GLOBAL TEMPLATE VARIABLES (AVAILABLE IN ALL HTML FILES)
# ==========================================================
@app.context_processor
def inject_global_vars():
    return dict(app_owner="Parikshit")


# ==========================================================
# STEP 12: HOME ROUTE
# ==========================================================


@app.route("/")
def home():
    #incident_prefill = request.args.get("incident", "")
    #return render_template("PC_IncidentAnalyser.html")
    return render_template("home.html")

@app.route(
    "/incidentLog_analyser",
    methods=["GET", "POST"]
)
#=============== adding this for log analyser=====================
@app.route(
    "/incidentLog_analyser",
    methods=["GET", "POST"]
)
def incident_workspace():

    if request.method == "GET":

        return render_template(
            "analyseIncidentLogs.html"
        )

    # ======================================================
    # COLLECT INCIDENT
    # ======================================================

    incident = request.form.get(
        "incident",
        "Log Investigation"
    )

    # ======================================================
    # COLLECT LOG CONTENT
    # ======================================================

    uploaded_files = []

    upload_fields = [

        "app_logs",
        "data_logs",
        "dynatrace_log",
        "product_logs",
        "middleware_logs",
        "api_logs"

    ]

    for field in upload_fields:

        files = request.files.getlist(
            field
        )

        for file in files:

            if file and file.filename:

                try:

                    content = file.read().decode(
                        "utf-8",
                        errors="ignore"
                    )

                    uploaded_files.append(

                        f"""

FILE: {file.filename}

{content[:5000]}

"""

                    )

                except Exception as e:

                    uploaded_files.append(

                        f"""

FILE: {file.filename}

Unable to read file.

Error:
{str(e)}

"""

                    )

    # ======================================================
    # BUILD EVIDENCE SUMMARY
    # ======================================================

    evidence_summary = "\n".join(
        uploaded_files
    )

    # ======================================================
    # AI PROMPT
    # ======================================================

    prompt = f"""

You are a Senior Production Support Engineer,
Site Reliability Engineer and RCA Specialist.

Analyze the uploaded logs carefully.

INCIDENT

{incident}

LOG EVIDENCE

{evidence_summary}

Return your response using EXACTLY the format below.

# SUMMARY

Provide a concise executive summary.

# LIKELY ROOT CAUSE

Identify the most probable root cause.

# EVIDENCE FOUND

List the log evidence supporting your conclusion.

# RECOMMENDED ACTIONS

Provide actionable troubleshooting steps.

# OPERATIONAL IMPACT

Describe the business and operational impact.

# CONFIDENCE

Choose only one:

HIGH
MEDIUM
LOW

Do not include any other headings.

"""

    # ======================================================
    # LLM ANALYSIS
    # ======================================================

    response = llm.invoke(
        prompt
    )

    ai_analysis = (

        response.content

        if hasattr(
            response,
            "content"
        )

        else str(response)

    )

    # ======================================================
    # RETURN RESULT
    # ======================================================

    return render_template(

        "analyseIncidentLogs.html",

        ai_analysis=ai_analysis

    )




#============== log analyser ends here ============================

@app.route("/incident-analysis")
def incident_analysis():

    incident_prefill = request.args.get(
        "incident",
        ""
    )

    return render_template(
        "PC_IncidentAnalyser.html"
    )


from trend_engine import get_recurring_issues

# print("RECURRING ISSUES:", get_recurring_issues())

# =========================== incidnet explorer code here===============


def get_all_incidents():
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()

    cursor.execute("""
        SELECT Incident, Category, Jira_Ticket_Id, Date, normalized_incident
        FROM knowledgeBase
        ORDER BY date DESC
    """)

    rows = cursor.fetchall()

    processed_incidents = []  # ✅ initialize list

    for r in rows:
        incident, category, ticket_id, date, normalized_incident = r

        final_category = category

        if not category or category.lower() == "unclassified":
            if normalized_incident:
                final_category = normalized_incident.replace("_", " ").title()

        processed_incidents.append((incident, final_category, ticket_id, date))

    conn.close()

    return processed_incidents  # ✅ inside function


# ======================== incident explprer code ends here====================




# ==========================================================
# ====== NEW CODE ADDED ON 19 MAY FOR PENDING INCIDENT TRACKING ======
# ==========================================================

def save_analyzed_incident(

    incident,
    solution,
    root_cause,
    category,
    priority,
    due_date,
    env,
    users,
    region,
    revenue,
    workaround,
    normalized_incident

):

    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()

    # ======================================================
    # AVOID DUPLICATE PENDING RECORDS commenting this block on 30th may
    # ======================================================

    #cursor.execute("""

     #   SELECT KB_ID
      #  FROM knowledgeBase
       # WHERE LOWER(TRIM(incident)) = LOWER(TRIM(?))
        #ORDER BY KB_ID DESC
        #LIMIT 1

    #""", (incident,))

    #existing = cursor.fetchone()

   # if existing:

    #    kb_id = existing[0]

     #   conn.close()

      #  print(
       #     f"Existing KB_ID = {kb_id}")

      #  return kb_id

    # ======================================================
    # INSERT PRELIMINARY INCIDENT RECORD
    # ======================================================

    now = datetime.now()

    date = now.strftime("%Y-%m-%d")
    time = now.strftime("%H:%M:%S")

    keywords = " ".join(
        incident.lower().split()
    )

    try:

        due_date_db = due_date.strftime(
            "%Y-%m-%d %H:%M:%S"
        )

    except:

        due_date_db = None

    cursor.execute("""

        INSERT INTO knowledgeBase (

            incident,
            solution,
            root_cause,
            category,
            date,
            time,
            keywords,
            jira_ticket_id,
            priority,
            due_date,
            environment,
            users_impacted,
            region,
            revenue_impact,
            workaround,
            normalized_incident

        )

        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)

    """, (

        incident,
        solution,
        root_cause,
        category,
        date,
        time,
        keywords,
        None,
        priority,
        due_date_db,
        env,
        users,
        region,
        revenue,
        workaround,
        normalized_incident

    ))
    try:

            kb_id = cursor.lastrowid

            conn.commit()

            #print(f"Saved KB_ID = {kb_id}")

            return kb_id

    finally:

        conn.close()


# ==========================================================
# ====== 19 MAY CODE ENDS ==================================
# ==========================================================











# =========================== dashboard creation =====================
@app.route("/dashboard")
def dashboard():

    # send_telegram_alert("🚀 IntelliIQ Test Alert: Telegram integration working!")
    # global_category_counts = get_global_category_distribution()
    # print("global_category_counts:", global_category_counts)
    # print("DEBUG max value:", max(global_category_counts.values()))

    incidents = get_all_incidents()
    # if global_category_counts:
    #   top_category = max(global_category_counts, key=global_category_counts.get)
    #  top_count = global_category_counts[top_category]
    # total = sum(global_category_counts.values())
    # top_percentage = round((top_count / total) * 100)
    # else:
    #   top_category = None
    #  top_percentage = 0

    # recommendation = "No recommendation available"

    global_category_counts = get_global_category_distribution()

    # Remove weak categories
    valid_categories = {
        k: v
        for k, v in global_category_counts.items()
        if k not in ["Unclassified", "Others", None, ""]
    }

    if valid_categories:
        top_category = max(valid_categories, key=valid_categories.get)
        top_count = valid_categories[top_category]
        total = sum(valid_categories.values())
        top_percentage = round((top_count / total) * 100)
    else:
        top_category = None
        top_percentage = 0

   # print("FINAL category counts:", global_category_counts)
   # print("VALID categories:", valid_categories)
   # print("TOP category:", top_category)
   # print("top_category:", top_category)

    recommendation = "No recommendation available"
    if top_category == "Frontend":
        recommendation = (
            "Frontend issues dominate — review UI flows, API calls, and error handling"
        )

    elif top_category == "Database":
        recommendation = "Database issues are frequent — check queries, indexing, and connection handling"

    elif top_category == "API":
        recommendation = "Review API configuration — check timeout settings, contact 3rd party provider"

    elif top_category == "Batch":
        recommendation = (
            "Batch job failures detected — review schedulers and job dependencies"
        )

    elif top_category == "Infrastructure":
        recommendation = (
            "Infrastructure issues rising — monitor memory, CPU, and server health"
        )

    else:
        recommendation = "Monitor incident trends for emerging patterns"

    return render_template(
        "dashboard.html",
        global_category_counts=global_category_counts,
        top_category=top_category,
        top_percentage=top_percentage,
        recommendation=recommendation,
        incidents=incidents,
        active_page="dashboard",
    )


# dashboard creaton ends here====================================

# ==========================================================
# STEP 13: ANALYZE INCIDENT
# ==========================================================


@app.route("/analyze", methods=["POST"])
def analyze():
    # print("Analyse function invoked")

    decision = ""
    incident = request.form.get("incident", "").strip()
    from normalization_engine import normalize_incident

    normalized_incident = normalize_incident(incident)

    product = request.form.get("product")
    # priority = request.form["priority"]
    env = request.form.get("environment")
    users = request.form.get("users_impacted")
    region = request.form.get("region_impacted")
    revenue = request.form.get("revenue_impact")
    workaround = request.form.get("workaround")

   # print("RAW:", incident)
   # print("NORMALIZED:", normalized_incident)

    priority, score = calculate_priority(env, users, revenue, workaround, region)
    # ===== PRIORITY REASONS =====
    priority_reasons = []

    if env == "Prod":
        priority_reasons.append("Production environment")

    if users == ">100":
        priority_reasons.append("High user impact (>100 users)")
    elif users == "30-100":
        priority_reasons.append("Moderate user impact (30–100 users)")
    elif users == "10-30":
        priority_reasons.append("Limited user impact (10–30 users)")
    else:
        priority_reasons.append("Minimal user impact (<10 users)")

    if revenue == "Yes":
        priority_reasons.append("Revenue impact present")

    if workaround == "No":
        priority_reasons.append("No workaround available")

    if region == "Global":
        priority_reasons.append("Global impact")

    due_date = calculate_due_date(priority)

    now = datetime.now(due_date.tzinfo)
    delta = due_date - now

    hours = int(delta.total_seconds() // 3600)

    if hours < 24:
        sla_text = f"In {hours} hours"
    else:
        days = hours // 24
        sla_text = f"In {days} days"

    # ==== for product based search =====
    incident_lower = incident.lower()

    issue_type = "general"

    if "batch" in incident_lower or "job" in incident_lower:
        issue_type = "batch"

    elif (
        "ui" in incident_lower
        or "frontend" in incident_lower
        or "screen" in incident_lower
    ):
        issue_type = "frontend"

    elif (
        "database" in incident_lower
        or "db" in incident_lower
        or "query" in incident_lower
    ):
        issue_type = "database"

    elif (
        "log" in incident_lower
        or "monitor" in incident_lower
        or "alert" in incident_lower
    ):
        issue_type = "monitoring"

    # ==== product based search ends=======

    ai_output = chain.invoke({"incident": incident})
    data = json.loads(ai_output)




    print("AI DAta: ", data)
    print("parikshit is working hard")

    # old SLA logic
    # if priority == "High":
    #   due_date = datetime.now() + timedelta(hours=4)
    # elif priority == "Medium":
    #   due_date = datetime.now() + timedelta(days=1)
    # else:
    #   due_date = datetime.now() + timedelta(days=3)
    # ================ calling kb_engine========================================

    # match, score, frequency, top_root_cause, matches = search_kb_new(incident)- commented this to replace the CSV with DB
    # ============ db search code starts ===================
    result = search_kb_new(incident)
    # ==========================================================
    # HISTORICAL RCA INTELLIGENCE
    # ==========================================================

    historical_rca = search_historical_rca(
        incident
    )

    historical_rca_found = (
        historical_rca is not None
    )
        # ==========================================================
    # RCA IS NOW THE PRIMARY SOURCE OF TRUTH
    # ==========================================================

    #show_kb_results = not historical_rca_found
    show_kb_results = result is not None

    if result:
        match = result.get("match")
        if match:
            existing_ticket = match.get("jira_ticket_id")
        else:
            existing_ticket = None

        score = result.get("score", 0)
        frequency = result.get("frequency", 0)
        top_root_cause = result.get("top_root_cause", "")
        matches = result.get("matches", [])

        


        # ===== CLUSTERING LOGIC START =====
        category_counts = {}

        for m in matches:
            row = m[0]
            incident_text = row[0]

            category = categorize_incident(incident_text)

            category_counts[category] = category_counts.get(category, 0) + 1

        # ===== CLUSTERING LOGIC END =====
    else:
        match = None
        score = 0
        frequency = 0
        top_root_cause = ""
        matches = []
        category_counts = {}
    # ============== db search code ends===================

    # ===================Kb_engine call ends =======================================

    # ================= calling decision logic ==================

    decision = get_decision(frequency, data)

    # ================= end of decision logic ====================

    # ===================== calling trends engine===================

    count_1d, count_3d, count_5d, count_7d, count_older, trend_message = (
        calculate_trends(matches, frequency)
    )
    # print("DEBUG → count_1d:", count_1d)
    # print("DEBUG → frequency:", frequency)
    # ===== TELEGRAM ALERT FOR SPIKE =====

    if count_1d >= 3 and count_1d >= 0.5 * frequency:
        alert_message = f"""
        🚨 IntelliIQ Alert: Spike Detected!

        Issue: {incident}
        Category: {categorize_incident(incident)}

        Recent Incidents (24 hrs): {count_1d}
        Total Matches: {frequency}

        Trend Insight: {trend_message}
        """

        send_telegram_alert(alert_message, priority)

    # ==================== END TREND ENGINE =========================

    # ===== CALLING SUGGESTION ENGINE =========================

    suggestions = generate_suggestions(data, matches)

    # ==================END SUGGESTION ENGINE ===================
    suggestions = enhance_with_domain(product, suggestions, incident)


    # ==========================================================
    # ====== NEW CODE ADDED ON 19 MAY FOR AUTO INCIDENT SAVE ======
    # ==========================================================

    try:

        category = categorize_incident(incident)

        if not category or category.lower() == "unclassified":
            if normalized_incident:
                category = normalized_incident.replace("_", " ").title()


        # =====================================================
        # INCIDENT PERSISTENCE
        #
        # Analyze now creates the knowledgeBase record.
        #
        # The returned KB_ID is passed to the UI and later
        # used by Create Ticket and Create Confluence to
        # update the SAME row instead of creating duplicates.
        # =====================================================
        kb_id=save_analyzed_incident(

            incident=incident,

            solution=data.get(
                "recommendations",
                ""
            ),

            root_cause=data.get(
                "root_cause",
                ""
            ),

            category=category,

            priority=priority,

            due_date=due_date,

            env=env,

            users=users,

            region=region,

            revenue=revenue,

            workaround=workaround,

            normalized_incident=normalized_incident

        )
        #print("ANALYZE KB_ID =", kb_id)

    except Exception as save_error:
        import traceback

        #print("Pending incident save error:",str(save_error))
        traceback.print_exc()

    # ==========================================================
    # ====== 19 MAY AUTO SAVE CODE ENDS ========================
    # ==========================================================


    # ===========troubleshooting suggestions code ends here=============

    # print("Match keys:", matches[0].keys()
    # if matches else "No matches found")

    if frequency > 3:
        pattern_flag = "Recurring Issue"
    elif frequency > 1:
        pattern_flag = "Occasional Issue"
    else:
        pattern_flag = "New / Rare Issue"

    if match and match.get("jira_ticket_id"):
        existing_ticket = match.get("jira_ticket_id")
        # print("Exisitng Ticket is :", existing_ticket)
    else:
        existing_ticket = None

        # print("exisitng ticket:", existing_ticket)

    ticket_list = []
    for m in matches:
        ticket_id = m[0][4]

        if ticket_id:
            ticket_list.append(ticket_id)
    global_category_counts = get_global_category_distribution()
    if global_category_counts:
        top_category = max(global_category_counts, key=global_category_counts.get)
        top_count = global_category_counts[top_category]
        total = sum(global_category_counts.values())
        top_percentage = round((top_count / total) * 100)
    else:
        top_category = None
        top_percentage = 0
    #print("Global Category Counts:", global_category_counts)

    priority_message = f"Based on the incident and its impact, this should be treated as a Priority {priority} incident (Score: {score})"

    return render_template(
        "PC_IncidentAnalyser.html",
        data=data,
        # due_date=due_date,
        sla_text=sla_text,
        due_date=due_date.strftime("%d %b %Y, %I:%M %p"),
        due_date_iso=due_date.isoformat(),
        priority=priority,
        priority_reasons=priority_reasons,
        incident=incident,
        kb_solution=match["solution"] if match else None,
        kb_root_cause=match["root_cause"] if match else None,
        match_score=score,
        frequency=frequency,
        top_root_cause=top_root_cause,
        pattern_flag=pattern_flag,
        existing_ticket=existing_ticket,
        ticket_list=ticket_list,
        suggestions=suggestions,
        historical_rca=historical_rca,
        historical_rca_found=historical_rca_found,
        show_kb_results=show_kb_results,
        count_1d=count_1d,
        count_3d=count_3d,
        count_5d=count_5d,
        count_7d=count_7d,
        count_older=count_older,
        trend_message=trend_message,
        decision=decision,
        product=product,
        category_counts=category_counts,
        global_category_counts=global_category_counts,
        top_category=top_category,
        top_percentage=top_percentage,
        # rca_output=rca_output,
        users_impacted=users,
        region=region,
        revenue_impact=revenue,
        workaround=workaround,
        environment=env,
        show_result=True,
        kb_id=kb_id,
        active_page="home",
    )







# ==========================================================
# STEP 14: CREATE JIRA TICKET
# ==========================================================


# ============= generating simple rca===================
def generate_rca_simple(
    incident, ticket_id, impact, notes, resolution_notes, status, team, fix_date
):

    prompt = f"""
    You are an expert support engineer.

    Generate a structured RCA in JSON format:

    {{
      "issue": "",
      "ticket_id": "",
      "impact": "",
      "root_cause": "",
      "resolution": "",
      "preventive_actions": "",
      "status": "",
      "team": "",
      "fix_date": ""
    }}

    Inputs:
    Incident: {incident}
    Ticket ID: {ticket_id}
    Impact: {impact}
    Notes: {notes}
    Resolution Notes: {resolution_notes}
    Status: {status}
    Team: {team}
    Fix Date: {fix_date}

    IMPORTANT:
    - Use resolution_notes to generate resolution
    - Expand it professionally
    - Output ONLY valid JSON
    """

    try:
        response = llm.invoke(prompt)

        raw_text = response.content.strip()
        #print("RAW LLM OUTPUT:", raw_text)

        # 🔥 Remove ```json wrapper
        if raw_text.startswith("```"):
            raw_text = raw_text.replace("```json", "").replace("```", "").strip()

        rca_output = json.loads(raw_text)

    except Exception as e:
        #print("RCA error:", e)

        rca_output = {
            "issue": incident,
            "ticket_id": ticket_id,
            "impact": impact,
            "root_cause": "Could not parse AI response",
            "resolution": resolution_notes,
            "preventive_actions": "Monitor system and logs",
            "status": status,
            "team": team,
            "fix_date": fix_date,
        }

    return rca_output


# ============= simple rca block ends =====================


@app.route("/create_ticket", methods=["POST"])
def create_ticket():
    if request.form["create"] == "no":
        return render_template("PC_IncidentAnalyser.html")

    # this is old value summary = request.form["summary"]

    # changed this on 17th april after indentifying duplication issue summary = request.form.get("summary")
    incident = request.form.get("incident")
        # =====================================================
    # UPDATE EXISTING INCIDENT RECORD
    #
    # Do NOT insert a new knowledgeBase row here.
    #
    # Analyze has already created the record.
    # Use KB_ID to update the existing row.
    # =====================================================
    kb_id = request.form.get("kb_id")

   # print("CREATE TICKET KB_ID =",kb_id)

    from normalization_engine import normalize_incident

    normalized_incident = normalize_incident(incident)

    summary = incident
    # changes above are for 17th april code
    impact = request.form["impact"]
    root_cause = request.form["root_cause"]
    recommendations = request.form["recommendations"]
    #print("Normalized:", normalized_incident)

    from datetime import datetime, timedelta

    # Always define due_date BEFORE using it
    # priority = request.form.get("priority")
    # ==== new columns added to the database
    env = request.form.get("environment")
    users = request.form.get("users_impacted")
    region = request.form.get("region_impacted")
    revenue = request.form.get("revenue_impact")
    workaround = request.form.get("workaround")
    # priority, _ = calculate_priority(env, users, revenue, workaround, region)
    # due_date = calculate_due_date(priority)
    priority = request.form.get("priority")
    due_date = request.form.get("due_date")

    # == new columns end here
    description = f"""
    Impact: {impact}
    Root Cause: {root_cause}
    Recommendations: {recommendations}
    """

    # ticket_key = create_jira_ticket(summary, description, due_date)
    from datetime import datetime

    parsed_date = datetime.fromisoformat(due_date)
    jira_due_date = parsed_date.strftime("%Y-%m-%d")

    ticket_key = create_jira_ticket(summary, description, jira_due_date)
    # =================== push rca to confluence=================

    # ================ rca to confluence ends ======================

    # ===== TELEGRAM ALERT FOR TICKET CREATION =====

    alert_message = f"""
    🎟 IntelliIQ Alert: New Ticket Created

    Ticket ID: {ticket_key}
    Summary: {summary}

    Impact: {impact}
    Root Cause: {root_cause}

    Recommendation:
    {recommendations}
    """
    from datetime import datetime, timedelta

    # Basic SLA logic (can refine later)
    # due_date = datetime.now() + timedelta(days=2)

    send_telegram_alert(alert_message, priority)

    ticket_link = f"{os.getenv('JIRA_URL')}/browse/{ticket_key}"
    jira_ticket_id = ticket_link.split("/")[-1]
    #print("New Ticket ID " + jira_ticket_id)
    #print("form data is here ", request.form)

    # =====================================================
    # updating the csv file with the new ticekt details
    # =====================================================

    # import csv
    # from datetime import datetime

    # now = datetime.now()
    # date = now.strftime("%Y-%m-%d")
    # time = now.strftime("%H:%M:%S")

    # incident = request.form.get("incident")
    solution = request.form.get("recommendations")
    root_cause = request.form.get("root_cause")

    keywords = " ".join(incident.lower().split())

    # ===== INSERT INTO SQLITE =====
    # =====================================================
# UPDATE EXISTING ANALYZED INCIDENT
# =====================================================

    kb_id = request.form.get("kb_id")

   # print("UPDATING KB_ID =",kb_id)

    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()

    try:

        parsed = datetime.fromisoformat(
            due_date
        )

        due_date_db = parsed.strftime(
            "%Y-%m-%d %H:%M:%S"
        )

    except:

        due_date_db = due_date
        #================== 30 may adding this block to debug the update command=======
        #print("\n" + "=" * 61)
        #print("CREATE TICKET UPDATE DEBUG")
        #print("=" * 61)

        #print("KB_ID             :", kb_id)
        #print("Incident          :", incident)
        #print("Solution          :", solution)
        #print("Root Cause        :", root_cause)
        #print("Jira Ticket ID    :", jira_ticket_id)
        #print("Priority          :", priority)
        #print("Due Date          :", due_date_db)
        #print("Environment       :", env)
        #print("Users Impacted    :", users)
        #print("Region            :", region)
        #print("Revenue Impact    :", revenue)
        #print("Workaround        :", workaround)
        #print("Normalized        :", normalized_incident)

        #print("=" * 61)


        #=================== debug ends on 30th may=============================

    cursor.execute(

        """
        UPDATE knowledgeBase

        SET

            solution = ?,
            root_cause = ?,
            jira_ticket_id = ?,
            priority = ?,
            due_date = ?,
            environment = ?,
            users_impacted = ?,
            region = ?,
            revenue_impact = ?,
            workaround = ?,
            normalized_incident = ?

        WHERE KB_ID = ?
        """,

        (

            solution,
            root_cause,
            jira_ticket_id,
            priority,
            due_date_db,
            env,
            users,
            region,
            revenue,
            workaround,
            normalized_incident,
            kb_id

        )

    )

    #print(f"Rows Updated = {cursor.rowcount}")

    conn.commit()
    conn.close()
    # ===== END SQLITE INSERT =====
    return render_template(
        "PC_IncidentAnalyser.html",
        ticket_link=ticket_link,
        summary=summary,
        impact=impact,
        root_cause=root_cause,
        recommendations=recommendations,
    )




# ==========================================================
# ====== NEW CODE ADDED ON 19 MAY FOR DASHBOARD TICKET CREATION ======
# ==========================================================

@app.route("/create_ticket_from_dashboard", methods=["POST"])
def create_ticket_from_dashboard():

    incident = request.form.get("incident")
    kb_id = request.form.get("kb_id")
    print("KB_ID:", kb_id)

    print("Dashboard Create Ticket Request:", incident)

    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()

    cursor.execute(
        """
        SELECT
            incident,
            solution,
            root_cause,
            priority,
            due_date
        FROM knowledgeBase
        WHERE KB_ID = ?
        ORDER BY KB_ID DESC
        LIMIT 1
        """,
        (kb_id,)

        
    )

    row = cursor.fetchone()

    if not row:

        conn.close()
        print("Incident not found in knowledgeBase")
        return "Incident not found"

    incident, solution, root_cause, priority, due_date = row

    description = f"""

Root Cause:
{root_cause}

Recommendations:
{solution}

"""

    try:

        parsed_due_date = datetime.fromisoformat(due_date)

        jira_due_date = parsed_due_date.strftime("%Y-%m-%d")

    except Exception as due_date_error:

        print("Due Date Parse Error:", str(due_date_error))
        jira_due_date = None

    ticket_key = create_jira_ticket(
        incident,
        description,
        jira_due_date
    )

    print("Returned Ticket:", ticket_key)

    cursor.execute(
        """
        UPDATE knowledgeBase
        SET Jira_Ticket_Id = ?
        WHERE KB_ID = ?
        """,
        (
            ticket_key,
            kb_id
        )
    )

    print("Rows Updated:", cursor.rowcount)

    conn.commit()
    conn.close()

    return redirect("/operations_dashboard")

# ==========================================================
# ====== 19 MAY DASHBOARD TICKET CREATION CODE ENDS ========
# ==========================================================




# ==========================================================
# ====== NEW CODE ADDED ON 20 MAY FOR DASHBOARD CONFLUENCE ======
# ==========================================================

@app.route("/create_confluence_from_dashboard", methods=["POST"])
def create_confluence_from_dashboard():

    incident = request.form.get("incident")
    kb_id = request.form.get("kb_id")

    print("KB_ID:", kb_id)

    print("Dashboard Create Confluence Request:", incident)

    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()

    cursor.execute(
        """
        SELECT
            Jira_Ticket_Id,
            incident,
            root_cause,
            solution
        FROM knowledgeBase
        WHERE KB_ID = ?
        ORDER BY KB_ID DESC
        LIMIT 1
        """,
        (kb_id,)
    )

    row = cursor.fetchone()

    if not row:

        conn.close()
        print("Incident not found in knowledgeBase")
        return "Incident not found"

    jira_key, incident, root_cause, solution = row

    impact = "Operational Impact"

    page_link = create_confluence_page(
        incident,
        impact,
        root_cause,
        solution,
        jira_key
    )

    print("Confluence Link:", page_link)

    cursor.execute(
        """
        UPDATE knowledgeBase
        SET confluence_link = ?
        WHERE KB_ID = ?
        """,
        (
            page_link,
            kb_id
        )
    )

    print("Rows Updated:", cursor.rowcount)

    try:

        add_jira_comment(
            jira_key,
            page_link
        )

    except Exception as jira_comment_error:

        print("Jira Comment Error:", str(jira_comment_error))

    conn.commit()
    conn.close()

    return redirect("/operations_dashboard")

# ==========================================================
# ====== 20 MAY DASHBOARD CONFLUENCE CODE ENDS =============
# ==========================================================







# ==========================================================
# STEP 15: CREATE CONFLUENCE PAGE
# ==========================================================


@app.route("/create_confluence", methods=["POST"])
def create_confluence():
    if request.form["create_conf"] == "no":
        return render_template("PC_IncidentAnalyser.html")

    # summary = request.form["summary"]
    incident = request.form.get("incident")
    impact = request.form["impact"]
    root_cause = request.form["root_cause"]
    recommendations = request.form["recommendations"]
    ticket_link = request.form["ticket_link"]

    result = search_kb_new(incident)

    if result:
        match = result["match"]
        matches = result["matches"]
    else:
        match = None
        matches = []

    ticket_list = []

    if match and match.get("jira_ticket_id"):
        ticket_list.append(match["jira_ticket_id"])

    jira_key = ticket_link.split("/")[-1]

    page_link = create_confluence_page(
        incident, impact, root_cause, recommendations, jira_key
    )

    add_jira_comment(jira_key, page_link)

    # ==========================================================
    # ====== NEW CODE ADDED ON 19 MAY FOR CONFLUENCE PERSISTENCE ======
    # ==========================================================

    try:

        conn = sqlite3.connect(DB_NAME)
        cursor = conn.cursor()

        cursor.execute(

            """
            UPDATE knowledgeBase
            SET confluence_link = ?
            WHERE jira_ticket_id = ?
            """,

            (
                page_link,
                jira_key
            )
        )

        conn.commit()
        conn.close()

    except Exception as conf_error:

        print("Confluence persistence error:",str(conf_error))

    # ==========================================================
    # ====== 19 MAY CONFLUENCE PERSISTENCE CODE ENDS ===========
    # ==========================================================

    return render_template(
            "PC_IncidentAnalyser.html",
            confluence_link=page_link,
            ticket_link=ticket_link,
            # rca_output=rca_output,
            # matches=matches,
            # ticket_list=ticket_list
        )

#===== performance snapshot trigger (manual - correct placement)=====
@app.route("/run_performance_snapshot")
def run_performance_snapshot():

    try:
        generate_performance_snapshot()
        return "✅ Performance snapshot generated successfully"

    except Exception as e:
        return f"❌ Error: {str(e)}"
#==== snapshot trigger ends========

# ==========================================================
# STEP 16: RUN APP
# ==========================================================


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port)
