# ==========================================================
# LOG ANALYZER ROUTES
# ==========================================================

from flask import (
    render_template,
    request
)

from log_analyzer import analyze_logs


# ==========================================================
# REGISTER ROUTES
# ==========================================================

def register_log_analyzer_routes(
    app,
    llm,
    db_name
):

    @app.route(
        "/analyze_logs",
        methods=["GET", "POST"]
    )
    def analyze_logs_page():

        if request.method == "GET":

            return render_template(
                "analyseIncidentLogs.html"
            )

        incident = request.form.get(
            "incident",
            "Log Analysis Investigation"
        )

        kb_id = request.form.get(
            "kb_id"
        )

        if not kb_id:

            return render_template(
                "analyseIncidentLogs.html",
                ai_analysis=
                "No KB_ID supplied."
            )

        result = analyze_logs(
            incident,
            int(kb_id),
            db_name,
            llm
        )

        return render_template(

            "analyseIncidentLogs.html",

            evidence=result["evidence"],

            ai_analysis=result["analysis"]

        )