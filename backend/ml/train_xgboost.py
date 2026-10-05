"""
ml/train_xgboost.py — XGBoost gradient boosting training for insider threat detection.
"""
import numpy as np
import xgboost as xgb
from sklearn.metrics import (
    classification_report, roc_auc_score, f1_score, accuracy_score
)
from sklearn.model_selection import cross_val_score
import joblib
import json
import os

MODELS_PATH = "./saved_models"
os.makedirs(MODELS_PATH, exist_ok=True)


def train_xgboost(X_train, y_train, X_test, y_test, feature_names=None):
    """
    Train XGBoost classifier for insider threat detection.

    Returns:
        Trained model and evaluation metrics dict
    """
    print("\n" + "="*60)
    print("⚡ TRAINING XGBOOST CLASSIFIER")
    print("="*60)

    # Class weight for imbalanced data
    scale_pos_weight = (y_train == 0).sum() / max((y_train == 1).sum(), 1)
    print(f"⚖️  scale_pos_weight = {scale_pos_weight:.2f}")

    model = xgb.XGBClassifier(
        n_estimators=300,
        max_depth=8,
        learning_rate=0.05,
        subsample=0.8,
        colsample_bytree=0.8,
        scale_pos_weight=scale_pos_weight,
        use_label_encoder=False,
        eval_metric="logloss",
        random_state=42,
        n_jobs=-1,
        tree_method="hist",  # Fast histogram-based training
    )

    # Fit with early stopping using eval set
    eval_set = [(X_test, y_test)]
    model.fit(
        X_train, y_train,
        eval_set=eval_set,
        verbose=50,
    )

    # ── Evaluation ───────────────────────────────────────────────────
    y_pred = model.predict(X_test)
    y_proba = model.predict_proba(X_test)[:, 1]

    accuracy = accuracy_score(y_test, y_pred)
    f1 = f1_score(y_test, y_pred, average="binary")
    roc_auc = roc_auc_score(y_test, y_proba)

    print(f"\n📊 EVALUATION RESULTS:")
    print(f"   Accuracy:  {accuracy:.4f}")
    print(f"   F1 Score:  {f1:.4f}")
    print(f"   ROC-AUC:   {roc_auc:.4f}")
    print(f"\n{classification_report(y_test, y_pred, target_names=['Normal', 'Threat'])}")

    # Feature importance
    if feature_names:
        importance = dict(zip(feature_names, model.feature_importances_))
        sorted_importance = sorted(importance.items(), key=lambda x: x[1], reverse=True)
        print("\n🔑 XGBoost Feature Importances:")
        for feat, imp in sorted_importance[:10]:
            bar = "█" * int(imp * 50)
            print(f"   {feat:<30} {bar} {imp:.4f}")

    # ── Save model ────────────────────────────────────────────────────
    model_path = os.path.join(MODELS_PATH, "xgb_model.joblib")
    joblib.dump(model, model_path)
    print(f"\n💾 Model saved to: {model_path}")

    metrics = {
        "model": "XGBoost",
        "accuracy": round(accuracy, 4),
        "f1_score": round(f1, 4),
        "roc_auc": round(roc_auc, 4),
        "n_estimators": model.n_estimators,
        "feature_importances": dict(zip(
            feature_names or [f"f{i}" for i in range(X_train.shape[1])],
            model.feature_importances_.tolist()
        )),
    }

    metrics_path = os.path.join(MODELS_PATH, "xgb_metrics.json")
    with open(metrics_path, "w") as f:
        json.dump(metrics, f, indent=2)

    return model, metrics


if __name__ == "__main__":
    import sys
    sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
    from ml.preprocessing import run_preprocessing_pipeline

    dataset_path = "../../dataset/synthetic_insider_threat.csv"
    X_train, X_test, y_train, y_test, features = run_preprocessing_pipeline(dataset_path)
    model, metrics = train_xgboost(X_train, y_train, X_test, y_test, features)
    print(f"\n✅ XGBoost training complete! ROC-AUC: {metrics['roc_auc']}")
