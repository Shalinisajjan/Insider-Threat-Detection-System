# %% [markdown]
# # Notebook 1: Exploratory Data Analysis & Feature Engineering
# ## Explainable Insider Threat Intelligence Platform
# **Dataset:** CERT Insider Threat Dataset r4.2 (Synthetic Version)
# 
# This notebook performs comprehensive EDA on the synthetic CERT insider threat dataset,
# analyzes feature distributions, correlations, and validates the feature engineering pipeline.

# %% [markdown]
# ## 1. Setup & Imports

# %%
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from sklearn.preprocessing import StandardScaler
import warnings
warnings.filterwarnings('ignore')

# Plotting style
plt.style.use('dark_background')
sns.set_palette("viridis")
plt.rcParams.update({
    'figure.facecolor': '#0f172a',
    'axes.facecolor': '#1e293b',
    'axes.edgecolor': '#334155',
    'text.color': '#e2e8f0',
    'axes.labelcolor': '#94a3b8',
    'xtick.color': '#64748b',
    'ytick.color': '#64748b',
    'grid.color': '#1e293b',
    'figure.figsize': (14, 6),
})

print("✅ Imports complete")

# %% [markdown]
# ## 2. Load Dataset

# %%
import os
import sys
sys.path.insert(0, '../backend')
sys.path.insert(0, '../dataset')

# Try to load existing dataset or generate it
dataset_path = '../dataset/synthetic_insider_threat.csv'
if not os.path.exists(dataset_path):
    print("Generating synthetic dataset...")
    from generate_synthetic import generate_dataset, save_dataset
    df_raw = generate_dataset(n_normal=1500, n_malicious=150)
    save_dataset(df_raw, dataset_path)
    print(f"✅ Dataset generated: {len(df_raw)} records")
else:
    df_raw = pd.read_csv(dataset_path)
    print(f"✅ Dataset loaded: {df_raw.shape[0]} rows × {df_raw.shape[1]} columns")

df_raw.head(5)

# %% [markdown]
# ## 3. Dataset Overview

# %%
print("=" * 60)
print("DATASET OVERVIEW")
print("=" * 60)
print(f"\nShape: {df_raw.shape}")
print(f"\nClass Distribution:")
class_counts = df_raw['label'].value_counts()
print(class_counts)
print(f"\nImbalance Ratio: {class_counts[0]/class_counts[1]:.1f}:1 (Normal:Threat)")

# %%
# Basic statistics
print("\nFeature Statistics:")
df_raw.describe().round(2)

# %%
# Missing values check
missing = df_raw.isnull().sum()
print("Missing Values:")
print(missing[missing > 0] if missing.any() else "✅ No missing values found")

# %% [markdown]
# ## 4. Class Distribution Visualization

# %%
fig, axes = plt.subplots(1, 2, figsize=(14, 5))

# Pie chart
colors = ['#10b981', '#ef4444']
axes[0].pie(class_counts.values, labels=['Normal', 'Insider Threat'],
            colors=colors, autopct='%1.1f%%', startangle=90,
            wedgeprops=dict(edgecolor='#0f172a', linewidth=2))
axes[0].set_title('Class Distribution', fontsize=14, fontweight='bold', color='#e2e8f0', pad=15)

# Bar chart
bars = axes[1].bar(['Normal (0)', 'Insider Threat (1)'], class_counts.values,
                   color=colors, edgecolor='#0f172a', linewidth=1.5, width=0.5)
axes[1].set_title('Absolute Count by Class', fontsize=14, fontweight='bold', color='#e2e8f0')
axes[1].set_ylabel('Count', color='#94a3b8')
for bar in bars:
    axes[1].text(bar.get_x() + bar.get_width() / 2., bar.get_height() + 5,
                 str(int(bar.get_height())), ha='center', va='bottom', color='#e2e8f0', fontweight='bold')

plt.tight_layout()
plt.savefig('../notebooks/figures/class_distribution.png', dpi=150, bbox_inches='tight', facecolor='#0f172a')
plt.show()

# %% [markdown]
# ## 5. Feature Distribution Analysis

# %%
FEATURES = [
    'login_frequency', 'late_night_logins', 'failed_login_count',
    'file_download_volume', 'usb_transfer_count', 'suspicious_url_count',
    'bulk_file_copy_count', 'after_hours_events', 'sensitive_file_accesses',
    'external_transfers', 'anomaly_ratio'
]

FEATURE_DISPLAY = {
    'login_frequency': 'Login Frequency',
    'late_night_logins': 'Late Night Logins',
    'failed_login_count': 'Failed Login Count',
    'file_download_volume': 'File Download Volume (MB)',
    'usb_transfer_count': 'USB Transfer Count',
    'suspicious_url_count': 'Suspicious URL Visits',
    'bulk_file_copy_count': 'Bulk File Copy Ops',
    'after_hours_events': 'After-Hours Events',
    'sensitive_file_accesses': 'Sensitive File Accesses',
    'external_transfers': 'External Transfers',
    'anomaly_ratio': 'Behavioral Anomaly Ratio'
}

# %%
fig, axes = plt.subplots(4, 3, figsize=(18, 16))
axes = axes.flatten()

normal = df_raw[df_raw['label'] == 0]
threat = df_raw[df_raw['label'] == 1]

for i, feat in enumerate(FEATURES):
    ax = axes[i]
    ax.hist(normal[feat], bins=30, alpha=0.6, color='#10b981', label='Normal', density=True)
    ax.hist(threat[feat], bins=30, alpha=0.6, color='#ef4444', label='Insider Threat', density=True)
    ax.set_title(FEATURE_DISPLAY[feat], fontsize=10, fontweight='bold', color='#e2e8f0')
    ax.legend(fontsize=8)
    ax.set_ylabel('Density', fontsize=8)

# Hide last empty subplot
axes[-1].set_visible(False)

plt.suptitle('Feature Distributions: Normal vs. Insider Threat', fontsize=16, fontweight='bold', 
             color='#e2e8f0', y=1.02)
plt.tight_layout()
plt.savefig('../notebooks/figures/feature_distributions.png', dpi=150, bbox_inches='tight', facecolor='#0f172a')
plt.show()

# %% [markdown]
# ## 6. Correlation Heatmap

# %%
plt.figure(figsize=(14, 10))
corr = df_raw[FEATURES + ['label']].corr()
mask = np.triu(np.ones_like(corr, dtype=bool))

cmap = sns.diverging_palette(240, 10, as_cmap=True)
sns.heatmap(corr, mask=mask, annot=True, fmt='.2f', cmap=cmap, center=0,
            linewidths=0.5, cbar_kws={"shrink": 0.8},
            annot_kws={'size': 8},
            xticklabels=[FEATURE_DISPLAY.get(f, f) for f in corr.columns],
            yticklabels=[FEATURE_DISPLAY.get(f, f) for f in corr.index])
plt.title('Feature Correlation Matrix', fontsize=14, fontweight='bold', color='#e2e8f0', pad=15)
plt.xticks(rotation=45, ha='right', fontsize=8)
plt.yticks(fontsize=8)
plt.tight_layout()
plt.savefig('../notebooks/figures/correlation_heatmap.png', dpi=150, bbox_inches='tight', facecolor='#0f172a')
plt.show()

# %% [markdown]
# ## 7. Feature Importance (Correlation with Label)

# %%
correlations_with_label = df_raw[FEATURES].corrwith(df_raw['label']).abs().sort_values(ascending=True)

plt.figure(figsize=(12, 6))
colors_bar = ['#ef4444' if c > 0.5 else '#f59e0b' if c > 0.3 else '#6366f1' 
              for c in correlations_with_label.values]
bars = plt.barh([FEATURE_DISPLAY.get(f, f) for f in correlations_with_label.index], 
                correlations_with_label.values, color=colors_bar, edgecolor='#0f172a')

plt.xlabel('Absolute Correlation with Label', fontsize=12, color='#94a3b8')
plt.title('Feature Correlation with Insider Threat Label', fontsize=14, fontweight='bold', color='#e2e8f0')
plt.axvline(x=0.5, color='#ef4444', linestyle='--', alpha=0.5, label='High Correlation (>0.5)')
plt.axvline(x=0.3, color='#f59e0b', linestyle='--', alpha=0.5, label='Medium Correlation (>0.3)')
plt.legend(fontsize=9)
plt.tight_layout()
plt.savefig('../notebooks/figures/feature_correlation_with_label.png', dpi=150, bbox_inches='tight', facecolor='#0f172a')
plt.show()

print("\nTop 5 Most Predictive Features:")
for feat, corr_val in correlations_with_label.sort_values(ascending=False).head(5).items():
    print(f"  {FEATURE_DISPLAY.get(feat, feat)}: {corr_val:.3f}")

# %% [markdown]
# ## 8. Feature Engineering Analysis

# %%
print("=" * 60)
print("FEATURE ENGINEERING SUMMARY")
print("=" * 60)

print("\n📊 Feature Statistics by Class:")
stats = df_raw.groupby('label')[FEATURES].agg(['mean', 'std', 'max'])
for feat in FEATURES[:5]:
    print(f"\n{FEATURE_DISPLAY.get(feat, feat)}:")
    print(f"  Normal:  mean={stats.loc[0, (feat, 'mean')]:.2f}, std={stats.loc[0, (feat, 'std')]:.2f}")
    print(f"  Threat:  mean={stats.loc[1, (feat, 'mean')]:.2f}, std={stats.loc[1, (feat, 'std')]:.2f}")
    ratio = stats.loc[1, (feat, 'mean')] / max(stats.loc[0, (feat, 'mean')], 0.001)
    print(f"  Ratio (Threat/Normal): {ratio:.1f}x")

# %%
# Feature scaling analysis
scaler = StandardScaler()
X = df_raw[FEATURES].values
X_scaled = scaler.fit_transform(X)

print("\n✅ Feature scaling (StandardScaler) applied")
print(f"  Scaled feature range: [{X_scaled.min():.2f}, {X_scaled.max():.2f}]")
print(f"  Mean (should be ~0): {X_scaled.mean():.4f}")
print(f"  Std  (should be ~1): {X_scaled.std():.4f}")

# %% [markdown]
# ## 9. Outlier Analysis

# %%
from scipy import stats as scipy_stats

print("Outlier Detection (Z-score > 3):")
for feat in FEATURES:
    z_scores = np.abs(scipy_stats.zscore(df_raw[feat]))
    n_outliers = (z_scores > 3).sum()
    print(f"  {FEATURE_DISPLAY.get(feat, feat)}: {n_outliers} outliers ({n_outliers/len(df_raw)*100:.1f}%)")

# %% [markdown]
# ## 10. Summary

# %%
print("=" * 60)
print("EDA SUMMARY")
print("=" * 60)
print(f"""
Dataset: CERT Insider Threat Dataset (Synthetic) r4.2
Shape: {df_raw.shape[0]} samples × {df_raw.shape[1]} features
Normal samples: {class_counts[0]} ({class_counts[0]/len(df_raw)*100:.1f}%)
Threat samples: {class_counts[1]} ({class_counts[1]/len(df_raw)*100:.1f}%)
Imbalance ratio: {class_counts[0]/class_counts[1]:.0f}:1

Key Findings:
1. USB transfers, sensitive file accesses, and external transfers 
   are the most discriminative features
2. Insider threats show significantly higher after-hours activity 
   (mean: {stats.loc[1, ('after_hours_events', 'mean')]:.1f}x vs Normal: {stats.loc[0, ('after_hours_events', 'mean')]:.1f}x)
3. The dataset has class imbalance — models must use class_weight='balanced'
4. All features are on different scales — StandardScaler is essential
5. Low inter-feature correlation — good for independent signal
""")
