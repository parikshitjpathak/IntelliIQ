# ==========================================================
# FUNCTION: get_decision
# Purpose:
# - Provide recommendation based on incident frequency
# ==========================================================

def get_decision(frequency, data):

    if frequency == 0:
        return f"🆕 New issue detected. I suggest you should log a new ticket  - {data.get('root_cause')}"

    elif frequency > 3:
        return "🔗 Looks like a recurring issue. Strongly recommend to link to an existing ticket"

    return "⚠️ Similar incidents found. Review existing ticket before creating a new one"



# ==========================================================
# END FUNCTION
# ==========================================================