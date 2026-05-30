# ==========================================================
# NORMALIZATION ENGINE V2
# ==========================================================

import re


# ==========================================================
# CLEAN TEXT
# ==========================================================

def clean_text(text):

    if not text:
        return ""

    text = str(text).lower().strip()

    text = re.sub(
        r"[^a-z0-9\s]",
        " ",
        text
    )

    text = re.sub(
        r"\s+",
        " ",
        text
    )

    return text


# ==========================================================
# INCIDENT CATEGORY RULES
# ==========================================================

CATEGORY_RULES = [

    # ------------------------------------------------------
    # PRODUCT / PLATFORM
    # ------------------------------------------------------

    (
        "guidewire issue",
        [
            "guidewire",
            "policycenter",
            "billingcenter",
            "claimcenter"
        ]
    ),

    (
        "oneshield issue",
        [
            "oneshield",
            "oneshield market",
            "oneshield policy"
        ]
    ),

    # ------------------------------------------------------
    # INSURANCE / BUSINESS
    # ------------------------------------------------------

    (
        "policy issue",
        [
            "policy",
            "policy creation",
            "policy issuance",
            "policy update",
            "policy endorsement",
            "policy renewal"
        ]
    ),

    (
        "quote issue",
        [
            "quote",
            "quotation",
            "rating",
            "premium calculation",
            "pricing"
        ]
    ),

    (
        "claim issue",
        [
            "claim",
            "claims",
            "fnol",
            "first notice of loss",
            "settlement"
        ]
    ),

    (
        "billing issue",
        [
            "billing",
            "invoice",
            "premium payment",
            "premium due",
            "payment posting"
        ]
    ),

    (
        "payment issue",
        [
            "payment",
            "payment gateway",
            "transaction",
            "checkout",
            "authorization",
            "refund"
        ]
    ),

    (
        "document generation issue",
        [
            "document",
            "pdf",
            "letter",
            "certificate",
            "statement",
            "document generation"
        ]
    ),

    (
        "underwriting issue",
        [
            "underwriting",
            "uw",
            "risk assessment",
            "risk review"
        ]
    ),

    (
        "customer issue",
        [
            "customer",
            "client",
            "insured",
            "policyholder"
        ]
    ),

    # ------------------------------------------------------
    # FUNCTIONAL
    # ------------------------------------------------------

    (
        "login issue",
        [
            "login",
            "log in",
            "signin",
            "sign in",
            "unable to login",
            "login failed"
        ]
    ),

    (
        "authentication issue",
        [
            "authentication",
            "authorization",
            "access denied",
            "credential",
            "sso",
            "token"
        ]
    ),

    (
        "ui issue",
        [
            "page",
            "screen",
            "button",
            "form",
            "frontend",
            "ajax",
            "ui",
            "display issue"
        ]
    ),

    (
        "report issue",
        [
            "report",
            "reporting",
            "dashboard report",
            "export report"
        ]
    ),

    (
        "batch job issue",
        [
            "batch",
            "scheduler",
            "scheduled job",
            "cron",
            "job failure",
            "dap jobs",
            "dap"

        ]
    ),

    (
        "email issue",
        [
            "email",
            "mail",
            "smtp",
            "notification email"
        ]
    ),

    # ------------------------------------------------------
    # TECHNICAL
    # ------------------------------------------------------

    (
        "database issue",
        [
            "database",
            "db",
            "oracle",
            "ora-600",
            "ora 600",
            "sql",
            "query",
            "jdbc",
            "odbc",
            "connection pool",
            "deadlock"
        ]
    ),

    (
        "api issue",
        [
            "api",
            "rest api",
            "soap",
            "endpoint",
            "web service"
        ]
    ),

    (
        "integration issue",
        [
            "integration",
            "third party",
            "external system",
            "vendor interface",
            "interface failure"
        ]
    ),

    (
        "garbage collection issue",
        [
            "garbage collection",
            "long gc",
            "gc pause",
            "jvm",
            "heap"
        ]
    ),

    (
        "memory issue",
        [
            "memory leak",
            "memory usage",
            "out of memory",
            "outofmemory"
        ]
    ),

    (
        "performance issue",
        [
            "slow",
            "latency",
            "performance",
            "response time",
            "high cpu"
        ]
    ),

    (
        "network issue",
        [
            "network",
            "dns",
            "firewall",
            "packet loss",
            "timeout"
        ]
    ),

    (
        "middleware issue",
        [
            "middleware",
            "websphere",
            "tomcat",
            "jboss",
            "weblogic"
        ]
    ),

    (
        "cloud issue",
        [
            "aws",
            "azure",
            "gcp",
            "cloud"
        ]
    ),

    (
        "security issue",
        [
            "security",
            "vulnerability",
            "cyber",
            "attack",
            "malware"
        ]
    ),

    (
        "infrastructure issue",
        [
            "server",
            "disk",
            "storage",
            "hardware",
            "infrastructure"
        ]
    ),

    # ------------------------------------------------------
    # GENERIC FALLBACK
    # ------------------------------------------------------

    (
        "application issue",
        [
            "application",
            "system",
            "service"
        ]
    )
]


# ==========================================================
# NORMALIZE INCIDENT
# ==========================================================

def normalize_incident(text):

    text = clean_text(text)

    if not text:
        return "other issue"

    for category, keywords in CATEGORY_RULES:

        for keyword in keywords:

            if keyword in text:
                return category

    return "other issue"