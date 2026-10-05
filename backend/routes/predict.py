"""
routes/predict.py — ML inference endpoints: threat classification and anomaly detection.
"""
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from typing import Optional, List
import numpy as np

from middleware.auth import require_analyst_or_admin
from ml.predict import predict_threat, predict_anomaly

router = APIRouter()


class PredictionRequest(BaseModel):
    user_id: str
    features: dict  # behavioral feature dictionary


class PredictionResponse(BaseModel):
    user_id: str
    is_threat: bool
    threat_probability: float
    threat_label: str
    confidence: str
    model_used: str
    top_features: List[dict]


class AnomalyRequest(BaseModel):
    user_id: str
    features: dict


class AnomalyResponse(BaseModel):
    user_id: str
    is_anomaly: bool
    anomaly_score: float
    severity: str
    description: str


@router.post("/predict", response_model=PredictionResponse)
async def predict_insider_threat(
    payload: PredictionRequest,
    current_user: dict = Depends(require_analyst_or_admin),
):
    """
    Run ML threat classification on a user's behavioral features.
    Uses Random Forest + XGBoost ensemble.
    """
    try:
        result = predict_threat(payload.user_id, payload.features)
        return PredictionResponse(**result)
    except FileNotFoundError:
        raise HTTPException(
            status_code=503,
            detail="ML models not trained yet. Run training scripts first.",
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Prediction error: {str(e)}")


@router.post("/anomaly-detect", response_model=AnomalyResponse)
async def detect_anomaly(
    payload: AnomalyRequest,
    current_user: dict = Depends(require_analyst_or_admin),
):
    """
    Run Isolation Forest anomaly detection on behavioral features.
    Returns anomaly score and severity.
    """
    try:
        result = predict_anomaly(payload.user_id, payload.features)
        return AnomalyResponse(**result)
    except FileNotFoundError:
        raise HTTPException(
            status_code=503,
            detail="Anomaly detection model not trained yet.",
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Anomaly detection error: {str(e)}")


@router.get("/model-info", response_model=dict)
async def get_model_info(current_user: dict = Depends(require_analyst_or_admin)):
    """Return information about available trained ML models and their metrics."""
    import os
    import json
    models_path = "./ml/saved_models"

    available = []
    model_files = {
        "random_forest": "rf_model.joblib",
        "xgboost": "xgb_model.joblib",
        "isolation_forest": "iso_forest_model.joblib",
        "lstm": "lstm_model.keras",
    }

    for model_name, filename in model_files.items():
        path = os.path.join(models_path, filename)
        available.append({
            "name": model_name,
            "filename": filename,
            "trained": os.path.exists(path),
            "size_kb": round(os.path.getsize(path) / 1024, 1) if os.path.exists(path) else 0,
        })

    # Load training summary if available
    training_summary = None
    summary_path = os.path.join(models_path, "training_summary.json")
    if os.path.exists(summary_path):
        try:
            with open(summary_path, "r") as f:
                training_summary = json.load(f)
        except Exception:
            pass

    return {
        "models": available,
        "models_path": models_path,
        "total_trained": sum(1 for m in available if m["trained"]),
        "training_summary": training_summary,
    }
