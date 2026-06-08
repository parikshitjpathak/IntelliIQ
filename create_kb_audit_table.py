import os
import sqlite3

from flask import Blueprint

create_audit_table_bp = Blueprint(
    "create_audit_table",
    __name__
)

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_NAME = os.path.join(BASE_DIR, "IntelliIQ.db")


@create_audit_table_bp.route("/create_audit_table")
def create_audit_table():

    try:

        conn = sqlite3.connect(DB_NAME)
        cursor = conn.cursor()

        cursor.execute("""

        CREATE TABLE IF NOT EXISTS kb_audit_log (

            audit_id INTEGER PRIMARY KEY AUTOINCREMENT,

            audit_time TEXT,

            route_name TEXT,

            kb_id INTEGER,

            incident TEXT,

            old_jira_ticket_id TEXT,

            new_jira_ticket_id TEXT,

            old_confluence_link TEXT,

            new_confluence_link TEXT,

            remarks TEXT

        )

        """)

        conn.commit()
        conn.close()

        return "SUCCESS : kb_audit_log table created"

    except Exception as e:

        return f"ERROR : {str(e)}"