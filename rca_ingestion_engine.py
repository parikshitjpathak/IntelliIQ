import sqlite3
import os
from datetime import datetime

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_NAME = os.path.join(BASE_DIR, "IntelliIQ.db")


# ==========================================================
# DB CONNECTION
# ==========================================================

def get_connection():
    return sqlite3.connect(DB_NAME)


# ==========================================================
# SAFE TEXT
# ==========================================================

def safe_text(value):

    if value is None:
        return ""

    return str(value).strip()


# ==========================================================
# INGEST RCA RECORD
# ==========================================================

def ingest_rca_record(
    ticket_id,
    incident,
    normalized_incident,
    category,
    root_cause,
    resolution_summary,
    preventive_action,
    priority
):

    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
        INSERT INTO rca_knowledge (
            ticket_id,
            incident,
            normalized_incident,
            category,
            root_cause,
            resolution_summary,
            preventive_action,
            priority,
            created_at
        )
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (

        safe_text(ticket_id),
        safe_text(incident),
        safe_text(normalized_incident),
        safe_text(category),
        safe_text(root_cause),
        safe_text(resolution_summary),
        safe_text(preventive_action),
        safe_text(priority),

        datetime.now().strftime(
            "%Y-%m-%d %H:%M:%S"
        )

    ))

    conn.commit()
    conn.close()


# ==========================================================
# BUILD RCA PAYLOAD
# ==========================================================

def build_rca_payload(
    incident_data,
    rca_response
):

    return {

        "ticket_id":
            incident_data.get(
                "jira_ticket_id",
                ""
            ),

        "incident":
            incident_data.get(
                "incident",
                ""
            ),

        "normalized_incident":
            incident_data.get(
                "normalized_incident",
                ""
            ),

        "category":
            incident_data.get(
                "category",
                ""
            ),

        "priority":
            incident_data.get(
                "priority",
                ""
            ),

        "root_cause":
            extract_section(
                rca_response,
                "Root Cause"
            ),

        "resolution_summary":
            extract_section(
                rca_response,
                "Resolution"
            ),

        "preventive_action":
            extract_section(
                rca_response,
                "Preventive"
            )

    }


# ==========================================================
# EXTRACT RCA SECTIONS
# ==========================================================

def extract_section(
    text,
    section_name
):

    if not text:
        return ""

    lines = text.splitlines()

    capture = False

    collected = []

    for line in lines:

        line_clean = line.strip()

        if (
            section_name.lower()
            in line_clean.lower()
        ):

            capture = True

            continue

        if capture:

            if (
                line_clean.startswith("###")
                or line_clean.startswith("##")
            ):

                break

            collected.append(line_clean)

    return " ".join(collected).strip()


# ==========================================================
# INGEST FULL RCA RESPONSE
# ==========================================================

def ingest_rca_response(
    incident_data,
    rca_response
):

    try:

        payload = build_rca_payload(
            incident_data,
            rca_response
        )

        ingest_rca_record(
            ticket_id=payload["ticket_id"],
            incident=payload["incident"],
            normalized_incident=payload["normalized_incident"],
            category=payload["category"],
            root_cause=payload["root_cause"],
            resolution_summary=payload["resolution_summary"],
            preventive_action=payload["preventive_action"],
            priority=payload["priority"]
        )

        return True

    except Exception as e:

        print(
            f"[RCA INGESTION ERROR] {str(e)}"
        )

        return False