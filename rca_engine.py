
# ==========================================================
# RCA ENGINE
# ==========================================================

import json
import sqlite3

from datetime import datetime

from flask import request, render_template

from normalization_engine import normalize_incident

from ticketing_service import (
    create_confluence_page,
    add_jira_comment
)


# ==========================================================
# REGISTER RCA ROUTES
# ==========================================================

def register_rca_routes(app, llm, DB_NAME):


    # ==========================================================
    # SIMPLE RCA GENERATOR
    # ==========================================================

    def generate_rca_simple(
        incident,
        ticket_id,
        impact,
        notes,
        resolution_notes,
        status,
        team,
        fix_date
    ):

        prompt = f"""
        You are an expert support engineer.

        Generate a structured RCA in JSON format.

        {{
          "issue": "",
          "ticket_id": "",
          "impact": "",
          "root_cause": "",
          "resolution": "",
          "preventive_actions": "",
          "status": "",
          "team": "",
          "fix_date": ""
        }}

        Incident: {incident}
        Ticket ID: {ticket_id}
        Impact: {impact}
        Notes: {notes}
        Resolution Notes: {resolution_notes}
        Status: {status}
        Team: {team}
        Fix Date: {fix_date}
        """

        try:

            response = llm.invoke(prompt)

            raw_text = response.content.strip()

            if raw_text.startswith("```"):
                raw_text = (
                    raw_text
                    .replace("```json", "")
                    .replace("```", "")
                    .strip()
                )

            #rca_output = json.loads(raw_text)
            # Remove markdown wrappers if present

            if raw_text.startswith("```json"):
                raw_text = raw_text.replace("```json", "")

            if raw_text.startswith("```"):
                raw_text = raw_text.replace("```", "")

            if raw_text.endswith("```"):
                raw_text = raw_text.replace("```", "")

            raw_text = raw_text.strip()
            if raw_text.startswith("json"):
                 raw_text = raw_text[4:].strip()

            print("RAW LLM OUTPUT:", raw_text)
            

            rca_output = json.loads(raw_text)

        except Exception as e:

            print("RCA error:", e)

            rca_output = {
                "issue": incident,
                "ticket_id": ticket_id,
                "impact": impact,
                "root_cause": "Could not parse AI response",
                "resolution": resolution_notes,
                "preventive_actions": "Unable to generate preventive actions, because AI response could not be parsed",
                "status": status,
                "team": team,
                "fix_date": fix_date,
            }

        return rca_output


    # ==========================================================
    # GET RCA TICKETS
    # ==========================================================

    def get_ticket_data():

        conn = sqlite3.connect(DB_NAME)
        cursor = conn.cursor()

        cursor.execute(
            """
            SELECT Incident, Date, Jira_Ticket_Id
            FROM Knowledgebase
            WHERE Jira_Ticket_Id IS NOT NULL
            AND Jira_Ticket_Id != ''
            ORDER BY Date DESC
            """
        )

        rows = cursor.fetchall()

        conn.close()

        return rows


    # ==========================================================
    # RCA PAGE
    # ==========================================================

    @app.route("/rca", methods=["GET", "POST"])
    def rca_page():

        tickets = get_ticket_data()

        if request.method == "POST":

            incident = request.form.get("incident")
            ticket_id = request.form.get("ticket_id")

            impact = request.form.get("impact")
            notes = request.form.get("notes")
            resolution_notes = request.form.get("resolution_notes")
            sla_miss_reason = request.form.get("sla_miss_reason")


            status = request.form.get("status")
            team = request.form.get("team")
            created_by = request.form.get("created_by")
            fix_date = request.form.get("fix_date")

            issue_reported_datetime = request.form.get("issue_reported_datetime")
            issue_resolved_datetime = request.form.get("issue_resolved_datetime")

            identified_by = request.form.get("identified_by")
            detection_method = request.form.get("detection_method")

            temporary_fix = request.form.get("temporary_fix")
            permanent_fix_available = request.form.get("permanent_fix_available")
            vendor_involvement = request.form.get("vendor_involvement")
            restart_required = request.form.get("restart_required")
            deployment_required = request.form.get("deployment_required")

            issue_duration = ""

            try:

                if issue_reported_datetime and issue_resolved_datetime:

                    start = datetime.fromisoformat(issue_reported_datetime)
                    end = datetime.fromisoformat(issue_resolved_datetime)

                    duration = end - start

                    total_minutes = int(duration.total_seconds() / 60)

                    hours = total_minutes // 60
                    minutes = total_minutes % 60

                    issue_duration = f"{hours} hrs {minutes} mins"

            except Exception as duration_error:

                print(
                    "Issue duration calculation error:",
                    str(duration_error)
                )

            rca_output = generate_rca_simple(
                incident,
                ticket_id,
                impact,
                notes,
                resolution_notes,
                status,
                team,
                fix_date
            )

            rca_output["issue_duration"] = issue_duration

            existing_rca_found = False
            existing_confluence_link = None

            try:

                conn = sqlite3.connect(DB_NAME)
                cursor = conn.cursor()

                cursor.execute(
                    """
                    SELECT confluence_link
                    FROM rca_knowledge
                    WHERE jira_ticket_id = ?
                    ORDER BY rca_id DESC
                    LIMIT 1
                    """,
                    (ticket_id,)
                )

                row = cursor.fetchone()

                if row:

                    existing_rca_found = True
                    existing_confluence_link = row[0]

                conn.close()

            except Exception as rca_check_error:

                print(
                    "RCA existence check error:",
                    str(rca_check_error)
                )

            try:

                normalized_incident = normalize_incident(incident)

                conn = sqlite3.connect(DB_NAME)
                cursor = conn.cursor()

                cursor.execute(
                    """
                    INSERT INTO rca_knowledge (

                        jira_ticket_id,
                        incident,
                        normalized_incident,
                        impact,
                        notes,
                        resolution_notes,
                        ai_root_cause,
                        ai_resolution,
                        preventive_actions,
                        status,
                        responsible_team,
                        fix_date,
                        created_by,
                        issue_reported_datetime,
                        issue_resolved_datetime,
                        identified_by,
                        detection_method,
                        issue_duration,
                        temporary_fix,
                        permanent_fix_available,
                        vendor_involvement,
                        restart_required,
                        deployment_required,
                        sla_miss_reason

                    )

                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """,

                    (

                        ticket_id,
                        incident,
                        normalized_incident,
                        impact,
                        notes,
                        resolution_notes,
                        rca_output.get("root_cause"),
                        rca_output.get("resolution"),
                        rca_output.get("preventive_actions"),
                        status,
                        team,
                        fix_date,
                        created_by,
                        issue_reported_datetime,
                        issue_resolved_datetime,
                        identified_by,
                        detection_method,
                        issue_duration,
                        temporary_fix,
                        permanent_fix_available,
                        vendor_involvement,
                        restart_required,
                        deployment_required,
                        sla_miss_reason

                    )
                )

                conn.commit()
                conn.close()

            except Exception as rca_db_error:

                print(
                    "RCA DB persistence error:",
                    str(rca_db_error)
                )

            return render_template(
                "rca.html",
                rca_output=rca_output,
                tickets=tickets,
                existing_rca_found=existing_rca_found,
                existing_confluence_link=existing_confluence_link
            )

        return render_template(
            "rca.html",
            rca_output=None,
            tickets=tickets,
            active_page="rca"
        )


    # ==========================================================
    # AJAX RCA CHECK
    # ==========================================================

    @app.route("/check_existing_rca/<ticket_id>")
    def check_existing_rca(ticket_id):

        try:

            conn = sqlite3.connect(DB_NAME)
            cursor = conn.cursor()

            cursor.execute(
                """
                SELECT confluence_link
                FROM rca_knowledge
                WHERE jira_ticket_id = ?
                ORDER BY rca_id DESC
                LIMIT 1
                """,
                (ticket_id,)
            )

            row = cursor.fetchone()

            conn.close()

            if row:

                return {
                    "exists": True,
                    "confluence_link": row[0],
                    "source": "rca_knowledge"
                }

            return {
                "exists": False
            }

        except Exception as e:

            return {
                "exists": False,
                "error": str(e)
            }


    # ==========================================================
    # PUSH RCA TO CONFLUENCE
    # ==========================================================

    @app.route("/push_rca_confluence", methods=["POST"])
    def push_rca_confluence():

        ticket_id = request.form.get("ticket_id")
        sla_miss_reason = request.form.get("sla_miss_reason","")

        conn = sqlite3.connect(DB_NAME)
        cursor = conn.cursor()

        cursor.execute(
            """
            SELECT Incident
            FROM Knowledgebase
            WHERE Jira_Ticket_Id = ?
            """,
            (ticket_id,)
        )

        row = cursor.fetchone()

        conn.close()

        incident = row[0] if row else "Unknown Incident"

        rca_output = request.form.get("rca_output")

        rca_data = json.loads(rca_output)

        content = f"""

🚨 Incident Summary
----------------------------------------
Issue: {rca_data.get("issue", "")}

🎟 Jira Ticket
----------------------------------------
Ticket ID: {rca_data.get("ticket_id", "")}

⏰ SLA Information
----------------------------------------
SLA Miss Reason: {sla_miss_reason}

📊 Business Impact
----------------------------------------
{rca_data.get("impact", "")}

📝 Investigation Notes
----------------------------------------
{request.form.get("notes", "")}

🛠 Resolution Implemented
----------------------------------------
{rca_data.get("resolution", "")}

🔍 Root Cause
----------------------------------------
{rca_data.get("root_cause", "")}

🛡 Preventive Actions
----------------------------------------
{rca_data.get("preventive_actions", "")}

👥 Responsible Team
----------------------------------------
{rca_data.get("team", "")}

🧑 RCA Created By
----------------------------------------
{request.form.get("created_by", "")}

📅 Fix Date
----------------------------------------
{rca_data.get("fix_date", "")}

⏱ Issue Duration
----------------------------------------
{rca_data.get("issue_duration", "")}

📌 Status
----------------------------------------
{rca_data.get("status", "")}

"""

        page_link = create_confluence_page(
            incident,
            "RCA Generated via IntelliIQ",
            content,
            "",
            ticket_id
        )

        add_jira_comment(ticket_id, page_link)

        try:

            conn = sqlite3.connect(DB_NAME)
            cursor = conn.cursor()

            cursor.execute(
                """
                UPDATE rca_knowledge
                SET confluence_link = ?
                WHERE jira_ticket_id = ?
                """,
                (
                    page_link,
                    ticket_id
                )
            )

            conn.commit()
            conn.close()

        except Exception as rca_conf_error:

            print(
                "RCA confluence update error:",
                str(rca_conf_error)
            )

        return render_template(
            "rca.html",
            success_message="RCA pushed to Confluence successfully!",
            page_link=page_link,
            rca_output=rca_data,
            tickets=get_ticket_data(),
        )
