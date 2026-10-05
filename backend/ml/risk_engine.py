"""
ml/risk_engine.py — Dynamic weighted risk scoring engine.

Risk Weights:
- External data sharing: +30
- USB transfer: +25
- Sensitive file access: +20
- Bulk file copy: +20
- Midnight/after-hours login: +15
- Failed login: +10 × count
- Suspicious URLs: +10

Risk Levels:
- LOW:    0–30
- MEDIUM: 31–70
- HIGH:   71–100
"""
from typing import Tuple, Dict, List
import math


# ─── Risk Weight Configuration ────────────────────────────────────────────────

RISK_WEIGHTS = {
    "external_data_sharing": 30,
    "usb_transfer": 25,
    "sensitive_file_access": 20,
    "bulk_file_copy": 20,
    "midnight_login": 15,
    "failed_login": 10,  # per occurrence
    "suspicious_urls": 10,
    "email_attachment": 15,
    "print_document": 5,
    "remote_access_after_hours": 20,
}

RISK_THRESHOLDS = {
    "LOW": (0, 30),
    "MEDIUM": (31, 70),
    "HIGH": (71, 100),
}


def get_risk_level(score: float) -> str:
    """Convert numeric risk score to risk level string."""
    if score <= 30:
        return "LOW"
    elif score <= 70:
        return "MEDIUM"
    else:
        return "HIGH"


def calculate_risk_score_from_event(event: dict) -> float:
    """
    Calculate risk contribution for a single activity event.
    Returns the point contribution of this specific event.
    """
    event_type = event.get("event_type", "")
    sensitivity = event.get("sensitivity_level", "low")
    is_after_hours = event.get("is_after_hours", False)
    login_status = event.get("login_status", "")
    transfer_size = event.get("transfer_size_mb", 0) or 0

    contribution = 0.0

    # USB transfer
    if event_type == "usb_transfer":
        contribution += RISK_WEIGHTS["usb_transfer"]
        if transfer_size > 500:
            contribution += 10  # Large transfer bonus

    # Email with attachment (potential exfiltration)
    elif event_type == "email_attachment":
        contribution += RISK_WEIGHTS["email_attachment"]
        if sensitivity in ["high", "critical"]:
            contribution += 15

    # File download — especially large or sensitive
    elif event_type == "file_download":
        if sensitivity in ["high", "critical"]:
            contribution += RISK_WEIGHTS["sensitive_file_access"]
        if transfer_size > 100:
            contribution += RISK_WEIGHTS["bulk_file_copy"]

    # File access to sensitive data
    elif event_type == "file_access":
        if sensitivity in ["high", "critical"]:
            contribution += RISK_WEIGHTS["sensitive_file_access"]

    # Login events
    elif event_type == "login":
        if login_status == "failed":
            contribution += RISK_WEIGHTS["failed_login"]
        if is_after_hours:
            contribution += RISK_WEIGHTS["midnight_login"]

    # Suspicious URL browsing
    elif event_type == "web_browse":
        if sensitivity in ["high", "critical"]:
            contribution += RISK_WEIGHTS["suspicious_urls"]

    # Remote access after hours
    elif event_type == "remote_access" and is_after_hours:
        contribution += RISK_WEIGHTS["remote_access_after_hours"]

    # Print — potential data leak
    elif event_type == "print_document":
        if sensitivity in ["high", "critical"]:
            contribution += RISK_WEIGHTS["print_document"] + 10

    return min(contribution, 50)  # Cap per-event contribution


def calculate_user_risk_score(
    activities: List[dict],
) -> Tuple[float, str, Dict[str, float]]:
    """
    Calculate overall risk score for a user based on their activity history.

    Returns:
        Tuple of (score: float, level: str, breakdown: dict)
    """
    if not activities:
        return 0.0, "LOW", {}

    breakdown = {
        "external_data_sharing": 0.0,
        "usb_transfer": 0.0,
        "sensitive_file_access": 0.0,
        "bulk_file_copy": 0.0,
        "midnight_login": 0.0,
        "failed_login": 0.0,
        "suspicious_urls": 0.0,
    }

    total_contribution = 0.0

    for act in activities:
        event_type = act.get("event_type", "")
        sensitivity = act.get("sensitivity_level", "low")
        is_after_hours = act.get("is_after_hours", False)
        login_status = act.get("login_status", "")
        transfer_size = act.get("transfer_size_mb", 0) or 0

        if event_type == "usb_transfer":
            pts = RISK_WEIGHTS["usb_transfer"]
            breakdown["usb_transfer"] += pts
            if transfer_size > 500:
                breakdown["external_data_sharing"] += 15

        elif event_type == "email_attachment" and sensitivity in ["high", "critical"]:
            pts = RISK_WEIGHTS["email_attachment"] + 15
            breakdown["external_data_sharing"] += pts

        elif event_type == "file_download":
            if sensitivity in ["high", "critical"]:
                breakdown["sensitive_file_access"] += RISK_WEIGHTS["sensitive_file_access"]
            if transfer_size > 100:
                breakdown["bulk_file_copy"] += RISK_WEIGHTS["bulk_file_copy"]

        elif event_type == "file_access" and sensitivity in ["high", "critical"]:
            breakdown["sensitive_file_access"] += RISK_WEIGHTS["sensitive_file_access"] * 0.5

        elif event_type == "login":
            if login_status == "failed":
                breakdown["failed_login"] += RISK_WEIGHTS["failed_login"]
            if is_after_hours:
                breakdown["midnight_login"] += RISK_WEIGHTS["midnight_login"]

        elif event_type == "web_browse" and sensitivity in ["high", "critical"]:
            breakdown["suspicious_urls"] += RISK_WEIGHTS["suspicious_urls"]

    # Apply logarithmic decay to prevent infinite accumulation
    final_breakdown = {}
    for key, raw_score in breakdown.items():
        if raw_score > 0:
            # Use log scaling: diminishing returns after first few events
            scaled = min(raw_score, 100) * 0.7 + math.log1p(raw_score) * 3
            final_breakdown[key] = round(min(scaled, 40), 2)
        else:
            final_breakdown[key] = 0.0

    total = sum(final_breakdown.values())
    # Normalize to 0-100 scale
    normalized_score = min(round(total, 1), 100.0)
    risk_level = get_risk_level(normalized_score)

    return normalized_score, risk_level, final_breakdown
