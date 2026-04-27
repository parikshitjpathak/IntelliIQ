# ==========================================================
# TICKET DASHBOARD MODULE (CLEAN + FINAL)
# ==========================================================

import sqlite3
from datetime import datetime
import requests
from requests.auth import HTTPBasicAuth
from flask import render_template, request, jsonify   # ✅ IMPORTANT

# ==========================================================
# CONFIGURATION
# ==========================================================

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_NAME = os.path.join(BASE_DIR, "IntelliIQ.db")

import os
from dotenv import load_dotenv

load_dotenv()

JIRA_BASE_URL = os.getenv("JIRA_URL")
EMAIL = os.getenv("JIRA_EMAIL")
API_TOKEN = os.getenv("JIRA_API_TOKEN")

# ==========================================================
# FETCH JIRA DETAILS
# ==========================================================

def get_jira_details(ticket_id):

    if not JIRA_BASE_URL or not ticket_id:
        return {"status": "Unknown", "due_date": None, "assignee": "Unassigned"}

    url = f"{JIRA_BASE_URL}/rest/api/3/issue/{ticket_id}"

    try:
        response = requests.get(
            url,
            headers={"Accept": "application/json"},
            auth=HTTPBasicAuth(JIRA_EMAIL, JIRA_API_TOKEN)
        )

        if response.status_code != 200:
            return {"status": "Unknown", "due_date": None, "assignee": "Unassigned"}

        data = response.json()

        status = data["fields"]["status"]["name"]
        due_date = data["fields"].get("duedate")

        assignee = data["fields"].get("assignee")
        assignee_name = assignee.get("displayName", "Unassigned") if isinstance(assignee, dict) else "Unassigned"

        return {
            "status": status,
            "due_date": due_date,
            "assignee": assignee_name
        }

    except:
        return {"status": "Error", "due_date": None, "assignee": "Unassigned"}


# ==========================================================
# FETCH + PROCESS TICKETS
# ==========================================================

def get_all_tickets():

    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()

    cursor.execute("""
                   
                   SELECT Incident, Category, Jira_Ticket_Id, Date, problem_ticket_id, due_date,normalized_incident    
                   FROM knowledgeBase
                   WHERE Jira_Ticket_Id IS NOT NULL AND Jira_Ticket_Id != ''
                   ORDER BY Date DESC
                   """)

    rows = cursor.fetchall()
    conn.close()

    tickets = []
    today = datetime.now()

    for r in rows:

        incident, category, ticket_id, date_str, problem_ticket_id,db_due_date,normalized_incident  = r
        # ===== CATEGORY FALLBACK LOGIC =====
        final_category = category

        if not category or category.lower() == "unclassified":
            if normalized_incident:
                final_category = normalized_incident.replace("_", " ").title()

        jira_data = get_jira_details(ticket_id)

        jira_status = jira_data["status"]
        jira_due_date = jira_data["due_date"]
        jira_assignee = jira_data["assignee"]

        #try:
         #   due_date_obj = datetime.strptime(jira_due_date, "%Y-%m-%d") if jira_due_date else None
        #except:
         #   due_date_obj = None
        try:
            due_date_obj = datetime.fromisoformat(db_due_date)
        except:
            due_date_obj = None

        try:
            created_date = datetime.strptime(date_str, "%Y-%m-%d")
            days_open = (today - created_date).days
        except:
            days_open = 0

        # SLA LOGIC
        if jira_status and jira_status.lower() in ["done", "closed", "resolved"]:
            sla_status = "Completed"
            sla_color = "blue"

        elif due_date_obj:
            now = datetime.now(due_date_obj.tzinfo)

            time_remaining = due_date_obj - now

            if time_remaining.total_seconds() < 0:
                sla_status = "Breached"
                sla_color = "red"
            elif time_remaining.total_seconds() <= 86400:  # 24 hours
                sla_status = "At Risk"
                sla_color = "orange"
            else:
                sla_status = "On Track"
                sla_color = "green"
        else:
            sla_status = "Unknown"
            sla_color = "grey"

        jira_link = f"{JIRA_BASE_URL}/browse/{ticket_id}"
        try:
            formatted_due_date = due_date_obj.strftime("%d %b %Y, %I:%M %p")
        except:
            formatted_due_date = db_due_date  # fallback

        tickets.append({
            "incident": incident,
            "category": final_category,
            "ticket_id": ticket_id,
            "date": date_str,
            "jira_status": jira_status,
            #"due_date": jira_due_date,
            "due_date": formatted_due_date,
            "assignee": jira_assignee,
            "sla_status": sla_status,
            "sla_color": sla_color,
            "jira_link": jira_link,
            "days_open": days_open,
            "problem_ticket_id": problem_ticket_id,
        })

    return tickets


# ==========================================================
# ROUTES
# ==========================================================

def register_ticket_dashboard(app):

    # ================================
    # PROBLEM DASHBOARD
    # ================================
    @app.route("/problem_dashboard")
    def problem_dashboard():

        conn = sqlite3.connect(DB_NAME)
        cursor = conn.cursor()

        cursor.execute("""
            SELECT id, incident, occurrence_count, window_days, created_at, jira_ticket_id
            FROM ProblemTickets
            ORDER BY created_at DESC
        """)

        rows = cursor.fetchall()
        conn.close()

        problems = []

        for r in rows:
            problems.append({
                "id": r[0],
                "incident": r[1],
                "count": r[2],
                "window": r[3],
                "created": r[4],
                "jira_ticket_id": r[5]
            })

        return render_template("problem_dashboard.html", problems=problems)


    # ================================
    # TICKET DASHBOARD
    # ================================
    @app.route("/ticket_dashboard")
    def ticket_dashboard():

        from early_warning_engine import get_early_warnings

        early_warnings = get_early_warnings()

        from trend_engine import get_recurring_issues

        problem_tickets = get_recurring_issues()
        tickets = get_all_tickets()



        return render_template(
            "ticket_dashboard.html",
            tickets=tickets,
            problem_tickets=problem_tickets,
            early_warnings=early_warnings
        )


    # ================================
    # CREATE PROBLEM TICKET
    # ================================
    @app.route("/create_problem_ticket", methods=["POST"])
    def create_problem_ticket():

        incident = request.form.get("incident")
        count = request.form.get("count")
        window_days = request.form.get("window_days")

        jira_url = f"{JIRA_BASE_URL}/rest/api/3/issue"

        payload = {
            "fields": {
                "project": {"key": "TES"},
                "summary": f"[PROBLEM] {incident}",
                "description": {
                    "type": "doc",
                    "version": 1,
                    "content": [{
                        "type": "paragraph",
                        "content": [{
                            "type": "text",
                            "text": f"Recurring Issue Detected\n\nIncident: {incident}\nOccurrences: {count}\nWindow: {window_days} days"
                        }]
                    }]
                },
                "issuetype": {"name": "Task"}
            }
        }

        response = requests.post(
            jira_url,
            json=payload,
            headers={"Accept": "application/json", "Content-Type": "application/json"},
            auth=HTTPBasicAuth(JIRA_EMAIL, JIRA_API_TOKEN)
        )

        jira_ticket_id = None

        if response.status_code == 201:
            jira_ticket_id = response.json().get("key")

        # SAVE TO DB
        conn = sqlite3.connect(DB_NAME)
        cursor = conn.cursor()

        cursor.execute("""
            INSERT INTO ProblemTickets (incident, occurrence_count, window_days, created_at, jira_ticket_id)
            VALUES (?, ?, ?, ?, ?)
        """, (
            incident,
            count,
            window_days,
            datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            jira_ticket_id
        ))

        cursor.execute("""
                       UPDATE knowledgeBase
                       SET problem_ticket_id = ?
                       WHERE Incident = ?
                       """, (jira_ticket_id, incident))

        conn.commit()
        conn.close()

        # ✅ CRITICAL FIX
        return jsonify({
            "status": "success",
            "jira_ticket_id": jira_ticket_id
        })