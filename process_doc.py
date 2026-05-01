# ==========================================================
# PROCESS RUNBOOK GENERATOR (FINAL WITH CONFLUENCE INTEGRATION)
# ==========================================================

from flask import render_template, request, session, jsonify
import uuid
import markdown
import requests
import os
import base64

# ==========================================================
# CONFLUENCE CONFIG
# ==========================================================

CONFLUENCE_URL = "https://parikshit-pathak.atlassian.net/wiki"
CONFLUENCE_EMAIL = "parikshitjpathak@gmail.com"
CONFLUENCE_API_TOKEN = os.getenv("CONFLUENCE_API_TOKEN")  # Set in env
SPACE_KEY = "PR"

# ==========================================================
# QUESTIONS
# ==========================================================

SECTIONS = [
    "overview","scope","tools","monitoring","failure",
    "troubleshooting","resolution","escalation",
    "sla","validation","prevention"
]

QUESTIONS = {
    "overview": "What is this process about?\nExample: Monitoring batch jobs.",
    "scope": "What systems are covered?\nExample: Claims, Policy.",
    "tools": "What tools are used?\nExample: SQL, Control-M.",
    "monitoring": "How do you monitor step-by-step?",
    "failure": "How do you detect failure?",
    "troubleshooting": "Common causes and checks?",
    "resolution": "How do you fix it?",
    "escalation": "When and whom to escalate?",
    "sla": "Expected timelines?",
    "validation": "How to confirm resolution?",
    "prevention": "How to avoid in future?"
}

# ==========================================================
# PROMPT BUILDER
# ==========================================================

def build_runbook_prompt(answers):

    return f"""
You are a senior SRE.

Create a PROFESSIONAL RUNBOOK.

STRICT:
- Fix grammar
- Expand details
- Add missing steps
- Use numbered steps
- Make it usable by L1

FORMAT:

### 📘 Overview
### 🎯 Scope
### 🛠 Tools
### 🔍 Monitoring Steps
### 🚨 Failure Detection
### 🧠 Troubleshooting
### 🔧 Resolution Steps
### 📞 Escalation
### ⏱ SLA
### ✅ Validation
### 🛡 Prevention

INPUT:
{answers}
"""

# ==========================================================
# CONFLUENCE PUSH
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

    if response.status_code == 200 or response.status_code == 201:
        page_id = response.json()["id"]
        return f"{CONFLUENCE_URL}/spaces/{SPACE_KEY}/pages/{page_id}"
    else:
        print("Confluence Error:", response.text)
        return None

# ==========================================================
# ROUTES
# ==========================================================

def register_process_doc(app, llm):

    @app.route("/process_doc")
    def process_doc_page():
        session.clear()
        session["answers"] = {}
        session["index"] = 0
        return render_template("process_doc.html", active_page="runbook")

    @app.route("/process_doc_chat", methods=["POST"])
    def process_doc_chat():

        user_input = request.json.get("message", "").strip()
        answers = session.get("answers", {})
        idx = session.get("index", 0)

        if idx == 0:
            session["index"] = 1
            return jsonify({
                "reply": "Let’s build a runbook.\n\n" + QUESTIONS[SECTIONS[0]],
                "progress": "0 / 11"
            })

        prev_section = SECTIONS[idx - 1]
        answers[prev_section] = user_input

        if idx < len(SECTIONS):
            session["answers"] = answers
            session["index"] = idx + 1
            return jsonify({
                "reply": QUESTIONS[SECTIONS[idx]],
                "progress": f"{len(answers)} / 11"
            })

        session["answers"] = answers

        return jsonify({
            "reply": "Click 'Generate Runbook' to create the document.",
            "progress": f"{len(answers)} / 11"
        })

    @app.route("/generate_process_doc", methods=["POST"])
    def generate_process_doc():

        answers = session.get("answers", {})

        # ===== LLM =====
        prompt = build_runbook_prompt(answers)

        try:
            response = llm.invoke(prompt)
            answer = response.content
        except Exception as e:
            print("LLM Error:", e)
            return jsonify({"error": "LLM failed"})

        # ===== FORMAT =====
        html_content = markdown.markdown(
            answer.replace("\n", "  \n"),
            extensions=["fenced_code", "tables"]
        )

        # ===== PUSH TO CONFLUENCE =====
        title = f"Runbook - {answers.get('overview', 'Process')}"
        link = create_confluence_page(title, html_content)

        return jsonify({
            "document": html_content,
            "link": link if link else "Failed to create Confluence page"
        })