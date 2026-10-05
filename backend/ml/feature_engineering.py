"""
ml/feature_engineering.py — Behavioral feature extraction from raw activity data.
Converts raw MongoDB activity documents to ML-ready feature vectors.
"""
import numpy as np
from typing import List, Dict, Any
from datetime import datetime, timezone, timedelta
from collections import defaultdict


# Feature definition with descriptions
FEATURE_DEFINITIONS = {
    "login_frequency": "Number of login events in the analysis period",
    "late_night_logins": "Logins occurring between 10 PM and 6 AM",
    "failed_login_count": "Number of failed authentication attempts",
    "file_download_volume": "Total MB of files downloaded",
    "usb_transfer_count": "Number of USB device transfer events",
    "suspicious_url_count": "Visits to high/critical sensitivity URLs",
    "bulk_file_copy_count": "Large file copy operations (>100MB)",
    "after_hours_events": "Total events occurring outside 7AM–9PM",
    "sensitive_file_accesses": "Accesses to high/critical sensitivity files",
    "external_transfers": "USB + email attachment events",
    "anomaly_ratio": "Ratio of anomalous to total events",
}


def extract_features_from_activities(
    activities: List[Dict[str, Any]],
    days: int = 30,
) -> Dict[str, float]:
    """
    Extract behavioral feature vector from a list of raw activity events.

    Args:
        activities: List of activity documents from MongoDB
        days: Period length for normalization

    Returns:
        Dict mapping feature names to float values
    """
    features = defaultdict(float)

    if not activities:
        return {k: 0.0 for k in FEATURE_DEFINITIONS}

    total_events = len(activities)
    period_days = max(days, 1)

    for act in activities:
        event_type = act.get("event_type", "")
        sensitivity = act.get("sensitivity_level", "low")
        is_after_hours = act.get("is_after_hours", False)
        login_status = act.get("login_status", "")
        transfer_size = float(act.get("transfer_size_mb", 0) or 0)

        # ── Login features ───────────────────────────────
        if event_type == "login":
            features["login_frequency"] += 1
            if login_status == "failed":
                features["failed_login_count"] += 1
            if is_after_hours:
                features["late_night_logins"] += 1

        # ── File features ────────────────────────────────
        elif event_type in ("file_download", "file_upload"):
            features["file_download_volume"] += transfer_size
            if sensitivity in ("high", "critical"):
                features["sensitive_file_accesses"] += 1
            if transfer_size > 100:
                features["bulk_file_copy_count"] += 1

        elif event_type == "file_access":
            if sensitivity in ("high", "critical"):
                features["sensitive_file_accesses"] += 1

        # ── USB features ─────────────────────────────────
        elif event_type in ("usb_connect", "usb_transfer"):
            features["usb_transfer_count"] += 1
            features["external_transfers"] += 1

        # ── Email / exfiltration ─────────────────────────
        elif event_type == "email_attachment":
            features["external_transfers"] += 1
            if sensitivity in ("high", "critical"):
                features["sensitive_file_accesses"] += 1

        # ── Web browsing ─────────────────────────────────
        elif event_type == "web_browse":
            if sensitivity in ("high", "critical"):
                features["suspicious_url_count"] += 1

        # ── After hours ──────────────────────────────────
        if is_after_hours:
            features["after_hours_events"] += 1

    # Compute anomaly ratio
    anomalous_events = (
        features["failed_login_count"] +
        features["late_night_logins"] +
        features["usb_transfer_count"] +
        features["suspicious_url_count"]
    )
    features["anomaly_ratio"] = anomalous_events / max(total_events, 1)

    # Normalize time-based features per day
    features["login_frequency"] = features["login_frequency"] / period_days
    features["after_hours_events"] = features["after_hours_events"] / period_days

    return {k: round(float(features.get(k, 0.0)), 4) for k in FEATURE_DEFINITIONS}


def features_to_array(features: Dict[str, float]) -> np.ndarray:
    """Convert feature dict to ordered numpy array for ML inference."""
    feature_order = list(FEATURE_DEFINITIONS.keys())
    return np.array([features.get(f, 0.0) for f in feature_order], dtype=np.float32)


def normalize_features(features: Dict[str, float], scaler=None) -> Dict[str, float]:
    """
    Optionally apply a pre-fitted scaler to normalize features.
    If no scaler provided, returns features as-is.
    """
    if scaler is None:
        return features

    arr = features_to_array(features).reshape(1, -1)
    scaled = scaler.transform(arr).flatten()
    return dict(zip(FEATURE_DEFINITIONS.keys(), scaled.tolist()))


def get_feature_summary(features: Dict[str, float]) -> str:
    """Generate human-readable feature summary for analysts."""
    lines = ["📊 Behavioral Feature Summary:"]
    lines.append("─" * 40)
    for key, value in features.items():
        description = FEATURE_DEFINITIONS.get(key, key)
        flag = ""
        # Highlight concerning values
        if key == "failed_login_count" and value > 3:
            flag = " ⚠️"
        elif key == "usb_transfer_count" and value > 2:
            flag = " 🚨"
        elif key == "late_night_logins" and value > 2:
            flag = " ⚠️"
        elif key == "suspicious_url_count" and value > 3:
            flag = " ⚠️"
        elif key == "anomaly_ratio" and value > 0.3:
            flag = " 🚨"
        lines.append(f"  {key:<30} = {value:.4f}{flag}")
    return "\n".join(lines)


if __name__ == "__main__":
    # Demo with sample activities
    sample_activities = [
        {"event_type": "login", "login_status": "failed", "is_after_hours": False, "sensitivity_level": "low"},
        {"event_type": "login", "login_status": "failed", "is_after_hours": False, "sensitivity_level": "low"},
        {"event_type": "usb_transfer", "is_after_hours": True, "transfer_size_mb": 450, "sensitivity_level": "high"},
        {"event_type": "file_download", "is_after_hours": True, "transfer_size_mb": 250, "sensitivity_level": "critical"},
        {"event_type": "web_browse", "is_after_hours": False, "sensitivity_level": "high"},
        {"event_type": "login", "login_status": "success", "is_after_hours": True, "sensitivity_level": "low"},
    ]

    features = extract_features_from_activities(sample_activities, days=7)
    print(get_feature_summary(features))
    print(f"\n🔢 Array shape: {features_to_array(features).shape}")
