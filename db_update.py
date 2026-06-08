import os
import sqlite3
from flask import Blueprint

db_update_test_bp = Blueprint(
    "db_update_test",
    __name__
)

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_NAME = os.path.join(BASE_DIR, "IntelliIQ.db")


@db_update_test_bp.route("/db_update_test")
def db_update_test():

    try:

        conn = sqlite3.connect(DB_NAME)
        cursor = conn.cursor()

        cursor.execute("""
            UPDATE knowledgeBase
            SET Jira_Ticket_Id = 'TEST-999'
            WHERE KB_ID = 52
        """)

        conn.commit()
        conn.close()

        return "KB_ID 52 updated to TEST-999"

    except Exception as e:

        return f"""
        <h2>DB Update Error</h2>
        <pre>{str(e)}</pre>
        """