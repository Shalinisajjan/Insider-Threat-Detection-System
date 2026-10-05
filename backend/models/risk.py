"""
models/risk.py — Pydantic schemas for Risk Scores.
"""
from pydantic import BaseModel
from typing import Optional, List, Dict
from datetime import datetime


class RiskScoreResponse(BaseModel):
    user_id: str
    username: Optional[str] = None
    full_name: Optional[str] = None
    department: Optional[str] = None
    risk_score: float
    risk_level: str  # LOW, MEDIUM, HIGH
    threat_probability: Optional[float] = 0.0
    anomaly_score: Optional[float] = 0.0
    score_breakdown: Optional[Dict[str, float]] = {}
    top_risk_factors: Optional[List[str]] = []
    calculated_at: datetime
    trend: Optional[str] = "stable"  # increasing, decreasing, stable


class RiskHistoryResponse(BaseModel):
    user_id: str
    history: List[Dict]
    average_score: float
    peak_score: float
    trend: str


class RiskLeaderboard(BaseModel):
    users: List[RiskScoreResponse]
    total: int


class BehavioralFeatures(BaseModel):
    user_id: str
    login_frequency: float = 0.0
    late_night_logins: int = 0
    failed_login_count: int = 0
    file_download_volume: float = 0.0
    usb_transfer_count: int = 0
    suspicious_url_count: int = 0
    bulk_file_copy_count: int = 0
    after_hours_events: int = 0
    sensitive_file_accesses: int = 0
    external_transfers: int = 0
    anomaly_ratio: float = 0.0
