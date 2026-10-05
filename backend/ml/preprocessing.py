"""
ml/preprocessing.py — Data preprocessing pipeline for the CERT Insider Threat dataset.
Handles CSV ingestion, cleaning, normalization, and train/test splitting.
"""
import pandas as pd
import numpy as np
from sklearn.preprocessing import LabelEncoder, MinMaxScaler
from sklearn.model_selection import train_test_split
from imblearn.over_sampling import SMOTE
import os
import joblib
import warnings
warnings.filterwarnings("ignore")


# ─── Feature columns expected in the dataset ──────────────────────────────────
FEATURE_COLUMNS = [
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

TARGET_COLUMN = "is_malicious"
MODELS_PATH = "./saved_models"


def load_dataset(filepath: str) -> pd.DataFrame:
    """Load dataset from CSV file."""
    print(f"📂 Loading dataset from: {filepath}")
    df = pd.read_csv(filepath)
    print(f"✅ Loaded {len(df):,} records with {len(df.columns)} columns")
    return df


def clean_data(df: pd.DataFrame) -> pd.DataFrame:
    """
    Clean raw dataset:
    - Drop duplicates
    - Handle missing values
    - Remove outliers
    """
    original_len = len(df)
    df = df.drop_duplicates()
    print(f"🗑️  Removed {original_len - len(df):,} duplicate rows")

    # Fill numeric NaN with median
    numeric_cols = df.select_dtypes(include=[np.number]).columns
    for col in numeric_cols:
        median_val = df[col].median()
        null_count = df[col].isna().sum()
        if null_count > 0:
            print(f"   Filling {null_count} NaN values in '{col}' with median={median_val:.2f}")
            df[col] = df[col].fillna(median_val)

    # Fill categorical NaN with 'unknown'
    cat_cols = df.select_dtypes(include=["object"]).columns
    for col in cat_cols:
        if col != TARGET_COLUMN:
            df[col] = df[col].fillna("unknown")

    # Remove extreme outliers using IQR (only on feature columns)
    feature_cols_present = [c for c in FEATURE_COLUMNS if c in df.columns]
    for col in feature_cols_present:
        Q1 = df[col].quantile(0.01)
        Q3 = df[col].quantile(0.99)
        df[col] = df[col].clip(Q1, Q3)

    print(f"✅ Cleaned dataset: {len(df):,} records remaining")
    return df


def engineer_features(df: pd.DataFrame) -> pd.DataFrame:
    """
    Feature engineering: add derived behavioral features.
    """
    if "login_frequency" in df.columns and "after_hours_events" in df.columns:
        df["after_hours_ratio"] = np.where(
            df["login_frequency"] > 0,
            df["after_hours_events"] / df["login_frequency"],
            0,
        )

    if "failed_login_count" in df.columns and "login_frequency" in df.columns:
        df["fail_rate"] = np.where(
            df["login_frequency"] > 0,
            df["failed_login_count"] / df["login_frequency"],
            0,
        )

    if "usb_transfer_count" in df.columns and "file_download_volume" in df.columns:
        df["total_data_moved"] = df["usb_transfer_count"] * 10 + df["file_download_volume"]

    if "suspicious_url_count" in df.columns and "sensitive_file_accesses" in df.columns:
        df["threat_indicator"] = df["suspicious_url_count"] + df["sensitive_file_accesses"]

    print("✅ Feature engineering complete")
    return df


def encode_labels(df: pd.DataFrame) -> pd.DataFrame:
    """Label-encode categorical columns."""
    cat_cols = df.select_dtypes(include=["object", "bool"]).columns.tolist()
    if TARGET_COLUMN in cat_cols:
        cat_cols.remove(TARGET_COLUMN)

    le_dict = {}
    for col in cat_cols:
        le = LabelEncoder()
        df[col] = le.fit_transform(df[col].astype(str))
        le_dict[col] = le

    # Encode target
    if TARGET_COLUMN in df.columns:
        if df[TARGET_COLUMN].dtype == object:
            df[TARGET_COLUMN] = (df[TARGET_COLUMN].str.lower() == "true").astype(int)
        else:
            df[TARGET_COLUMN] = df[TARGET_COLUMN].astype(int)

    print("✅ Label encoding complete")
    return df, le_dict


def normalize_features(
    X_train: np.ndarray,
    X_test: np.ndarray,
    save_scaler: bool = True,
) -> tuple:
    """Apply MinMax normalization and optionally save scaler."""
    scaler = MinMaxScaler()
    X_train_scaled = scaler.fit_transform(X_train)
    X_test_scaled = scaler.transform(X_test)

    if save_scaler:
        os.makedirs(MODELS_PATH, exist_ok=True)
        joblib.dump(scaler, os.path.join(MODELS_PATH, "scaler.joblib"))
        print(f"💾 Scaler saved to {MODELS_PATH}/scaler.joblib")

    return X_train_scaled, X_test_scaled, scaler


def apply_smote(X_train: np.ndarray, y_train: np.ndarray) -> tuple:
    """Apply SMOTE to balance class distribution."""
    original_distribution = np.bincount(y_train.astype(int))
    print(f"📊 Before SMOTE: {dict(enumerate(original_distribution))}")

    smote = SMOTE(random_state=42)
    X_resampled, y_resampled = smote.fit_resample(X_train, y_train)

    new_distribution = np.bincount(y_resampled.astype(int))
    print(f"📊 After SMOTE: {dict(enumerate(new_distribution))}")

    return X_resampled, y_resampled


def run_preprocessing_pipeline(filepath: str, test_size: float = 0.2, use_smote: bool = True):
    """
    Full preprocessing pipeline.

    Returns:
        X_train, X_test, y_train, y_test, feature_names
    """
    print("\n" + "="*60)
    print("🚀 STARTING DATA PREPROCESSING PIPELINE")
    print("="*60)

    # Load
    df = load_dataset(filepath)

    # Clean
    df = clean_data(df)

    # Engineer features
    df = engineer_features(df)

    # Encode
    df, le_dict = encode_labels(df)

    # Select features
    available_features = [c for c in FEATURE_COLUMNS if c in df.columns]
    derived_features = ["after_hours_ratio", "fail_rate", "total_data_moved", "threat_indicator"]
    available_derived = [c for c in derived_features if c in df.columns]
    all_features = available_features + available_derived

    print(f"\n📋 Using {len(all_features)} features: {all_features}")

    if TARGET_COLUMN not in df.columns:
        raise ValueError(f"Target column '{TARGET_COLUMN}' not found in dataset!")

    X = df[all_features].values
    y = df[TARGET_COLUMN].values

    print(f"📊 Dataset shape: X={X.shape}, y distribution={np.bincount(y.astype(int))}")

    # Split
    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=test_size, random_state=42, stratify=y
    )
    print(f"✂️  Train/Test split: {len(X_train)} / {len(X_test)}")

    # SMOTE for class imbalance
    if use_smote and np.bincount(y_train.astype(int)).min() > 1:
        X_train, y_train = apply_smote(X_train, y_train)

    # Normalize
    X_train, X_test, scaler = normalize_features(X_train, X_test)

    print("\n✅ PREPROCESSING COMPLETE!")
    print("="*60 + "\n")

    return X_train, X_test, y_train, y_test, all_features


if __name__ == "__main__":
    import sys
    filepath = sys.argv[1] if len(sys.argv) > 1 else "../dataset/synthetic_insider_threat.csv"
    X_train, X_test, y_train, y_test, features = run_preprocessing_pipeline(filepath)
    print(f"Ready for training: X_train shape = {X_train.shape}")
