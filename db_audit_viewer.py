import os
import sqlite3

from flask import Blueprint

db_audit_bp = Blueprint(
    "db_audit",
    __name__
)

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_NAME = os.path.join(BASE_DIR, "IntelliIQ.db")


@db_audit_bp.route("/db_audit")
def db_audit():

    try:

        db_exists = os.path.exists(DB_NAME)

        conn = sqlite3.connect(
            DB_NAME,
            timeout=30
        )

        conn.row_factory = sqlite3.Row

        cursor = conn.cursor()

        cursor.execute("""
            SELECT *
            FROM kb_audit_log
            ORDER BY audit_id DESC
            LIMIT 100
        """)

        rows = cursor.fetchall()

        conn.close()

        output = f"""

        <h2>KB Audit Log</h2>

        <b>BASE_DIR:</b> {BASE_DIR}<br>
        <b>DB_NAME:</b> {DB_NAME}<br>
        <b>DB_EXISTS:</b> {db_exists}<br>

        <hr>

        """

        if not rows:

            output += "<b>No Audit Records Found</b><br>"

        else:

            for row in rows:

                output += str(dict(row))
                output += "<br><br>"

        return output

    except Exception as e:

        return f"""

        <h2>Audit Viewer Error</h2>

        <b>BASE_DIR:</b> {BASE_DIR}<br>
        <b>DB_NAME:</b> {DB_NAME}<br>

        <hr>

        <pre>{str(e)}</pre>

        """