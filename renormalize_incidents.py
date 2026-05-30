# ==========================================================
# RE-NORMALIZE HISTORICAL INCIDENTS
# ==========================================================

import os
import sqlite3

from normalization_engine import normalize_incident


BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_NAME = os.path.join(BASE_DIR, "IntelliIQ.db")


def normalize_category(normalized_value):

    if not normalized_value:
        return "Other Issue"

    return normalized_value.title()


def renormalize_knowledgebase(cursor):

    updated = 0

    cursor.execute("""
        SELECT KB_ID, Incident
        FROM knowledgeBase
    """)

    rows = cursor.fetchall()

    for kb_id, incident in rows:

        normalized = normalize_incident(incident)
        category = normalize_category(normalized)

        cursor.execute("""
            UPDATE knowledgeBase
            SET
                normalized_incident = ?,
                Category = ?
            WHERE KB_ID = ?
        """, (
            normalized,
            category,
            kb_id
        ))

        updated += 1

    return updated


def renormalize_rca(cursor):

    updated = 0

    cursor.execute("""
        SELECT rca_id, incident
        FROM rca_knowledge
    """)

    rows = cursor.fetchall()

    for rca_id, incident in rows:

        normalized = normalize_incident(incident)

        cursor.execute("""
            UPDATE rca_knowledge
            SET normalized_incident = ?
            WHERE rca_id = ?
        """, (
            normalized,
            rca_id
        ))

        updated += 1

    return updated


def main():

    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()

    print("\n================================")
    print("RE-NORMALIZATION STARTED")
    print("================================")

    kb_count = renormalize_knowledgebase(cursor)
    rca_count = renormalize_rca(cursor)

    conn.commit()
    conn.close()

    print("\n================================")
    print("RE-NORMALIZATION COMPLETE")
    print("================================")

    print(f"\nKnowledgeBase Updated : {kb_count}")
    print(f"RCA Knowledge Updated : {rca_count}\n")


if __name__ == "__main__":
    main()