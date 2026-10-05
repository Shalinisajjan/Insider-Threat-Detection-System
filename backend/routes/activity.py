"""
routes/activity.py — Activity monitoring: log ingestion and retrieval endpoints.
"""
from fastapi import APIRouter, HTTPException, status, Depends, Query
from datetime import datetime, timezone, timedelta
from bson import ObjectId
from typing import Optional

from database import get_activities_collection, get_users_collection, get_alerts_collection
from models.activity import ActivityLogRequest, ActivityResponse, ActivityListResponse, ActivitySummary
from middleware.auth import get_current_user, require_analyst_or_admin
from ml.risk_engine import calculate_risk_score_from_event

router = APIRouter()


def _serialize_activity(act: dict, username: str = None) -> dict:
    return {
        "id": str(act["_id"]),
        "user_id": act["user_id"],
        "username": username or act.get("username"),
        "event_type": act["event_type"],
        "timestamp": act["timestamp"],
        "ip_address": act.get("ip_address"),
        "device_id": act.get("device_id"),
        "file_name": act.get("file_name"),
        "transfer_size_mb": act.get("transfer_size_mb", 0.0),
        "url": act.get("url"),
        "login_status": act.get("login_status"),
        "sensitivity_level": act.get("sensitivity_level", "low"),
        "is_after_hours": act.get("is_after_hours", False),
        "location": act.get("location"),
        "risk_contribution": act.get("risk_contribution", 0.0),
    }


@router.post("/log", response_model=ActivityResponse, status_code=status.HTTP_201_CREATED)
async def log_activity(
    payload: ActivityLogRequest,
    current_user: dict = Depends(get_current_user),
):
    """
    Log a user activity event.
    Automatically triggers risk score recalculation.
    """
    activities_col = get_activities_collection()
    users_col = get_users_collection()

    # Determine if after-hours (before 7 AM or after 9 PM)
    now = datetime.now(timezone.utc)
    is_after_hours = payload.is_after_hours or (now.hour < 7 or now.hour >= 21)

    # Calculate risk contribution for this event
    risk_contribution = calculate_risk_score_from_event(payload.model_dump())

    activity_doc = {
        **payload.model_dump(),
        "timestamp": now,
        "is_after_hours": is_after_hours,
        "risk_contribution": risk_contribution,
        "logged_by": str(current_user["_id"]),
    }

    result = await activities_col.insert_one(activity_doc)
    activity_doc["_id"] = result.inserted_id

    # Update user's risk score asynchronously-style (inline for simplicity)
    user = await users_col.find_one({"_id": ObjectId(payload.user_id)})
    if user:
        await _recalculate_user_risk(payload.user_id, users_col, activities_col)

    # Auto-create alert if risk contribution is high
    if risk_contribution >= 25:
        await _auto_create_alert(payload, risk_contribution, now)

    username = user["username"] if user else None
    return ActivityResponse(**_serialize_activity(activity_doc, username))


@router.get("/user/{user_id}", response_model=ActivityListResponse)
async def get_user_activities(
    user_id: str,
    page: int = Query(1, ge=1),
    per_page: int = Query(20, ge=1, le=100),
    event_type: Optional[str] = None,
    days: int = Query(30, ge=1, le=365),
    current_user: dict = Depends(require_analyst_or_admin),
):
    """Get activity history for a specific user."""
    activities_col = get_activities_collection()
    users_col = get_users_collection()

    query: dict = {
        "user_id": user_id,
        "timestamp": {"$gte": datetime.now(timezone.utc) - timedelta(days=days)},
    }
    if event_type:
        query["event_type"] = event_type

    total = await activities_col.count_documents(query)
    skip = (page - 1) * per_page
    cursor = activities_col.find(query).sort("timestamp", -1).skip(skip).limit(per_page)
    activities = await cursor.to_list(length=per_page)

    user = await users_col.find_one({"_id": ObjectId(user_id)})
    username = user["username"] if user else None

    return ActivityListResponse(
        activities=[ActivityResponse(**_serialize_activity(a, username)) for a in activities],
        total=total,
        page=page,
        per_page=per_page,
    )


@router.get("/all", response_model=ActivityListResponse)
async def get_all_activities(
    page: int = Query(1, ge=1),
    per_page: int = Query(50, ge=1, le=200),
    event_type: Optional[str] = None,
    days: int = Query(7, ge=1, le=90),
    current_user: dict = Depends(require_analyst_or_admin),
):
    """Get all platform activity events (Analyst/Admin only)."""
    activities_col = get_activities_collection()

    query: dict = {
        "timestamp": {"$gte": datetime.now(timezone.utc) - timedelta(days=days)},
    }
    if event_type:
        query["event_type"] = event_type

    total = await activities_col.count_documents(query)
    skip = (page - 1) * per_page
    cursor = activities_col.find(query).sort("timestamp", -1).skip(skip).limit(per_page)
    activities = await cursor.to_list(length=per_page)

    return ActivityListResponse(
        activities=[ActivityResponse(**_serialize_activity(a)) for a in activities],
        total=total,
        page=page,
        per_page=per_page,
    )


@router.get("/summary/{user_id}", response_model=ActivitySummary)
async def get_activity_summary(
    user_id: str,
    days: int = Query(30, ge=1, le=365),
    current_user: dict = Depends(require_analyst_or_admin),
):
    """Get a behavioral summary for a user over a given period."""
    activities_col = get_activities_collection()
    since = datetime.now(timezone.utc) - timedelta(days=days)

    pipeline = [
        {"$match": {"user_id": user_id, "timestamp": {"$gte": since}}},
        {
            "$group": {
                "_id": "$user_id",
                "total_events": {"$sum": 1},
                "login_attempts": {
                    "$sum": {"$cond": [{"$eq": ["$event_type", "login"]}, 1, 0]}
                },
                "failed_logins": {
                    "$sum": {
                        "$cond": [
                            {"$and": [
                                {"$eq": ["$event_type", "login"]},
                                {"$eq": ["$login_status", "failed"]},
                            ]},
                            1, 0,
                        ]
                    }
                },
                "file_downloads": {
                    "$sum": {"$cond": [{"$eq": ["$event_type", "file_download"]}, 1, 0]}
                },
                "usb_transfers": {
                    "$sum": {"$cond": [{"$eq": ["$event_type", "usb_transfer"]}, 1, 0]}
                },
                "after_hours_events": {
                    "$sum": {"$cond": ["$is_after_hours", 1, 0]}
                },
                "suspicious_urls": {
                    "$sum": {
                        "$cond": [
                            {"$and": [
                                {"$eq": ["$event_type", "web_browse"]},
                                {"$in": ["$sensitivity_level", ["high", "critical"]]},
                            ]},
                            1, 0,
                        ]
                    }
                },
                "high_sensitivity_accesses": {
                    "$sum": {
                        "$cond": [
                            {"$in": ["$sensitivity_level", ["high", "critical"]]},
                            1, 0,
                        ]
                    }
                },
            }
        },
    ]

    results = await activities_col.aggregate(pipeline).to_list(length=1)
    if not results:
        return ActivitySummary(user_id=user_id, period_days=days, total_events=0,
                               login_attempts=0, failed_login_count=0, file_downloads=0,
                               usb_transfer_count=0, after_hours_events=0,
                               suspicious_url_count=0, high_sensitivity_accesses=0)

    r = results[0]
    return ActivitySummary(
        user_id=user_id,
        total_events=r["total_events"],
        login_attempts=r["login_attempts"],
        failed_login_count=r["failed_logins"],
        file_downloads=r["file_downloads"],
        usb_transfer_count=r["usb_transfers"],
        after_hours_events=r["after_hours_events"],
        suspicious_url_count=r["suspicious_urls"],
        high_sensitivity_accesses=r["high_sensitivity_accesses"],
        period_days=days,
    )


@router.get("/timeline/{user_id}", response_model=dict)
async def get_threat_timeline(
    user_id: str,
    days: int = Query(7, ge=1, le=90),
    current_user: dict = Depends(require_analyst_or_admin),
):
    """Get daily activity counts for a threat timeline chart."""
    activities_col = get_activities_collection()
    since = datetime.now(timezone.utc) - timedelta(days=days)

    pipeline = [
        {"$match": {"user_id": user_id, "timestamp": {"$gte": since}}},
        {
            "$group": {
                "_id": {
                    "$dateToString": {"format": "%Y-%m-%d", "date": "$timestamp"}
                },
                "count": {"$sum": 1},
                "risk_sum": {"$sum": "$risk_contribution"},
            }
        },
        {"$sort": {"_id": 1}},
    ]

    results = await activities_col.aggregate(pipeline).to_list(length=days)
    return {
        "user_id": user_id,
        "timeline": [
            {"date": r["_id"], "count": r["count"], "risk_sum": round(r["risk_sum"], 2)}
            for r in results
        ],
    }


@router.get("/heatmap/{user_id}", response_model=dict)
async def get_activity_heatmap(
    user_id: str,
    days: int = Query(30, ge=1, le=90),
    current_user: dict = Depends(require_analyst_or_admin),
):
    """Get activity heatmap data — counts per hour-of-day and day-of-week."""
    activities_col = get_activities_collection()
    since = datetime.now(timezone.utc) - timedelta(days=days)

    pipeline = [
        {"$match": {"user_id": user_id, "timestamp": {"$gte": since}}},
        {
            "$group": {
                "_id": {
                    "hour": {"$hour": "$timestamp"},
                    "weekday": {"$dayOfWeek": "$timestamp"},
                },
                "count": {"$sum": 1},
                "risk_sum": {"$sum": "$risk_contribution"},
            }
        },
    ]

    results = await activities_col.aggregate(pipeline).to_list(length=200)

    matrix = {}
    for r in results:
        hour = r["_id"]["hour"]
        weekday = r["_id"]["weekday"] - 1  # 1-7 to 0-6
        key = f"{weekday}-{hour}"
        matrix[key] = {"count": r["count"], "risk_sum": round(r["risk_sum"], 2)}

    return {"user_id": user_id, "heatmap": matrix, "days": days}


# ─── Internal helpers ──────────────────────────────────────────────────────────

async def _recalculate_user_risk(user_id: str, users_col, activities_col):
    """Recalculate and store updated risk score for a user."""
    from ml.risk_engine import calculate_user_risk_score

    since = datetime.now(timezone.utc) - timedelta(days=30)
    activities = await activities_col.find(
        {"user_id": user_id, "timestamp": {"$gte": since}}
    ).to_list(length=1000)

    score, level, breakdown = calculate_user_risk_score(activities)

    await users_col.update_one(
        {"_id": ObjectId(user_id)},
        {"$set": {"risk_score": score, "risk_level": level}},
    )


async def _auto_create_alert(payload: ActivityLogRequest, risk_contribution: float, timestamp):
    """Create an automatic alert for high-risk events."""
    alerts_col = get_alerts_collection()

    # Map event type to alert type
    alert_type_map = {
        "usb_transfer": "usb_abuse",
        "file_download": "data_exfiltration",
        "web_browse": "abnormal_browsing",
        "login": "suspicious_login",
        "file_access": "data_exfiltration",
        "email_attachment": "data_exfiltration",
    }

    alert_type = alert_type_map.get(payload.event_type, "anomaly_detected")
    severity = "critical" if risk_contribution >= 40 else "high" if risk_contribution >= 25 else "medium"

    title_map = {
        "usb_abuse": "USB Device Abuse Detected",
        "data_exfiltration": "Potential Data Exfiltration",
        "abnormal_browsing": "Abnormal Web Browsing Activity",
        "suspicious_login": "Suspicious Login Attempt",
        "anomaly_detected": "Anomalous Behavior Detected",
    }

    alert_doc = {
        "user_id": payload.user_id,
        "alert_type": alert_type,
        "severity": severity,
        "title": title_map.get(alert_type, "Security Alert"),
        "description": f"High-risk event '{payload.event_type}' detected. Risk contribution: +{risk_contribution}",
        "risk_score": risk_contribution,
        "status": "open",
        "is_read": False,
        "timestamp": timestamp,
        "resolved_at": None,
        "resolved_by": None,
        "related_activity_ids": [],
    }

    await alerts_col.insert_one(alert_doc)
