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

        db_exists = os.path.exists(DB_NAME)

        conn = sqlite3.connect(
            DB_NAME,
            timeout=30
        )

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

        cursor.execute("""
            SELECT name
            FROM sqlite_master
            WHERE type='table'
            AND name='kb_audit_log'
        """)

        table_check = cursor.fetchone()

        cursor.execute("""
            SELECT COUNT(*)
            FROM sqlite_master
        """)

        master_count = cursor.fetchone()[0]

        file_size = os.path.getsize(DB_NAME)

        conn.close()

        return f"""

        <h2>Create Audit Table</h2>

        <b>BASE_DIR:</b> {BASE_DIR}<br>
        <b>DB_NAME:</b> {DB_NAME}<br>
        <b>DB_EXISTS:</b> {db_exists}<br>
        <b>FILE_SIZE:</b> {file_size}<br>
        <b>MASTER_COUNT:</b> {master_count}<br>

        <hr>

        <b>TABLE_CHECK:</b> {table_check}

        """

    except Exception as e:

        return f"""

        <h2>Create Audit Table Error</h2>

        <b>BASE_DIR:</b> {BASE_DIR}<br>
        <b>DB_NAME:</b> {DB_NAME}<br>

        <hr>

        <pre>{str(e)}</pre>

        """