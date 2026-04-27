# ==========================================================
# FILE: insurance_copilot.py
# PURPOSE:
# - Insurance Domain AI Copilot
# - Query handling
# - Query tracking (SQLite)
# - Top query trends
# ==========================================================

from flask import render_template, request
import sqlite3


# ==========================================================
# CONFIGURATION BLOCK
# (Update DB path here if needed)
# ==========================================================
#DB_PATH = r"D:\pythonPractice\IntelliIQ.db"
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_NAME = os.path.join(BASE_DIR, "IntelliIQ.db")

# ==========================================================
# DATABASE FUNCTIONS
# ==========================================================

def save_query(query):
    """Save user query into database"""

    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()

    cursor.execute("""
        INSERT INTO CopilotQueries (query)
        VALUES (?)
    """, (query,))

    conn.commit()
    conn.close()


def get_top_queries():
    """Fetch top 5 most searched queries"""

    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()

    cursor.execute("""
        SELECT query, COUNT(*) as count
        FROM CopilotQueries
        GROUP BY query
        ORDER BY count DESC
        LIMIT 5
    """)

    rows = cursor.fetchall()
    conn.close()

    return rows


# ==========================================================
# PROMPT GENERATION BLOCK
# (SAFE TO MODIFY PROMPT HERE ONLY)
# ==========================================================

def build_prompt(query):
    """Build AI prompt"""

    prompt = f"""
You are an expert Insurance Domain Support Copilot.

You assist across roles:
- Underwriter → business risk
- Business Analyst → workflows
- Product Owner → feature value
- Support Engineer → troubleshooting
- SRE → monitoring

Technologies:
OneShield, Guidewire, Jutro, Java, Oracle, SQL,
Dynatrace, Splunk, Datadog, NewRelic,
Informatica, WebMethods, ServiceNow, Jira, Autosys

------------------------------------------------------------

INSTRUCTIONS:

1. Identify query type:
   - Technical
   - Business
   - Operational
   - Mixed

2. Provide structured response.

3. Include ONLY relevant sections:

### 🔍 Overview

### 🛠 Step-by-Step Approach

### 💻 Implementation Example (if needed)

### ⚙️ Automation / Scheduling (if needed)

### 📊 Business Perspective (if needed)

### ✅ Best Practices

### ⚠️ Risks / Considerations

------------------------------------------------------------

RULES:
- Avoid generic answers
- Give practical implementation
- Include code/scheduler if automation involved
- Keep response concise and structured

------------------------------------------------------------

User Query:
{query}
"""
    return prompt


# ==========================================================
# MAIN ROUTE REGISTRATION
# ==========================================================

def register_insurance_copilot(app, llm):

    @app.route("/insurance_copilot", methods=["GET", "POST"])
    def insurance_copilot():

        answer = None  # Always initialize
        top_queries = get_top_queries()  # Always load trends

        if request.method == "POST":

            # ==================================================
            # STEP 1: GET USER INPUT
            # ==================================================
            query = request.form.get("query")

            if query:
                # ==================================================
                # STEP 2: SAVE QUERY
                # ==================================================
                save_query(query)

                # ==================================================
                # STEP 3: BUILD PROMPT
                # ==================================================
                prompt = build_prompt(query)

                # ==================================================
                # STEP 4: CALL LLM
                # ==================================================
                try:
                    response = llm.invoke(prompt)
                    answer = response.content
                except Exception as e:
                    print("Copilot Error:", e)
                    answer = "Error generating response"

        # ==================================================
        # STEP 5: RETURN RESPONSE
        # ==================================================
        return render_template(
            "Insurance_copilot.html",
            answer=answer,
            top_queries=top_queries
        )