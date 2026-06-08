import os
import sqlite3

from flask import Blueprint
from datetime import datetime

db_update_test_bp = Blueprint(
    "db_update_test",
    __name__
)

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_NAME = os.path.join(BASE_DIR, "IntelliIQ.db")


@db_update_test_bp.route("/db_update")
def db_update():

    try:

        db_exists = os.path.exists(DB_NAME)

        conn = sqlite3.connect(
            DB_NAME,
            timeout=30
        )

        cursor = conn.cursor()

        cursor.execute("""
            SELECT COUNT(*)
            FROM sqlite_master
        """)

        master_count = cursor.fetchone()[0]

        file_size = os.path.getsize(DB_NAME)

        cursor.execute("""

            INSERT INTO kb_audit_log (

                audit_time,
                route_name,
                kb_id,
                incident,
                old_jira_ticket_id,
                new_jira_ticket_id,
                old_confluence_link,
                new_confluence_link,
                remarks

            )

            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)

        """, (

            datetime.now().strftime(
                "%Y-%m-%d %H:%M:%S"
            ),

            "MANUAL_TEST",

            999,

            "Audit Test Incident",

            None,

            "TEST-999",

            None,

            None,

            "Audit Test Record"

        ))

        audit_id = cursor.lastrowid

        conn.commit()

        conn.close()

        return f"""

        <h2>Audit Test Insert Success</h2>

        <b>BASE_DIR:</b> {BASE_DIR}<br>
        <b>DB_NAME:</b> {DB_NAME}<br>
        <b>DB_EXISTS:</b> {db_exists}<br>
        <b>FILE_SIZE:</b> {file_size}<br>
        <b>MASTER_COUNT:</b> {master_count}<br>

        <hr>

        <b>AUDIT_ID:</b> {audit_id}

        """

    except Exception as e:

        return f"""

        <h2>Audit Test Insert Error</h2>

        <b>BASE_DIR:</b> {BASE_DIR}<br>
        <b>DB_NAME:</b> {DB_NAME}<br>

        <hr>

        <pre>{str(e)}</pre>

        """