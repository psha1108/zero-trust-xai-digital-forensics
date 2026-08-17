"""
Constants for synthetic data generation.
"""

ROLES = ["admin", "employee", "finance_user", "hr_user", "guest"]

BROWSERS = [
    "Chrome", "Firefox", "Safari", "Edge", "Opera"
]

OPERATING_SYSTEMS = [
    "Windows", "MacOS", "Linux", "iOS", "Android"
]

RESOURCES = [
    "dashboard", "profile", "hr_records", "finance_reports",
    "admin_panel", "confidential_documents", "forensic_reports"
]

RESOURCE_SENSITIVITY = {
    "dashboard": "low",
    "profile": "low",
    "hr_records": "medium",
    "finance_reports": "high",
    "admin_panel": "critical",
    "confidential_documents": "critical",
    "forensic_reports": "critical"
}

RESOURCE_SENSITIVITY_SCORE = {
    "low": 1,
    "medium": 2,
    "high": 3,
    "critical": 4
}

RISK_LABELS = ["low", "medium", "high"]

SCENARIOS = {
    "low": [
        "normal_office_login",
        "normal_resource_access",
        "normal_short_session",
        "normal_admin_login"
    ],
    "medium": [
        "new_ip_login",
        "new_device_login",
        "unusual_time_login",
        "slightly_high_failed_attempts",
        "medium_sensitive_resource_access"
    ],
    "high": [
        "brute_force_then_success",
        "unauthorized_admin_access",
        "sensitive_resource_abuse",
        "session_hijack_simulation",
        "ip_change_during_session",
        "device_change_during_session",
        "rapid_access_attempts",
        "multiple_failed_logins"
    ]
}

WORKING_HOUR_START = 8
WORKING_HOUR_END = 18

IP_PREFIXES = {
    "internal": ["192.168.", "10.0.", "172.16."],
    "external": ["203.0.113.", "198.51.100.", "104.28.", "185.12.", "92.10."]
}

DEVICE_PREFIXES = ["DEV-", "WIN-", "MAC-", "MOB-"]
