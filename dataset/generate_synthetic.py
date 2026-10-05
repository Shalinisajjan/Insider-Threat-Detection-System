"""
dataset/generate_synthetic.py — Synthetic CERT-like Insider Threat Dataset Generator.

Generates realistic user behavioral data including:
- Normal users (85%)
- Malicious insiders (15%)

Each record represents a user's behavioral profile over 30 days.
"""
import numpy as np
import pandas as pd
import os
import sys
from datetime import datetime

np.random.seed(42)

N_USERS = 2000
MALICIOUS_RATIO = 0.15
OUTPUT_DIR = os.path.dirname(os.path.abspath(__file__))
OUTPUT_FILE = os.path.join(OUTPUT_DIR, "synthetic_insider_threat.csv")


def generate_normal_user() -> dict:
    """Generate behavioral features for a normal (benign) user."""
    return {
        "login_frequency": np.random.poisson(5),
        "late_night_logins": np.random.poisson(0.3),
        "failed_login_count": np.random.poisson(0.5),
        "file_download_volume": abs(np.random.normal(50, 30)),        # MB
        "usb_transfer_count": np.random.poisson(0.5),
        "suspicious_url_count": np.random.poisson(0.2),
        "bulk_file_copy_count": np.random.poisson(0.3),
        "after_hours_events": np.random.poisson(1),
        "sensitive_file_accesses": np.random.poisson(2),
        "external_transfers": np.random.poisson(0.3),
        "anomaly_ratio": abs(np.random.normal(0.05, 0.05)),
        "is_malicious": 0,
    }


def generate_malicious_user(threat_type: str = "random") -> dict:
    """Generate behavioral features for a malicious insider."""
    # Randomly choose a threat type if not specified
    if threat_type == "random":
        threat_type = np.random.choice(
            ["data_theft", "sabotage", "privilege_abuse", "slow_exfil"],
            p=[0.4, 0.2, 0.25, 0.15],
        )

    base = {
        "login_frequency": np.random.poisson(6),
        "is_malicious": 1,
        "threat_type": threat_type,
    }

    if threat_type == "data_theft":
        # Large downloads, USB usage, after-hours access
        base.update({
            "late_night_logins": np.random.poisson(4),
            "failed_login_count": np.random.poisson(1),
            "file_download_volume": abs(np.random.normal(800, 300)),
            "usb_transfer_count": np.random.poisson(8),
            "suspicious_url_count": np.random.poisson(3),
            "bulk_file_copy_count": np.random.poisson(10),
            "after_hours_events": np.random.poisson(8),
            "sensitive_file_accesses": np.random.poisson(20),
            "external_transfers": np.random.poisson(12),
            "anomaly_ratio": abs(np.random.normal(0.7, 0.15)),
        })

    elif threat_type == "sabotage":
        # Failed logins, suspicious URLs, privilege abuse
        base.update({
            "late_night_logins": np.random.poisson(2),
            "failed_login_count": np.random.poisson(8),
            "file_download_volume": abs(np.random.normal(100, 50)),
            "usb_transfer_count": np.random.poisson(2),
            "suspicious_url_count": np.random.poisson(12),
            "bulk_file_copy_count": np.random.poisson(3),
            "after_hours_events": np.random.poisson(5),
            "sensitive_file_accesses": np.random.poisson(15),
            "external_transfers": np.random.poisson(4),
            "anomaly_ratio": abs(np.random.normal(0.55, 0.15)),
        })

    elif threat_type == "privilege_abuse":
        # Accessing sensitive files, browsing restricted areas
        base.update({
            "late_night_logins": np.random.poisson(1),
            "failed_login_count": np.random.poisson(2),
            "file_download_volume": abs(np.random.normal(200, 100)),
            "usb_transfer_count": np.random.poisson(1),
            "suspicious_url_count": np.random.poisson(6),
            "bulk_file_copy_count": np.random.poisson(6),
            "after_hours_events": np.random.poisson(3),
            "sensitive_file_accesses": np.random.poisson(35),
            "external_transfers": np.random.poisson(6),
            "anomaly_ratio": abs(np.random.normal(0.45, 0.12)),
        })

    else:  # slow_exfil — gradual data exfiltration
        base.update({
            "late_night_logins": np.random.poisson(2),
            "failed_login_count": np.random.poisson(0.5),
            "file_download_volume": abs(np.random.normal(150, 60)),
            "usb_transfer_count": np.random.poisson(3),
            "suspicious_url_count": np.random.poisson(2),
            "bulk_file_copy_count": np.random.poisson(4),
            "after_hours_events": np.random.poisson(4),
            "sensitive_file_accesses": np.random.poisson(10),
            "external_transfers": np.random.poisson(5),
            "anomaly_ratio": abs(np.random.normal(0.35, 0.10)),
        })

    return base


def generate_dataset(n_users: int = N_USERS, malicious_ratio: float = MALICIOUS_RATIO) -> pd.DataFrame:
    """Generate complete synthetic dataset."""
    print("🏭 Generating Synthetic Insider Threat Dataset")
    print(f"   Total users: {n_users:,}")
    print(f"   Malicious ratio: {malicious_ratio:.1%}")

    records = []
    n_malicious = int(n_users * malicious_ratio)
    n_normal = n_users - n_malicious

    print(f"\n👤 Generating {n_normal:,} normal users...")
    for _ in range(n_normal):
        records.append(generate_normal_user())

    print(f"🚨 Generating {n_malicious:,} malicious users...")
    for _ in range(n_malicious):
        records.append(generate_malicious_user())

    df = pd.DataFrame(records)

    # Add metadata columns
    departments = ["Engineering", "Finance", "HR", "Legal", "Sales", "IT", "Marketing", "Operations"]
    df["department"] = np.random.choice(departments, size=len(df))
    df["tenure_months"] = np.random.randint(1, 120, size=len(df))
    df["user_id"] = [f"USER_{i:05d}" for i in range(len(df))]

    # Shuffle
    df = df.sample(frac=1, random_state=42).reset_index(drop=True)

    print(f"\n✅ Dataset generated: {len(df):,} records")
    print(f"   Normal users: {(df['is_malicious'] == 0).sum():,}")
    print(f"   Malicious users: {(df['is_malicious'] == 1).sum():,}")
    print(f"\n📊 Feature Statistics:")
    feature_cols = [c for c in df.columns if c not in ["is_malicious", "department", "user_id", "threat_type"]]
    print(df[feature_cols].describe().round(2).to_string())

    return df


def save_dataset(df: pd.DataFrame, filepath: str):
    """Save dataset to CSV."""
    df.to_csv(filepath, index=False)
    size_kb = os.path.getsize(filepath) / 1024
    print(f"\n💾 Dataset saved to: {filepath}")
    print(f"   File size: {size_kb:.1f} KB")
    print(f"   Records: {len(df):,}")
    print(f"   Columns: {list(df.columns)}")


if __name__ == "__main__":
    print("="*60)
    print("AI INSIDER THREAT — SYNTHETIC DATASET GENERATOR")
    print("="*60)
    print(f"Timestamp: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")

    df = generate_dataset()
    save_dataset(df, OUTPUT_FILE)

    print("\n🎉 Done! Use this dataset to train your ML models.")
    print(f"   Run: python backend/ml/train_rf.py {OUTPUT_FILE}")
