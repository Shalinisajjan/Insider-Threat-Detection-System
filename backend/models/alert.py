"""
models/alert.py — Pydantic schemas for Alerts and Notifications.
"""
from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime
from enum import Enum


class AlertSeverity(str, Enum):
    low = "low"
    medium = "medium"
    high = "high"
    critical = "critical"


class AlertType(str, Enum):
    suspicious_login = "suspicious_login"
    data_exfiltration = "data_exfiltration"
    usb_abuse = "usb_abuse"
    bulk_file_copy = "bulk_file_copy"
    abnormal_browsing = "abnormal_browsing"
    after_hours_access = "after_hours_access"
    privilege_escalation = "privilege_escalation"
    anomaly_detected = "anomaly_detected"


class AlertStatus(str, Enum):
    open = "open"
    investigating = "investigating"
    resolved = "resolved"
    false_positive = "false_positive"


# ─── Schemas ──────────────────────────────────────────────────────────────────

class AlertResponse(BaseModel):
    id: str
    user_id: str
    username: Optional[str] = None
    alert_type: AlertType
    severity: AlertSeverity
    title: str
    description: str
    risk_score: float
    status: AlertStatus
    is_read: bool
    timestamp: datetime
    resolved_at: Optional[datetime] = None
    resolved_by: Optional[str] = None
    related_activity_ids: List[str] = []


class AlertListResponse(BaseModel):
    alerts: List[AlertResponse]
    total: int
    unread_count: int


class AlertUpdateRequest(BaseModel):
    status: Optional[AlertStatus] = None
    is_read: Optional[bool] = None
    notes: Optional[str] = None


class AlertStatsResponse(BaseModel):
    total: int
    open: int
    investigating: int
    resolved: int
    critical: int
    high: int
    medium: int
    low: int
    today: int
