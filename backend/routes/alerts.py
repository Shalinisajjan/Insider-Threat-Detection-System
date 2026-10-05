"""
routes/alerts.py — Alert management endpoints.
"""
from fastapi import APIRouter, HTTPException, status, Depends, Query
from datetime import datetime, timezone, timedelta
from bson import ObjectId
from typing import Optional

from database import get_alerts_collection, get_users_collection
from models.alert import AlertResponse, AlertListResponse, AlertUpdateRequest, AlertStatsResponse
from middleware.auth import get_current_user, require_analyst_or_admin

router = APIRouter()


def _serialize_alert(alert: dict, username: str = None) -> dict:
    return {
        "id": str(alert["_id"]),
        "user_id": alert["user_id"],
        "username": username,
        "alert_type": alert["alert_type"],
        "severity": alert["severity"],
        "title": alert["title"],
        "description": alert["description"],
        "risk_score": alert.get("risk_score", 0.0),
        "status": alert.get("status", "open"),
        "is_read": alert.get("is_read", False),
        "timestamp": alert["timestamp"],
        "resolved_at": alert.get("resolved_at"),
        "resolved_by": alert.get("resolved_by"),
        "related_activity_ids": alert.get("related_activity_ids", []),
    }


@router.get("/", response_model=AlertListResponse)
async def get_alerts(
    page: int = Query(1, ge=1),
    per_page: int = Query(20, ge=1, le=100),
    severity: Optional[str] = None,
    status: Optional[str] = None,
    alert_type: Optional[str] = None,
    unread_only: bool = False,
    days: int = Query(30, ge=1, le=365),
    current_user: dict = Depends(require_analyst_or_admin),
):
    """Get all alerts with filtering and pagination."""
    alerts_col = get_alerts_collection()
    users_col = get_users_collection()

    query: dict = {
        "timestamp": {"$gte": datetime.now(timezone.utc) - timedelta(days=days)},
    }
    if severity:
        query["severity"] = severity
    if status:
        query["status"] = status
    if alert_type:
        query["alert_type"] = alert_type
    if unread_only:
        query["is_read"] = False

    total = await alerts_col.count_documents(query)
    unread_count = await alerts_col.count_documents({"is_read": False, "status": "open"})
    skip = (page - 1) * per_page

    cursor = alerts_col.find(query).sort("timestamp", -1).skip(skip).limit(per_page)
    alerts = await cursor.to_list(length=per_page)

    # Enrich with usernames
    result = []
    for alert in alerts:
        try:
            user = await users_col.find_one({"_id": ObjectId(alert["user_id"])})
            username = user["username"] if user else None
        except Exception:
            username = None
        result.append(AlertResponse(**_serialize_alert(alert, username)))

    return AlertListResponse(alerts=result, total=total, unread_count=unread_count)


@router.get("/stats", response_model=AlertStatsResponse)
async def get_alert_stats(current_user: dict = Depends(require_analyst_or_admin)):
    """Get alert statistics for the dashboard."""
    alerts_col = get_alerts_collection()
    today_start = datetime.now(timezone.utc).replace(hour=0, minute=0, second=0)

    total = await alerts_col.count_documents({})
    open_count = await alerts_col.count_documents({"status": "open"})
    investigating = await alerts_col.count_documents({"status": "investigating"})
    resolved = await alerts_col.count_documents({"status": "resolved"})
    critical = await alerts_col.count_documents({"severity": "critical"})
    high = await alerts_col.count_documents({"severity": "high"})
    medium = await alerts_col.count_documents({"severity": "medium"})
    low = await alerts_col.count_documents({"severity": "low"})
    today = await alerts_col.count_documents({"timestamp": {"$gte": today_start}})

    return AlertStatsResponse(
        total=total, open=open_count, investigating=investigating,
        resolved=resolved, critical=critical, high=high, medium=medium,
        low=low, today=today,
    )


@router.get("/threats", response_model=dict)
async def get_threats(
    days: int = Query(7, ge=1, le=90),
    current_user: dict = Depends(require_analyst_or_admin),
):
    """Get threat trends over time (for chart visualization)."""
    alerts_col = get_alerts_collection()
    since = datetime.now(timezone.utc) - timedelta(days=days)

    pipeline = [
        {"$match": {"timestamp": {"$gte": since}}},
        {
            "$group": {
                "_id": {
                    "date": {"$dateToString": {"format": "%Y-%m-%d", "date": "$timestamp"}},
                    "severity": "$severity",
                },
                "count": {"$sum": 1},
            }
        },
        {"$sort": {"_id.date": 1}},
    ]

    results = await alerts_col.aggregate(pipeline).to_list(length=1000)

    # Restructure for chart consumption
    trend_data: dict = {}
    for r in results:
        date = r["_id"]["date"]
        severity = r["_id"]["severity"]
        if date not in trend_data:
            trend_data[date] = {"date": date, "critical": 0, "high": 0, "medium": 0, "low": 0}
        trend_data[date][severity] = r["count"]

    return {"trends": list(trend_data.values()), "days": days}


@router.get("/{alert_id}", response_model=AlertResponse)
async def get_alert(
    alert_id: str,
    current_user: dict = Depends(require_analyst_or_admin),
):
    """Get a specific alert by ID."""
    alerts_col = get_alerts_collection()
    users_col = get_users_collection()

    try:
        alert = await alerts_col.find_one({"_id": ObjectId(alert_id)})
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid alert ID")

    if not alert:
        raise HTTPException(status_code=404, detail="Alert not found")

    try:
        user = await users_col.find_one({"_id": ObjectId(alert["user_id"])})
        username = user["username"] if user else None
    except Exception:
        username = None

    return AlertResponse(**_serialize_alert(alert, username))


@router.patch("/{alert_id}", response_model=AlertResponse)
async def update_alert(
    alert_id: str,
    payload: AlertUpdateRequest,
    current_user: dict = Depends(require_analyst_or_admin),
):
    """Update alert status or mark as read."""
    alerts_col = get_alerts_collection()
    users_col = get_users_collection()

    update_data: dict = {}
    if payload.status is not None:
        update_data["status"] = payload.status.value
        if payload.status.value == "resolved":
            update_data["resolved_at"] = datetime.now(timezone.utc)
            update_data["resolved_by"] = current_user["username"]
    if payload.is_read is not None:
        update_data["is_read"] = payload.is_read
    if payload.notes is not None:
        update_data["notes"] = payload.notes

    if not update_data:
        raise HTTPException(status_code=400, detail="No fields to update")

    try:
        result = await alerts_col.find_one_and_update(
            {"_id": ObjectId(alert_id)},
            {"$set": update_data},
            return_document=True,
        )
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid alert ID")

    if not result:
        raise HTTPException(status_code=404, detail="Alert not found")

    try:
        user = await users_col.find_one({"_id": ObjectId(result["user_id"])})
        username = user["username"] if user else None
    except Exception:
        username = None

    return AlertResponse(**_serialize_alert(result, username))


@router.post("/mark-all-read", status_code=status.HTTP_200_OK)
async def mark_all_read(current_user: dict = Depends(require_analyst_or_admin)):
    """Mark all alerts as read."""
    alerts_col = get_alerts_collection()
    result = await alerts_col.update_many({"is_read": False}, {"$set": {"is_read": True}})
    return {"marked_read": result.modified_count}
