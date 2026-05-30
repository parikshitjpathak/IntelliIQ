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
import sqlite3
import re
from collections import Counter
from datetime import datetime, timedelta

from flask import render_template, request
import markdown

from dotenv import load_dotenv
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_NAME = os.path.join(BASE_DIR, "IntelliIQ.db")

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

    # SLA
    if any(word in query for word in [
        "sla",
        "breach",
        "breaches",
        "missed sla",
        "sla miss"
    ]):
        return "sla"

    # MTTR
    if any(word in query for word in [
        "mttr",
        "resolution time",
        "resolve faster",
        "long resolution",
        "improve mttr"
    ]):
        return "mttr"

    # RCA
    if any(word in query for word in [
        "root cause",
        "recurring root cause",
        "rca"
    ]):
        return "rca"

    # Stability Check
    if (
        "stable right now" in query
        or "is the system stable" in query
    ):
        return "stability_check"

    # Stability
    if any(word in query for word in [
        "stable",
        "stability",
        "improve system",
        "optimize",
        "fix"
    ]):
        return "stability"

    # Risk
    if any(word in query for word in [
        "risk",
        "fail",
        "trigger",
        "break"
    ]):
        return "risk"

    # Analysis
    if any(word in query for word in [
        "why",
        "analysis",
        "reason"
    ]):
        return "analysis"

    return "stability"



#===========intent detection ends here==================

# ==========================================================
# EXTRACT TIME WINDOW
# ==========================================================
def extract_time_window(query: str):

    query = query.lower()

    if "all data" in query:
        return None

    if "entire duration" in query:
        return None

    if "full history" in query:
        return None
    
    if "last 5 days" in query:
        return 5
    
    if "past 5 days" in query:
        return 5

    if "last 7 days" in query:
        return 7

    if "past 7 days" in query:
        return 7

    if "last 15 days" in query:
        return 15

    if "past 15 days" in query:
        return 15

    if "last 30 days" in query:
        return 30

    if "past 30 days" in query:
        return 30

    if "last month" in query:
        return 30

    if "last 2 months" in query:
        return 60

    if "past 2 months" in query:
        return 60

    if "last 60 days" in query:
        return 60

    if "last 90 days" in query:
        return 90

    if "past 90 days" in query:
        return 90

    # Default behavior
    return 7

#============== time extraction ends here====================


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
# Old FETCH RECURRING ISSUES
# ==========================================================
#def get_recurring_issues_data():
 #   try:
  #      from trend_engine import get_recurring_issues
   #     return get_recurring_issues()
    #except Exception as e:
     #   print("Trend Engine Error:", e)
      #  return []

#============ fetch recurring issues=====================
def get_recurring_issues_data(days=5):

    try:

        from trend_engine import get_recurring_issues

        return get_recurring_issues(days=days)

    except Exception as e:

        print("Trend Engine Error:", e)

        return []



#=========== end fetching recurring issues =================

#======= Building SLA Intelligence =========================
def get_sla_intelligence(days=7):

    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    if days is None:
        cutoff_date = None
    else:
        cutoff_date = (
        datetime.now()
        - timedelta(days=days)
    ).strftime("%Y-%m-%d")

    #cursor.execute("""
        # SELECT
        #    sla_miss_reason,
          #  COUNT(*)
     #   FROM rca_knowledge
      ##  WHERE sla_miss_reason IS NOT NULL
        #  AND sla_miss_reason <> ''
         # AND sla_miss_reason <> 'Not Applicable'
        #GROUP BY sla_miss_reason
        #ORDER BY COUNT(*) DESC
    #""")

    #===========  new sql conditional query====================
    if cutoff_date:

        cursor.execute("""
        SELECT
            sla_miss_reason,
            COUNT(*)
        FROM rca_knowledge
        WHERE sla_miss_reason IS NOT NULL
          AND sla_miss_reason <> ''
          AND sla_miss_reason <> 'Not Applicable'
          AND date(created_at) >= ?
        GROUP BY sla_miss_reason
        ORDER BY COUNT(*) DESC
    """, (cutoff_date,))

    else:

        cursor.execute("""
        SELECT
            sla_miss_reason,
            COUNT(*)
        FROM rca_knowledge
        WHERE sla_miss_reason IS NOT NULL
          AND sla_miss_reason <> ''
          AND sla_miss_reason <> 'Not Applicable'
        GROUP BY sla_miss_reason
        ORDER BY COUNT(*) DESC
    """)




    #============ sql conditional query ends =====================

    rows = cursor.fetchall()
   # print("SLA Window Days =", days)
   # print("SLA Cutoff Date =", cutoff_date)
   # print("SLA Records Found =", len(rows))
    #cursor.execute("""
     #       SELECT COUNT(*)
      #      FROM knowledgeBase
       #     WHERE due_date IS NOT NULL
        #    AND status NOT IN (
         #       'Resolved',
          #      'Closed'
           # )
            #AND datetime(due_date)
             #   < datetime('now')
        #""")
    
    #====== new query for status fixing=======================
    if cutoff_date:

        cursor.execute("""
            SELECT COUNT(*)
            FROM knowledgeBase
            WHERE due_date IS NOT NULL
            AND COALESCE(status,'') <> 'Done'
            AND Date >= ?
            AND datetime(due_date) < datetime('now')
        """, (cutoff_date,))

    else:

        cursor.execute("""
            SELECT COUNT(*)
            FROM knowledgeBase
            WHERE due_date IS NOT NULL
            AND COALESCE(status,'') <> 'Done'
            AND datetime(due_date) < datetime('now')
        """)




    #====== new query with status fixed ends==========

    overdue_count = cursor.fetchone()[0]

    #========= to fetch open/closed incidents but not rca done===========
    #cursor.execute("""
     #       SELECT priority, COUNT(*)
      #      FROM knowledgeBase
       #     WHERE due_date IS NOT NULL
        #    AND status NOT IN (
         #       'Resolved',
          #      'Closed'
           # )
            #AND datetime(due_date) < datetime('now')
            #GROUP BY priority
       # """)
    #======== new priority query===============
    if cutoff_date:

        cursor.execute("""
            SELECT priority, COUNT(*)
            FROM knowledgeBase
            WHERE due_date IS NOT NULL
            AND COALESCE(status,'') <> 'Done'
            AND Date >= ?
            AND datetime(due_date) < datetime('now')
            GROUP BY priority
        """, (cutoff_date,))

    else:

        cursor.execute("""
            SELECT priority, COUNT(*)
            FROM knowledgeBase
            WHERE due_date IS NOT NULL
            AND COALESCE(status,'') <> 'Done'
            AND datetime(due_date) < datetime('now')
            GROUP BY priority
        """)




    #======== end of new priority query==========

    priority_rows = cursor.fetchall()
   # print("Overdue Incident Count =", overdue_count)
   # print("Priority Breakdown =", priority_rows)





    #========== fetching ends here =======================================



    conn.close()

    if not rows:

        return (
            "SLA Intelligence:\n"
            "Status: Insufficient Data\n"
        )

    output = (
        "SLA Intelligence:\n"
        "Evidence:\n"
    )

    total = 0

    for reason, count in rows:

        total += count

        output += (
            f"- {reason}: {count}\n"
        )

    output += (
        f"\nTotal SLA Breaches Analysed: {total}\n"
    )

    output += (
        f"Open Incidents Past SLA Due Date: "
        f"{overdue_count}\n"
    )

    #====== adding additional condition to change the output=================
    if priority_rows:

        output += "\nOverdue Critical Incidents:\n"

        for priority, count in priority_rows:

            output += (
                f"- {priority}: {count}\n"
            )


    #====== additional condition ends ==================================

    return output


#======== SLA Intelligence Ends here======================

# ==========================================================
# MTTR INTELLIGENCE
# ==========================================================
def get_mttr_intelligence(days=7):

    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    if days is None:
        cutoff_date = None
    else:
         cutoff_date = (
        datetime.now()
        - timedelta(days=days)
        ).strftime("%Y-%m-%d")

    # ------------------------------------------------------
    # INCIDENT DATA
    # ------------------------------------------------------
    #cursor.execute("""
     #   SELECT
      #      jira_ticket_id,
       #     date,
        #    time,
         #   resolved_date,
          #  priority
        #FROM knowledgeBase
        #WHERE resolved_date IS NOT NULL
    #""")

    #====== new sql query =============
    if cutoff_date:

        cursor.execute("""
            SELECT
                jira_ticket_id,
                date,
                time,
                resolved_date,
                priority
            FROM knowledgeBase
            WHERE resolved_date IS NOT NULL
            AND date >= ?
        """, (cutoff_date,))

    else:

        cursor.execute("""
            SELECT
                jira_ticket_id,
                date,
                time,
                resolved_date,
                priority
            FROM knowledgeBase
            WHERE resolved_date IS NOT NULL
        """)



    #====== new sql query ends ==============

    incidents = cursor.fetchall()
   # print("MTTR Window Days =", days)
   # print("MTTR Cutoff Date =", cutoff_date)
   # print("MTTR Incidents Found =", len(incidents))

    mttr_hours = []

    priority_mttr = {}

    for row in incidents:

        try:

            ticket_id = row[0]
            date_value = row[1]
            time_value = row[2]
            resolved_value = row[3]
            priority = row[4] or "Unknown"

            created_dt = datetime.strptime(
                f"{date_value} {time_value}",
                "%Y-%m-%d %H:%M:%S"
            )

            resolved_dt = datetime.strptime(
                resolved_value[:19],
                "%Y-%m-%dT%H:%M:%S"
            )

            hours = (
                resolved_dt - created_dt
            ).total_seconds() / 3600

            if hours < 0:
                continue

            mttr_hours.append(hours)

            priority_mttr.setdefault(
                priority,
                []
            ).append(hours)

        except Exception:
            continue

    # ------------------------------------------------------
    # RCA DATA
    # ------------------------------------------------------
    cursor.execute("""
        SELECT
            sla_miss_reason,
            COUNT(*)
        FROM rca_knowledge
        WHERE sla_miss_reason IS NOT NULL
          AND sla_miss_reason <> ''
          AND sla_miss_reason <> 'Not Applicable'
        GROUP BY sla_miss_reason
        ORDER BY COUNT(*) DESC
    """)

    rca_rows = cursor.fetchall()

    conn.close()

    # ------------------------------------------------------
    # VALIDATION
    # ------------------------------------------------------
    if not mttr_hours:

        return (
            "MTTR Intelligence:\n"
            "Insufficient Data\n"
        )

    avg_mttr = round(
        sum(mttr_hours) / len(mttr_hours),
        2
    )

    highest_mttr = round(
        max(mttr_hours),
        2
    )
    long_running_count = len([
        h for h in mttr_hours
        if h > 168
    ])

    long_running_percent = round(
        (
            long_running_count
            / len(mttr_hours)
        ) * 100,
        1
    )

    # ------------------------------------------------------
    # BUILD OUTPUT
    # ------------------------------------------------------
    output = (
        "MTTR Intelligence:\n"
        "Evidence:\n"
    )

    output += (
        f"- Resolved Incidents Analysed: "
        f"{len(mttr_hours)}\n"
    )

    output += (
        f"- Average MTTR: "
        f"{avg_mttr} hours\n"
    )

    output += (
        f"- Longest Resolution Time: "
        f"{highest_mttr} hours\n"
    )
    output += (
        f"- Incidents Exceeding "
        f"7 Days Resolution Time: "
        f"{long_running_count}\n"
    )

    output += (
        f"- Percentage of Long-Running "
        f"Incidents: "
        f"{long_running_percent}%\n"
    )

    # ------------------------------------------------------
    # PRIORITY BREAKDOWN
    # ------------------------------------------------------
    output += "\nPriority Breakdown:\n"

    highest_priority = None
    highest_mttr = 0

    for priority, values in sorted(
        priority_mttr.items()
    ):

        avg_priority = round(
            sum(values) / len(values),
            2
        )

    days = round(
        avg_priority / 24,
        1
    )

    output += (
        f"- {priority}: "
        f"{avg_priority} hours "
        f"({days} days) "
        f"({len(values)} incidents)\n"
    )

    if avg_priority > highest_mttr:

        highest_mttr = avg_priority
        highest_priority = priority

    if highest_priority:

        output += (
            f"\nSlowest Priority: "
            f"{highest_priority} "
            f"({highest_mttr} hours / "
            f"{round(highest_mttr / 24, 1)} days)\n"
        )
    # ------------------------------------------------------
    # HISTORICAL RCA FACTORS
    # ------------------------------------------------------
    if rca_rows:

        output += (
            "\nHistorical Delay Factors:\n"
        )

        for reason, count in rca_rows:

            output += (
                f"- {reason}: "
                f"{count}\n"
            )

    return output

# ==========================================================
#=======mttr intelligence ends=============================

#================= historical intelligence function =================
# ==========================================================
# HISTORICAL RCA INTELLIGENCE
# ==========================================================

def get_historical_rca_intelligence(days=7):

    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    if days is None:
         cutoff_date = None
    else:
         cutoff_date = (
        datetime.now()
        - timedelta(days=days)
    ).strftime("%Y-%m-%d")

    summary = "\n\nHistorical RCA Intelligence:\n"

    # ------------------------------------------------------
    # RECURRING INCIDENT CATEGORIES
    # ------------------------------------------------------

    #cursor.execute("""
     #   SELECT
      #      normalized_incident,
       #     COUNT(*)
        #FROM rca_knowledge
        #WHERE normalized_incident IS NOT NULL
        #GROUP BY normalized_incident
        #ORDER BY COUNT(*) DESC
        #LIMIT 5
    #""")

    #========  new query =================
    if cutoff_date:

     cursor.execute("""
            SELECT
                normalized_incident,
                COUNT(*)
            FROM rca_knowledge
            WHERE normalized_incident IS NOT NULL
            AND date(created_at) >= ?
            GROUP BY normalized_incident
            ORDER BY COUNT(*) DESC
            LIMIT 5
        """, (cutoff_date,))

    else:

     cursor.execute("""
        SELECT
            normalized_incident,
            COUNT(*)
        FROM rca_knowledge
        WHERE normalized_incident IS NOT NULL
        GROUP BY normalized_incident
        ORDER BY COUNT(*) DESC
        LIMIT 5
    """)



    #========= new query ends ==================

    categories = cursor.fetchall()
   # print("Historical RCA Days =", days)
   # print("Historical RCA Cutoff =", cutoff_date)
   # print("Historical RCA Categories =", len(categories))

    if categories:

        summary += "\nRecurring Incident Categories:\n"

        for category, count in categories:

            summary += f"- {category.title()}: {count}\n"

    # ------------------------------------------------------
    # SLA MISS REASONS
    # ------------------------------------------------------

    cursor.execute("""
        SELECT
            sla_miss_reason,
            COUNT(*)
        FROM rca_knowledge
        WHERE
            sla_miss_reason IS NOT NULL
            AND TRIM(sla_miss_reason) != ''
        GROUP BY sla_miss_reason
        ORDER BY COUNT(*) DESC
        LIMIT 5
    """)

    reasons = cursor.fetchall()

    if reasons:

        summary += "\nHistorical SLA Miss Reasons:\n"

        for reason, count in reasons:

            summary += f"- {reason}: {count}\n"

    # ------------------------------------------------------
    # OPERATIONAL PATTERNS
    # ------------------------------------------------------

    cursor.execute("""
        SELECT COUNT(*)
        FROM rca_knowledge
        WHERE LOWER(restart_required) = 'yes'
    """)
    restart_count = cursor.fetchone()[0]

    cursor.execute("""
        SELECT COUNT(*)
        FROM rca_knowledge
        WHERE LOWER(deployment_required) = 'yes'
    """)
    deployment_count = cursor.fetchone()[0]

    cursor.execute("""
        SELECT COUNT(*)
        FROM rca_knowledge
        WHERE LOWER(permanent_fix_available) = 'yes'
    """)
    permanent_yes = cursor.fetchone()[0]

    cursor.execute("""
        SELECT COUNT(*)
        FROM rca_knowledge
        WHERE LOWER(permanent_fix_available) = 'planned'
    """)
    permanent_planned = cursor.fetchone()[0]

    summary += "\nOperational Patterns:\n"

    summary += f"- Restart Required: {restart_count}\n"
    summary += f"- Deployment Required: {deployment_count}\n"
    summary += f"- Permanent Fix Available: {permanent_yes}\n"
    summary += f"- Permanent Fix Planned: {permanent_planned}\n"

    conn.close()

    return summary




#================== historical intelligence function ends===============

# ==========================================================
# HISTORICAL RCA MATCH INTELLIGENCE
# ==========================================================
def get_historical_rca_match_intelligence(days=None):

    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()

    if days is None:

        cutoff_date = None

    else:

        cutoff_date = (
            datetime.now()
            - timedelta(days=days)
        ).strftime("%Y-%m-%d")

    output = "\nHistorical RCA Match Intelligence:\n"

    # ======================================================
    # TOP RECURRING INCIDENT CATEGORIES
    # ======================================================

    if cutoff_date:

        cursor.execute("""
            SELECT
                normalized_incident,
                COUNT(*)
            FROM rca_knowledge
            WHERE normalized_incident IS NOT NULL
            AND date(created_at) >= ?
            GROUP BY normalized_incident
            ORDER BY COUNT(*) DESC
            LIMIT 5
        """, (cutoff_date,))

    else:

        cursor.execute("""
            SELECT
                normalized_incident,
                COUNT(*)
            FROM rca_knowledge
            WHERE normalized_incident IS NOT NULL
            GROUP BY normalized_incident
            ORDER BY COUNT(*) DESC
            LIMIT 5
        """)

    categories = cursor.fetchall()

    if categories:

        output += "\nTop Recurring Incident Categories:\n"

        for category, count in categories:

            output += (
                f"- {category}: {count}\n"
            )

    # ======================================================
    # ROOT CAUSE EXAMPLES
    # ======================================================

    if cutoff_date:

        cursor.execute("""
            SELECT DISTINCT ai_root_cause
            FROM rca_knowledge
            WHERE ai_root_cause IS NOT NULL
            AND ai_root_cause <> ''
            AND ai_root_cause <> 'Could not parse AI response'
            AND date(created_at) >= ?
            ORDER BY created_at DESC
            LIMIT 5
        """, (cutoff_date,))

    else:

        cursor.execute("""
            SELECT DISTINCT ai_root_cause
            FROM rca_knowledge
            WHERE ai_root_cause IS NOT NULL
            AND ai_root_cause <> ''
            AND ai_root_cause <> 'Could not parse AI response'
            ORDER BY created_at DESC
            LIMIT 5
        """)

    causes = cursor.fetchall()

    if causes:

        output += "\nRecent Historical Root Cause Examples:\n"

        for row in causes:

            output += f"- {row[0]}\n"

    # ======================================================
    # RESOLUTION EXAMPLES
    # ======================================================

    if cutoff_date:

        cursor.execute("""
            SELECT DISTINCT ai_resolution
            FROM rca_knowledge
            WHERE ai_resolution IS NOT NULL
            AND ai_resolution <> ''
            AND date(created_at) >= ?
            ORDER BY created_at DESC
            LIMIT 5
        """, (cutoff_date,))

    else:

        cursor.execute("""
            SELECT DISTINCT ai_resolution
            FROM rca_knowledge
            WHERE ai_resolution IS NOT NULL
            AND ai_resolution <> ''
            ORDER BY created_at DESC
            LIMIT 5
        """)

    resolutions = cursor.fetchall()

    if resolutions:

        output += "\nRecent Resolution Patterns:\n"

        for row in resolutions:

            output += f"- {row[0]}\n"

    # ======================================================
    # PREVENTIVE ACTIONS
    # ======================================================

    if cutoff_date:

        cursor.execute("""
            SELECT preventive_actions
            FROM rca_knowledge
            WHERE preventive_actions IS NOT NULL
            AND preventive_actions <> ''
            AND date(created_at) >= ?
            ORDER BY created_at DESC
            LIMIT 5
        """, (cutoff_date,))

    else:

        cursor.execute("""
            SELECT preventive_actions
            FROM rca_knowledge
            WHERE preventive_actions IS NOT NULL
            AND preventive_actions <> ''
            ORDER BY created_at DESC
            LIMIT 5
        """)

    actions = cursor.fetchall()

    if actions:

        output += "\nRecent Preventive Actions:\n"

        for row in actions:

            output += f"- {row[0]}\n"

    # ======================================================
    # OPERATIONAL PATTERNS
    # ======================================================

    if cutoff_date:

        cursor.execute("""
            SELECT COUNT(*)
            FROM rca_knowledge
            WHERE restart_required='Yes'
            AND date(created_at) >= ?
        """, (cutoff_date,))

    else:

        cursor.execute("""
            SELECT COUNT(*)
            FROM rca_knowledge
            WHERE restart_required='Yes'
        """)

    restart_count = cursor.fetchone()[0]

    if cutoff_date:

        cursor.execute("""
            SELECT COUNT(*)
            FROM rca_knowledge
            WHERE deployment_required='Yes'
            AND date(created_at) >= ?
        """, (cutoff_date,))

    else:

        cursor.execute("""
            SELECT COUNT(*)
            FROM rca_knowledge
            WHERE deployment_required='Yes'
        """)

    deployment_count = cursor.fetchone()[0]

    if cutoff_date:

        cursor.execute("""
            SELECT COUNT(*)
            FROM rca_knowledge
            WHERE vendor_involvement IS NOT NULL
            AND LOWER(TRIM(vendor_involvement)) <> 'not required'
            AND date(created_at) >= ?
        """, (cutoff_date,))

    else:

         cursor.execute("""
            SELECT COUNT(*)
            FROM rca_knowledge
            WHERE vendor_involvement IS NOT NULL
            AND LOWER(TRIM(vendor_involvement)) <> 'not required'
        """)

    vendor_count = cursor.fetchone()[0]

    if cutoff_date:

        cursor.execute("""
            SELECT COUNT(*)
            FROM rca_knowledge
            WHERE permanent_fix_available='Yes'
            AND date(created_at) >= ?
        """, (cutoff_date,))

    else:

        cursor.execute("""
            SELECT COUNT(*)
            FROM rca_knowledge
            WHERE permanent_fix_available='Yes'
        """)

    permanent_fix_count = cursor.fetchone()[0]

    output += "\nOperational Patterns:\n"

    output += (
        f"- Restart Required: {restart_count}\n"
    )

    output += (
        f"- Deployment Required: {deployment_count}\n"
    )

    output += (
        f"- Vendor Involvement: {vendor_count}\n"
    )

    output += (
        f"- Permanent Fix Available: {permanent_fix_count}\n"
    )

    conn.close()

    return output

#========== rca historical match ends======================



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
def build_system_summary(issues, intent, days=7):

    historical_rca = get_historical_rca_intelligence(days)
    historical_match = get_historical_rca_match_intelligence(days)
    print("\n=== HISTORICAL RCA MATCH ===")
    print(historical_match)
    print("===========================\n")

    # ------------------------------------------------------
    # SLA
    # ------------------------------------------------------
    if intent == "sla":

        return (
            get_sla_intelligence(days)
            + historical_rca
        )

    # ------------------------------------------------------
    # MTTR
    # ------------------------------------------------------
    if intent == "mttr":

        return (
            get_mttr_intelligence(days)
            + historical_rca
        )

    summary = ""

    # ------------------------------------------------------
    # RECURRING ISSUES
    # ------------------------------------------------------
    if issues:

        summary += "Recurring issues:\n"

        for i, issue in enumerate(issues[:5], 1):

            summary += (
                f"{i}. {issue['incident']} "
                f"— {issue['count']} occurrences\n"
            )

    else:

        summary += (
            "No significant recurring issues detected.\n"
        )

    # ------------------------------------------------------
    # CATEGORY PATTERNS
    # ------------------------------------------------------
    categories = [

        issue.get("category")

        for issue in issues

        if issue.get("category")

    ]

    if categories:

        counts = Counter(categories)

        summary += "\nTop categories:\n"

        for cat, count in counts.most_common(3):

            summary += (
                f"- {cat}: {count}\n"
            )

    # ------------------------------------------------------
    # RECENT INCIDENTS
    # ------------------------------------------------------
    recent = get_recent_incidents()

    if not recent:

        summary += (
            "\nSystem stable in last 10 days.\n"
        )

    else:

        summary += (
            f"\nRecent incidents "
            f"(last 10 days): {len(recent)}\n"
        )

    # ------------------------------------------------------
    # OPEN CRITICAL INCIDENTS
    # ------------------------------------------------------
    open_critical = get_open_high_priority()

    if open_critical:

        summary += (
            f"\nOpen P1/P2 incidents: "
            f"{len(open_critical)}\n"
        )

    else:

        summary += (
            "\nNo open critical incidents.\n"
        )

    # ------------------------------------------------------
    # SLA INTELLIGENCE
    # ------------------------------------------------------
    sla_data = get_sla_intelligence(days)

   # print("\n=== SLA DATA ===")
   # print(sla_data)
   # print("================\n")

    summary += "\n\n"
    summary += sla_data

    # ------------------------------------------------------
    # HISTORICAL RCA INTELLIGENCE
    # ------------------------------------------------------
   # print("\n=== HISTORICAL RCA ===")
   # print(historical_rca)
   # print("======================\n")

    summary += "\n\n"
    summary += historical_rca
    summary += "\n\n"
    summary += historical_match

    return summary


#============ build summary ends ===============================

# ==========================================================
# BUILD PROMPT
# ==========================================================
def build_prompt(summary, intent):

    # ------------------------------------------------------
    # INTENT OBJECTIVES
    # ------------------------------------------------------

    if intent == "sla":

        goal = """
Determine what is causing SLA breaches and how SLA performance can be improved.

Focus on:
- SLA breach evidence
- Historical RCA factors
- Open incidents past SLA due date
- Priority backlog
- Recurring SLA patterns
"""

    elif intent == "mttr":

        goal = """
Determine why MTTR is elevated and how MTTR can be improved.

Focus on:
- Resolution delays
- Long-running incidents
- Priority resolution times
- Historical RCA factors
- Operational bottlenecks
"""

    elif intent == "rca":

        goal = """
Identify recurring root causes and recurring failure patterns.

Focus on:
- Historical RCA records
- Root cause trends
- Preventive actions
- Repeated failures
"""

    elif intent == "stability":

        goal = """
Assess current system stability and identify actions required to improve stability.

Focus on:
- Open critical incidents
- Recurring incidents
- Operational health indicators
- Emerging risks
"""

    elif intent == "risk":

        goal = """
Identify operational risks and incidents likely to recur.

Focus on:
- Incident trends
- Recurring failures
- Backlog indicators
- Future operational risks
"""

    elif intent == "analysis":

        goal = """
Explain what is going wrong and why incidents are occurring.

Focus on:
- Operational weaknesses
- Recurring incident patterns
- Process gaps
- Historical evidence
"""

    else:

        goal = """
Provide operational insights using available evidence.
"""

    # ------------------------------------------------------
    # COMMON ADVISOR FRAMEWORK
    # ------------------------------------------------------

    prompt = f"""
You are an expert Site Reliability Engineer and Operations Advisor.

Analyze ONLY the supplied evidence.

Evidence:

{summary}

Objective:

{goal}

Core Rules:

1. Use supplied evidence first.
2. Do not invent facts.
3. Historical RCA evidence may be used as confirmed causes.
4. Potential contributing factors must be clearly identified as hypotheses.
5. Do not present hypotheses as facts.
6. Whenever counts, percentages, MTTR values, SLA counts or priority breakdowns exist, include the numerical values in the narrative.
7. Recommendations must be traceable to evidence.
8. Avoid generic recommendations.
9. Use operational language suitable for managers and support leaders.

Provide the response using EXACTLY the structure below.

### 🔍 Overview

Summarize the operational situation using actual evidence.

If numerical values exist, include them.

Examples:

GOOD:
- Display documented breach counts.
- Display overdue incident counts.
- Display priority breakdown counts.
- Ensure priority totals reconcile to the overall count.

BAD:
- Several incidents exist
- Many tickets are overdue

### 📊 Key Findings

Highlight the most important operational findings.

Always include supporting numbers when available.

GOOD:
- 42.9% of incidents exceeded 7 days resolution time.
- P4 incidents average 691.63 hours (28.8 days).

BAD:
- Some incidents took longer to resolve.

### ✅ Confirmed Causes

Only include causes directly supported by evidence.

Historical RCA factors may be used.

Examples:
- Delayed Triage (3 documented RCA records)
- Vendor Dependency (5 documented RCA records)
- Assignment Delay (4 documented RCA records)

Do not invent confirmed causes.

### 💡 Potential Contributing Factors

These are operational hypotheses requiring validation.

Examples:
- Prioritization challenges
- Escalation delays
- Capacity constraints
- Workload imbalance
- Ownership delays
- Incident backlog

Whenever possible, connect hypotheses to evidence.

GOOD:
- Incident backlog may be contributing to delays, as 21 incidents are currently overdue.

BAD:
- Incident backlog may exist.

Do not present contributing factors as facts.

### 🛠 Recommendations

Recommendations must:

- Reference actual evidence
- Reference numerical findings
- Address confirmed causes
- Address recurring patterns
- Provide practical operational actions

GOOD:
- Prioritize closure of 10 overdue P1 incidents.
- Review triage workflow responsible for 3 documented Delayed Triage breaches.
- Investigate 9 incidents exceeding 7 days resolution time.

BAD:
- Improve prioritization.
- Improve process.

Every recommendation should be traceable to one or more findings.

### 📈 Expected Outcome

Describe measurable operational improvements expected if recommendations are implemented.
"""

    return prompt
#=========== Prompt Building Ends==================


# ==========================================================
# MAIN INSIGHT FUNCTION
# ==========================================================
def build_system_insight(query: str):

    days = extract_time_window(query)
    #print("Days mentioned", days)

    #issues = get_recurring_issues_data()
    issues = get_recurring_issues_data(
        days if days is not None else 99999
    )
    intent = detect_intent(query)
    summary = build_system_summary(issues,intent,days)

   
    #print("DETECTED INTENT =", intent)

      
    

   

    

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

    if days is None:

      scope_text = "Entire data history"

    else:

        scope_text = f"Past {days} days"

    query_context = (
        f"<b>You Asked:</b> {query}<br>"
        f"<b>Analysis Scope:</b> "
        f"{scope_text}<br>"
       
    )

    return prefix + query_context + formatted




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