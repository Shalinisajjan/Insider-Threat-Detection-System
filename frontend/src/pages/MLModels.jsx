/**
 * pages/MLModels.jsx — Machine Learning Models status, comparison, and metrics.
 * Shows training metrics for RF, XGBoost, Isolation Forest, and LSTM.
 */
import { useState, useEffect } from 'react';
import {
  BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip,
  ResponsiveContainer, RadarChart, Radar, PolarGrid,
  PolarAngleAxis, PolarRadiusAxis, Cell,
} from 'recharts';
import { predictAPI, explainAPI } from '../api/axios';
import toast from 'react-hot-toast';

// ─── Static model comparison data (updated when models are trained) ───
const MODEL_DESCRIPTIONS = {
  random_forest: {
    name: 'Random Forest',
    icon: '🌲',
    color: '#10b981',
    description: 'Ensemble of decision trees using bootstrap aggregation. Excellent for handling imbalanced datasets with class_weight="balanced". Provides native feature importance and supports SHAP TreeExplainer.',
    type: 'Classification',
    use_case: 'Threat Classification',
    params: 'n_estimators=200, max_depth=20, class_weight=balanced',
  },
  xgboost: {
    name: 'XGBoost',
    icon: '⚡',
    color: '#f59e0b',
    description: 'Gradient boosting with extreme speed and regularization. Uses scale_pos_weight to handle class imbalance. Excellent ROC-AUC performance on tabular behavioral data.',
    type: 'Classification',
    use_case: 'Risk Prediction',
    params: 'n_estimators=300, max_depth=6, learning_rate=0.05',
  },
  isolation_forest: {
    name: 'Isolation Forest',
    icon: '🌳',
    color: '#6366f1',
    description: 'Unsupervised anomaly detection that isolates observations by randomly selecting features and split values. No labels needed — detects statistical outliers in behavior patterns.',
    type: 'Anomaly Detection',
    use_case: 'Zero-Day Anomaly',
    params: 'n_estimators=200, contamination=0.1, max_samples=auto',
  },
  lstm: {
    name: 'LSTM Network',
    icon: '🧠',
    color: '#ec4899',
    description: 'Long Short-Term Memory deep learning model for sequential behavior analysis. Captures temporal dependencies in user activity patterns across time windows.',
    type: 'Deep Learning',
    use_case: 'Sequential Analysis',
    params: 'layers=[64,32], dropout=0.3, epochs=20, batch_size=32',
  },
};

// Default metrics shown when no trained models exist
const DEFAULT_METRICS = [
  { model: 'Random Forest', accuracy: 96.8, precision: 95.2, recall: 97.1, f1: 96.1, roc_auc: 98.9, key: 'random_forest', trained: false },
  { model: 'XGBoost', accuracy: 97.2, precision: 96.8, recall: 96.5, f1: 96.6, roc_auc: 99.1, key: 'xgboost', trained: false },
  { model: 'Isolation Forest', accuracy: 91.4, precision: 88.7, recall: 93.2, f1: 90.9, roc_auc: 94.3, key: 'isolation_forest', trained: false },
  { model: 'LSTM', accuracy: 95.6, precision: 94.1, recall: 96.0, f1: 95.0, roc_auc: 97.8, key: 'lstm', trained: false },
];

const MetricBar = ({ value, max = 100, color }) => (
  <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
    <div style={{
      flex: 1, height: 6, background: 'rgba(255,255,255,0.06)', borderRadius: 3, overflow: 'hidden',
    }}>
      <div style={{
        height: '100%', width: `${(value / max) * 100}%`,
        background: color, borderRadius: 3,
        transition: 'width 0.8s ease',
      }} />
    </div>
    <span style={{ fontSize: 12, fontWeight: 700, color, minWidth: 38, textAlign: 'right' }}>
      {value.toFixed(1)}%
    </span>
  </div>
);

const CustomTooltip = ({ active, payload, label }) => {
  if (!active || !payload?.length) return null;
  return (
    <div style={{
      background: '#0f1e36', border: '1px solid rgba(99,102,241,0.3)',
      borderRadius: 8, padding: '10px 14px', fontSize: 12,
    }}>
      <div style={{ color: '#94a3b8', marginBottom: 4 }}>{label}</div>
      {payload.map((p, i) => (
        <div key={i} style={{ color: p.color || '#6366f1', fontWeight: 600 }}>
          {p.name}: {typeof p.value === 'number' ? p.value.toFixed(1) : p.value}%
        </div>
      ))}
    </div>
  );
};

export default function MLModels() {
  const [metrics, setMetrics] = useState(DEFAULT_METRICS);
  const [globalImportance, setGlobalImportance] = useState([]);
  const [modelInfo, setModelInfo] = useState(null);
  const [loading, setLoading] = useState(true);
  const [selectedModel, setSelectedModel] = useState('random_forest');

  useEffect(() => {
    fetchData();
  }, []);

  const fetchData = async () => {
    setLoading(true);
    try {
      const [infoRes, importanceRes] = await Promise.allSettled([
        predictAPI.getModelInfo(),
        explainAPI.getGlobalImportance(),
      ]);

      if (infoRes.status === 'fulfilled' && infoRes.value.data) {
        const info = infoRes.value.data;
        setModelInfo(info);
        // Merge with training summary if available
        if (info.training_summary) {
          const ts = info.training_summary;
          setMetrics(DEFAULT_METRICS.map(m => {
            const key = m.key;
            if (ts[key]) {
              return {
                ...m,
                accuracy: (ts[key].accuracy || m.accuracy / 100) * 100,
                f1: (ts[key].f1_score || m.f1 / 100) * 100,
                roc_auc: (ts[key].roc_auc || m.roc_auc / 100) * 100,
                trained: true,
              };
            }
            return m;
          }));
        }
      }

      if (importanceRes.status === 'fulfilled') {
        setGlobalImportance(importanceRes.value.data.feature_importance || []);
      }
    } catch {
      // Use default metrics
    } finally {
      setLoading(false);
    }
  };

  const sel = MODEL_DESCRIPTIONS[selectedModel];
  const selMetrics = metrics.find(m => m.key === selectedModel) || metrics[0];

  const radarData = metrics.map(m => ({
    model: m.model.split(' ')[0],
    Accuracy: m.accuracy,
    F1: m.f1,
    'ROC-AUC': m.roc_auc,
  }));

  const barData = metrics.map(m => ({
    name: m.model.split(' ').slice(0, 2).join(' '),
    Accuracy: m.accuracy,
    F1: m.f1,
    'ROC-AUC': m.roc_auc,
    color: MODEL_DESCRIPTIONS[m.key]?.color || '#6366f1',
  }));

  if (loading) {
    return (
      <div style={{ display: 'flex', justifyContent: 'center', padding: 80 }}>
        <div className="spinner" style={{ width: 40, height: 40 }} />
      </div>
    );
  }

  return (
    <div style={{ animation: 'fadeInUp 0.4s ease forwards' }}>
      {/* ─── Header ─────────────────────────────────────── */}
      <div className="page-header">
        <div>
          <h1 className="page-title">🤖 ML Models</h1>
          <p className="page-subtitle">Machine learning model performance, comparison metrics & SHAP feature importance</p>
        </div>
        <button className="btn btn-secondary btn-sm" onClick={fetchData}>🔄 Refresh</button>
      </div>

      {/* ─── Model Status Cards ────────────────────────── */}
      <div className="grid-4" style={{ marginBottom: 24 }}>
        {Object.entries(MODEL_DESCRIPTIONS).map(([key, info]) => {
          const m = metrics.find(x => x.key === key);
          const isSelected = selectedModel === key;
          return (
            <div
              key={key}
              className="card"
              style={{
                cursor: 'pointer',
                borderColor: isSelected ? `${info.color}60` : 'rgba(255,255,255,0.06)',
                boxShadow: isSelected ? `0 0 20px ${info.color}20` : 'none',
              }}
              onClick={() => setSelectedModel(key)}
            >
              <div style={{ display: 'flex', alignItems: 'center', gap: 10, marginBottom: 12 }}>
                <span style={{ fontSize: 24 }}>{info.icon}</span>
                <div>
                  <div style={{ fontSize: 14, fontWeight: 700, color: '#e2e8f0' }}>{info.name}</div>
                  <div style={{ fontSize: 10, color: info.color, fontWeight: 600, textTransform: 'uppercase' }}>
                    {info.type}
                  </div>
                </div>
                <div style={{
                  marginLeft: 'auto',
                  width: 8, height: 8, borderRadius: '50%',
                  background: m?.trained ? '#10b981' : '#f59e0b',
                  boxShadow: `0 0 6px ${m?.trained ? '#10b981' : '#f59e0b'}`,
                }} title={m?.trained ? 'Trained' : 'Demo metrics'} />
              </div>
              <div style={{ fontSize: 13, color: '#64748b', marginBottom: 12, lineHeight: 1.5 }}>
                {info.use_case}
              </div>
              {m && (
                <div style={{ display: 'flex', flexDirection: 'column', gap: 6 }}>
                  <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: 11, color: '#475569', marginBottom: 2 }}>
                    <span>ROC-AUC</span><span style={{ color: info.color, fontWeight: 700 }}>{m.roc_auc.toFixed(1)}%</span>
                  </div>
                  <MetricBar value={m.roc_auc} color={info.color} />
                  <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: 11, color: '#475569', marginTop: 4 }}>
                    <span>F1 Score</span><span style={{ color: info.color, fontWeight: 700 }}>{m.f1.toFixed(1)}%</span>
                  </div>
                  <MetricBar value={m.f1} color={info.color} />
                </div>
              )}
            </div>
          );
        })}
      </div>

      {/* ─── Selected Model Deep Dive ──────────────────── */}
      <div className="grid-2" style={{ marginBottom: 24 }}>
        {/* Info card */}
        <div className="card">
          <div style={{ display: 'flex', alignItems: 'center', gap: 12, marginBottom: 16 }}>
            <span style={{ fontSize: 32 }}>{sel.icon}</span>
            <div>
              <div style={{ fontSize: 18, fontWeight: 800, color: '#e2e8f0' }}>{sel.name}</div>
              <div style={{ fontSize: 12, color: sel.color, fontWeight: 600 }}>{sel.type} · {sel.use_case}</div>
            </div>
          </div>
          <p style={{ fontSize: 13, color: '#94a3b8', lineHeight: 1.7, marginBottom: 16 }}>
            {sel.description}
          </p>
          <div style={{
            padding: '10px 14px',
            background: 'rgba(255,255,255,0.03)',
            border: '1px solid rgba(255,255,255,0.06)',
            borderRadius: 8,
            fontSize: 11, fontFamily: 'monospace', color: '#64748b',
          }}>
            <span style={{ color: '#6366f1', fontWeight: 700 }}>Params:</span> {sel.params}
          </div>
        </div>

        {/* Metrics breakdown */}
        <div className="card">
          <div className="chart-title">📊 {selMetrics.model} — Full Metrics</div>
          <div style={{ display: 'flex', flexDirection: 'column', gap: 14 }}>
            {[
              { label: 'Accuracy', value: selMetrics.accuracy },
              { label: 'Precision', value: selMetrics.precision },
              { label: 'Recall', value: selMetrics.recall },
              { label: 'F1 Score', value: selMetrics.f1 },
              { label: 'ROC-AUC', value: selMetrics.roc_auc },
            ].map(({ label, value }) => (
              <div key={label}>
                <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: 12, marginBottom: 4 }}>
                  <span style={{ color: '#94a3b8' }}>{label}</span>
                  <span style={{ color: sel.color, fontWeight: 700 }}>{value?.toFixed(1) || '—'}%</span>
                </div>
                <MetricBar value={value || 0} color={sel.color} />
              </div>
            ))}
          </div>
          {!selMetrics.trained && (
            <div style={{
              marginTop: 12, fontSize: 11, color: '#f59e0b',
              background: 'rgba(245,158,11,0.08)', border: '1px solid rgba(245,158,11,0.2)',
              borderRadius: 6, padding: '6px 10px',
            }}>
              ⚠️ Showing expected demo metrics. Run training scripts to see real values.
            </div>
          )}
        </div>
      </div>

      {/* ─── Comparison Bar Chart ──────────────────────── */}
      <div className="chart-container" style={{ marginBottom: 24 }}>
        <div className="chart-title">📈 Model Performance Comparison</div>
        <ResponsiveContainer width="100%" height={280}>
          <BarChart data={barData} barSize={20} barGap={4}>
            <CartesianGrid strokeDasharray="3 3" stroke="rgba(255,255,255,0.04)" />
            <XAxis dataKey="name" tick={{ fontSize: 11, fill: '#94a3b8' }} />
            <YAxis domain={[85, 100]} tick={{ fontSize: 10, fill: '#475569' }} />
            <Tooltip content={<CustomTooltip />} />
            <Bar dataKey="Accuracy" fill="#6366f1" radius={[3, 3, 0, 0]}>
              {barData.map((entry, i) => (
                <Cell key={i} fill={`${entry.color}cc`} />
              ))}
            </Bar>
            <Bar dataKey="F1" fill="#10b981" radius={[3, 3, 0, 0]}>
              {barData.map((entry, i) => (
                <Cell key={i} fill={`${entry.color}88`} />
              ))}
            </Bar>
            <Bar dataKey="ROC-AUC" fill="#f59e0b" radius={[3, 3, 0, 0]}>
              {barData.map((entry, i) => (
                <Cell key={i} fill={`${entry.color}55`} />
              ))}
            </Bar>
          </BarChart>
        </ResponsiveContainer>
        <div style={{ display: 'flex', gap: 20, justifyContent: 'center', marginTop: 8 }}>
          {[
            { label: 'Accuracy', color: 'opacity 0.8' },
            { label: 'F1 Score', color: 'opacity 0.55' },
            { label: 'ROC-AUC', color: 'opacity 0.35' },
          ].map(({ label }) => (
            <div key={label} style={{ display: 'flex', alignItems: 'center', gap: 6, fontSize: 11, color: '#64748b' }}>
              <div style={{ width: 10, height: 10, background: '#6366f1', borderRadius: 2 }} />
              {label}
            </div>
          ))}
        </div>
      </div>

      {/* ─── Comparison Table ──────────────────────────── */}
      <div className="card" style={{ padding: 0, overflow: 'hidden', marginBottom: 24 }}>
        <div style={{ padding: '16px 20px', borderBottom: '1px solid rgba(255,255,255,0.06)' }}>
          <div className="chart-title" style={{ margin: 0 }}>📋 Model Evaluation Summary Table</div>
        </div>
        <table className="data-table">
          <thead>
            <tr>
              <th>Model</th>
              <th>Type</th>
              <th>Accuracy</th>
              <th>Precision</th>
              <th>Recall</th>
              <th>F1 Score</th>
              <th>ROC-AUC</th>
              <th>Status</th>
            </tr>
          </thead>
          <tbody>
            {metrics.map((m) => {
              const info = MODEL_DESCRIPTIONS[m.key];
              return (
                <tr key={m.key} style={{ cursor: 'pointer' }} onClick={() => setSelectedModel(m.key)}>
                  <td>
                    <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
                      <span>{info?.icon}</span>
                      <span style={{ fontWeight: 600 }}>{m.model}</span>
                    </div>
                  </td>
                  <td><span style={{ fontSize: 11, color: info?.color }}>{info?.type}</span></td>
                  <td><span style={{ color: '#e2e8f0', fontWeight: 600 }}>{m.accuracy.toFixed(1)}%</span></td>
                  <td><span style={{ color: '#e2e8f0' }}>{m.precision?.toFixed(1) || '—'}%</span></td>
                  <td><span style={{ color: '#e2e8f0' }}>{m.recall?.toFixed(1) || '—'}%</span></td>
                  <td>
                    <span style={{ fontWeight: 700, color: info?.color }}>{m.f1.toFixed(1)}%</span>
                  </td>
                  <td>
                    <span style={{
                      fontWeight: 800, color: m.roc_auc >= 98 ? '#10b981' : m.roc_auc >= 95 ? '#f59e0b' : '#ef4444',
                    }}>{m.roc_auc.toFixed(1)}%</span>
                  </td>
                  <td>
                    <span style={{
                      fontSize: 10, fontWeight: 600, padding: '2px 8px', borderRadius: 10,
                      background: m.trained ? 'rgba(16,185,129,0.15)' : 'rgba(245,158,11,0.15)',
                      color: m.trained ? '#10b981' : '#f59e0b',
                    }}>
                      {m.trained ? '✅ Trained' : '📊 Demo'}
                    </span>
                  </td>
                </tr>
              );
            })}
          </tbody>
        </table>
      </div>

      {/* ─── SHAP Global Feature Importance ───────────── */}
      {globalImportance.length > 0 && (
        <div className="chart-container" style={{ marginBottom: 24 }}>
          <div className="chart-title">🧠 SHAP Global Feature Importance (Random Forest)</div>
          <div style={{ display: 'flex', flexDirection: 'column', gap: 10, marginTop: 8 }}>
            {globalImportance.map((feat, i) => (
              <div key={i} style={{ display: 'flex', alignItems: 'center', gap: 12 }}>
                <div style={{ width: 200, fontSize: 12, color: '#94a3b8', flexShrink: 0, textAlign: 'right' }}>
                  {feat.feature_name}
                </div>
                <div style={{ flex: 1, height: 20, background: 'rgba(255,255,255,0.04)', borderRadius: 4, overflow: 'hidden' }}>
                  <div style={{
                    height: '100%', width: `${feat.percentage}%`,
                    background: `linear-gradient(90deg, #6366f180, #6366f1)`,
                    borderRadius: 4, transition: 'width 0.8s ease',
                  }} />
                </div>
                <div style={{ width: 70, fontSize: 12, color: '#818cf8', fontWeight: 700, textAlign: 'right' }}>
                  {feat.percentage.toFixed(1)}%
                </div>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* ─── Training Instructions ────────────────────── */}
      <div className="card" style={{
        background: 'rgba(99,102,241,0.05)',
        border: '1px solid rgba(99,102,241,0.2)',
      }}>
        <div className="chart-title">🚀 Train ML Models</div>
        <p style={{ fontSize: 13, color: '#94a3b8', marginBottom: 16, lineHeight: 1.6 }}>
          To train all models on real data and see actual metrics, run the training pipeline from the backend directory:
        </p>
        <div style={{
          background: '#060f1e', border: '1px solid rgba(255,255,255,0.06)',
          borderRadius: 8, padding: '16px', fontFamily: 'monospace', fontSize: 12, color: '#e2e8f0',
        }}>
          <div style={{ color: '#475569', marginBottom: 4 }}># Step 1: Generate synthetic dataset</div>
          <div style={{ color: '#10b981' }}>python dataset/generate_synthetic.py</div>
          <div style={{ color: '#475569', marginTop: 12, marginBottom: 4 }}># Step 2: Train all ML models</div>
          <div style={{ color: '#10b981' }}>cd backend && python -m ml.train_all</div>
          <div style={{ color: '#475569', marginTop: 12, marginBottom: 4 }}># Step 3: Restart backend to load new models</div>
          <div style={{ color: '#10b981' }}>uvicorn main:app --reload</div>
        </div>
      </div>
    </div>
  );
}
