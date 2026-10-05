"""
routes/explain.py — SHAP Explainability endpoints.
"""
from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel
from typing import List, Optional
from bson import ObjectId
from datetime import datetime, timezone, timedelta

from database import get_activities_collection, get_users_collection
from middleware.auth import require_analyst_or_admin
from ml.shap_explainer import explain_prediction

router = APIRouter()


class ExplanationResponse(BaseModel):
    user_id: str
    username: Optional[str] = None
    risk_score: float
    prediction: str
    explanation_text: str
    top_features: List[dict]
    shap_values: dict
    summary: str
    recommended_actions: List[str]
    generated_at: str


@router.get("/explain/{user_id}", response_model=ExplanationResponse)
async def get_explanation(
    user_id: str,
    days: int = Query(30, ge=1, le=365),
    current_user: dict = Depends(require_analyst_or_admin),
):
    """
    Generate a SHAP-based explainable AI explanation for a user's risk score.
    Returns feature importance, waterfall data, and analyst-readable summary.
    """
    users_col = get_users_collection()
    activities_col = get_activities_collection()

    # Fetch user
    try:
        user = await users_col.find_one({"_id": ObjectId(user_id)})
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid user ID")

    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    # Collect behavioral features from activity history
    since = datetime.now(timezone.utc) - timedelta(days=days)
    activities = await activities_col.find(
        {"user_id": user_id, "timestamp": {"$gte": since}}
    ).to_list(length=1000)

    # Build feature vector
    features = _compute_features(activities)

    # Generate SHAP explanation
    try:
        explanation = explain_prediction(user_id, features)
    except FileNotFoundError:
        raise HTTPException(
            status_code=503,
            detail="ML models not trained. Run training scripts first.",
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Explanation error: {str(e)}")

    risk_score = user.get("risk_score", 0.0)
    prediction = "THREAT" if risk_score >= 70 else "SUSPICIOUS" if risk_score >= 40 else "NORMAL"

    # Generate analyst-readable explanation
    explanation_text = _generate_explanation_text(explanation["top_features"], risk_score)
    recommended_actions = _get_recommended_actions(risk_score, explanation["top_features"])
    summary = _generate_summary(user.get("username", "Unknown"), risk_score, explanation["top_features"])

    return ExplanationResponse(
        user_id=user_id,
        username=user.get("username"),
        risk_score=risk_score,
        prediction=prediction,
        explanation_text=explanation_text,
        top_features=explanation["top_features"],
        shap_values=explanation.get("shap_values", {}),
        summary=summary,
        recommended_actions=recommended_actions,
        generated_at=datetime.now(timezone.utc).isoformat(),
    )


@router.get("/global-importance", response_model=dict)
async def get_global_feature_importance(
    current_user: dict = Depends(require_analyst_or_admin),
):
    """Get global SHAP feature importance across all predictions."""
    try:
        from ml.shap_explainer import get_global_importance
        importance = get_global_importance()
        return {"feature_importance": importance, "model": "Random Forest"}
    except Exception as e:
        raise HTTPException(status_code=503, detail=f"Model not ready: {str(e)}")


# ─── Helpers ──────────────────────────────────────────────────────────────────

def _compute_features(activities: list) -> dict:
    """Compute behavioral features from raw activity list."""
    from collections import defaultdict

    features = defaultdict(float)
    features["login_frequency"] = sum(1 for a in activities if a["event_type"] == "login")
    features["late_night_logins"] = sum(
        1 for a in activities
        if a["event_type"] == "login" and a.get("is_after_hours", False)
    )
    features["failed_login_count"] = sum(
        1 for a in activities
        if a["event_type"] == "login" and a.get("login_status") == "failed"
    )
    features["file_download_volume"] = sum(
        a.get("transfer_size_mb", 0) for a in activities if a["event_type"] == "file_download"
    )
    features["usb_transfer_count"] = sum(
        1 for a in activities if a["event_type"] == "usb_transfer"
    )
    features["suspicious_url_count"] = sum(
        1 for a in activities
        if a["event_type"] == "web_browse" and a.get("sensitivity_level") in ["high", "critical"]
    )
    features["bulk_file_copy_count"] = sum(
        1 for a in activities if a["event_type"] in ["file_download", "usb_transfer"]
        and a.get("transfer_size_mb", 0) > 100
    )
    features["after_hours_events"] = sum(1 for a in activities if a.get("is_after_hours", False))
    features["sensitive_file_accesses"] = sum(
        1 for a in activities if a.get("sensitivity_level") in ["high", "critical"]
    )
    features["external_transfers"] = sum(
        1 for a in activities if a["event_type"] in ["email_attachment", "usb_transfer"]
    )
    total = max(len(activities), 1)
    features["anomaly_ratio"] = (
        features["after_hours_events"] + features["failed_login_count"]
    ) / total

    return dict(features)


def _generate_explanation_text(top_features: list, risk_score: float) -> str:
    if not top_features:
        return "No significant risk factors identified in the analysis period."

    high_factors = [f for f in top_features if f.get("impact", 0) > 0]
    if not high_factors:
        return "User behavior appears within normal parameters."

    factor_names = [f["feature_name"] for f in high_factors[:3]]
    joined = ", ".join(factor_names)

    level = "critically high" if risk_score >= 70 else "elevated" if risk_score >= 40 else "slightly elevated"
    return (
        f"Risk score is {level} (score: {risk_score:.1f}/100) primarily due to: {joined}. "
        f"These behavioral indicators are consistent with insider threat patterns identified "
        f"in the CERT Insider Threat dataset."
    )


def _get_recommended_actions(risk_score: float, top_features: list) -> list:
    actions = []
    if risk_score >= 70:
        actions.extend([
            "🚨 Immediately escalate to Security Operations Center (SOC)",
            "🔒 Consider temporary account suspension pending investigation",
            "📋 Initiate formal incident response procedure",
        ])
    elif risk_score >= 40:
        actions.extend([
            "👁️ Increase monitoring frequency for this user",
            "📞 Schedule manager review meeting",
            "🔍 Request IT audit of recent file access",
        ])

    feature_actions = {
        "usb_transfer_count": "🖱️ Review and restrict USB device policy for this user",
        "suspicious_url_count": "🌐 Block access to flagged URLs and review browsing history",
        "failed_login_count": "🔑 Review authentication logs and enforce MFA",
        "file_download_volume": "📂 Audit downloaded files and check for data exfiltration",
        "late_night_logins": "🌙 Investigate after-hours system access justification",
    }

    for f in top_features[:3]:
        action = feature_actions.get(f.get("feature_key", ""))
        if action and action not in actions:
            actions.append(action)

    return actions


def _generate_summary(username: str, risk_score: float, top_features: list) -> str:
    level = "HIGH RISK" if risk_score >= 70 else "MEDIUM RISK" if risk_score >= 40 else "LOW RISK"
    top = top_features[0]["feature_name"] if top_features else "no specific factors"
    return (
        f"User '{username}' has been flagged as {level} with a score of {risk_score:.1f}/100. "
        f"Primary contributing factor: {top}."
    )
