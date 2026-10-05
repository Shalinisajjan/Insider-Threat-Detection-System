"""
ml/train_lstm.py — LSTM deep learning model for sequential behavioral pattern analysis.
Detects temporal anomalies in user behavior sequences.
"""
import numpy as np
import os
import json

MODELS_PATH = "./saved_models"
os.makedirs(MODELS_PATH, exist_ok=True)

# Sequence parameters
SEQUENCE_LENGTH = 10  # Number of time steps
N_FEATURES = 11       # Number of behavioral features


def create_sequences(X: np.ndarray, y: np.ndarray, seq_len: int = SEQUENCE_LENGTH):
    """
    Transform flat feature arrays into time-series sequences for LSTM.
    Each sample represents the last `seq_len` activity windows.
    """
    Xs, ys = [], []
    for i in range(len(X) - seq_len):
        Xs.append(X[i: i + seq_len])
        ys.append(y[i + seq_len])
    return np.array(Xs), np.array(ys)


def build_lstm_model(seq_len: int, n_features: int):
    """Build LSTM model architecture."""
    try:
        import tensorflow as tf
        from tensorflow import keras
        from tensorflow.keras.models import Sequential
        from tensorflow.keras.layers import (
            LSTM, Dense, Dropout, BatchNormalization, Bidirectional
        )
        from tensorflow.keras.regularizers import l2
    except ImportError:
        raise ImportError(
            "TensorFlow not installed. Install with: pip install tensorflow"
        )

    model = Sequential([
        Bidirectional(LSTM(128, return_sequences=True, kernel_regularizer=l2(0.001)),
                      input_shape=(seq_len, n_features)),
        Dropout(0.3),
        BatchNormalization(),

        LSTM(64, return_sequences=False),
        Dropout(0.2),
        BatchNormalization(),

        Dense(32, activation="relu"),
        Dropout(0.2),
        Dense(1, activation="sigmoid"),  # Binary: threat / normal
    ])

    model.compile(
        optimizer=keras.optimizers.Adam(learning_rate=0.001),
        loss="binary_crossentropy",
        metrics=["accuracy", keras.metrics.AUC(name="auc")],
    )

    print("🏗️  LSTM Architecture:")
    model.summary()
    return model


def train_lstm(X_train, y_train, X_test, y_test, epochs=30, batch_size=32):
    """
    Train Bidirectional LSTM for sequential threat detection.

    Returns:
        Trained model and training history
    """
    print("\n" + "="*60)
    print("🧠 TRAINING BIDIRECTIONAL LSTM")
    print("="*60)

    try:
        import tensorflow as tf
        from tensorflow import keras
    except ImportError:
        print("⚠️  TensorFlow not installed. Skipping LSTM training.")
        return None, {}

    # Create sequences
    X_train_seq, y_train_seq = create_sequences(X_train, y_train, SEQUENCE_LENGTH)
    X_test_seq, y_test_seq = create_sequences(X_test, y_test, SEQUENCE_LENGTH)
    print(f"📊 Sequence shapes: train={X_train_seq.shape}, test={X_test_seq.shape}")

    n_features = X_train_seq.shape[2]
    model = build_lstm_model(SEQUENCE_LENGTH, n_features)

    # Callbacks
    callbacks = [
        keras.callbacks.EarlyStopping(
            monitor="val_auc", patience=5, restore_best_weights=True, mode="max"
        ),
        keras.callbacks.ReduceLROnPlateau(
            monitor="val_loss", factor=0.5, patience=3, min_lr=1e-6
        ),
        keras.callbacks.ModelCheckpoint(
            filepath=os.path.join(MODELS_PATH, "lstm_best.keras"),
            monitor="val_auc", save_best_only=True, mode="max",
        ),
    ]

    # Class weights for imbalanced data
    neg, pos = np.bincount(y_train_seq.astype(int))
    class_weight = {0: 1.0, 1: neg / max(pos, 1)}
    print(f"⚖️  Class weights: Normal={class_weight[0]:.2f}, Threat={class_weight[1]:.2f}")

    history = model.fit(
        X_train_seq, y_train_seq,
        validation_data=(X_test_seq, y_test_seq),
        epochs=epochs,
        batch_size=batch_size,
        class_weight=class_weight,
        callbacks=callbacks,
        verbose=1,
    )

    # Evaluation
    results = model.evaluate(X_test_seq, y_test_seq, verbose=0)
    metric_names = model.metrics_names
    print(f"\n📊 EVALUATION RESULTS:")
    for name, value in zip(metric_names, results):
        print(f"   {name}: {value:.4f}")

    # Save final model
    model_path = os.path.join(MODELS_PATH, "lstm_model.keras")
    model.save(model_path)
    print(f"\n💾 LSTM model saved to: {model_path}")

    # Save history
    history_data = {
        "loss": [float(v) for v in history.history["loss"]],
        "val_loss": [float(v) for v in history.history["val_loss"]],
        "accuracy": [float(v) for v in history.history["accuracy"]],
        "val_accuracy": [float(v) for v in history.history["val_accuracy"]],
        "auc": [float(v) for v in history.history["auc"]],
        "val_auc": [float(v) for v in history.history["val_auc"]],
    }

    metrics = {
        "model": "Bidirectional LSTM",
        "final_loss": float(results[0]),
        "final_accuracy": float(results[1]),
        "final_auc": float(results[2]) if len(results) > 2 else 0.0,
        "epochs_trained": len(history.history["loss"]),
        "sequence_length": SEQUENCE_LENGTH,
    }

    metrics_path = os.path.join(MODELS_PATH, "lstm_metrics.json")
    with open(metrics_path, "w") as f:
        json.dump({**metrics, "history": history_data}, f, indent=2)

    return model, metrics


if __name__ == "__main__":
    import sys
    sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
    from ml.preprocessing import run_preprocessing_pipeline

    dataset_path = "../../dataset/synthetic_insider_threat.csv"
    X_train, X_test, y_train, y_test, features = run_preprocessing_pipeline(dataset_path)
    model, metrics = train_lstm(X_train, y_train, X_test, y_test, epochs=20)
    if model:
        print(f"\n✅ LSTM training complete! AUC: {metrics.get('final_auc', 'N/A')}")
