/**
 * pages/Analytics.jsx — Risk analytics, SHAP global importance, and risk leaderboard.
 */
import { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import {
  BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip,
  ResponsiveContainer, RadarChart, Radar, PolarGrid,
  PolarAngleAxis, PolarRadiusAxis, Cell,
} from 'recharts';
import { riskAPI, explainAPI, usersAPI } from '../api/axios';
import toast from 'react-hot-toast';

const RISK_COLORS = {
  HIGH: '#ef4444', MEDIUM: '#f59e0b', LOW: '#10b981',
};

const CustomTooltip = ({ active, payload, label }) => {
  if (!active || !payload?.length) return null;
  return (
    <div style={{ background: '#0f1e36', border: '1px solid rgba(99,102,241,0.3)', borderRadius: 8, padding: '10px 14px', fontSize: 12 }}>
      <div style={{ color: '#94a3b8', marginBottom: 4 }}>{label}</div>
      {payload.map((p, i) => (
        <div key={i} style={{ color: p.color || '#6366f1', fontWeight: 600 }}>
          {p.name}: {typeof p.value === 'number' ? p.value.toFixed(2) : p.value}
        </div>
      ))}
    </div>
  );
};

export default function Analytics() {
  const navigate = useNavigate();
  const [riskOverview, setRiskOverview] = useState({});
  const [leaderboard, setLeaderboard] = useState([]);
  const [globalImportance, setGlobalImportance] = useState([]);
  const [userStats, setUserStats] = useState({});
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetchData();
  }, []);

  const fetchData = async () => {
    setLoading(true);
    try {
      const [overviewRes, leaderboardRes, importanceRes, userStatsRes] = await Promise.allSettled([
        riskAPI.getOverview(),
        riskAPI.getLeaderboard({ limit: 15 }),
        explainAPI.getGlobalImportance(),
        usersAPI.stats(),
      ]);
      if (overviewRes.status === 'fulfilled') setRiskOverview(overviewRes.value.data);
      if (leaderboardRes.status === 'fulfilled') setLeaderboard(leaderboardRes.value.data.users || []);
      if (importanceRes.status === 'fulfilled') setGlobalImportance(importanceRes.value.data.feature_importance || []);
      if (userStatsRes.status === 'fulfilled') setUserStats(userStatsRes.value.data);
    } catch {
      toast.error('Failed to load analytics');
    } finally {
      setLoading(false);
    }
  };

  // Data for risk distribution bar chart
  const distData = [
    { name: 'HIGH', value: riskOverview.high_risk_users || 0, fill: '#ef4444' },
    { name: 'MEDIUM', value: riskOverview.medium_risk_users || 0, fill: '#f59e0b' },
    { name: 'LOW', value: riskOverview.low_risk_users || 0, fill: '#10b981' },
  ];

  // Radar chart data from global feature importance
  const radarData = globalImportance.slice(0, 7).map((f) => ({
    feature: f.feature_name.split(' ').slice(0, 2).join(' '),
    importance: Math.round(f.percentage),
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
      {/* Header */}
      <div className="page-header">
        <div>
          <h1 className="page-title">📊 Risk Analytics</h1>
          <p className="page-subtitle">Global threat metrics, SHAP feature importance & risk distribution</p>
        </div>
        <button className="btn btn-secondary btn-sm" onClick={fetchData}>🔄 Refresh</button>
      </div>

      {/* ─── KPI Row ──────────────────────────────────────── */}
      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(4, 1fr)', gap: 14, marginBottom: 24 }}>
        {[
          { label: 'Avg Risk Score', value: riskOverview.average_risk_score?.toFixed(1) || '0', icon: '📊', color: '#6366f1' },
          { label: 'High Risk Users', value: riskOverview.high_risk_users || 0, icon: '🔴', color: '#ef4444' },
          { label: 'Medium Risk', value: riskOverview.medium_risk_users || 0, icon: '🟡', color: '#f59e0b' },
          { label: 'Total Monitored', value: riskOverview.total_users || 0, icon: '👥', color: '#10b981' },
        ].map((kpi, i) => (
          <div key={i} className="stat-card">
            <div className="stat-icon" style={{ background: `${kpi.color}20`, color: kpi.color }}>
              {kpi.icon}
            </div>
            <div>
              <div className="stat-value" style={{ color: kpi.color, WebkitTextFillColor: kpi.color }}>{kpi.value}</div>
              <div className="stat-label">{kpi.label}</div>
            </div>
          </div>
        ))}
      </div>

      {/* ─── Charts Row ───────────────────────────────────── */}
      <div className="grid-2" style={{ marginBottom: 24 }}>
        {/* Risk Distribution Bar Chart */}
        <div className="chart-container">
          <div className="chart-title">📊 Risk Level Distribution</div>
          <ResponsiveContainer width="100%" height={220}>
            <BarChart data={distData} barSize={60}>
              <CartesianGrid strokeDasharray="3 3" stroke="rgba(255,255,255,0.04)" />
              <XAxis dataKey="name" tick={{ fontSize: 12, fill: '#94a3b8', fontWeight: 700 }} />
              <YAxis tick={{ fontSize: 11, fill: '#475569' }} />
              <Tooltip content={<CustomTooltip />} />
              <Bar dataKey="value" radius={[6, 6, 0, 0]} name="Users">
                {distData.map((entry, i) => (
                  <Cell key={i} fill={entry.fill} />
                ))}
              </Bar>
            </BarChart>
          </ResponsiveContainer>
        </div>

        {/* SHAP Radar Chart */}
        <div className="chart-container">
          <div className="chart-title">🧠 SHAP Feature Importance Radar</div>
          {radarData.length > 0 ? (
            <ResponsiveContainer width="100%" height={220}>
              <RadarChart data={radarData}>
                <PolarGrid stroke="rgba(255,255,255,0.06)" />
                <PolarAngleAxis dataKey="feature" tick={{ fontSize: 9, fill: '#64748b' }} />
                <PolarRadiusAxis angle={30} domain={[0, 100]} tick={{ fontSize: 9, fill: '#475569' }} />
                <Radar
                  name="Importance" dataKey="importance"
                  stroke="#6366f1" fill="#6366f1" fillOpacity={0.2}
                  strokeWidth={2}
                />
                <Tooltip content={<CustomTooltip />} />
              </RadarChart>
            </ResponsiveContainer>
          ) : (
            <div className="empty-state">
              <div className="empty-state-icon">🧠</div>
              <div className="empty-state-text">Train ML models to see SHAP importance</div>
            </div>
          )}
        </div>
      </div>

      {/* ─── Global Feature Importance Bars ──────────────── */}
      {globalImportance.length > 0 && (
        <div className="chart-container" style={{ marginBottom: 24 }}>
          <div className="chart-title">🔑 Global SHAP Feature Importance</div>
          <div style={{ display: 'flex', flexDirection: 'column', gap: 10 }}>
            {globalImportance.map((feat, i) => (
              <div key={i} style={{ display: 'flex', alignItems: 'center', gap: 12 }}>
                <div style={{ width: 220, fontSize: 12, color: '#94a3b8', flexShrink: 0, textAlign: 'right' }}>
                  {feat.feature_name}
                </div>
                <div style={{ flex: 1, height: 18, background: 'rgba(255,255,255,0.04)', borderRadius: 4, overflow: 'hidden' }}>
                  <div style={{
                    height: '100%',
                    width: `${feat.percentage}%`,
                    background: `linear-gradient(90deg, #6366f180, #6366f1)`,
                    borderRadius: 4,
                    transition: 'width 0.8s ease',
                  }} />
                </div>
                <div style={{ width: 60, fontSize: 12, color: '#818cf8', fontWeight: 700, textAlign: 'right' }}>
                  {feat.percentage.toFixed(1)}%
                </div>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* ─── Risk Leaderboard Table ───────────────────────── */}
      <div className="card" style={{ padding: 0, overflow: 'hidden' }}>
        <div style={{ padding: '16px 20px', borderBottom: '1px solid rgba(255,255,255,0.06)', display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
          <div className="chart-title" style={{ margin: 0 }}>⚠️ Risk Leaderboard — Top Threats</div>
          <span style={{ fontSize: 12, color: '#475569' }}>{leaderboard.length} users</span>
        </div>
        {leaderboard.length === 0 ? (
          <div className="empty-state">
            <div className="empty-state-icon">✅</div>
            <div className="empty-state-text">No high-risk users detected</div>
          </div>
        ) : (
          <table className="data-table">
            <thead>
              <tr>
                <th>#</th>
                <th>User</th>
                <th>Department</th>
                <th>Risk Score</th>
                <th>Risk Level</th>
                <th>Action</th>
              </tr>
            </thead>
            <tbody>
              {leaderboard.map((u, i) => {
                const rColor = RISK_COLORS[u.risk_level] || '#10b981';
                return (
                  <tr key={i}>
                    <td style={{ color: '#475569', fontWeight: 700, fontSize: 13 }}>#{i + 1}</td>
                    <td>
                      <div style={{ display: 'flex', alignItems: 'center', gap: 10 }}>
                        <div style={{
                          width: 30, height: 30,
                          background: 'linear-gradient(135deg, #6366f1, #4f46e5)',
                          borderRadius: '50%',
                          display: 'flex', alignItems: 'center', justifyContent: 'center',
                          fontSize: 12, fontWeight: 700, color: '#fff', flexShrink: 0,
                        }}>
                          {u.full_name?.[0] || '?'}
                        </div>
                        <div>
                          <div style={{ fontSize: 13, fontWeight: 600, color: '#e2e8f0' }}>{u.full_name || u.username}</div>
                          <div style={{ fontSize: 11, color: '#475569' }}>@{u.username}</div>
                        </div>
                      </div>
                    </td>
                    <td style={{ fontSize: 12, color: '#64748b' }}>{u.department || '—'}</td>
                    <td>
                      {/* Mini risk bar */}
                      <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
                        <div style={{ width: 80, height: 6, background: 'rgba(255,255,255,0.06)', borderRadius: 3, overflow: 'hidden' }}>
                          <div style={{ height: '100%', width: `${u.risk_score}%`, background: rColor, borderRadius: 3 }} />
                        </div>
                        <span style={{ fontSize: 13, fontWeight: 800, color: rColor }}>{u.risk_score?.toFixed(1)}</span>
                      </div>
                    </td>
                    <td>
                      <span style={{
                        fontSize: 11, fontWeight: 700, padding: '3px 10px',
                        borderRadius: 20, background: `${rColor}15`, color: rColor,
                        textTransform: 'uppercase', letterSpacing: '0.05em',
                      }}>
                        {u.risk_level}
                      </span>
                    </td>
                    <td>
                      <button
                        className="btn btn-secondary btn-sm"
                        onClick={() => navigate(`/investigation/${u.user_id}`)}
                      >
                        🔍 Investigate
                      </button>
                    </td>
                  </tr>
                );
              })}
            </tbody>
          </table>
        )}
      </div>
    </div>
  );
}
