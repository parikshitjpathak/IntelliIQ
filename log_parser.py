# ==========================================================
# LOG PARSER
# ==========================================================

import os
import re
import sqlite3


# ==========================================================
# ERROR PATTERNS
# ==========================================================

ERROR_PATTERNS = {

    "NullPointerException":
        r"NullPointerException",

    "OutOfMemoryError":
        r"OutOfMemoryError",

    "Connection Timeout":
        r"timeout|connection timeout|read timeout|socket timeout",

    "HTTP 500":
        r"HTTP\s*500|500 Internal Server Error|Response Code:\s*500|Internal Server Error",

    "HTTP 503":
        r"HTTP\s*503|503 Service Unavailable|Response Code:\s*503",

    "ORA Error":
        r"ORA-\d+",

    "GC Pause":
        r"GC pause|garbage collection pause",

    "Mount Missing":
        r"mount point unavailable|mount missing|No such file or directory",

    "Authentication Failure":
        r"authentication failed|invalid token|invalid token signature",

    "SOAP Fault":
        r"SOAP Fault|soap fault"
}


# ==========================================================
# PARSE SINGLE FILE
# ==========================================================

def parse_log_file(file_path):

    results = {}

    for error_type in ERROR_PATTERNS:

        results[error_type] = 0

    try:

        with open(
            file_path,
            "r",
            encoding="utf-8",
            errors="ignore"
        ) as f:

            content = f.read()

        for error_type, pattern in ERROR_PATTERNS.items():

            matches = re.findall(
                pattern,
                content,
                flags=re.IGNORECASE
            )

            results[error_type] = len(matches)

        return {

            "file_name":
                os.path.basename(file_path),

            "errors":
                results
        }

    except Exception as e:

        print(
            f"Failed to parse {file_path}"
        )

        print(e)

        return {

            "file_name":
                os.path.basename(file_path),

            "errors":
                {}
        }


# ==========================================================
# ANALYZE INCIDENT LOGS
# ==========================================================

def analyze_incident_logs(
    kb_id,
    db_name
):

    conn = sqlite3.connect(
        db_name
    )

    cursor = conn.cursor()

    cursor.execute(
        """
        SELECT file_path
        FROM incident_evidence
        WHERE incident_id = ?
        """,
        (kb_id,)
    )

    rows = cursor.fetchall()

    conn.close()

    aggregated_results = {}

    for error_type in ERROR_PATTERNS:

        aggregated_results[
            error_type
        ] = 0

    for row in rows:

        file_path = row[0]

        parsed = parse_log_file(
            file_path
        )

        for error_type, count in parsed[
            "errors"
        ].items():

            aggregated_results[
                error_type
            ] += count

    aggregated_results = {

        k: v

        for k, v in aggregated_results.items()

        if v > 0
    }

    return aggregated_results