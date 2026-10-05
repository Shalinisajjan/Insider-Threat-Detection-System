"""
models/activity.py — Pydantic schemas for User Activity events.
"""
from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime
from enum import Enum


class EventType(str, Enum):
    login = "login"
    logout = "logout"
    file_access = "file_access"
    file_download = "file_download"
    file_upload = "file_upload"
    file_delete = "file_delete"
    usb_connect = "usb_connect"
    usb_transfer = "usb_transfer"
    web_browse = "web_browse"
    email_send = "email_send"
    email_attachment = "email_attachment"
    remote_access = "remote_access"
    print_document = "print_document"
    suspicious_process = "suspicious_process"


class SensitivityLevel(str, Enum):
    low = "low"
    medium = "medium"
    high = "high"
    critical = "critical"


class LoginStatus(str, Enum):
    success = "success"
    failed = "failed"
    locked = "locked"


# ─── Request Schemas ──────────────────────────────────────────────────────────

class ActivityLogRequest(BaseModel):
    user_id: str
    event_type: EventType
    ip_address: Optional[str] = None
    device_id: Optional[str] = None
    file_name: Optional[str] = None
    file_path: Optional[str] = None
    transfer_size_mb: Optional[float] = 0.0
    url: Optional[str] = None
    login_status: Optional[LoginStatus] = None
    sensitivity_level: Optional[SensitivityLevel] = SensitivityLevel.low
    is_after_hours: Optional[bool] = False
    location: Optional[str] = None
    details: Optional[dict] = {}


# ─── Response Schemas ─────────────────────────────────────────────────────────

class ActivityResponse(BaseModel):
    id: str
    user_id: str
    username: Optional[str] = None
    event_type: EventType
    timestamp: datetime
    ip_address: Optional[str] = None
    device_id: Optional[str] = None
    file_name: Optional[str] = None
    transfer_size_mb: Optional[float] = 0.0
    url: Optional[str] = None
    login_status: Optional[str] = None
    sensitivity_level: SensitivityLevel
    is_after_hours: bool
    location: Optional[str] = None
    risk_contribution: Optional[float] = 0.0


class ActivityListResponse(BaseModel):
    activities: List[ActivityResponse]
    total: int
    page: int
    per_page: int


class ActivitySummary(BaseModel):
    user_id: str
    total_events: int
    login_attempts: int
    failed_logins: int
    file_downloads: int
    usb_transfers: int
    after_hours_events: int
    suspicious_urls: int
    high_sensitivity_accesses: int
    period_days: int
