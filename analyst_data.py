import sqlite3
from datetime import datetime
import os


# ============================================================
# ================= DB CONFIG ================================
# ============================================================

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_NAME = os.path.join(BASE_DIR, "IntelliIQ.db")


# ============================================================
# ============ ANALYST DATA FETCH (DB ONLY) ===================
# ============================================================

def get_analyst_tickets():

    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()

    cursor.execute("""
        SELECT 
            Incident,
            Category,
            Jira_Ticket_Id,
            Date,
            Time,
            problem_ticket_id,
            priority,
            due_date,
            normalized_incident,
            status,
            assigned_to,
            resolved_date
        FROM knowledgeBase
        WHERE Jira_Ticket_Id IS NOT NULL AND Jira_Ticket_Id != ''
        ORDER BY Date DESC
    """)

    rows = cursor.fetchall()
    conn.close()

    tickets = []
    now = datetime.now()

    for r in rows:

        (
            incident,
            category,
            ticket_id,
            date_str,
            time_str,
            problem_ticket_id,
            priority,
            due_date_str,
            normalized_incident,
            status,
            assigned_to,
            resolved_date_str
        ) = r

        # ================= CATEGORY =================
        final_category = category
        if not category or category.lower() == "unclassified":
            if normalized_incident:
                final_category = normalized_incident.replace("_", " ").title()

        # ================= DATETIME =================
        try:
            created_dt = datetime.strptime(f"{date_str} {time_str}", "%Y-%m-%d %H:%M:%S")
        except:
            created_dt = None

        # Due datetime
        try:
            due_dt = datetime.fromisoformat(due_date_str) if due_date_str else None
        except:
            due_dt = None

        # Resolved datetime
        try:
            if resolved_date_str:
                resolved_dt = datetime.fromisoformat(resolved_date_str.replace("+0530", "+05:30"))
            else:
                resolved_dt = None
        except:
            resolved_dt = None

        # ================= DAYS OPEN =================
        try:
            days_open = (now - created_dt).days if created_dt else 0
        except:
            days_open = 0

        # ================= SLA LOGIC =================
       
       # ================= SLA LOGIC =================
        status_clean = (status or "").lower()

        # Normalize datetime (remove timezone safely)
        if due_dt is not None:
            due_dt = due_dt.replace(tzinfo=None)

        if resolved_dt is not None:
            resolved_dt = resolved_dt.replace(tzinfo=None)

        if status_clean == "done":

            if due_dt is not None and resolved_dt is not None:

                if resolved_dt <= due_dt:
                    sla_status = "Completed"
                else:
                    sla_status = "Breached"

            else:
                sla_status = "Completed"

        else:

            if due_dt is not None:

                if now > due_dt:
                    sla_status = "Breached"

                else:

                    time_diff = (due_dt - now).total_seconds()

                    if time_diff <= 86400:
                        sla_status = "At Risk"
                    else:
                        sla_status = "On Track"

            else:
                sla_status = "Unknown"



        # ================= FINAL OBJECT =================
        tickets.append({
            "incident": incident,
            "category": final_category,
            "ticket_id": ticket_id,
            "date": date_str,
            "time": time_str,
            "status": status,
            "assigned_to": assigned_to or "Unassigned",
            "priority": priority or "Unknown",
            "due_date": due_date_str,
            "resolved_date": resolved_date_str,
            "sla_status": sla_status,
            "days_open": days_open,
            "problem_ticket_id": problem_ticket_id
        })

    return tickets