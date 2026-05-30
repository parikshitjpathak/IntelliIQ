import sqlite3
import os
import re

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_NAME = os.path.join(BASE_DIR, "IntelliIQ.db")

# Only true filler words
STOPWORDS = {
    "the", "is", "a", "an", "of", "to", "in",
    "on", "for", "with", "and", "or",
    "get", "getting", "does", "do", "did"
}

# Synonym normalization
SYNONYM_MAP = {

    # failure family
    "error": "failure",
    "errors": "failure",
    "exception": "failure",
    "exceptions": "failure",
    "failed": "failure",
    "failing": "failure",
    "unable": "failure",
    "cannot": "failure",
    "can't": "failure",

    # garbage collection family
    "gc": "garbage",
    "garbagecollection": "garbage",
    "garbagecollector": "garbage",

    
    # login family
    "signin": "login",
    "sign-in": "login",
    "authentication": "login",
    "auth": "login",
    "sso": "login",

    # payment family
    "transaction": "payment",
    "transactions": "payment",
    "gateway": "payment",
    "txn": "payment",
    

    # database family
    "db": "database",
    "sql": "database",
    "deadlock": "database",

    # integration
    "interface": "integration",
    "webservice": "integration",
    "soap": "integration",
    "webmethods": "integration",
    "web-methods": "integration",

     # application
    "app": "application",
    "apps": "application",

    # api
    "rest": "api",

    # claims
    "claim": "claims",
    "claimsubmission": "claims",
    "claimsubmission": "claims",
    "adjudication": "claims",

    # billing family
    "invoice": "billing",
    "invoicing": "billing",
    "premium": "billing",

    # document family
    "documents": "document",
    "pdf": "document",

    # service
    "svc": "service",

    # policy
    "policies": "policy",
    "policyissuance": "policy",
    "issuance": "policy",
    "renewal": "policy",
    "endorsement": "policy",

    # server
    "srv": "server",

    # authentication
    "auth": "login",
    "authenticate": "login",

    # single sign-on
    "sso": "login",

    # timeout
    "timeouts": "timeout"


}


def normalize_text(text):

    text = (text or "").lower()

    # ORA-600 -> ora600
    text = re.sub(r'ora[\s\-]*(\d+)', r'ora\1', text)

    # remove punctuation
    text = re.sub(r'[^a-z0-9\s]', ' ', text)

    # phrase normalization
    text = text.replace("not working", "failure")
    text = text.replace("unable to access", "login failure")
    text = text.replace("unable to login", "login failure")
    text = text.replace("timed out", "timeout")
    text = text.replace("time out", "timeout")

    text = text.replace(
        "connection refused",
        "connectivity failure"
    )

    text = text.replace(
        "service unavailable",
        "service failure"
    )

    text = text.replace(
        "internal server error",
        "failure"
    )

    text = text.replace(
        "page not loading",
        "failure"
    )

    text = text.replace(
        "unable to submit claim",
        "claims failure"
    )

    text = text.replace(
        "unable to create policy",
        "policy failure"
    )

    words = []

    for word in text.split():

        word = SYNONYM_MAP.get(word, word)

        if word not in STOPWORDS:
            words.append(word)

    return set(words)


def calculate_similarity(query_words, db_words):

    if not query_words or not db_words:
        return 0

    common = query_words.intersection(db_words)

    score = len(common)

    # bonus for important technical matches
    for token in common:

        if token.startswith("ora"):
            score += 3

        elif token in {
            "login",
            "payment",
            "database",
            "ajax",
            "api",
            "timeout",
            "claims",
            "policy"
        }:
            score += 2

    return score


def search_kb(incident):

    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()

    incident_words = normalize_text(incident)

    if not incident_words:
        conn.close()
        return None

    cursor.execute("""
        SELECT
            Incident,
            Solution,
            Root_Cause,
            Keywords,
            Jira_Ticket_Id,
            Date
        FROM knowledgeBase
    """)

    rows = cursor.fetchall()

    best_match = None
    best_score = 0
    all_matches = []

    for row in rows:

        db_text = (
            (row[0] or "")
            + " "
            + (row[3] or "")
        )

        db_words = normalize_text(db_text)

        score = calculate_similarity(
            incident_words,
            db_words

        )
        if score > 0:
            print(
                "MATCH:",
                row[0],
                "Score:",
                score
            )

        #=== old logic for matching incidents
        if score > 0:
            all_matches.append((row, score))

        #======= new matching logic below commented==========  

        #if score >= 2:
         #   all_matches.append((row, score))  

       #======= new matching logic ends ==========     

        if score > best_score:
            best_score = score
            best_match = row

    conn.close()

    # sort strongest matches first
    all_matches.sort(
        key=lambda x: x[1],
        reverse=True
    )
    #===== new code added below==============
    top_score = all_matches[0][1]

    filtered_matches = []

    for row, score in all_matches:

        if score >= max(2, top_score - 1):
            filtered_matches.append((row, score))


    #===== new code ends ====================

    if not best_match:
        return None

    # aggressive recall
    #========== changing the logic here too
    #if best_score < 1:
    #    return None

    #======== new logic below======
    if best_score < 2:
        return None


    #========= new logic end ========

    print("Incident words:", incident_words)
    print("DB words:", db_words)
    print("Score:", score)

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
        #"matches": all_matches[:20]
        "matches": filtered_matches[:20]
    }