# ==========================================================
# TICKET DASHBOARD MODULE (CLEAN + FULL + RISK INTEGRATED)
# ==========================================================
import os
import sqlite3
from datetime import datetime
import requests
from requests.auth import HTTPBasicAuth
from flask import render_template, request, jsonify
from dotenv import load_dotenv
from risk_engine import classify_ticket_risk  # ✅ NEW

# ==========================================================
# CONFIGURATION
# ==========================================================
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_NAME = os.path.join(BASE_DIR, "IntelliIQ.db")

#load_dotenv("mykeys.env")
#=============== below is the new code on 11 may===============

env=os.getenv("ENV","local")
if env=="local" :
    load_dotenv("mykeys.env")
    #print("the env is ",env)
else:
    load_dotenv()    
#load_dotenv()

#============= 11 may code ends========================

JIRA_BASE_URL = os.getenv("JIRA_URL")
JIRA_EMAIL = os.getenv("JIRA_EMAIL")
JIRA_API_TOKEN = os.getenv("JIRA_API_TOKEN")

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
        SELECT Incident, Category, Jira_Ticket_Id, Date, Time,
               problem_ticket_id, due_date, normalized_incident,status,resolved_date,
               confluence_link
        FROM knowledgeBase
        WHERE 1=1           
        ORDER BY Date DESC
    """)

    rows = cursor.fetchall()
    conn.close()

    tickets = []
    today = datetime.now()

    for r in rows:

        incident, category, ticket_id, date_str, time_str, problem_ticket_id, db_due_date, normalized_incident, status,resolved_date, confluence_link = r

        # CATEGORY
        final_category = category
        if not category or category.lower() == "unclassified":
            if normalized_incident:
                final_category = normalized_incident.replace("_", " ").title()

        # JIRA
        jira_data = get_jira_details(ticket_id)
        jira_status = jira_data["status"]
        jira_assignee = jira_data["assignee"]

        # DATES
        try:
            created_dt = datetime.strptime(f"{date_str} {time_str}", "%Y-%m-%d %H:%M:%S")
            days_open = (today - created_dt).days
        except:
            created_dt = None
            days_open = 0

        try:
            due_date_obj = datetime.fromisoformat(db_due_date)
        except:
            due_date_obj = None


       # DUE DATE FORMAT
        try:
            formatted_due_date = due_date_obj.strftime("%d %b %Y, %I:%M %p")
        except:
            try:
                 due_dt = datetime.fromisoformat(db_due_date)
                 formatted_due_date = due_dt.strftime("%d %b %Y, %I:%M %p")
            except:
                 formatted_due_date = db_due_date


        try:
             resolved_dt = datetime.fromisoformat(resolved_date.replace("Z", "+00:00"))
             formatted_resolved = resolved_dt.strftime("%d %b %Y, %I:%M %p")
        except:
            formatted_resolved = resolved_date

            

        # SLA
        if jira_status and jira_status.lower() in ["done", "closed", "resolved"]:
            sla_status = "Completed"
            sla_color = "blue"

        elif due_date_obj:
            now = datetime.now(due_date_obj.tzinfo)
            time_remaining = due_date_obj - now

            if time_remaining.total_seconds() < 0:
                sla_status = "Breached"
                sla_color = "red"
            elif time_remaining.total_seconds() <= 86400:
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
            formatted_due_date = db_due_date

       # ================= SLA MET logic commented on 3rd may=================
        #sla_met = "-"

        #try:
         #   if status and status.lower() == "done":

                # FIX timezone format (+0530 → +05:30)
              #  clean_resolved = resolved_date[:-2] + ":" + resolved_date[-2:]

               # resolved_dt = datetime.fromisoformat(clean_resolved)
                #due_dt = datetime.fromisoformat(db_due_date)

                #if resolved_dt <= due_dt:
                 #   sla_met = "YES"
                #else:
                 #   sla_met = "NO"

        #except Exception as e:
         #   sla_met = "-"

            #===================== old sla logic=====================


            # ================= FIXED SLA LOGIC =================
            
        sla_met = "-"
        #print("Entering sla logic")

        try:
             if status and status.lower() == "done" and resolved_date and db_due_date:
                #print("The status is ", status)

                # Normalize resolved_date (+0530 → +05:30)
                if "+" in resolved_date:
                    clean_resolved = resolved_date[:-2] + ":" + resolved_date[-2:]
                else:
                    clean_resolved = resolved_date

               #===== fixing due_date parsing (format inconsistency)=====
                if "+" in db_due_date:
                    clean_due = db_due_date[:-2] + ":" + db_due_date[-2:]
                else:
                    clean_due = db_due_date  # keep as-is, DO NOT slice
                #==== fix ends========

                #resolved_dt = datetime.fromisoformat(clean_resolved)
                #due_dt = datetime.fromisoformat(clean_due)

                resolved_dt = datetime.fromisoformat(clean_resolved).replace(tzinfo=None)
                due_dt = datetime.fromisoformat(clean_due).replace(tzinfo=None)

                if resolved_dt <= due_dt:
                    sla_met = "YES"
                else:
                    sla_met = "NO"

        except Exception as e:
            # keep default "-"
            print("SLA Error",e)







        tickets.append({
            "incident": incident,
            "category": final_category,
            "ticket_id": ticket_id,
            "date": date_str,
            "time": time_str,                 # ✅ CRITICAL FIX
            "status": jira_status,
            "due_date": db_due_date,          # ✅ RAW for risk engine
            "due_date_display": formatted_due_date,
            "assignee": jira_assignee,
            "sla_status": sla_status,
            "sla_color": sla_color,
            "jira_link": jira_link,
            "days_open": days_open,
            "status": status,
            "sla_met": sla_met,
            "resolved_date": resolved_date,
            "resolved_date_display":formatted_resolved,
            "problem_ticket_id": problem_ticket_id,

            # ==========================================================
            # ====== NEW CODE ADDED ON 19 MAY FOR PENDING ACTIONS ======
            # ==========================================================

            "confluence_link": confluence_link,

            "jira_missing":
                not ticket_id,

            "confluence_missing":

                (
                    not confluence_link
                    and date_str >= "2026-05-19"
                )

            # ==========================================================
            # ====== 19 MAY PENDING ACTION CODE ENDS ===================
            # ==========================================================

        })

    # ✅ APPLY RISK ENGINE
    tickets = classify_ticket_risk(tickets)

    return tickets

# ==========================================================
# ROUTES
# ==========================================================
def register_ticket_dashboard(app):

    # ================================
    # PROBLEM DASHBOARD (UNCHANGED)
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

        return render_template(
            "problem_dashboard.html",
            problems=problems,
            active_page="problem"
        )


    # ================================
    # TICKET DASHBOARD (UPDATED)
    # ================================
    @app.route("/ticket_dashboard")
    def ticket_dashboard():

        from early_warning_engine import get_early_warnings
        from trend_engine import get_recurring_issues

        early_warnings = get_early_warnings()
        problem_tickets = get_recurring_issues()

        # MAP EXISTING PROBLEM TICKETS
        conn = sqlite3.connect(DB_NAME)
        cursor = conn.cursor()

        cursor.execute("""
            SELECT incident, jira_ticket_id
            FROM ProblemTickets
            WHERE jira_ticket_id IS NOT NULL
        """)

        rows = cursor.fetchall()
        conn.close()

        existing_map = {
            r[0].strip().lower(): r[1]
            for r in rows
        }

        for p in problem_tickets:
            key = p["incident"].strip().lower()
            p["problem_ticket_id"] = existing_map.get(key)

        # MAIN TICKETS (NOW WITH RISK)
        tickets = get_all_tickets()

                    #===== adding risk summary counts (3rd May - dashboard enhancement)=====
        summary = {
                "high": 0,
                "medium": 0,
                "safe": 0,
                "sla_met": 0,
                "sla_breached": 0
            }

        for t in tickets:

                risk = t.get("risk_level")
                sla_met = t.get("sla_met")
                status = (t.get("status") or "").lower()
                sla_status = (t.get("sla_status") or "").lower()

                # HIGH
                if risk == "High":
                    summary["high"] += 1

                # MEDIUM
                if risk == "Medium":
                    summary["medium"] += 1

                # SAFE
                if risk == "Safe":
                    summary["safe"] += 1

                # SLA MET
                if sla_met == "YES":
                    summary["sla_met"] += 1

                # SLA BREACHED
                # includes:
                # - Closed Breached
                # - Active breached
                if risk == "Closed Breached" or sla_status == "breached":
                    summary["sla_breached"] += 1

            #==== summary logic ends========



        return render_template(
            "operations_dashboard.html",
            tickets=tickets,
            problem_tickets=problem_tickets,
            early_warnings=early_warnings,
            summary=summary,
            active_page="dashboard"
        )


    # ================================
    # CREATE PROBLEM TICKET (UNCHANGED)
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

        return jsonify({
            "status": "success",
            "jira_ticket_id": jira_ticket_id
        })