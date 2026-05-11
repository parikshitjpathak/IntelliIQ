from datetime import datetime


# ============================================================
# ================= RISK CLASSIFICATION =======================
# ============================================================

def classify_ticket_risk(tickets):

    results = []
    now = datetime.now()

    for t in tickets:

        status = (t.get("status") or "").lower()
        due_date_str = t.get("due_date")
        date_str = t.get("date")
        time_str = t.get("time")

        risk = "Safe"
        #===== handling completed tickets separately (3rd May fix)=====
        # If ticket is Done → use SLA Met instead of time logic
        if status == "done":

            if t.get("sla_met") == "NO":
                risk = "Closed Breached"
            else:
                risk = "Safe"

            t["risk_level"] = risk
            results.append(t)
            continue
#==== completed ticket logic ends========


        # ================= PARSE DATES =================
        try:
            due_dt = datetime.fromisoformat(due_date_str)
        except:
            due_dt = None

        try:
            created_dt = datetime.strptime(f"{date_str} {time_str}", "%Y-%m-%d %H:%M:%S")
        except:
            created_dt = None

        # ================= RISK LOGIC =================
        if due_dt and created_dt:

            total_sla = (due_dt - created_dt).total_seconds()
            remaining = (due_dt - now).total_seconds()

            # ❌ Avoid divide issues
            if total_sla <= 0:
                risk = "Safe"
            else:

                remaining_percent = (remaining / total_sla) * 100

                # ================= CRITICAL / HIGH =================
                # Already breached → ALWAYS HIGH
                #if remaining <= 0:
                 #   risk = "High"

                #===== fixing logic for completed tickets (Option B)=====
                if remaining <= 0:

                    if status == "done":
                        risk = "Closed Breached"   # NEW CATEGORY
                    else:
                        risk = "High"
                #==== fix ends======== 

                else:

                    # To Do nearing breach → HIGH
                    if status == "to do":
                        if remaining_percent <= 25:
                            risk = "High"

                    # In Progress nearing → MEDIUM
                    elif status == "in progress":
                        if remaining_percent <= 25:
                            risk = "Medium"

        # ================= FINAL =================
        t["risk_level"] = risk
        results.append(t)

    return results