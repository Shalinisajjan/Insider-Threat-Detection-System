"""
ml/train_isolation_forest.py — Isolation Forest for unsupervised anomaly detection.
Detects behavioral anomalies without requiring labeled data.
"""
import numpy as np
from sklearn.ensemble import IsolationForest
from sklearn.metrics import classification_report, roc_auc_score
import joblib
import json
import os

MODELS_PATH = "./saved_models"
os.makedirs(MODELS_PATH, exist_ok=True)


def train_isolation_forest(X_train, X_test=None, y_test=None, contamination=0.1):
    """
    Train Isolation Forest anomaly detection model.

    Args:
        X_train:        Training data (all normal + some anomalies)
        X_test:         Optional test data for evaluation
        y_test:         Optional true labels (1=malicious, 0=normal)
        contamination:  Expected proportion of anomalies (default 10%)

    Returns:
        Trained model and metrics dict
    """
    print("\n" + "="*60)
    print("🌲 TRAINING ISOLATION FOREST (Anomaly Detection)")
    print("="*60)
    print(f"   Contamination rate: {contamination:.1%}")

    model = IsolationForest(
        n_estimators=200,
        contamination=contamination,
        max_samples="auto",
        max_features=1.0,
        bootstrap=False,
        random_state=42,
        n_jobs=-1,
    )

    model.fit(X_train)
    print("✅ Isolation Forest trained successfully")

    metrics = {"model": "Isolation Forest", "contamination": contamination}

    if X_test is not None:
        # Predict: -1 = anomaly, 1 = normal
        preds_raw = model.predict(X_test)
        # Convert to binary: 1 = anomaly (threat), 0 = normal
        preds = np.where(preds_raw == -1, 1, 0)
        scores = -model.score_samples(X_test)  # Higher = more anomalous

        anomaly_count = preds.sum()
        print(f"🔍 Detected {anomaly_count} anomalies out of {len(preds)} samples ({anomaly_count/len(preds):.1%})")

        if y_test is not None:
            roc_auc = roc_auc_score(y_test, scores)
            print(f"\n📊 EVALUATION (vs labeled data):")
            print(f"   ROC-AUC: {roc_auc:.4f}")
            print(f"\n{classification_report(y_test, preds, target_names=['Normal', 'Anomaly'])}")
            metrics["roc_auc"] = round(roc_auc, 4)

        metrics["anomaly_rate"] = round(float(anomaly_count / len(preds)), 4)

    # Save model
    model_path = os.path.join(MODELS_PATH, "iso_forest_model.joblib")
    joblib.dump(model, model_path)
    print(f"\n💾 Isolation Forest saved to: {model_path}")

    metrics_path = os.path.join(MODELS_PATH, "iso_forest_metrics.json")
    with open(metrics_path, "w") as f:
        json.dump(metrics, f, indent=2)

    return model, metrics


def get_anomaly_score(model: IsolationForest, X: np.ndarray) -> np.ndarray:
    """
    Get anomaly scores for input samples.
    Higher score = more anomalous.
    Returns normalized scores in [0, 1].
    """
    raw_scores = -model.score_samples(X)
    # Normalize to 0-1
    min_s = raw_scores.min()
    max_s = raw_scores.max()
    if max_s == min_s:
        return np.zeros_like(raw_scores)
    return (raw_scores - min_s) / (max_s - min_s)


if __name__ == "__main__":
    import sys
    sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
    from ml.preprocessing import run_preprocessing_pipeline

    dataset_path = "../../dataset/synthetic_insider_threat.csv"
    X_train, X_test, y_train, y_test, features = run_preprocessing_pipeline(dataset_path)
    model, metrics = train_isolation_forest(X_train, X_test, y_test)
    print(f"\n✅ Isolation Forest training complete!")
