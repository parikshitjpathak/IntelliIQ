# ==========================================================
# PROCESS RUNBOOK GENERATOR
# VERSIONING ENABLED
# ==========================================================

from flask import render_template, request, session, jsonify
import markdown
import requests
import os
import sqlite3
import base64
from datetime import datetime

# ==========================================================
# CONFLUENCE CONFIG
# ==========================================================

CONFLUENCE_URL = "https://parikshit-pathak.atlassian.net/wiki"
CONFLUENCE_EMAIL = "parikshitjpathak@gmail.com"
CONFLUENCE_API_TOKEN = os.getenv("CONFLUENCE_API_TOKEN")

SPACE_KEY = "PR"

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_NAME = os.path.join(BASE_DIR, "IntelliIQ.db")

# ==========================================================
# PROCESS QUESTIONS
# ==========================================================

PROCESS_SECTIONS = [
    "scope",
    "tools",
    "prerequisites",
    "steps",
    "dependencies",
    "validation",
    "frequency"
]

PROCESS_QUESTIONS = {
    "scope": "What systems, applications, or teams are covered?",
    "tools": "What tools/platforms are used?",
    "prerequisites": "What access, approvals, or setup is required before starting?",
    "steps": "Provide detailed step-by-step execution of the process.",
    "dependencies": "Any system/team/process dependencies?",
    "validation": "How do you confirm the process was successful?",
    "frequency": "How often is this process performed?"
}

# ==========================================================
# INCIDENT QUESTIONS
# ==========================================================

INCIDENT_SECTIONS = [
    "failure",
    "troubleshooting",
    "resolution",
    "escalation",
    "sla",
    "prevention"
]

INCIDENT_QUESTIONS = {
    "failure": "How do you detect or identify the failure?",
    "troubleshooting": "What are common causes and diagnostic steps?",
    "resolution": "How do you resolve the issue?",
    "escalation": "When and to whom should this issue be escalated?",
    "sla": "What is the expected response/resolution SLA?",
    "prevention": "How can this issue be prevented in the future?"
}

# ==========================================================
# PROMPT BUILDER
# ==========================================================

def build_runbook_prompt(
    answers,
    created_by,
    runbook_type,
    runbook_title
):

    if runbook_type == "process":

        format_section = """
FORMAT STRICTLY USING THESE HEADINGS ONLY:

# 📘 Overview
# 🎯 Scope
# 🛠 Tools Used
# 🔐 Prerequisites
# 📝 Step-by-Step Procedure
# 🔗 Dependencies
# ✅ Validation Steps
# 🔁 Frequency
"""

    else:

        format_section = """
FORMAT STRICTLY USING THESE HEADINGS ONLY:

# 🚨 Incident Overview
# 🔍 Failure Detection
# 🧠 Troubleshooting Steps
# 🔧 Resolution Steps
# 📞 Escalation Matrix
# ⏱ SLA Expectations
# 🛡 Prevention Recommendations
"""

    return f"""
You are a senior Site Reliability Engineer (SRE).

Create a PROFESSIONAL ENTERPRISE RUNBOOK.

RUNBOOK TITLE:
{runbook_title}

Created By:
{created_by}

RUNBOOK TYPE:
{runbook_type}

{format_section}

USER INPUT:
{answers}
"""

# ==========================================================
# CONFLUENCE
# ==========================================================

def create_confluence_page(title, content_html):

    url = f"{CONFLUENCE_URL}/rest/api/content"

    auth = base64.b64encode(
        f"{CONFLUENCE_EMAIL}:{CONFLUENCE_API_TOKEN}".encode()
    ).decode()

    headers = {
        "Authorization": f"Basic {auth}",
        "Content-Type": "application/json"
    }

    data = {
        "type": "page",
        "title": title,
        "space": {"key": SPACE_KEY},
        "body": {
            "storage": {
                "value": content_html,
                "representation": "storage"
            }
        }
    }

    response = requests.post(url, json=data, headers=headers)

    if response.status_code in [200, 201]:

        page_id = response.json()["id"]

        return f"{CONFLUENCE_URL}/spaces/{SPACE_KEY}/pages/{page_id}"

    else:

        print("Confluence Error:", response.text)

        return None

# ==========================================================
# TITLE
# ==========================================================

def generate_safe_title(title):

    if not title:
        return "Runbook"

    title = title.replace("\n", " ").strip()

    return title

# ==========================================================
# VERSION FETCH
# ==========================================================

def get_next_runbook_version(runbook_title):

    try:

        conn = sqlite3.connect(DB_NAME)

        cursor = conn.cursor()

        cursor.execute("""
            SELECT MAX(runbook_ver)
            FROM runbook
            WHERE bookname LIKE ?
        """, (f"{runbook_title}%",))

        row = cursor.fetchone()

        conn.close()

        if row and row[0]:

            return row[0] + 1

        return 1

    except Exception as e:

        print("Version Fetch Error:", e)

        return 1

# ==========================================================
# SAVE RUNBOOK
# ==========================================================

def save_runbook(
    bookname,
    runbook_type,
    createdby,
    bookurl,
    status,
    version
):

    try:

        conn = sqlite3.connect(DB_NAME)

        cursor = conn.cursor()

        cursor.execute("""
            INSERT INTO runbook
            (
                bookname,
                runbook_type,
                createdby,
                bookurl,
                created_at,
                status,
                runbook_ver
            )
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (
            bookname,
            runbook_type,
            createdby,
            bookurl,
            datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            status,
            version
        ))

        conn.commit()

        conn.close()

        print("Runbook saved successfully")

    except Exception as e:

        print("Runbook DB Error:", e)

# ==========================================================
# ROUTES
# ==========================================================

def register_process_doc(app, llm):

    @app.route("/process_doc")
    def process_doc_page():

        session.clear()

        session["answers"] = {}
        session["index"] = 0

        return render_template(
            "process_doc.html",
            active_page="runbook"
        )

    # ======================================================
    # CHAT FLOW
    # ======================================================

    @app.route("/process_doc_chat", methods=["POST"])
    def process_doc_chat():

        runbook_type = request.json.get("runbook_type", "process")
        runbook_title = request.json.get("runbook_title", "Runbook")

        session["runbook_type"] = runbook_type
        session["runbook_title"] = runbook_title

        if runbook_type == "incident":

            sections = INCIDENT_SECTIONS
            questions = INCIDENT_QUESTIONS

        else:

            sections = PROCESS_SECTIONS
            questions = PROCESS_QUESTIONS

        user_input = request.json.get("message", "").strip()

        answers = session.get("answers", {})
        idx = session.get("index", 0)

        if idx == 0:

            session["index"] = 1

            return jsonify({
                "reply": f"Let’s build a {runbook_type} runbook for '{runbook_title}'.\n\n{questions[sections[0]]}",
                "progress": f"Question 1 of {len(sections)}"
            })

        if not user_input:

            return jsonify({
                "reply": "Please provide a response before continuing.",
                "progress": f"Question {idx} of {len(sections)}"
            })

        prev_section = sections[idx - 1]

        answers[prev_section] = user_input

        acknowledgement = ""

        lower_input = user_input.lower()

        if prev_section == "dependencies":

            if lower_input in [
                "none",
                "no",
                "na",
                "n/a",
                "not applicable"
            ]:

                answers["dependencies"] = "No major dependencies."

                acknowledgement = "Dependencies marked as not applicable.\n\n"

        if idx < len(sections):

            session["answers"] = answers
            session["index"] = idx + 1

            return jsonify({
                "reply": acknowledgement + questions[sections[idx]],
                "progress": f"Question {idx + 1} of {len(sections)}"
            })

        session["answers"] = answers

        return jsonify({
            "reply": "Workflow completed successfully.\n\nClick 'Generate Runbook' to continue.",
            "progress": "Workflow completed"
        })

    # ======================================================
    # GENERATE DOCUMENT
    # ======================================================

    @app.route("/generate_process_doc", methods=["POST"])
    def generate_process_doc():

        data = request.get_json() or {}

        created_by = data.get("created_by", "Unknown")
        runbook_type = data.get("runbook_type", "process")
        runbook_title = data.get("runbook_title", "Runbook")

        answers = session.get("answers", {})

        version = get_next_runbook_version(runbook_title)

        versioned_title = f"{runbook_title} v{version}"

        prompt = build_runbook_prompt(
            answers,
            created_by,
            runbook_type,
            versioned_title
        )

        try:

            response = llm.invoke(prompt)

            answer = response.content

        except Exception as e:

            print("LLM Error:", e)

            return jsonify({
                "error": "LLM failed"
            })

        html_content = markdown.markdown(
            answer.replace("\n", "  \n"),
            extensions=["fenced_code", "tables"]
        )

        html_content = f"""
        <p><b>Created By:</b> {created_by}</p>
        <p><b>Runbook Version:</b> v{version}</p>
        <hr>
        {html_content}
        """

        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        final_title = f"{versioned_title} - {timestamp}"

        link = create_confluence_page(
            final_title,
            html_content
        )

        status = "Success" if link else "Failed"

        save_runbook(
            bookname=runbook_title,
            runbook_type=runbook_type,
            createdby=created_by,
            bookurl=link if link else "N/A",
            status=status,
            version=version
        )

        session.clear()

        return jsonify({
            "document": html_content,
            "link": link if link else "Failed to create Confluence page"
        })

    # ======================================================
    # REPOSITORY PAGE
    # ======================================================

    @app.route("/runbook_repository")
    def runbook_repository():

        return render_template(
            "runbook_repo.html",
            active_page="repository"
        )

    # ======================================================
    # FETCH RUNBOOKS
    # ======================================================

    @app.route("/get_runbooks", methods=["POST"])
    def get_runbooks():

        data = request.get_json() or {}

        title = data.get("title", "")
        creator = data.get("creator", "")
        runbook_type = data.get("type", "")

        conn = sqlite3.connect(DB_NAME)

        conn.row_factory = sqlite3.Row

        cursor = conn.cursor()

        query = """
            SELECT *
            FROM runbook
            WHERE 1=1
        """

        params = []

        if title:

            query += " AND bookname LIKE ?"

            params.append(f"%{title}%")

        if creator:

            query += " AND createdby LIKE ?"

            params.append(f"%{creator}%")

        if runbook_type:

            query += " AND runbook_type = ?"

            params.append(runbook_type)

        query += " ORDER BY created_at DESC"

        cursor.execute(query, params)

        rows = cursor.fetchall()

        conn.close()

        results = []

        for row in rows:

            results.append({
                "bookname": row["bookname"],
                "runbook_type": row["runbook_type"],
                "createdby": row["createdby"],
                "bookurl": row["bookurl"],
                "created_at": row["created_at"],
                "status": row["status"],
                "runbook_ver": row["runbook_ver"]
            })

        return jsonify(results)