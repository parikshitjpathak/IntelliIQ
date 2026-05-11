import sqlite3
import os
from datetime import datetime

from rca_ingestion_engine import (
    ingest_rca_record
)

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_NAME = os.path.join(BASE_DIR, "IntelliIQ.db")


# ==========================================================
# DB CONNECTION
# ==========================================================

def get_connection():
    return sqlite3.connect(DB_NAME)


# ==========================================================
# CHECK EXISTING
# ==========================================================

def already_ingested(ticket_id):

    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
        SELECT 1
        FROM rca_knowledge
        WHERE ticket_id = ?
    """, (
        ticket_id,
    ))

    exists = cursor.fetchone()

    conn.close()

    return exists is not None


# ==========================================================
# PROCESS KNOWLEDGEBASE RECORDS
# ==========================================================

def process_rca_records(limit=50):

    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
        SELECT
            Jira_Ticket_Id,
            Incident,
            normalized_incident,
            Category,
            Root_Cause,
            Solution,
            priority
        FROM knowledgeBase
        WHERE Root_Cause IS NOT NULL
        AND TRIM(Root_Cause) != ''
        ORDER BY Date DESC
        LIMIT ?
    """, (
        limit,
    ))

    rows = cursor.fetchall()

    conn.close()

    inserted = 0
    skipped = 0

    for row in rows:

        (
            ticket_id,
            incident,
            normalized_incident,
            category,
            root_cause,
            solution,
            priority
        ) = row

        if not ticket_id:
            skipped += 1
            continue

        if already_ingested(ticket_id):
            skipped += 1
            continue

        preventive_action = build_preventive_action(
            root_cause,
            solution
        )

        try:

            ingest_rca_record(
                ticket_id=ticket_id,
                incident=incident,
                normalized_incident=normalized_incident,
                category=category,
                root_cause=root_cause,
                resolution_summary=solution,
                preventive_action=preventive_action,
                priority=priority
            )

            inserted += 1

        except Exception as e:

            print(
                f"[RCA PROCESS ERROR] "
                f"{ticket_id} : {str(e)}"
            )

    return {
        "inserted": inserted,
        "skipped": skipped
    }


# ==========================================================
# PREVENTIVE ACTION BUILDER
# ==========================================================

def build_preventive_action(
    root_cause,
    solution
):

    text = (
        f"{root_cause} {solution}"
    ).lower()

    recommendations = []

    if "timeout" in text:

        recommendations.append(
            "Implement timeout monitoring "
            "and alerting"
        )

    if "database" in text:

        recommendations.append(
            "Review DB optimization and "
            "query performance"
        )

    if "deployment" in text:

        recommendations.append(
            "Strengthen deployment "
            "validation checks"
        )

    if "api" in text:

        recommendations.append(
            "Introduce API health "
            "monitoring"
        )

    if "memory" in text:

        recommendations.append(
            "Monitor memory utilization "
            "proactively"
        )

    if not recommendations:

        recommendations.append(
            "Review recurring operational "
            "patterns and preventive controls"
        )

    return ". ".join(recommendations)


# ==========================================================
# MAIN
# ==========================================================

if __name__ == "__main__":

    result = process_rca_records()

    print("\n===== RCA POST PROCESSOR =====")

    print(
        f"Inserted : {result['inserted']}"
    )

    print(
        f"Skipped  : {result['skipped']}"
    )

    print("================================\n")