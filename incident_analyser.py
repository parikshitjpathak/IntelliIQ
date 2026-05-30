import os
import sqlite3

from flask import (
    Blueprint,
    render_template,
    request
)

from werkzeug.utils import secure_filename

from normalization_engine import normalize_incident
from historical_rca_engine import search_historical_rca


# ==========================================================
# BLUEPRINT
# ==========================================================

incident_bp = Blueprint(
    "incident_bp",
    __name__
)


# ==========================================================
# CONFIG
# ==========================================================

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

DB_NAME = os.path.join(BASE_DIR, "IntelliIQ.db")

UPLOAD_FOLDER = os.path.join(BASE_DIR, "uploaded_logs")

os.makedirs(UPLOAD_FOLDER, exist_ok=True)


# ==========================================================
# INCIDENT ANALYSER PAGE
# ==========================================================

@incident_bp.route("/incident_analyser", methods=["GET", "POST"])
def incident_analyser():

    # ======================================================
    # GET
    # ======================================================

    if request.method == "GET":

        return render_template(
            "analyseIncidents.html",
            active_page="home"
        )


    # ======================================================
    # FORM INPUTS
    # ======================================================

    incident = request.form.get("incident", "").strip()

    product = request.form.get("product", "")

    environment = request.form.get("environment", "")

    priority = request.form.get("priority", "")

    users_impacted = request.form.get("users_impacted", "")

    region = request.form.get("region_impacted", "")

    revenue_impact = request.form.get("revenue_impact", "")

    workaround = request.form.get("workaround", "")


    print("\n=== INCIDENT ANALYSER ===")

    print("Incident:", incident)

    print("Product:", product)

    print("Environment:", environment)

    print("Priority:", priority)


    # ======================================================
    # NORMALIZATION
    # ======================================================

    normalized_incident = normalize_incident(incident)

    print("Normalized Incident:", normalized_incident)


    # ======================================================
    # HISTORICAL RCA
    # ======================================================

    historical_rca = search_historical_rca(incident)

    historical_rca_found = historical_rca is not None

    print("Historical RCA Retrieved")


    # ======================================================
    # DB CONNECTION
    # ======================================================

    conn = sqlite3.connect(DB_NAME)

    cursor = conn.cursor()


    # ======================================================
    # FETCH LATEST KB_ID
    # ======================================================

    cursor.execute(
        "SELECT MAX(KB_ID) FROM knowledgeBase"
    )

    row = cursor.fetchone()

    incident_id = row[0]

    print("KB_ID:", incident_id)


    # ======================================================
    # FILE HANDLING
    # ======================================================

    file_mappings = {

        "app_logs": "Application Logs",

        "data_logs": "Database Logs",

        "dynatrace_log": "Dynatrace Logs",

        "product_logs": "Product Logs",

        "middleware_logs": "Middleware Logs",

        "api_logs": "API Logs"
    }


    for field_name, evidence_type in file_mappings.items():

        uploaded_files = request.files.getlist(field_name)

        for file in uploaded_files:

            if not file or file.filename == "":
                continue

            filename = secure_filename(file.filename)

            save_path = os.path.join(
                UPLOAD_FOLDER,
                filename
            )

            file.save(save_path)

            print("Saved:", filename)

            cursor.execute(
                """
                INSERT INTO incident_evidence (

                    incident_id,
                    evidence_type,
                    file_name,
                    file_path

                )

                VALUES (?, ?, ?, ?)
                """,
                (
                    incident_id,
                    evidence_type,
                    filename,
                    save_path
                )
            )


    conn.commit()

    conn.close()


    # ======================================================
    # FINAL RENDER
    # ======================================================

    return render_template(

        "analyseIncidents.html",

        incident=incident,

        product=product,

        environment=environment,

        priority=priority,

        normalized_incident=normalized_incident,

        historical_rca=historical_rca,

        historical_rca_found=historical_rca_found,

        show_result=True,

        active_page="home"
    )