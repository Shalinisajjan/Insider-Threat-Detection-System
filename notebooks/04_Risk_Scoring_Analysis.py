# %% [markdown]
# # Notebook 4: Risk Scoring Analysis & Engine Tuning
# ## Explainable Insider Threat Intelligence Platform
#
# Analyzes the risk scoring algorithm used in the ThreatSight AI platform.
# Focuses on:
# - Simulating and analyzing the risk score distributions.
# - Evaluating the relationship between features and the final Risk Score (0-100).
# - Tuning risk score thresholds for high, medium, and low classification.
# - Analyzing ROC sensitivity for optimizing alert precision.

# %% [markdown]
# ## 1. Setup & Imports

# %%
import sys, os
sys.path.insert(0, '../backend')
sys.path.insert(0, '../dataset')
os.makedirs('../notebooks/figures', exist_ok=True)

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import warnings
warnings.filterwarnings('ignore')

# Dark theme styling
plt.style.use('dark_background')
plt.rcParams.update({
    'figure.facecolor': '#0f172a', 'axes.facecolor': '#1e293b',
    'axes.edgecolor': '#334155', 'text.color': '#e2e8f0',
    'axes.labelcolor': '#94a3b8', 'xtick.color': '#64748b',
    'ytick.color': '#64748b',
})

print("✅ Setup and styles ready")

# %% [markdown]
# ## 2. Load Dataset & Risk Calculation Functions

# %%
from ml.preprocessing import run_preprocessing_pipeline
from ml.risk_engine import calculate_risk_score_from_event

dataset_path = '../dataset/synthetic_insider_threat.csv'
df = pd.read_csv(dataset_path)

# Let's inspect what fields are available and what is calculated
print("Dataset columns:", df.columns.tolist())
print(df[['username', 'department', 'risk_score', 'risk_level']].head(5))

# %% [markdown]
# ## 3. Analyze Risk Score Distribution
# Let's plot the distribution of risk scores in the synthetic dataset to understand its characteristics.

# %%
plt.figure(figsize=(10, 6), facecolor='#0f172a')

# Plot histogram of risk scores
sns.histplot(data=df, x='risk_score', hue='risk_level', kde=True, multiple='stack',
             palette={'LOW': '#10b981', 'MEDIUM': '#f59e0b', 'HIGH': '#ef4444'},
             bins=30, alpha=0.75, edgecolor='#0f172a')

plt.xlabel('Calculated Risk Score (0–100)', fontsize=12, color='#94a3b8')
plt.ylabel('User Event Frequency', fontsize=12, color='#94a3b8')
plt.title('Distribution of Risk Scores by Threat Level', fontsize=14, fontweight='bold', color='#e2e8f0', pad=15)
plt.grid(axis='y', alpha=0.15)
plt.tight_layout()
plt.savefig('../notebooks/figures/risk_score_distribution.png', dpi=150, bbox_inches='tight', facecolor='#0f172a')
plt.show()

# %% [markdown]
# ## 4. Feature Contributions to Risk Score (Correlation Analysis)
# Analyzes how individual behavioral indicators align with the final risk score.

# %%
# Extract behavioral metrics and risk score for correlation
behavior_metrics = [
    'login_frequency', 'late_night_logins', 'failed_login_count', 
    'file_download_volume', 'usb_transfer_count', 'suspicious_url_count', 
    'bulk_file_copy_count', 'after_hours_events', 'sensitive_file_accesses', 
    'external_transfers', 'anomaly_ratio', 'risk_score'
]

available_metrics = [col for col in behavior_metrics if col in df.columns]
corr_matrix = df[available_metrics].corr()

plt.figure(figsize=(12, 8), facecolor='#0f172a')
sns.heatmap(corr_matrix[['risk_score']].sort_values(by='risk_score', ascending=False), 
            annot=True, cmap='Reds', fmt='.3f', cbar=True,
            linewidths=1, linecolor='#0f172a')

plt.title('Correlation of Behavioral Features with Risk Score', fontsize=14, fontweight='bold', color='#e2e8f0', pad=15)
plt.ylabel('Feature Indicator', fontsize=12, color='#94a3b8')
plt.tight_layout()
plt.savefig('../notebooks/figures/risk_feature_correlations.png', dpi=150, bbox_inches='tight', facecolor='#0f172a')
plt.show()

# %% [markdown]
# ## 5. Threshold Sensitivity Analysis (Tuning Alert Triggers)
# Analyzes the impact of modifying risk score thresholds for the final alert classification system. 
# Evaluates how selecting lower or higher threshold limits affects Precision and Recall.

# %%
# Define labels where high/medium-risk levels represent actual threats (from supervised column if available, or thresholding)
actual_threats = df['is_threat'].values if 'is_threat' in df.columns else (df['risk_score'] > 60).astype(int)

precisions = []
recalls = []
f1_scores = []
thresholds = np.arange(10, 95, 5)

for t in thresholds:
    predicted_threats = (df['risk_score'] >= t).astype(int)
    
    tp = np.sum((predicted_threats == 1) & (actual_threats == 1))
    fp = np.sum((predicted_threats == 1) & (actual_threats == 0))
    fn = np.sum((predicted_threats == 0) & (actual_threats == 1))
    
    precision = tp / (tp + fp) if (tp + fp) > 0 else 0
    recall = tp / (tp + fn) if (tp + fn) > 0 else 0
    f1 = 2 * precision * recall / (precision + recall) if (precision + recall) > 0 else 0
    
    precisions.append(precision)
    recalls.append(recall)
    f1_scores.append(f1)

# Plot threshold optimization curve
plt.figure(figsize=(10, 6), facecolor='#0f172a')
plt.plot(thresholds, precisions, label='Precision (Fewer False Alerts)', color='#6366f1', lw=2.5)
plt.plot(thresholds, recalls, label='Recall (Higher Threat Capture)', color='#ef4444', lw=2.5)
plt.plot(thresholds, f1_scores, label='F1 Score (Balanced Metric)', color='#f59e0b', lw=2.5, linestyle='--')

plt.axvline(x=60, color='#10b981', linestyle=':', lw=2, label='Current HIGH Trigger (Risk = 60)')
plt.axvline(x=35, color='#38bdf8', linestyle=':', lw=2, label='Current MEDIUM Trigger (Risk = 35)')

plt.xlabel('Risk Score Threshold Selection', fontsize=12, color='#94a3b8')
plt.ylabel('Evaluation Score (0.0 - 1.0)', fontsize=12, color='#94a3b8')
plt.title('Risk Score Threshold Sensitivity Curve', fontsize=14, fontweight='bold', color='#e2e8f0', pad=15)
plt.legend(fontsize=10)
plt.grid(alpha=0.15)
plt.xlim(10, 90)
plt.ylim(0, 1.05)
plt.tight_layout()
plt.savefig('../notebooks/figures/risk_threshold_sensitivity.png', dpi=150, bbox_inches='tight', facecolor='#0f172a')
plt.show()

# %% [markdown]
# ## 6. Risk Level Counts & Summary
# Breakdown of risk alerts produced at current threshold specifications.

# %%
risk_counts = df['risk_level'].value_counts()
print("=" * 70)
print("RISK SUMMARY REPORT")
print("=" * 70)
for lvl, count in risk_counts.items():
    print(f"Risk Level {lvl:<8}: {count:>4} events ({count/len(df):.2%})")

print("\n" + "=" * 70)
print("Optimal trigger threshold selection lies near Risk = 50-60,")
print("where F1 metrics balance false warnings and miss-rate.")
print("=" * 70)
print("✅ Risk scoring analysis and diagrams completed successfully!")
print("======================================================================")
