# rules.py
import re
from datetime import timedelta

ISSUE_TYPE_PATTERNS = {
    "hardware": [r"laptop|desktop|keyboard|mouse|screen|monitor|hardware|printer|battery|fan|disk|ssd|hdd"],
    "software": [r"crash|bug|install|update|license|software|patch|error code|timeout"],
    "network":  [r"wifi|network|latency|vpn|dns|ip|router|switch|bandwidth|packet|disconnect"],
    "password/access": [r"password|login|signin|account locked|2fa|mfa|access denied|permission"],
    "security": [r"phish|malware|virus|ransom|unauthori[sz]ed|breach|security alert|siem|incident"],
}

TEAM_BY_TYPE = {
    "hardware": "End User Computing",
    "software": "Applications Support",
    "network": "Network Ops",
    "password/access": "Service Desk",
    "security": "Security Operations",
    "other": "Service Desk",
}

SEVERITY_TO_BASE_PRIORITY = {
    "Critical": "High",
    "High": "High",
    "Medium": "Medium",
    "Low": "Low",
}

# Example threshold to up-prioritize by users affected
USERS_AFFECTED_BOOST = {
    1: 0,      # 1–4 users -> no boost
    5: 1,      # 5–19 -> +1 level
    20: 2,     # 20–99 -> +2 levels
    100: 3,    # 100+ -> +3 levels
}

PRIORITY_ORDER = ["Low", "Medium", "High", "Urgent"]

# Escalation/resolution SLA suggestions (illustrative)
SLA_BY_TYPE = {
    "security": timedelta(hours=4),
    "network": timedelta(hours=8),
    "password/access": timedelta(hours=4),
    "hardware": timedelta(hours=16),
    "software": timedelta(hours=24),
    "other": timedelta(hours=24),
}

def match_issue_type(text: str) -> str:
    # Handle missing or non-string values safely
    if text is None:
        return "other"

    t = str(text).lower().strip()

    if not t:
        return "other"

    for issue_type, patterns in ISSUE_TYPE_PATTERNS.items():
        for pat in patterns:
            if re.search(pat, t):
                return issue_type

    return "other"

def boost_for_users_affected(n: int) -> int:
    # Map user counts to boost steps
    if n is None:
        return 0
    if n >= 100:
        return USERS_AFFECTED_BOOST[100]
    if n >= 20:
        return USERS_AFFECTED_BOOST[20]
    if n >= 5:
        return USERS_AFFECTED_BOOST[5]
    return USERS_AFFECTED_BOOST[1]

def clamp_priority(level_index: int) -> str:
    level_index = max(0, min(level_index, len(PRIORITY_ORDER) - 1))
    return PRIORITY_ORDER[level_index]
