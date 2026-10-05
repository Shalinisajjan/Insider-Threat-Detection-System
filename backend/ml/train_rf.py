"""
ml/train_rf.py — Random Forest classifier training for insider threat detection.
"""
import numpy as np
import pandas as pd
from sklearn.ensemble import RandomForestClassifier
from sklearn.model_selection import GridSearchCV, cross_val_score
from sklearn.metrics import (
    classification_report, confusion_matrix,
    roc_auc_score, f1_score, accuracy_score
)
import joblib
import os
import json


MODELS_PATH = "./saved_models"
os.makedirs(MODELS_PATH, exist_ok=True)


def train_random_forest(X_train, y_train, X_test, y_test, feature_names=None, tune_hyperparams=False):
    """
    Train a Random Forest classifier with optional hyperparameter tuning.

    Args:
        X_train, y_train: Training data
        X_test, y_test:   Test data
        feature_names:    List of feature names for importance plot
        tune_hyperparams: Whether to run GridSearchCV

    Returns:
        Trained model and evaluation metrics dict
    """
    print("\n" + "="*60)
    print("🌲 TRAINING RANDOM FOREST CLASSIFIER")
    print("="*60)

    if tune_hyperparams:
        print("🔍 Running GridSearchCV (this may take a few minutes)...")
        param_grid = {
            "n_estimators": [100, 200],
            "max_depth": [10, 20, None],
            "min_samples_split": [2, 5],
            "min_samples_leaf": [1, 2],
            "class_weight": ["balanced"],
        }
        base_rf = RandomForestClassifier(random_state=42, n_jobs=-1)
        grid_search = GridSearchCV(
            base_rf, param_grid, cv=5, scoring="f1", n_jobs=-1, verbose=1
        )
        grid_search.fit(X_train, y_train)
        model = grid_search.best_estimator_
        print(f"✅ Best params: {grid_search.best_params_}")
    else:
        # Production-ready default parameters
        model = RandomForestClassifier(
            n_estimators=200,
            max_depth=20,
            min_samples_split=2,
            min_samples_leaf=1,
            class_weight="balanced",
            random_state=42,
            n_jobs=-1,
        )
        model.fit(X_train, y_train)

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

    # Cross-validation
    cv_scores = cross_val_score(model, X_train, y_train, cv=5, scoring="f1")
    print(f"   5-Fold CV F1: {cv_scores.mean():.4f} ± {cv_scores.std():.4f}")

    # Feature importance
    if feature_names:
        importance = dict(zip(feature_names, model.feature_importances_))
        sorted_importance = sorted(importance.items(), key=lambda x: x[1], reverse=True)
        print("\n🔑 Top Feature Importances:")
        for feat, imp in sorted_importance[:10]:
            bar = "█" * int(imp * 50)
            print(f"   {feat:<30} {bar} {imp:.4f}")

    # ── Save model ────────────────────────────────────────────────────
    model_path = os.path.join(MODELS_PATH, "rf_model.joblib")
    joblib.dump(model, model_path)
    print(f"\n💾 Model saved to: {model_path}")

    metrics = {
        "model": "Random Forest",
        "accuracy": round(accuracy, 4),
        "f1_score": round(f1, 4),
        "roc_auc": round(roc_auc, 4),
        "cv_f1_mean": round(float(cv_scores.mean()), 4),
        "cv_f1_std": round(float(cv_scores.std()), 4),
        "n_estimators": model.n_estimators,
        "feature_importances": dict(zip(
            feature_names or [f"f{i}" for i in range(X_train.shape[1])],
            model.feature_importances_.tolist()
        )),
    }

    metrics_path = os.path.join(MODELS_PATH, "rf_metrics.json")
    with open(metrics_path, "w") as f:
        json.dump(metrics, f, indent=2)
    print(f"📊 Metrics saved to: {metrics_path}")

    return model, metrics


if __name__ == "__main__":
    import sys
    sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

    from ml.preprocessing import run_preprocessing_pipeline

    dataset_path = "../../dataset/synthetic_insider_threat.csv"
    if not os.path.exists(dataset_path):
        print("❌ Dataset not found. Run dataset/generate_synthetic.py first.")
        sys.exit(1)

    X_train, X_test, y_train, y_test, features = run_preprocessing_pipeline(dataset_path)
    model, metrics = train_random_forest(X_train, y_train, X_test, y_test, features)
    print(f"\n✅ Training complete! ROC-AUC: {metrics['roc_auc']}")
