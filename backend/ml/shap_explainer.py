"""
ml/shap_explainer.py — SHAP-based Explainable AI for insider threat predictions.
Uses TreeExplainer for Random Forest and XGBoost models.
"""
import numpy as np
import joblib
import os
import json
from typing import Optional

try:
    import shap
    SHAP_AVAILABLE = True
except ImportError:
    SHAP_AVAILABLE = False
    print("⚠️  SHAP not installed. Run: pip install shap")

MODELS_PATH = os.path.join(os.path.dirname(__file__), "saved_models")

FEATURE_ORDER = [
    "login_frequency",
    "late_night_logins",
    "failed_login_count",
    "file_download_volume",
    "usb_transfer_count",
    "suspicious_url_count",
    "bulk_file_copy_count",
    "after_hours_events",
    "sensitive_file_accesses",
    "external_transfers",
    "anomaly_ratio",
]

FEATURE_DISPLAY_NAMES = {
    "login_frequency": "Login Frequency",
    "late_night_logins": "Late Night Logins",
    "failed_login_count": "Failed Login Count",
    "file_download_volume": "File Download Volume (MB)",
    "usb_transfer_count": "USB Transfer Count",
    "suspicious_url_count": "Suspicious URL Visits",
    "bulk_file_copy_count": "Bulk File Copy Operations",
    "after_hours_events": "After-Hours Events",
    "sensitive_file_accesses": "Sensitive File Accesses",
    "external_transfers": "External Data Transfers",
    "anomaly_ratio": "Behavioral Anomaly Ratio",
}


def _load_rf_model():
    path = os.path.join(MODELS_PATH, "rf_model.joblib")
    if not os.path.exists(path):
        raise FileNotFoundError("RF model not found. Train it first.")
    return joblib.load(path)


def _load_scaler():
    path = os.path.join(MODELS_PATH, "scaler.joblib")
    if os.path.exists(path):
        return joblib.load(path)
    return None


def _features_to_array(features: dict) -> np.ndarray:
    return np.array([[features.get(f, 0.0) for f in FEATURE_ORDER]], dtype=np.float32)


def explain_prediction(user_id: str, features: dict) -> dict:
    """
    Generate SHAP explanations for a single user prediction.

    Args:
        user_id: User identifier
        features: Behavioral feature dictionary

    Returns:
        Dict with top_features (name, shap_value, direction) and raw shap_values
    """
    if not SHAP_AVAILABLE:
        return _fallback_explanation(features)

    model = _load_rf_model()
    scaler = _load_scaler()

    X = _features_to_array(features)
    if scaler is not None:
        X = scaler.transform(X)

    # Create SHAP TreeExplainer
    explainer = shap.TreeExplainer(model)
    shap_values = explainer.shap_values(X)

    # For binary classification, use class 1 (threat) SHAP values
    if isinstance(shap_values, list):
        sv = shap_values[1][0]  # Class 1 (threat) for single sample
    else:
        sv = shap_values[0]

    # Build explanation with feature names
    feature_explanations = []
    for i, (feat_key, sv_val) in enumerate(zip(FEATURE_ORDER, sv)):
        feature_explanations.append({
            "feature_key": feat_key,
            "feature_name": FEATURE_DISPLAY_NAMES.get(feat_key, feat_key),
            "shap_value": round(float(sv_val), 4),
            "feature_value": round(float(features.get(feat_key, 0.0)), 4),
            "impact": "positive" if sv_val > 0 else "negative",
            "magnitude": round(abs(float(sv_val)), 4),
        })

    # Sort by absolute SHAP value
    feature_explanations.sort(key=lambda x: x["magnitude"], reverse=True)

    # Base value (expected prediction)
    if hasattr(explainer, "expected_value"):
        expected = explainer.expected_value
        base_value = float(expected[1]) if isinstance(expected, np.ndarray) else float(expected)
    else:
        base_value = 0.5

    return {
        "user_id": user_id,
        "top_features": feature_explanations[:8],
        "shap_values": {
            "values": [round(float(v), 4) for v in sv],
            "feature_names": FEATURE_ORDER,
            "base_value": round(base_value, 4),
        },
        "explanation_type": "SHAP TreeExplainer",
    }


def get_global_importance() -> list:
    """
    Get global SHAP feature importance from the RF model.
    Returns sorted feature importance list.
    """
    if not SHAP_AVAILABLE:
        return _fallback_global_importance()

    model = _load_rf_model()

    # Use model's built-in feature importances as proxy for global SHAP
    importances = model.feature_importances_

    result = []
    for feat_key, importance in zip(FEATURE_ORDER, importances):
        result.append({
            "feature_key": feat_key,
            "feature_name": FEATURE_DISPLAY_NAMES.get(feat_key, feat_key),
            "importance": round(float(importance), 4),
            "percentage": round(float(importance) * 100, 2),
        })

    result.sort(key=lambda x: x["importance"], reverse=True)
    return result


def _fallback_explanation(features: dict) -> dict:
    """Fallback when SHAP is not available — uses feature values directly."""
    explanations = []
    for feat_key in FEATURE_ORDER:
        val = features.get(feat_key, 0.0)
        # Simple heuristic: higher value = higher impact
        explanations.append({
            "feature_key": feat_key,
            "feature_name": FEATURE_DISPLAY_NAMES.get(feat_key, feat_key),
            "shap_value": round(float(val) * 0.1, 4),
            "feature_value": round(float(val), 4),
            "impact": "positive" if val > 0 else "neutral",
            "magnitude": round(abs(float(val)) * 0.1, 4),
        })

    explanations.sort(key=lambda x: x["magnitude"], reverse=True)
    return {
        "user_id": "unknown",
        "top_features": explanations[:8],
        "shap_values": {"values": [], "feature_names": FEATURE_ORDER, "base_value": 0.5},
        "explanation_type": "Heuristic (SHAP unavailable)",
    }


def _fallback_global_importance() -> list:
    """Fallback global importance when SHAP or model unavailable."""
    default_weights = {
        "usb_transfer_count": 0.20,
        "sensitive_file_accesses": 0.18,
        "external_transfers": 0.15,
        "failed_login_count": 0.12,
        "suspicious_url_count": 0.10,
        "bulk_file_copy_count": 0.09,
        "late_night_logins": 0.07,
        "file_download_volume": 0.05,
        "after_hours_events": 0.02,
        "anomaly_ratio": 0.01,
        "login_frequency": 0.01,
    }
    return [
        {
            "feature_key": k,
            "feature_name": FEATURE_DISPLAY_NAMES.get(k, k),
            "importance": v,
            "percentage": round(v * 100, 1),
        }
        for k, v in sorted(default_weights.items(), key=lambda x: x[1], reverse=True)
    ]
