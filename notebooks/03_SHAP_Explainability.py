# %% [markdown]
# # Notebook 3: Explainable AI (XAI) using SHAP
# ## Explainable Insider Threat Intelligence Platform
#
# Generates model explanations using **SHAP (SHapley Additive exPlanations)**.
# Key visualizations:
# - Global Feature Importance (Beeswarm and Bar plots)
# - Local Interpretability (Waterfall plots for High-Risk & Low-Risk users)
# - Feature Dependence analysis (interplay between activity metrics)

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
# ## 2. Load Pretrained Random Forest Model & Data

# %%
import joblib
from ml.preprocessing import run_preprocessing_pipeline

# Check if model exists
model_path = '../backend/ml/saved_models/random_forest.joblib'
if not os.path.exists(model_path):
    print("⚠️ Pretrained Random Forest model not found. Training one now...")
    from ml.train_rf import train_random_forest
    dataset_path = '../dataset/synthetic_insider_threat.csv'
    X_train, X_test, y_train, y_test, feature_names = run_preprocessing_pipeline(dataset_path)
    rf_model, _ = train_random_forest(X_train, y_train, X_test, y_test, feature_names)
else:
    print("✅ Loading pretrained Random Forest model...")
    rf_model = joblib.load(model_path)
    dataset_path = '../dataset/synthetic_insider_threat.csv'
    X_train, X_test, y_train, y_test, feature_names = run_preprocessing_pipeline(dataset_path)

# Convert testing sets to Pandas DataFrames for clearer labels in SHAP
X_test_df = pd.DataFrame(X_test, columns=feature_names)
print(f"Loaded {X_test_df.shape[0]} test samples with {len(feature_names)} features.")

# %% [markdown]
# ## 3. Compute SHAP Values

# %%
import shap

print("Computing SHAP values using TreeExplainer...")
# Use TreeExplainer for tree-based ensemble models
explainer = shap.TreeExplainer(rf_model)
# Calculate SHAP values for test dataset
shap_values = explainer(X_test_df)

# For classification, shape of SHAP values is [samples, features, classes]
# We extract the SHAP values for the positive class (insider threat class = index 1)
if len(shap_values.shape) == 3:
    # shape: (n_samples, n_features, 2) -> extract class 1
    class_1_shap_values = shap_values[:, :, 1]
else:
    class_1_shap_values = shap_values

print("✅ SHAP computation complete!")
print("SHAP values shape:", class_1_shap_values.shape)

# %% [markdown]
# ## 4. Global Interpretability: SHAP Beeswarm Plot
# The beeswarm plot shows how high and low values of each feature affect the threat probability.

# %%
plt.figure(figsize=(10, 6), facecolor='#0f172a')
# Render beeswarm using shap API
shap.plots.beeswarm(class_1_shap_values, max_display=10, show=False)
plt.title("SHAP Global Feature Importance (Beeswarm Plot)", fontsize=14, fontweight='bold', color='#e2e8f0', pad=20)
plt.tight_layout()
plt.savefig('../notebooks/figures/shap_beeswarm.png', dpi=150, bbox_inches='tight', facecolor='#0f172a')
plt.show()

# %% [markdown]
# ## 5. Global Interpretability: SHAP Feature Importance Bar Chart
# Average absolute SHAP values across all samples represent global feature contribution.

# %%
plt.figure(figsize=(10, 6), facecolor='#0f172a')
shap.plots.bar(class_1_shap_values, max_display=10, show=False)
plt.title("SHAP Global Feature Importance (Mean Absolute SHAP)", fontsize=14, fontweight='bold', color='#e2e8f0', pad=20)
plt.tight_layout()
plt.savefig('../notebooks/figures/shap_global_bar.png', dpi=150, bbox_inches='tight', facecolor='#0f172a')
plt.show()

# %% [markdown]
# ## 6. Local Interpretability: High-Risk User Explanation (Waterfall)
# Explains a specific user identified as a threat. We see exactly which behaviors pushed their score up.

# %%
# Find indices of high-risk threat users in our test set
threat_indices = np.where(y_test == 1)[0]
if len(threat_indices) > 0:
    target_idx = threat_indices[0]
    print(f"Explaining High-Risk User at test index {target_idx}:")
    
    plt.figure(figsize=(10, 6), facecolor='#0f172a')
    shap.plots.waterfall(class_1_shap_values[target_idx], max_display=10, show=False)
    plt.title(f"SHAP Threat Explanation — User #{target_idx}", fontsize=14, fontweight='bold', color='#e2e8f0', pad=20)
    plt.tight_layout()
    plt.savefig('../notebooks/figures/shap_waterfall_threat.png', dpi=150, bbox_inches='tight', facecolor='#0f172a')
    plt.show()
else:
    print("No threat samples found in the test subset.")

# %% [markdown]
# ## 7. Local Interpretability: Low-Risk User Explanation (Waterfall)
# Explains a normal user, showing how normal features push their score below the baseline.

# %%
normal_indices = np.where(y_test == 0)[0]
if len(normal_indices) > 0:
    target_idx = normal_indices[0]
    print(f"Explaining Low-Risk (Normal) User at test index {target_idx}:")
    
    plt.figure(figsize=(10, 6), facecolor='#0f172a')
    shap.plots.waterfall(class_1_shap_values[target_idx], max_display=10, show=False)
    plt.title(f"SHAP Normal Explanation — User #{target_idx}", fontsize=14, fontweight='bold', color='#e2e8f0', pad=20)
    plt.tight_layout()
    plt.savefig('../notebooks/figures/shap_waterfall_normal.png', dpi=150, bbox_inches='tight', facecolor='#0f172a')
    plt.show()
else:
    print("No normal samples found in the test subset.")

# %% [markdown]
# ## 8. Feature Dependence Analysis
# Looks at the relationship between values of top features and their SHAP values. 
# Also helps show interaction effects when another variable is used for coloring.

# %%
# Identify top features
top_features = ['usb_transfer_count', 'login_frequency', 'file_download_volume']

for feature in top_features:
    if feature in feature_names:
        plt.figure(figsize=(8, 5), facecolor='#0f172a')
        shap.plots.scatter(class_1_shap_values[:, feature], color=class_1_shap_values[:, 'after_hours_events'], show=False)
        plt.title(f"SHAP Dependence Plot: {feature}", fontsize=13, fontweight='bold', color='#e2e8f0', pad=15)
        plt.tight_layout()
        plt.savefig(f'../notebooks/figures/shap_dependence_{feature}.png', dpi=150, bbox_inches='tight', facecolor='#0f172a')
        plt.show()

# %% [markdown]
# ## 9. Technical Summary
# Summary of the SHAP explanations and explainability patterns.

# %%
print("=" * 70)
print("EXPLAINABILITY (SHAP) REPORT SUMMARY")
print("=" * 70)
# Extract and display top features by mean absolute SHAP
mean_shap = np.abs(class_1_shap_values.values).mean(axis=0)
shap_imp_df = pd.DataFrame({
    'Feature': feature_names,
    'Mean |SHAP|': mean_shap
}).sort_values(by='Mean |SHAP|', ascending=False)

print(shap_imp_df.to_string(index=False))
print("\n" + "=" * 70)
print("✅ SHAP explainability analyses and figures saved successfully!")
print("======================================================================")
