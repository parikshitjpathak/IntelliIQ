# ==========================================================
# FUNCTION: enhance_with_domain
# ==========================================================

def enhance_with_domain(product, suggestions, incident):

    incident_lower = incident.lower()
    domain_suggestions = []

    # ================= GUIDEWIRE =================
    if product and "guidewire" in product.lower():

        if any(word in incident_lower for word in ["ajax", "ui", "frontend", "screen"]):
            domain_suggestions = [
                "Check Guidewire Jutro frontend logs",
                "Analyze browser console errors (Jutro UI)",
                "Validate API responses from Guidewire backend",
                "Check Datadog logs for frontend/API errors"
            ]

        elif any(word in incident_lower for word in ["batch", "job"]):
            domain_suggestions = [
                "Check Guidewire batch server status",
                "Review batch job execution logs",
                "Validate batch scheduler configuration"
            ]

        elif any(word in incident_lower for word in ["db", "database", "query"]):
            domain_suggestions = [
                "Check PostgreSQL database connectivity",
                "Analyze slow queries or locks",
                "Validate DB connection pool usage"
            ]

        else:
            domain_suggestions = [
                "Check Guidewire logs in Datadog/Splunk",
                "Validate application server health",
                "Review recent deployments or config changes"
            ]

    # ================= ONESHIELD =================
    elif product and "one" in product.lower():

        if any(word in incident_lower for word in ["db", "database", "oracle"]):
            domain_suggestions = [
                "Check Oracle DB for locks and blocking sessions",
                "Analyze slow queries in Oracle DB",
                "Validate DB connection pool"
            ]

        elif any(word in incident_lower for word in ["batch", "job"]):
            domain_suggestions = [
                "Check OneShield batch job execution",
                "Validate job scheduler status",
                "Review logs for failed jobs"
            ]

        elif any(word in incident_lower for word in ["policy", "submission"]):
            domain_suggestions = [
                "Check policy processing workflow",
                "Validate rating engine logic",
                "Review backend service logs"
            ]

        else:
            domain_suggestions = [
                "Check OneShield backend service logs",
                "Validate API responses",
                "Review system integration points"
            ]

    # ================= FINAL MERGE =================
    return domain_suggestions + suggestions