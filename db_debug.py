import os
import sqlite3
from flask import Blueprint
from datetime import datetime

db_debug_bp = Blueprint("db_debug", __name__)

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_NAME = os.path.join(BASE_DIR, "IntelliIQ.db")


@db_debug_bp.route("/db_debug")
def db_debug():

    try:

        conn = sqlite3.connect(DB_NAME)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()

        db_exists = os.path.exists(DB_NAME)
        current_dir = os.getcwd()

        db_stats = os.stat(DB_NAME)

        db_modified = datetime.fromtimestamp(
            db_stats.st_mtime
        )

        cursor.execute("""
            SELECT COUNT(*)
            FROM knowledgeBase
        """)

        total_rows = cursor.fetchone()[0]

        cursor.execute("""
            SELECT
                KB_ID,
                Incident,
                Jira_Ticket_Id,
                confluence_link,
                Date,
                Time
            FROM knowledgeBase
            ORDER BY KB_ID DESC
            LIMIT 100
        """)

        rows = cursor.fetchall()

        conn.close()

        output = f"""
        <h2>Database Debug</h2>

        <b>DB Path:</b> {DB_NAME}<br>
        <b>DB Exists:</b> {db_exists}<br>
        <b>Current Directory:</b> {current_dir}<br>
        <b>DB Last Modified:</b> {db_modified}<br>
        <b>Total Rows:</b> {total_rows}<br><hr>
        """

        for row in rows:
            output += str(dict(row)) + "<br><br>"

        return output

    except Exception as e:

        return f"""
        <h2>DB Debug Error</h2>
        <pre>{str(e)}</pre>
        """