import os
import sqlite3
from flask import Blueprint

db_debug_bp = Blueprint("db_debug", __name__)

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_NAME = os.path.join(BASE_DIR, "IntelliIQ.db")


@db_debug_bp.route("/db_debug")
def db_debug():

    try:

        db_exists = os.path.exists(DB_NAME)
        current_dir = os.getcwd()

        conn = sqlite3.connect(DB_NAME)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()

        # Total rows
        cursor.execute("""
            SELECT COUNT(*)
            FROM knowledgeBase
        """)
        total_rows = cursor.fetchone()[0]

        # Fetch all rows
        cursor.execute("""
            SELECT
            KB_ID,
            Incident,
            Jira_Ticket_Id,
            confluence_link,
            due_date,
            status
        FROM knowledgeBase
        WHERE lower(Incident) LIKE '%ajax%'
        ORDER BY KB_ID DESC
        """)

        
    

        rows = cursor.fetchall()

        conn.close()

        output = ""

        for row in rows:
            output += str(dict(row)) + "<br><br>"

        return output

        html = f"""
        <html>
        <head>
            <title>IntelliIQ DB Debug</title>
            <style>
                body {{
                    font-family: Arial, sans-serif;
                    padding: 20px;
                }}

                table {{
                    border-collapse: collapse;
                    width: 100%;
                }}

                th, td {{
                    border: 1px solid #ccc;
                    padding: 8px;
                    text-align: left;
                }}

                th {{
                    background-color: #f2f2f2;
                }}

                tr:nth-child(even) {{
                    background-color: #f9f9f9;
                }}
            </style>
        </head>
        <body>

        <h2>IntelliIQ Database Debug</h2>

        <p><b>DB Path:</b> {DB_NAME}</p>
        <p><b>DB Exists:</b> {db_exists}</p>
        <p><b>Current Working Directory:</b> {current_dir}</p>
        <p><b>Total Rows in knowledgeBase:</b> {total_rows}</p>

        <hr>

        <table>
            <tr>
                <th>KB_ID</th>
                <th>Incident</th>
                <th>Jira Ticket ID</th>
                <th>Confluence URL</th>
                <th>Due Date</th>
                <th>Status</th>
            </tr>
        """

        for row in rows:
            for row in rows:
                print(dict(row))
                return str(dict(row))

            html += f"""
            <tr>
                <td>{row['KB_ID']}</td>
                <td>{row['incident']}</td>
                <td>{row['jira_ticket_id']}</td>
                <td>{row['confluence_url']}</td>
                <td>{row['due_date']}</td>
                <td>{row['status']}</td>
            </tr>
            """

        html += """
        </table>

        </body>
        </html>
        """

        return html

    except Exception as e:

        return f"""
        <h2>DB Debug Error</h2>
        <pre>{str(e)}</pre>
        """