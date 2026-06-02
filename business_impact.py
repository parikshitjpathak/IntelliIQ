# ==========================================================
# BUSINESS IMPACT INTELLIGENCE CONFIGURATION
# ==========================================================

POLICIES_PER_HOUR = 9
AVERAGE_PREMIUM = 400
SLA_HOURS = 4

REVENUE_PER_HOUR = (
    POLICIES_PER_HOUR *
    AVERAGE_PREMIUM
)

# ==========================================================
# CONFIGURATION ENDS
# ==========================================================

# ==========================================================
# ANOMALY DETECTION CONFIGURATION
# ==========================================================

ANOMALY_DURATION_HOURS = 100

# ==========================================================
# ANOMALY DETECTION CONFIGURATION ENDS
# ==========================================================

# ==========================================================
# DIRECT REVENUE IMPACT CATEGORIES
# ==========================================================

DIRECT_REVENUE_CATEGORIES = [

    "Policy Issue",
    "Policy Issuance",
    "Policy Renewal",

    "Payment Issue",
    "Payment Processing",

    "Claims",

    "Login Issue",
    "Customer Access",

    "Quote Generation",

    "Agent/Broker Portal"

]

# ==========================================================
# INDIRECT REVENUE IMPACT CATEGORIES
# ==========================================================

INDIRECT_REVENUE_CATEGORIES = [

    "Database Issue",
    "Database",

    "Infrastructure",

    "Oracle",

    "Middleware",

    "Application Server",

    "Network",

    "Storage",

    "Compliance",

    "Security"

]





# ==========================================================
# REVENUE IMPACT CLASSIFICATION
# ==========================================================

def classify_revenue_impact(
    category,
    revenue_impact
):

    category = (
        category or ""
    ).strip()

    if category in DIRECT_REVENUE_CATEGORIES:

        return (
            "Direct Revenue Impact",
            "Revenue generating service affected"
        )

    if category in INDIRECT_REVENUE_CATEGORIES:

        return (
            "Indirect Revenue Impact",
            "Supporting service affected"
        )

    if str(
        revenue_impact
    ).lower() == "yes":

        return (
            "Indirect Revenue Impact",
            "Revenue impact flag enabled"
        )

    return (
        None,
        None
    )
# ==========================================================
# INCIDENT DURATION CALCULATION
# ==========================================================

from datetime import datetime


def calculate_duration_hours(
    incident_date,
    incident_time,
    resolved_date
):

    try:

        start_time = datetime.strptime(
            f"{incident_date} {incident_time}",
            "%Y-%m-%d %H:%M:%S"
        )

        resolved_date = (
            resolved_date
            .replace("T", " ")
            .split("+")[0]
        )

        end_time = datetime.strptime(
            resolved_date,
            "%Y-%m-%d %H:%M:%S.%f"
        )

        duration_hours = (
            end_time -
            start_time
        ).total_seconds() / 3600

        return round(
            duration_hours,
            2
        )

    except Exception as e:

        print(f"Duration calculation error = {e}")

        return 0
    # ==========================================================
# REVENUE CALCULATION ENGINE
# ==========================================================

def calculate_revenue_metrics(
    duration_hours
):

    potential_impact = (
        duration_hours *
        REVENUE_PER_HOUR
    )

    if duration_hours < SLA_HOURS:

        potential_saved = (
            SLA_HOURS -
            duration_hours
        ) * REVENUE_PER_HOUR

    else:

        potential_saved = 0

    return (

        round(
            potential_impact,
            2
        ),

        round(
            potential_saved,
            2
        )

    )
#duration = 2

#impact, saved = (
  #  calculate_revenue_metrics(
   #     duration
    #)
#)

#print(f"Impact = {impact}")
#print(f"Saved = {saved}")

# ==========================================================
# SQLITE DATA EXTRACTION
# ==========================================================

import sqlite3
import os
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_NAME = os.path.join(BASE_DIR, "IntelliIQ.db")




def get_business_impact_records():

    conn = sqlite3.connect(DB_NAME)

    conn.row_factory = sqlite3.Row

    cursor = conn.cursor()

    cursor.execute("""

        SELECT

            KB_ID,
            Incident,
            Category,
            Jira_Ticket_Id,
            revenue_impact,
            resolved_date,
            Date,
            Time

        FROM knowledgeBase

        WHERE resolved_date IS NOT NULL

    """)

    rows = cursor.fetchall()

    conn.close()

    #print(f"Records Retrieved = {len(rows)}")

    return rows
# ==========================================================
# KPI AGGREGATION ENGINE
# ==========================================================

def calculate_business_kpis():

    rows = get_business_impact_records()

    revenue_incident_count = 0

    total_revenue_impact = 0

    total_revenue_saved = 0

    sla_success_count = 0

    for row in rows:

        impact_type, reason = classify_revenue_impact(

            row["Category"],
            row["revenue_impact"]

        )

        if not impact_type:

            continue

        revenue_incident_count += 1

        duration_hours = calculate_duration_hours(

            row["Date"],
            row["Time"],
            row["resolved_date"]

        )
        #print(f"KB_ID={row['KB_ID']} Duration={duration_hours}") 

        impact, saved = calculate_revenue_metrics(

            duration_hours
        )

        total_revenue_impact += impact

        total_revenue_saved += saved

        if duration_hours <= SLA_HOURS:

            sla_success_count += 1

    if revenue_incident_count:

        sla_success_percentage = round(

            (
                sla_success_count /
                revenue_incident_count
            ) * 100,

            2

        )

    else:

        sla_success_percentage = 0

    return {

        "revenue_incident_count":
            revenue_incident_count,

        "potential_revenue_impact":
            round(
                total_revenue_impact,
                2
            ),

        "potential_revenue_saved":
            round(
                total_revenue_saved,
                2
            ),

        "sla_success_percentage":
            sla_success_percentage
        
                          

    }

# ==========================================================
# CATEGORY SUMMARY ENGINE
# ==========================================================

def get_category_summary():

    rows = get_business_impact_records()

    category_summary = {}

    for row in rows:

        impact_type, reason = classify_revenue_impact(

            row["Category"],
            row["revenue_impact"]

        )

        if not impact_type:

            continue

        duration_hours = calculate_duration_hours(

            row["Date"],
            row["Time"],
            row["resolved_date"]

        )

        impact, saved = calculate_revenue_metrics(

            duration_hours
        )

        category = (
            row["Category"]
            or
            "Unclassified"
        )

        if category not in category_summary:

            category_summary[category] = {

                "category": category,
                "count": 0,
                "revenue_impact": 0,
                "revenue_saved": 0

            }

        category_summary[category]["count"] += 1

        category_summary[category]["revenue_impact"] += impact

        category_summary[category]["revenue_saved"] += saved

    return sorted(

        category_summary.values(),

        key=lambda x:
            x["revenue_impact"],

        reverse=True

    )
# ==========================================================
# TOP REVENUE IMPACTING INCIDENTS
# ==========================================================

def get_top_revenue_incidents():

    rows = get_business_impact_records()

    incidents = []

    for row in rows:

        impact_type, reason = classify_revenue_impact(

            row["Category"],
            row["revenue_impact"]

        )

        if not impact_type:

            continue

        duration_hours = calculate_duration_hours(

            row["Date"],
            row["Time"],
            row["resolved_date"]

        )

        impact, saved = calculate_revenue_metrics(

            duration_hours
        )

        incidents.append({

            "ticket":
                row["Jira_Ticket_Id"],

            "incident":
                row["Incident"],

            "category":
                row["Category"],

            "impact_type":
                impact_type,

            "duration":
                duration_hours,

            "impact":
                impact,

            "saved":
                saved

        })

    incidents = sorted(

        incidents,

        key=lambda x:
            x["impact"],

        reverse=True

    )

    return incidents[:10]

# ==========================================================
# REVENUE IMPACT ANOMALY DETECTION
# ==========================================================

def get_revenue_impact_anomalies():

    rows = get_business_impact_records()

    anomalies = []

    for row in rows:

        impact_type, reason = classify_revenue_impact(

            row["Category"],
            row["revenue_impact"]

        )

        if not impact_type:

            continue

        duration_hours = calculate_duration_hours(

            row["Date"],
            row["Time"],
            row["resolved_date"]

        )

        impact, saved = calculate_revenue_metrics(

            duration_hours
        )

        if duration_hours >= ANOMALY_DURATION_HOURS:

            anomalies.append({

                "ticket":
                    row["Jira_Ticket_Id"],

                "incident":
                    row["Incident"],

                "category":
                    row["Category"],

                "duration":
                    duration_hours,

                "impact":
                    impact,

                "reason":
                    "Extended Duration"

            })

    return sorted(

        anomalies,

        key=lambda x:
            x["impact"],

        reverse=True

    )


# ==========================================================
# BUSINESS VALUE PRESERVATION INDEX
# ==========================================================

def calculate_business_value_preservation():

    kpis = calculate_business_kpis()

    impact = kpis[
        "potential_revenue_impact"
    ]

    saved = kpis[
        "potential_revenue_saved"
    ]

    if impact == 0:

        return 0

    return round(

        (
            saved /
            impact
        ) * 100,

        2

    )
# ==========================================================
# HIGHEST REVENUE IMPACT CATEGORY
# ==========================================================

def get_highest_impact_category():

    categories = get_category_summary()

    if not categories:

        return None

    return categories[0]

#========== test block temp========================
if __name__ == "__main__":

    kpis = calculate_business_kpis()

    #print(f"Revenue Incidents = {kpis['revenue_incident_count']}")

    #print(f"Potential Revenue Impact = {kpis['potential_revenue_impact']}")

    #print(f"Potential Revenue Saved = {kpis['potential_revenue_saved']}")

    #print(f"SLA Success % = {kpis['sla_success_percentage']}")

    #print(f"Business Value Preservation = {calculate_business_value_preservation()}")

    highest = get_highest_impact_category()

    #print(f"Highest Impact Category = {highest['category']}")
    #print(f"Highest Impact Value = ${highest['revenue_impact']:,.0f}")

    top_incidents = get_top_revenue_incidents()

    #print(f"Top Revenue Incidents = {len(top_incidents)}")

    anomalies = get_revenue_impact_anomalies()

    #print(f"Anomaly Count = {len(anomalies)}")

    for anomaly in anomalies:

        print(f"Anomaly Ticket = {anomaly['ticket']} Duration = {anomaly['duration']} Impact = ${anomaly['impact']:,.0f}")

   #=============test block ends ====================================#

# ==========================================================
# BUSINESS IMPACT ROUTES
# ==========================================================

from flask import render_template


def register_business_impact_routes(app):

    @app.route("/business_impact")

    def business_impact():

        kpis = calculate_business_kpis()

        category_summary = get_category_summary()

        top_incidents = get_top_revenue_incidents()

        anomalies = get_revenue_impact_anomalies()

        business_value_preservation = (
            calculate_business_value_preservation()
        )

        highest_category = (
            get_highest_impact_category()
        )
        impact_type_chart = get_impact_type_chart_data()
        category_chart = get_category_chart_data()
        top_incidents_chart = (get_top_incidents_chart_data())
        saved_category_chart = (get_saved_by_category_chart_data())

        return render_template(

            "business_impact.html",

            revenue_incident_count=
                kpis["revenue_incident_count"],

            potential_revenue_impact=
                kpis["potential_revenue_impact"],

            potential_revenue_saved=
                kpis["potential_revenue_saved"],

            sla_success_percentage=
                kpis["sla_success_percentage"],

            business_value_percentage=
                business_value_preservation,

            category_summary=
                category_summary,

            top_incidents=
                top_incidents,

            anomalies=
                anomalies,

            highest_category=
                highest_category,

            policies_per_hour=
                POLICIES_PER_HOUR,

            average_premium=
                AVERAGE_PREMIUM,

            revenue_per_hour=
                REVENUE_PER_HOUR,

            impact_type_chart=
                impact_type_chart,


            category_chart=
                category_chart,

            top_incidents_chart=
                top_incidents_chart,

            saved_category_chart=
                saved_category_chart,    

            sla_hours=
                SLA_HOURS

        )

# ==========================================================
# IMPACT TYPE CHART DATA
# ==========================================================

def get_impact_type_chart_data():

    rows = get_business_impact_records()

    direct_count = 0

    indirect_count = 0

    for row in rows:

        impact_type, reason = classify_revenue_impact(

            row["Category"],
            row["revenue_impact"]

        )

        if impact_type == "Direct Revenue Impact":

            direct_count += 1

        elif impact_type == "Indirect Revenue Impact":

            indirect_count += 1

    return {

        "labels": [

            "Direct Revenue Impact",
            "Indirect Revenue Impact"

        ],

        "values": [

            direct_count,
            indirect_count

        ]

    }
impact_chart = get_impact_type_chart_data()

# ==========================================================
# CATEGORY IMPACT CHART
# ==========================================================

def get_category_chart_data():

    categories = get_category_summary()

    labels = []
    values = []

    for item in categories:

        labels.append(
            item["category"]
        )

        values.append(
            round(
                item["revenue_impact"],
                0
            )
        )

    return {

        "labels": labels,

        "values": values

    }
# ==========================================================
# TOP INCIDENTS CHART
# ==========================================================

def get_top_incidents_chart_data():

    incidents = get_top_revenue_incidents()
    #print(incidents[0])

    labels = []
    values = []

    for item in incidents[:10]:

        labels.append(
            item["ticket"]
        )

        values.append(
            round(
                item["impact"],
                0
            )
        )

    return {

        "labels": labels,

        "values": values

    }
# ==========================================================
# REVENUE SAVED BY CATEGORY
# ==========================================================

def get_saved_by_category_chart_data():

    categories = get_category_summary()

    labels = []
    values = []

    for item in categories:

        labels.append(
            item["category"]
        )

        values.append(
            round(
                item["revenue_saved"],
                0
            )
        )

    return {

        "labels": labels,

        "values": values

    }   

#print(f"Impact Type Chart = {impact_chart}")
#===== This is the end of the python file=======