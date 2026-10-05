# %% [markdown]
# # Notebook 2: ML Model Training & Evaluation
# ## Explainable Insider Threat Intelligence Platform
#
# Trains and evaluates four ML models:
# - **Random Forest** (Classification)
# - **XGBoost** (Gradient Boosting)
# - **Isolation Forest** (Anomaly Detection)
# - **LSTM** (Deep Learning, Sequential)
#
# Compares all models using Accuracy, Precision, Recall, F1, and ROC-AUC.

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
import matplotlib.patches as mpatches
import seaborn as sns
from sklearn.metrics import (
    classification_report, confusion_matrix, roc_auc_score,
    f1_score, accuracy_score, precision_score, recall_score,
    roc_curve, auc
)
import warnings
warnings.filterwarnings('ignore')

plt.style.use('dark_background')
plt.rcParams.update({
    'figure.facecolor': '#0f172a', 'axes.facecolor': '#1e293b',
    'axes.edgecolor': '#334155', 'text.color': '#e2e8f0',
    'axes.labelcolor': '#94a3b8', 'xtick.color': '#64748b',
    'ytick.color': '#64748b',
})

print("✅ Setup complete")

# %% [markdown]
# ## 2. Load & Preprocess Data

# %%
from ml.preprocessing import run_preprocessing_pipeline

dataset_path = '../dataset/synthetic_insider_threat.csv'
X_train, X_test, y_train, y_test, feature_names = run_preprocessing_pipeline(dataset_path)

print(f"Training samples: {len(X_train)} | Test samples: {len(X_test)}")
print(f"Threat rate (train): {y_train.mean():.2%} | Threat rate (test): {y_test.mean():.2%}")
print(f"Features ({len(feature_names)}): {feature_names}")

# %% [markdown]
# ## 3. Train Random Forest

# %%
from ml.train_rf import train_random_forest

print("Training Random Forest...")
rf_model, rf_metrics = train_random_forest(X_train, y_train, X_test, y_test, feature_names)
y_pred_rf = rf_model.predict(X_test)
y_proba_rf = rf_model.predict_proba(X_test)[:, 1]
print(f"✅ RF — Accuracy: {rf_metrics['accuracy']:.4f} | F1: {rf_metrics['f1_score']:.4f} | ROC-AUC: {rf_metrics['roc_auc']:.4f}")

# %% [markdown]
# ## 4. Train XGBoost

# %%
from ml.train_xgboost import train_xgboost

print("Training XGBoost...")
xgb_model, xgb_metrics = train_xgboost(X_train, y_train, X_test, y_test, feature_names)
y_pred_xgb = xgb_model.predict(X_test)
y_proba_xgb = xgb_model.predict_proba(X_test)[:, 1]
print(f"✅ XGB — Accuracy: {xgb_metrics['accuracy']:.4f} | F1: {xgb_metrics['f1_score']:.4f} | ROC-AUC: {xgb_metrics['roc_auc']:.4f}")

# %% [markdown]
# ## 5. Train Isolation Forest (Anomaly Detection)

# %%
from ml.train_isolation_forest import train_isolation_forest

print("Training Isolation Forest...")
iso_model, iso_metrics = train_isolation_forest(X_train, X_test, y_test)
print(f"✅ ISO — Accuracy: {iso_metrics.get('accuracy', 'N/A')} | F1: {iso_metrics.get('f1_score', 'N/A')}")

# %% [markdown]
# ## 6. Train LSTM (Deep Learning)

# %%
lstm_model = None
lstm_metrics = {}
try:
    from ml.train_lstm import train_lstm
    print("Training LSTM (this may take 1-3 minutes)...")
    lstm_model, lstm_metrics = train_lstm(X_train, y_train, X_test, y_test, epochs=20, batch_size=32)
    if lstm_model:
        print(f"✅ LSTM — Accuracy: {lstm_metrics.get('accuracy', 'N/A'):.4f}")
    else:
        print("⚠️  LSTM training skipped")
except Exception as e:
    print(f"⚠️  LSTM not available: {e}")

# %% [markdown]
# ## 7. Model Comparison Table

# %%
results = []

def add_result(name, y_true, y_pred, y_proba=None, extra_metrics=None):
    row = {
        'Model': name,
        'Accuracy': accuracy_score(y_true, y_pred) * 100,
        'Precision': precision_score(y_true, y_pred, zero_division=0) * 100,
        'Recall': recall_score(y_true, y_pred, zero_division=0) * 100,
        'F1 Score': f1_score(y_true, y_pred, zero_division=0) * 100,
    }
    if y_proba is not None:
        row['ROC-AUC'] = roc_auc_score(y_true, y_proba) * 100
    else:
        row['ROC-AUC'] = None
    if extra_metrics:
        row.update(extra_metrics)
    results.append(row)

add_result('Random Forest', y_test, y_pred_rf, y_proba_rf)
add_result('XGBoost', y_test, y_pred_xgb, y_proba_xgb)

# Isolation Forest — convert -1/1 anomaly scores to 0/1
if iso_model:
    iso_raw = iso_model.predict(X_test)
    y_pred_iso = (iso_raw == -1).astype(int)
    iso_scores = -iso_model.decision_function(X_test)
    add_result('Isolation Forest', y_test, y_pred_iso, iso_scores)

# LSTM results
if lstm_metrics:
    results.append({
        'Model': 'LSTM',
        'Accuracy': lstm_metrics.get('accuracy', 0) * 100,
        'Precision': lstm_metrics.get('precision', 0) * 100,
        'Recall': lstm_metrics.get('recall', 0) * 100,
        'F1 Score': lstm_metrics.get('f1_score', 0) * 100,
        'ROC-AUC': lstm_metrics.get('roc_auc', 0) * 100,
    })

df_results = pd.DataFrame(results)
df_results = df_results.set_index('Model')
print("\n" + "=" * 70)
print("MODEL PERFORMANCE COMPARISON")
print("=" * 70)
print(df_results.round(2).to_string())

# %% [markdown]
# ## 8. Visualization: Model Comparison Bar Chart

# %%
metrics_to_plot = ['Accuracy', 'Precision', 'Recall', 'F1 Score', 'ROC-AUC']
models = df_results.index.tolist()
colors = ['#10b981', '#f59e0b', '#6366f1', '#ec4899']

x = np.arange(len(metrics_to_plot))
width = 0.2

fig, ax = plt.subplots(figsize=(16, 7))

for i, (model, color) in enumerate(zip(models, colors)):
    values = [df_results.loc[model, m] if pd.notna(df_results.loc[model, m]) else 0 
              for m in metrics_to_plot]
    bars = ax.bar(x + i * width, values, width, label=model, color=color, alpha=0.85, edgecolor='#0f172a')
    for bar, val in zip(bars, values):
        if val > 0:
            ax.text(bar.get_x() + bar.get_width() / 2., bar.get_height() + 0.3,
                    f'{val:.1f}', ha='center', va='bottom', fontsize=7, color='#94a3b8')

ax.set_ylabel('Score (%)', fontsize=12, color='#94a3b8')
ax.set_title('ML Model Performance Comparison', fontsize=14, fontweight='bold', color='#e2e8f0', pad=15)
ax.set_xticks(x + width * (len(models) - 1) / 2)
ax.set_xticklabels(metrics_to_plot, fontsize=11)
ax.set_ylim(80, 102)
ax.legend(fontsize=10)
ax.grid(axis='y', alpha=0.2)
ax.axhline(y=95, color='#6366f1', linestyle='--', alpha=0.4, label='95% threshold')
plt.tight_layout()
plt.savefig('../notebooks/figures/model_comparison.png', dpi=150, bbox_inches='tight', facecolor='#0f172a')
plt.show()

# %% [markdown]
# ## 9. ROC Curves

# %%
fig, ax = plt.subplots(figsize=(10, 7))

# RF ROC
fpr_rf, tpr_rf, _ = roc_curve(y_test, y_proba_rf)
ax.plot(fpr_rf, tpr_rf, color='#10b981', lw=2.5, label=f'Random Forest (AUC={roc_auc_score(y_test, y_proba_rf):.3f})')

# XGBoost ROC
fpr_xgb, tpr_xgb, _ = roc_curve(y_test, y_proba_xgb)
ax.plot(fpr_xgb, tpr_xgb, color='#f59e0b', lw=2.5, label=f'XGBoost (AUC={roc_auc_score(y_test, y_proba_xgb):.3f})')

# Isolation Forest ROC (if available)
if iso_model:
    iso_scores = -iso_model.decision_function(X_test)
    fpr_iso, tpr_iso, _ = roc_curve(y_test, iso_scores)
    ax.plot(fpr_iso, tpr_iso, color='#6366f1', lw=2.5, label=f'Isolation Forest (AUC={roc_auc_score(y_test, iso_scores):.3f})')

ax.plot([0, 1], [0, 1], color='#334155', lw=1.5, linestyle='--', label='Random Classifier')
ax.set_xlabel('False Positive Rate', fontsize=12, color='#94a3b8')
ax.set_ylabel('True Positive Rate', fontsize=12, color='#94a3b8')
ax.set_title('ROC Curves — Insider Threat Detection', fontsize=14, fontweight='bold', color='#e2e8f0', pad=15)
ax.legend(fontsize=10)
ax.grid(alpha=0.15)
ax.set_xlim([0, 1])
ax.set_ylim([0, 1.02])
plt.tight_layout()
plt.savefig('../notebooks/figures/roc_curves.png', dpi=150, bbox_inches='tight', facecolor='#0f172a')
plt.show()

# %% [markdown]
# ## 10. Confusion Matrices

# %%
fig, axes = plt.subplots(1, 3, figsize=(18, 5))

cm_configs = [
    ('Random Forest', y_pred_rf, '#10b981'),
    ('XGBoost', y_pred_xgb, '#f59e0b'),
]
if iso_model:
    iso_raw = iso_model.predict(X_test)
    y_pred_iso = (iso_raw == -1).astype(int)
    cm_configs.append(('Isolation Forest', y_pred_iso, '#6366f1'))

for ax, (name, y_pred, color) in zip(axes, cm_configs):
    cm = confusion_matrix(y_test, y_pred)
    sns.heatmap(cm, annot=True, fmt='d', cmap='Blues', ax=ax,
                cbar=False, linewidths=2, linecolor='#0f172a',
                xticklabels=['Normal', 'Threat'],
                yticklabels=['Normal', 'Threat'],
                annot_kws={'size': 14, 'weight': 'bold'})
    ax.set_title(f'{name}\nConfusion Matrix', fontsize=12, fontweight='bold', color='#e2e8f0')
    ax.set_xlabel('Predicted', fontsize=10, color='#94a3b8')
    ax.set_ylabel('Actual', fontsize=10, color='#94a3b8')

plt.suptitle('Confusion Matrices — All Models', fontsize=14, fontweight='bold', color='#e2e8f0', y=1.02)
plt.tight_layout()
plt.savefig('../notebooks/figures/confusion_matrices.png', dpi=150, bbox_inches='tight', facecolor='#0f172a')
plt.show()

# %% [markdown]
# ## 11. Feature Importance (Random Forest)

# %%
importances = rf_model.feature_importances_
indices = np.argsort(importances)[::-1]

plt.figure(figsize=(14, 6))
colors_bar = ['#ef4444' if i < 3 else '#f59e0b' if i < 6 else '#6366f1' for i in range(len(importances))]
bars = plt.bar(range(len(importances)), importances[indices], color=colors_bar, edgecolor='#0f172a', alpha=0.85)

plt.xticks(range(len(importances)), 
           [feature_names[i] for i in indices], 
           rotation=45, ha='right', fontsize=9)
plt.ylabel('Feature Importance (Gini)', fontsize=12, color='#94a3b8')
plt.title('Random Forest — Feature Importance', fontsize=14, fontweight='bold', color='#e2e8f0', pad=15)

high = mpatches.Patch(color='#ef4444', label='Top 3')
med = mpatches.Patch(color='#f59e0b', label='4–6')
low = mpatches.Patch(color='#6366f1', label='7+')
plt.legend(handles=[high, med, low], fontsize=9)
plt.tight_layout()
plt.savefig('../notebooks/figures/feature_importance_rf.png', dpi=150, bbox_inches='tight', facecolor='#0f172a')
plt.show()

# %% [markdown]
# ## 12. Summary Report

# %%
print("=" * 70)
print("FINAL MODEL EVALUATION SUMMARY")
print("=" * 70)
print(df_results.round(2).to_string())

best_f1 = df_results['F1 Score'].idxmax()
best_auc = df_results['ROC-AUC'].dropna().idxmax()
print(f"\n🏆 Best F1 Score: {best_f1} ({df_results.loc[best_f1, 'F1 Score']:.2f}%)")
print(f"🏆 Best ROC-AUC: {best_auc} ({df_results.loc[best_auc, 'ROC-AUC']:.2f}%)")
print("\n✅ All models trained and saved to backend/ml/saved_models/")
