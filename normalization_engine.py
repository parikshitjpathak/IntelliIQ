import re

def clean_text(text: str) -> str:
    if not text:
        return ""

    text = text.lower()

    # Normalize common variations / typos
    text = text.replace("erros", "errors")
    text = text.replace("signin", "sign in")
    text = text.replace("log-in", "login")
    text = text.replace("db", "database")

    # Remove special characters
    text = re.sub(r'[^a-z0-9\s]', ' ', text)

    # Normalize spaces
    text = re.sub(r'\s+', ' ', text).strip()

    return text


CATEGORY_RULES = [

    # ================= DATABASE =================
    ("database issue", [
        "ora", "oracle", "mysql", "postgres", "sql server", "mongodb",
        "database", "rdbms", "query", "table", "index", "schema",
        "insert", "update", "delete", "select",
        "deadlock", "lock", "blocking", "table locked",
        "connection pool", "database connection", "db connection failed",
        "query timeout", "long running query",
        "constraint", "cursor", "transaction failure",
        "replication lag", "data inconsistency",
        "backup failure", "restore issue", "tablespace full"
    ]),

    # ================= INFRASTRUCTURE =================
    ("infrastructure issue", [
        "server down", "host down", "instance down", "node down",
        "cpu high", "memory high", "disk full", "disk latency",
        "vm", "virtual machine", "hardware failure",
        "os issue", "linux issue", "windows server", "mount missing",
        "process down", "thread exhaustion", "mount" ,"heap memory",
        "filesystem full", "i o wait", "swap usage high",
        "autoscaling issue"
    ]),

    # ================= NETWORK =================
    ("network issue", [
        "network", "latency", "packet loss", "dns issue",
        "ip not reachable", "vpn issue",
        "firewall blocked", "port blocked",
        "load balancer issue", "cdn issue",
        "network congestion", "routing issue"
    ]),

    # ================= INTEGRATION =================
    ("integration issue", [
        "api failure", "api error", "rest", "soap",
        "endpoint not reachable", "third party", "vendor issue",
        "http 500", "http 502", "http 503", "gateway error",
        "webhook failure", "message not received",
        "payload error", "schema mismatch",
        "etl failure", "data sync issue",
        "batch interface failure", "queue not processed"
    ]),

    # ================= MIDDLEWARE =================
    ("middleware issue", [
        "weblogic", "websphere", "tomcat", "jboss",
        "kafka", "mq", "rabbitmq", "webmethods",
        "queue stuck", "consumer not processing",
        "thread pool exhausted", "connection pool exhausted",
        "app server down"
    ]),

    # ================= SECURITY =================
    ("security issue", [
        "unauthorized access", "authorization failure",
        "access denied", "ssl certificate expired",
        "token invalid", "cyber attack", "ddos",
        "firewall alert"
    ]),

    # ================= DATA / BATCH =================
    ("data issue", [
        "batch job failed", "scheduler failure", "cron job failed",
        "etl failed", "data mismatch", "report mismatch",
        "file not processed", "duplicate records",
        "missing records"
    ]),

    # ================= CLOUD / DEVOPS =================
    ("cloud issue", [
        "aws", "azure", "gcp",
        "pod crash", "container restart",
        "kubernetes issue",
        "deployment failed", "pipeline failed",
        "ci cd failure", "scaling issue"
    ]),

    # ================= APPLICATION ================= (KEEP LAST)
    ("application issue", [
        "app", "application", "portal", "system", "platform",
        "ui", "ux", "screen", "page", "dashboard",
        "login", "logout", "session expired",
        "button not working", "click not working",
        "form error", "validation error",
        "crash", "freeze", "hang", "payment" ,"payment failure",
        "payment gateway","gateway",
        "slow response", "latency", "timeout",
        "feature not working",
        "null pointer", "exception", "bug", "defect",
        "deployment issue", "release issue", "version issue",
        "code issue", "frontend", "backend", "microservice"
    ])
]


def normalize_incident(text: str) -> str:
    text = clean_text(text)

    for category, keywords in CATEGORY_RULES:
        if any(k in text for k in keywords):
            return category

    return "other issue"