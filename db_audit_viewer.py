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

        conn = sqlite3.connect(DB_NAME)
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

        output = "<h2>KB Audit Log</h2><hr>"

        for row in rows:

            output += str(dict(row))
            output += "<br><br>"

        return output

    except Exception as e:

        return f"""
        <h2>Audit Viewer Error</h2>
        <pre>{str(e)}</pre>
        """