"""
ml/train_all.py — Master training script.
Generates dataset and trains all models in sequence.
"""
import os
import sys
import json

# Ensure the backend directory is in the path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

DATASET_PATH = os.path.join(os.path.dirname(__file__), "../../dataset/synthetic_insider_threat.csv")
MODELS_PATH = os.path.join(os.path.dirname(__file__), "saved_models")


def run_all():
    print("\n" + "="*70)
    print("🚀 AI INSIDER THREAT PLATFORM — FULL MODEL TRAINING PIPELINE")
    print("="*70)

    # Step 1: Generate dataset if not exists
    if not os.path.exists(DATASET_PATH):
        print("\n📊 Step 1: Generating synthetic dataset...")
        sys.path.insert(0, os.path.join(os.path.dirname(__file__), "../../dataset"))
        from generate_synthetic import generate_dataset, save_dataset
        df = generate_dataset()
        save_dataset(df, DATASET_PATH)
    else:
        print(f"\n📊 Step 1: Dataset found at {DATASET_PATH}")

    # Step 2: Preprocessing
    print("\n🔧 Step 2: Running preprocessing pipeline...")
    from ml.preprocessing import run_preprocessing_pipeline
    X_train, X_test, y_train, y_test, features = run_preprocessing_pipeline(DATASET_PATH)

    all_metrics = {}

    # Step 3: Random Forest
    print("\n🌲 Step 3: Training Random Forest...")
    from ml.train_rf import train_random_forest
    rf_model, rf_metrics = train_random_forest(X_train, y_train, X_test, y_test, features)
    all_metrics["random_forest"] = rf_metrics

    # Step 4: XGBoost
    print("\n⚡ Step 4: Training XGBoost...")
    from ml.train_xgboost import train_xgboost
    xgb_model, xgb_metrics = train_xgboost(X_train, y_train, X_test, y_test, features)
    all_metrics["xgboost"] = xgb_metrics

    # Step 5: Isolation Forest
    print("\n🌳 Step 5: Training Isolation Forest...")
    from ml.train_isolation_forest import train_isolation_forest
    iso_model, iso_metrics = train_isolation_forest(X_train, X_test, y_test)
    all_metrics["isolation_forest"] = iso_metrics

    # Step 6: LSTM (optional — requires TensorFlow)
    print("\n🧠 Step 6: Training LSTM (requires TensorFlow)...")
    try:
        from ml.train_lstm import train_lstm
        lstm_model, lstm_metrics = train_lstm(X_train, y_train, X_test, y_test, epochs=20)
        if lstm_model:
            all_metrics["lstm"] = lstm_metrics
    except Exception as e:
        print(f"⚠️  LSTM skipped: {e}")

    # Summary
    print("\n" + "="*70)
    print("📊 TRAINING SUMMARY")
    print("="*70)
    for model_name, metrics in all_metrics.items():
        print(f"\n  {model_name.upper().replace('_', ' ')}:")
        for k, v in metrics.items():
            if isinstance(v, (int, float)):
                print(f"    {k}: {v}")

    # Save combined metrics
    summary_path = os.path.join(MODELS_PATH, "training_summary.json")
    os.makedirs(MODELS_PATH, exist_ok=True)
    with open(summary_path, "w") as f:
        json.dump(all_metrics, f, indent=2, default=str)
    print(f"\n💾 Training summary saved to: {summary_path}")

    print("\n✅ ALL MODELS TRAINED SUCCESSFULLY!")
    print("   Start the backend: uvicorn main:app --reload")
    print("="*70 + "\n")


if __name__ == "__main__":
    run_all()
