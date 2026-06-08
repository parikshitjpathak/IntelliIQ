import os
import sqlite3

from flask import Blueprint
from datetime import datetime

db_tables_bp = Blueprint(
    "db_tables",
    __name__
)

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_NAME = os.path.join(BASE_DIR, "IntelliIQ.db")


@db_tables_bp.route("/db_tables")
def db_tables():

    try:

        db_exists = os.path.exists(DB_NAME)

        current_dir = os.getcwd()

        db_modified = "N/A"
        file_size = "N/A"

        if db_exists:

            db_stats = os.stat(DB_NAME)

            db_modified = datetime.fromtimestamp(
                db_stats.st_mtime
            )

            file_size = db_stats.st_size

        conn = sqlite3.connect(
            DB_NAME,
            timeout=30
        )

        conn.row_factory = sqlite3.Row

        cursor = conn.cursor()

        cursor.execute("""

            SELECT
                name

            FROM sqlite_master

            WHERE type='table'

            ORDER BY name

        """)

        tables = cursor.fetchall()

        cursor.execute("""

            SELECT COUNT(*)

            FROM sqlite_master

            WHERE type='table'

        """)

        table_count = cursor.fetchone()[0]

        conn.close()

        output = f"""

        <h2>Database Table Inventory</h2>

        <b>BASE_DIR:</b> {BASE_DIR}<br>
        <b>DB_NAME:</b> {DB_NAME}<br>
        <b>Current Directory:</b> {current_dir}<br>
        <b>DB Exists:</b> {db_exists}<br>
        <b>DB Last Modified:</b> {db_modified}<br>
        <b>DB File Size:</b> {file_size}<br>
        <b>Total Tables:</b> {table_count}<br>

        <hr>

        <h3>Tables Found</h3>

        """

        if not tables:

            output += "<b>No Tables Found</b>"

        else:

            for table in tables:

                output += f"{table['name']}<br>"

        return output

    except Exception as e:

        return f"""

        <h2>Database Tables Error</h2>

        <b>BASE_DIR:</b> {BASE_DIR}<br>
        <b>DB_NAME:</b> {DB_NAME}<br>

        <hr>

        <pre>{str(e)}</pre>

        """