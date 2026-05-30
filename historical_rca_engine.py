# ==========================================================
# HISTORICAL RCA ENGINE
# Purpose:
# - Search historical RCA repository
# - Return previous RCA intelligence
# - Use similarity scoring from KB engine
# - Return best RCA match + top matches
# ==========================================================

import sqlite3
import os

from kb_engine import (
    calculate_similarity,
    normalize_text
)

# ==========================================================
# DATABASE CONFIG
# ==========================================================

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_NAME = os.path.join(BASE_DIR, "IntelliIQ.db")


# ==========================================================
# CALCULATE CONFIDENCE
# ==========================================================

def get_confidence(score):

    if score >= 6:
        return "High"

    elif score >= 3:
        return "Medium"

    return "Low"


# ==========================================================
# SEARCH HISTORICAL RCA
# ==========================================================

def search_historical_rca(incident):

    if not incident:
        return None

    query_words = normalize_text(
        incident
    )

    if not query_words:
        return None

    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()

    try:

        cursor.execute(
            """
            SELECT

                rca_id,
                jira_ticket_id,
                incident,
                normalized_incident,
                ai_root_cause,
                ai_resolution,
                preventive_actions,
                confluence_link,
                responsible_team,
                fix_date,
                created_at

            FROM RCA_Knowledge
            """
        )

        rows = cursor.fetchall()

        scored_matches = []

        for row in rows:

            rca_text = (
                (row[2] or "")
                + " "
                + (row[4] or "")
                + " "
                + (row[5] or "")
            )

            db_words = normalize_text(
                rca_text
            )

            score = calculate_similarity(
                query_words,
                db_words
            )

            if score > 0:

                scored_matches.append(
                    (row, score)
                )
             
        conn.close()

        if not scored_matches:
            return None

        scored_matches.sort(
            key=lambda x: x[1],
            reverse=True
        )

        best_match = scored_matches[0][0]
        best_score = scored_matches[0][1]

        #=================== for frequency calculation========================
       # cursor.execute(
        #    """
         #   SELECT COUNT(*)
          #  FROM RCA_Knowledge
           # WHERE normalized_incident = ?
            #""",
            #(best_match[3],)
        #)

        #occurrence_count = cursor.fetchone()[0]
        occurrence_count = len(scored_matches)


        #=================== frequency calculation ends here =======================

        if best_score < 2:
            return None

        confidence = get_confidence(
            best_score
        )

        top_matches = []

        for row, score in scored_matches[:3]:

            top_matches.append({

                "match_score": score,

                "confidence": get_confidence(score),

                "jira_ticket_id": row[1],

                "incident": row[2],

                "root_cause": row[4],

                "resolution": row[5],

                "confluence_link": row[7]

            })
        #print("Occurrence count is :", occurrence_count)

        return {

            "found": True,

            "match_score": best_score,

            "confidence": confidence,

            "jira_ticket_id": best_match[1],

            "incident": best_match[2],

            "normalized_incident": best_match[3],

            "root_cause": best_match[4],

            "resolution": best_match[5],

            "preventive_actions": best_match[6],

            "confluence_link": best_match[7],

            "responsible_team": best_match[8],

            "fix_date": best_match[9],

            "created_at": best_match[10],

           "occurrence_count": occurrence_count,

            "top_matches": top_matches

        }

    except Exception as e:

        conn.close()

        print(
            "Historical RCA search error:",
            str(e)
        )

        return None


# ==========================================================
# GET RCA BY JIRA TICKET
# ==========================================================

def get_historical_rca_by_ticket(ticket_id):

    if not ticket_id:
        return None

    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()

    try:

        cursor.execute(
            """
            SELECT

                jira_ticket_id,
                incident,
                normalized_incident,
                ai_root_cause,
                ai_resolution,
                preventive_actions,
                confluence_link,
                responsible_team,
                fix_date,
                created_at

            FROM RCA_Knowledge

            WHERE jira_ticket_id = ?

            ORDER BY rca_id DESC
            LIMIT 1
            """,
            (ticket_id,)
        )

        row = cursor.fetchone()

        conn.close()

        if not row:
            return None

        return {

            "found": True,

            "jira_ticket_id": row[0],

            "incident": row[1],

            "normalized_incident": row[2],

            "root_cause": row[3],

            "resolution": row[4],

            "preventive_actions": row[5],

            "confluence_link": row[6],

            "responsible_team": row[7],

            "fix_date": row[8],

            "created_at": row[9]

        }

    except Exception as e:

        conn.close()

        print(
            "Historical RCA ticket search error:",
            str(e)
        )

        return None


# ==========================================================
# CHECK IF RCA EXISTS
# ==========================================================

def historical_rca_exists(incident):

    result = search_historical_rca(
        incident
    )

    return result is not None