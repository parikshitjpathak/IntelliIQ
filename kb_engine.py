import sqlite3
import os

STOPWORDS = {
    # Generic noise
    "error", "issue", "failed", "failure", "problem",
    "not", "working", "unable",

    # UI noise
    "page", "screen",

    # Grammar / filler
    "the", "is", "a", "an", "of", "to", "in", "on", "for", "with", "and", "or",

    # Weak verbs
    "get", "getting", "does", "do", "did"
}

#DB_PATH = r"D:\pythonPractice\IntelliIQ.db"
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_NAME = os.path.join(BASE_DIR, "IntelliIQ.db")

def search_kb(incident):

    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()

    # Normalize input
    incident_words = set(
        word for word in (incident or "").lower().split()
        if word not in STOPWORDS
    )
    if len(incident_words) < 2:
        return None

    best_match = None
    best_score = 0
    all_matches = []

    # Fetch all records
    cursor.execute("""
    SELECT Incident, Solution, Root_Cause, Keywords, Jira_Ticket_Id, Date
    FROM knowledgeBase
    """)

    rows = cursor.fetchall()

    for row in rows:
        # Combine Incident + Keywords for better matching
        db_text = ((row[0] or "") + " " + (row[3] or "")).lower()
        db_words = set(
            word for word in db_text.split()
            if word not in STOPWORDS
        )

        # Calculate match score
        score = len(incident_words.intersection(db_words))

        if score > 0:
            all_matches.append((row, score))

        if score > best_score:
            best_score = score
            best_match = row

    conn.close()

    # 🚨 Avoid weak matches (like just "error")
    if best_score < 2:
        return None

    if not best_match:
        return None

    return {
        "match": {
            "incident": best_match[0],
            "solution": best_match[1],
            "root_cause": best_match[2],
            "keywords": best_match[3],
            "jira_ticket_id": best_match[4]
        },
        "score": best_score,
        "frequency": len(all_matches),
        "top_root_cause": best_match[2],
        "matches": all_matches
    }