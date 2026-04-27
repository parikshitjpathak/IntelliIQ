import re

# ==========================================================
# FUNCTION: generate_suggestions
# Purpose:
# - Generate troubleshooting steps from AI recommendations
# - Add fallback and escalation steps
# ==========================================================

def generate_suggestions(data, matches):
    suggestions = []

    recommendations = data.get("recommendations")

    if recommendations:
        steps = re.split(r'\.\s+', recommendations)
        suggestions = [s.strip() for s in steps if s.strip()]

    if not suggestions:
        suggestions = [
            "Check application logs for errors",
            "Validate recent changes or deployments"
        ]

    suggestions.append("If issue persists, escalate with logs and impact details")

    # Additional fallback if no matches
    if not matches:
        suggestions.append("Check application logs for error patterns")
        suggestions.append("Validate recent deployments or configuration changes")

    suggestions.append("If issue persists, consider escalating with detailed logs and impact analysis")

    return suggestions

# ==========================================================
# END FUNCTION
# ==========================================================