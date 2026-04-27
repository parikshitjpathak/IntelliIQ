import sqlite3
import requests
from datetime import datetime

# 🔧 CONFIG (UPDATE THESE)
import os
from dotenv import load_dotenv

load_dotenv()

JIRA_BASE_URL = os.getenv("JIRA_URL")
EMAIL = os.getenv("JIRA_EMAIL")
API_TOKEN = os.getenv("JIRA_API_TOKEN")

#DB_NAME = r"D:\pythonPractice\IntelliIQ.db"



BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_NAME = os.path.join(BASE_DIR, "IntelliIQ.db")


def fetch_jira_ticket(ticket_id):
    url = f"{JIRA_BASE_URL}/rest/api/3/issue/{ticket_id}"

    response = requests.get(
        url,
        auth=(EMAIL, API_TOKEN),
        headers={"Accept": "application/json"}
    )

    if response.status_code != 200:
        print(f"❌ Failed to fetch {ticket_id}: {response.status_code}")
        return None

    data = response.json()

    try:
        status = data["fields"]["status"]["name"]
        assignee = data["fields"]["assignee"]
        assigned_to = assignee["displayName"] if assignee else "Unassigned"
        resolved_date = data["fields"]["resolutiondate"]

        return {
            "status": status,
            "assigned_to": assigned_to,
            "resolved_date": resolved_date
        }

    except Exception as e:
        print(f"⚠️ Error parsing {ticket_id}: {e}")
        return None


def update_db(ticket_id, jira_data):
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()

    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    cursor.execute("""
                   UPDATE knowledgeBase
                   SET status        = ?,
                       assigned_to   = ?,
                       resolved_date = ?,
                       last_synced   = ?
                   WHERE Jira_Ticket_Id = ?
                   """, (
                       jira_data["status"],
                       jira_data["assigned_to"],
                       jira_data["resolved_date"],
                       now,
                       ticket_id
                   ))

    conn.commit()
    conn.close()


def run_sync():
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()

    cursor.execute("SELECT Jira_Ticket_Id FROM knowledgeBase WHERE Jira_Ticket_Id IS NOT NULL")
    tickets = cursor.fetchall()

    conn.close()

    print(f"🔄 Syncing {len(tickets)} tickets...")

    for (ticket_id,) in tickets:
        jira_data = fetch_jira_ticket(ticket_id)

        if jira_data:
            update_db(ticket_id, jira_data)
            print(f"✅ Updated {ticket_id}")
        else:
            print(f"❌ Skipped {ticket_id}")


if __name__ == "__main__":
    run_sync()