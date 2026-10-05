"""
ml/predict.py — Unified ML inference module.
Loads trained models and provides prediction functions for the API.
"""
import numpy as np
import joblib
import os
import json
from typing import Optional

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


def _load_model(filename: str):
    """Load a joblib model, raising FileNotFoundError if not found."""
    path = os.path.join(MODELS_PATH, filename)
    if not os.path.exists(path):
        raise FileNotFoundError(f"Model not found at: {path}. Run training scripts first.")
    return joblib.load(path)


def _load_scaler():
    """Load the feature scaler."""
    scaler_path = os.path.join(MODELS_PATH, "scaler.joblib")
    if os.path.exists(scaler_path):
        return joblib.load(scaler_path)
    return None


def _features_to_array(features: dict) -> np.ndarray:
    """Convert feature dict to ordered numpy array."""
    arr = [features.get(f, 0.0) for f in FEATURE_ORDER]
    return np.array([arr], dtype=np.float32)


def predict_threat(user_id: str, features: dict) -> dict:
    """
    Run ensemble threat classification (RF + XGBoost).

    Returns prediction result dict.
    """
    X = _features_to_array(features)

    # Apply scaler if available
    scaler = _load_scaler()
    if scaler is not None:
        X = scaler.transform(X)

    # Load models
    rf_model = _load_model("rf_model.joblib")
    try:
        xgb_model = _load_model("xgb_model.joblib")
        has_xgb = True
    except FileNotFoundError:
        has_xgb = False

    # RF prediction
    rf_proba = rf_model.predict_proba(X)[0][1]
    rf_pred = rf_model.predict(X)[0]

    # Ensemble with XGBoost if available
    if has_xgb:
        xgb_proba = xgb_model.predict_proba(X)[0][1]
        # Weighted ensemble (XGBoost slightly weighted higher for precision)
        final_proba = 0.45 * rf_proba + 0.55 * xgb_proba
        model_used = "RF + XGBoost Ensemble"
    else:
        final_proba = rf_proba
        model_used = "Random Forest"

    is_threat = bool(final_proba >= 0.5)
    threat_label = "THREAT" if final_proba >= 0.7 else "SUSPICIOUS" if final_proba >= 0.5 else "NORMAL"
    confidence = "High" if abs(final_proba - 0.5) > 0.3 else "Medium" if abs(final_proba - 0.5) > 0.1 else "Low"

    # Get top feature importances
    feature_importances = rf_model.feature_importances_
    top_features = sorted(
        [{"feature_name": name.replace("_", " ").title(),
          "feature_key": name,
          "importance": round(float(imp), 4),
          "value": features.get(name, 0)}
         for name, imp in zip(FEATURE_ORDER, feature_importances)],
        key=lambda x: x["importance"],
        reverse=True,
    )[:7]

    return {
        "user_id": user_id,
        "is_threat": is_threat,
        "threat_probability": round(float(final_proba), 4),
        "threat_label": threat_label,
        "confidence": confidence,
        "model_used": model_used,
        "top_features": top_features,
    }


def predict_anomaly(user_id: str, features: dict) -> dict:
    """
    Run Isolation Forest anomaly detection.

    Returns anomaly score and severity.
    """
    X = _features_to_array(features)

    scaler = _load_scaler()
    if scaler is not None:
        X = scaler.transform(X)

    iso_model = _load_model("iso_forest_model.joblib")

    # -1 = anomaly, 1 = normal
    pred = iso_model.predict(X)[0]
    score_raw = -iso_model.score_samples(X)[0]  # Higher = more anomalous

    # Normalize score to 0-100
    anomaly_score = min(float(score_raw) * 50, 100.0)
    is_anomaly = pred == -1

    if anomaly_score >= 70:
        severity = "CRITICAL"
        description = "Highly anomalous behavior detected. Immediate investigation required."
    elif anomaly_score >= 50:
        severity = "HIGH"
        description = "Significant deviation from baseline behavior pattern."
    elif anomaly_score >= 30:
        severity = "MEDIUM"
        description = "Moderate behavioral anomaly observed."
    else:
        severity = "LOW"
        description = "Minor deviation from baseline. Continue monitoring."

    return {
        "user_id": user_id,
        "is_anomaly": is_anomaly,
        "anomaly_score": round(anomaly_score, 2),
        "severity": severity,
        "description": description,
    }
