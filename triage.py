# triage.py
# This module contains the core triage logic for analyzing IT support tickets.
from typing import Dict, Any
from rules import (
    match_issue_type, TEAM_BY_TYPE, SEVERITY_TO_BASE_PRIORITY,
    PRIORITY_ORDER, boost_for_users_affected, clamp_priority
)

def base_priority_from_severity(severity: str) -> str:
    if not severity:
        return "Medium"
    return SEVERITY_TO_BASE_PRIORITY.get(severity.title(), "Medium")

def priority_to_index(p: str) -> int:
    try:
        return PRIORITY_ORDER.index(p)
    except ValueError:
        return PRIORITY_ORDER.index("Medium")

def suggest_priority(issue_desc: str, severity: str, users_affected: Any, escalated: Any) -> str:
    base = base_priority_from_severity(severity)
    idx = priority_to_index(base)

    # User impact boost
    try:
        ua = int(users_affected) if users_affected is not None and users_affected != "" else 1
    except ValueError:
        ua = 1
    idx += boost_for_users_affected(ua)

    # Escalation boost
    if str(escalated).strip().lower() in {"true", "yes", "y", "1"}:
        idx += 1

    # Keyword-driven boosts (e.g., outage)
    text = (issue_desc or "").lower()
    if any(w in text for w in ["outage", "down", "cannot connect", "production"]):
        idx += 1

    return clamp_priority(idx)

def suggest_team(issue_type: str, department: str = "") -> str:
    # Basic mapping first
    team = TEAM_BY_TYPE.get(issue_type, "Service Desk")
    # Example override for specialized departments
    if issue_type == "software" and department and department.lower() in {"finance", "hr"}:
        return f"{department.title()} Apps Support"
    return team

def triage_ticket(ticket: Dict[str, Any]) -> Dict[str, Any]:
    issue_desc = ticket.get("Issue description", "")
    severity = ticket.get("Severity", "")
    dept = ticket.get("Department", "")
    users = ticket.get("Number of users affected", "")
    escalated = ticket.get("Escalated or not", "")

    issue_type = match_issue_type(issue_desc)
    priority = suggest_priority(issue_desc, severity, users, escalated)
    team = suggest_team(issue_type, dept)

    return {
        **ticket,
        "Issue type": issue_type,
        "Suggested priority": priority,
        "Suggested team": team,
    }
