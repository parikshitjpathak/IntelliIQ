import os
import sqlite3
import socket
import platform

from flask import Blueprint
from datetime import datetime

db_environment_debug_bp = Blueprint(
    "db_environment_debug",
    __name__
)

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_NAME = os.path.join(BASE_DIR, "IntelliIQ.db")


@db_environment_debug_bp.route("/db_environment_debug")
def db_environment_debug():

    try:

        db_exists = os.path.exists(DB_NAME)

        db_stats = os.stat(DB_NAME)

        db_modified = datetime.fromtimestamp(
            db_stats.st_mtime
        )

        conn = sqlite3.connect(DB_NAME)
        cursor = conn.cursor()

        cursor.execute("""
            SELECT COUNT(*)
            FROM knowledgeBase
        """)

        total_rows = cursor.fetchone()[0]

        conn.close()

        return f"""

        <h2>Environment Debug</h2>

        <b>Hostname:</b> {socket.gethostname()}<br>
        <b>Python Version:</b> {platform.python_version()}<br>
        <b>Operating System:</b> {platform.platform()}<br>

        <hr>

        <b>DB Path:</b> {DB_NAME}<br>
        <b>DB Exists:</b> {db_exists}<br>
        <b>DB Last Modified:</b> {db_modified}<br>
        <b>Total Rows:</b> {total_rows}<br>

        """

    except Exception as e:

        return f"""
        <h2>Environment Debug Error</h2>
        <pre>{str(e)}</pre>
        """