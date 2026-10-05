"""
routes/risk.py — Risk scoring endpoints.
"""
from fastapi import APIRouter, Depends, Query
from datetime import datetime, timezone, timedelta
from bson import ObjectId
from typing import Optional

from database import get_risk_scores_collection, get_users_collection, get_activities_collection
from models.risk import RiskScoreResponse, RiskHistoryResponse, RiskLeaderboard
from middleware.auth import require_analyst_or_admin
from ml.risk_engine import calculate_user_risk_score

router = APIRouter()


@router.get("/score/{user_id}", response_model=RiskScoreResponse)
async def get_risk_score(
    user_id: str,
    current_user: dict = Depends(require_analyst_or_admin),
):
    """Get current risk score for a specific user."""
    users_col = get_users_collection()
    activities_col = get_activities_collection()
    risk_col = get_risk_scores_collection()

    try:
        user = await users_col.find_one({"_id": ObjectId(user_id)})
    except Exception:
        from fastapi import HTTPException
        raise HTTPException(status_code=400, detail="Invalid user ID")

    if not user:
        from fastapi import HTTPException
        raise HTTPException(status_code=404, detail="User not found")

    # Recalculate from last 30 days of activity
    since = datetime.now(timezone.utc) - timedelta(days=30)
    activities = await activities_col.find(
        {"user_id": user_id, "timestamp": {"$gte": since}}
    ).to_list(length=1000)

    score, level, breakdown = calculate_user_risk_score(activities)
    top_factors = _get_top_risk_factors(breakdown)

    now = datetime.now(timezone.utc)

    # Persist
    await risk_col.insert_one({
        "user_id": user_id,
        "risk_score": score,
        "risk_level": level,
        "breakdown": breakdown,
        "calculated_at": now,
    })

    # Update user document
    await users_col.update_one(
        {"_id": ObjectId(user_id)},
        {"$set": {"risk_score": score, "risk_level": level}},
    )

    return RiskScoreResponse(
        user_id=user_id,
        username=user.get("username"),
        full_name=user.get("full_name"),
        department=user.get("department"),
        risk_score=score,
        risk_level=level,
        score_breakdown=breakdown,
        top_risk_factors=top_factors,
        calculated_at=now,
    )


@router.get("/history/{user_id}", response_model=RiskHistoryResponse)
async def get_risk_history(
    user_id: str,
    days: int = Query(30, ge=1, le=365),
    current_user: dict = Depends(require_analyst_or_admin),
):
    """Get historical risk scores for trend analysis."""
    risk_col = get_risk_scores_collection()
    since = datetime.now(timezone.utc) - timedelta(days=days)

    cursor = risk_col.find(
        {"user_id": user_id, "calculated_at": {"$gte": since}}
    ).sort("calculated_at", 1)
    records = await cursor.to_list(length=1000)

    if not records:
        return RiskHistoryResponse(
            user_id=user_id, history=[], average_score=0.0, peak_score=0.0, trend="stable"
        )

    scores = [r["risk_score"] for r in records]
    history = [
        {
            "date": r["calculated_at"].strftime("%Y-%m-%d %H:%M"),
            "score": r["risk_score"],
            "level": r["risk_level"],
        }
        for r in records
    ]

    avg = sum(scores) / len(scores)
    peak = max(scores)

    # Trend calculation
    if len(scores) >= 2:
        recent_avg = sum(scores[-5:]) / len(scores[-5:])
        early_avg = sum(scores[:5]) / len(scores[:5])
        if recent_avg > early_avg + 5:
            trend = "increasing"
        elif recent_avg < early_avg - 5:
            trend = "decreasing"
        else:
            trend = "stable"
    else:
        trend = "stable"

    return RiskHistoryResponse(
        user_id=user_id,
        history=history,
        average_score=round(avg, 2),
        peak_score=round(peak, 2),
        trend=trend,
    )


@router.get("/leaderboard", response_model=RiskLeaderboard)
async def get_risk_leaderboard(
    limit: int = Query(10, ge=1, le=50),
    current_user: dict = Depends(require_analyst_or_admin),
):
    """Get top highest-risk users (leaderboard)."""
    users_col = get_users_collection()

    cursor = users_col.find({"risk_level": {"$in": ["HIGH", "MEDIUM"]}}).sort(
        "risk_score", -1
    ).limit(limit)
    users = await cursor.to_list(length=limit)

    result = []
    for user in users:
        result.append(
            RiskScoreResponse(
                user_id=str(user["_id"]),
                username=user.get("username"),
                full_name=user.get("full_name"),
                department=user.get("department"),
                risk_score=user.get("risk_score", 0.0),
                risk_level=user.get("risk_level", "LOW"),
                calculated_at=user.get("updated_at", datetime.now(timezone.utc)),
            )
        )

    return RiskLeaderboard(users=result, total=len(result))


@router.get("/analytics/overview", response_model=dict)
async def risk_overview(current_user: dict = Depends(require_analyst_or_admin)):
    """Get high-level risk analytics for the dashboard."""
    users_col = get_users_collection()

    total = await users_col.count_documents({})
    high_risk = await users_col.count_documents({"risk_level": "HIGH"})
    medium_risk = await users_col.count_documents({"risk_level": "MEDIUM"})
    low_risk = await users_col.count_documents({"risk_level": "LOW"})

    # Average risk score
    pipeline = [{"$group": {"_id": None, "avg_score": {"$avg": "$risk_score"}}}]
    avg_result = await users_col.aggregate(pipeline).to_list(length=1)
    avg_score = round(avg_result[0]["avg_score"], 2) if avg_result else 0.0

    return {
        "total_users": total,
        "high_risk_users": high_risk,
        "medium_risk_users": medium_risk,
        "low_risk_users": low_risk,
        "average_risk_score": avg_score,
        "risk_distribution": {
            "HIGH": round(high_risk / total * 100, 1) if total else 0,
            "MEDIUM": round(medium_risk / total * 100, 1) if total else 0,
            "LOW": round(low_risk / total * 100, 1) if total else 0,
        },
    }


def _get_top_risk_factors(breakdown: dict) -> list:
    """Return top contributing risk factors as human-readable strings."""
    factor_labels = {
        "external_data_sharing": "External data sharing detected",
        "usb_transfer": "Excessive USB device usage",
        "sensitive_file_access": "Access to sensitive files",
        "bulk_file_copy": "Bulk file copy operations",
        "midnight_login": "After-hours / midnight login activity",
        "failed_login": "Multiple failed login attempts",
        "suspicious_urls": "Visits to suspicious URLs",
    }

    sorted_factors = sorted(breakdown.items(), key=lambda x: x[1], reverse=True)
    return [
        factor_labels.get(k, k.replace("_", " ").title())
        for k, v in sorted_factors
        if v > 0
    ][:5]
