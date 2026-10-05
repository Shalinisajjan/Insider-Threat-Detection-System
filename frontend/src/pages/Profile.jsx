/**
 * pages/Profile.jsx — User profile and self-risk assessment page.
 */
import { useState, useEffect } from 'react';
import { useAuth } from '../context/AuthContext';
import { riskAPI, activityAPI, predictAPI } from '../api/axios';
import toast from 'react-hot-toast';

export default function Profile() {
  const { user } = useAuth();
  const [riskData, setRiskData] = useState(null);
  const [summary, setSummary] = useState(null);
  const [modelInfo, setModelInfo] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    if (user?.id) fetchProfileData();
  }, [user]);

  const fetchProfileData = async () => {
    setLoading(true);
    try {
      const [riskRes, summaryRes, modelRes] = await Promise.allSettled([
        riskAPI.getScore(user.id),
        activityAPI.getSummary(user.id, { days: 30 }),
        predictAPI.getModelInfo(),
      ]);
      if (riskRes.status === 'fulfilled') setRiskData(riskRes.value.data);
      if (summaryRes.status === 'fulfilled') setSummary(summaryRes.value.data);
      if (modelRes.status === 'fulfilled') setModelInfo(modelRes.value.data);
    } catch {}
    finally { setLoading(false); }
  };

  const riskScore = riskData?.risk_score ?? user?.risk_score ?? 0;
  const riskLevel = riskData?.risk_level ?? user?.risk_level ?? 'LOW';
  const riskColor = riskLevel === 'HIGH' ? '#ef4444' : riskLevel === 'MEDIUM' ? '#f59e0b' : '#10b981';

  // Ring progress
  const circumference = 2 * Math.PI * 54;
  const offset = circumference - (riskScore / 100) * circumference;

  return (
    <div style={{ animation: 'fadeInUp 0.4s ease forwards' }}>
      <div className="page-header">
        <div>
          <h1 className="page-title">👤 My Profile</h1>
          <p className="page-subtitle">Your account information and personal risk assessment</p>
        </div>
        <button className="btn btn-secondary btn-sm" onClick={fetchProfileData}>🔄 Refresh</button>
      </div>

      <div className="grid-2" style={{ alignItems: 'start' }}>
        {/* ─── Profile Card ──────────────────────────────── */}
        <div style={{ display: 'flex', flexDirection: 'column', gap: 16 }}>
          <div className="card">
            <div style={{ display: 'flex', alignItems: 'center', gap: 16, marginBottom: 20 }}>
              <div style={{
                width: 64, height: 64,
                background: 'linear-gradient(135deg, #6366f1, #4f46e5)',
                borderRadius: '50%',
                display: 'flex', alignItems: 'center', justifyContent: 'center',
                fontSize: 26, fontWeight: 900, color: '#fff',
                boxShadow: '0 0 20px rgba(99,102,241,0.4)',
              }}>
                {user?.full_name?.[0] || '?'}
              </div>
              <div>
                <div style={{ fontSize: 18, fontWeight: 800, color: '#e2e8f0' }}>{user?.full_name}</div>
                <div style={{ fontSize: 13, color: '#6366f1', fontWeight: 600 }}>@{user?.username}</div>
                <div style={{ fontSize: 12, color: '#475569' }}>{user?.email}</div>
              </div>
            </div>

            <div style={{ display: 'flex', flexDirection: 'column', gap: 10 }}>
              {[
                { label: 'Department', value: user?.department },
                { label: 'Role', value: user?.role?.toUpperCase() },
                { label: 'Account Status', value: user?.is_active ? '✅ Active' : '🚫 Disabled' },
                { label: 'Last Login', value: user?.last_login ? new Date(user.last_login).toLocaleString() : 'N/A' },
              ].map((row, i) => (
                <div key={i} style={{
                  display: 'flex', justifyContent: 'space-between', alignItems: 'center',
                  padding: '10px 14px',
                  background: 'rgba(255,255,255,0.02)',
                  borderRadius: 8,
                  border: '1px solid rgba(255,255,255,0.04)',
                }}>
                  <span style={{ fontSize: 12, color: '#475569', textTransform: 'uppercase', letterSpacing: '0.05em' }}>{row.label}</span>
                  <span style={{ fontSize: 13, color: '#e2e8f0', fontWeight: 600 }}>{row.value || 'N/A'}</span>
                </div>
              ))}
            </div>
          </div>

          {/* ML Model Status */}
          {modelInfo && (
            <div className="card">
              <div className="chart-title" style={{ marginBottom: 12 }}>🤖 ML Model Status</div>
              <div style={{ display: 'flex', flexDirection: 'column', gap: 8 }}>
                {modelInfo.models.map((m, i) => (
                  <div key={i} style={{
                    display: 'flex', alignItems: 'center', justifyContent: 'space-between',
                    padding: '8px 12px',
                    background: 'rgba(255,255,255,0.02)',
                    borderRadius: 8, border: '1px solid rgba(255,255,255,0.04)',
                  }}>
                    <div>
                      <div style={{ fontSize: 12, fontWeight: 600, color: '#e2e8f0' }}>
                        {m.name.replace(/_/g, ' ').replace(/\b\w/g, (c) => c.toUpperCase())}
                      </div>
                      <div style={{ fontSize: 11, color: '#475569', fontFamily: 'monospace' }}>{m.filename}</div>
                    </div>
                    <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
                      {m.size_kb > 0 && <span style={{ fontSize: 11, color: '#475569' }}>{m.size_kb} KB</span>}
                      <span style={{
                        fontSize: 11, fontWeight: 700,
                        padding: '2px 8px', borderRadius: 20,
                        background: m.trained ? 'rgba(16,185,129,0.15)' : 'rgba(239,68,68,0.15)',
                        color: m.trained ? '#34d399' : '#f87171',
                      }}>
                        {m.trained ? '✓ Trained' : '✗ Not Trained'}
                      </span>
                    </div>
                  </div>
                ))}
                <div style={{ fontSize: 11, color: '#475569', marginTop: 4, padding: '0 4px' }}>
                  {modelInfo.total_trained}/{modelInfo.models.length} models trained
                </div>
              </div>
            </div>
          )}
        </div>

        {/* ─── Risk Assessment ───────────────────────────── */}
        <div style={{ display: 'flex', flexDirection: 'column', gap: 16 }}>
          {/* Risk Score Ring */}
          <div className="card" style={{ textAlign: 'center' }}>
            <div className="chart-title" style={{ marginBottom: 20 }}>⚡ Your Risk Assessment</div>
            {loading ? (
              <div style={{ padding: 40 }}><div className="spinner" style={{ width: 40, height: 40, margin: '0 auto' }} /></div>
            ) : (
              <>
                {/* SVG Ring */}
                <div style={{ position: 'relative', display: 'inline-block', marginBottom: 16 }}>
                  <svg width="140" height="140" viewBox="0 0 140 140">
                    {/* Background ring */}
                    <circle cx="70" cy="70" r="54" fill="none" stroke="rgba(255,255,255,0.06)" strokeWidth="10" />
                    {/* Progress ring */}
                    <circle
                      cx="70" cy="70" r="54" fill="none"
                      stroke={riskColor} strokeWidth="10"
                      strokeDasharray={circumference}
                      strokeDashoffset={offset}
                      strokeLinecap="round"
                      transform="rotate(-90 70 70)"
                      style={{ transition: 'stroke-dashoffset 1s ease', filter: `drop-shadow(0 0 8px ${riskColor})` }}
                    />
                    {/* Center text */}
                    <text x="70" y="65" textAnchor="middle" fill={riskColor} fontSize="26" fontWeight="900">
                      {riskScore.toFixed(0)}
                    </text>
                    <text x="70" y="82" textAnchor="middle" fill="#475569" fontSize="11">/ 100</text>
                  </svg>
                </div>
                <div style={{
                  fontSize: 14, fontWeight: 800, color: riskColor,
                  background: `${riskColor}15`, padding: '4px 20px',
                  borderRadius: 20, display: 'inline-block', marginBottom: 8,
                }}>
                  {riskLevel} RISK
                </div>
                {riskData?.top_risk_factors?.length > 0 && (
                  <div style={{ textAlign: 'left', marginTop: 16 }}>
                    <div style={{ fontSize: 12, color: '#475569', marginBottom: 8, textTransform: 'uppercase', letterSpacing: '0.05em' }}>
                      Top Risk Factors
                    </div>
                    {riskData.top_risk_factors.slice(0, 3).map((f, i) => (
                      <div key={i} style={{
                        fontSize: 12, color: '#94a3b8', padding: '6px 10px',
                        background: 'rgba(239,68,68,0.05)',
                        borderLeft: '2px solid rgba(239,68,68,0.3)',
                        borderRadius: '0 6px 6px 0', marginBottom: 6,
                      }}>
                        {f}
                      </div>
                    ))}
                  </div>
                )}
              </>
            )}
          </div>

          {/* Activity Summary */}
          {summary && (
            <div className="card">
              <div className="chart-title" style={{ marginBottom: 12 }}>📋 Activity Summary (30 days)</div>
              <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 10 }}>
                {[
                  { label: 'Total Events', value: summary.total_events, icon: '📊' },
                  { label: 'Login Attempts', value: summary.login_attempts, icon: '🔑' },
                  { label: 'Failed Logins', value: summary.failed_login_count, icon: '❌', alert: summary.failed_login_count > 3 },
                  { label: 'File Downloads', value: summary.file_downloads, icon: '⬇️' },
                  { label: 'USB Transfers', value: summary.usb_transfer_count, icon: '💾', alert: summary.usb_transfer_count > 0 },
                  { label: 'After Hours', value: summary.after_hours_events, icon: '🌙', alert: summary.after_hours_events > 5 },
                  { label: 'Suspicious URLs', value: summary.suspicious_url_count, icon: '🌐', alert: summary.suspicious_url_count > 2 },
                  { label: 'High Sensitivity', value: summary.high_sensitivity_accesses, icon: '🔐' },
                ].map((s, i) => (
                  <div key={i} style={{
                    padding: '10px 12px',
                    background: s.alert ? 'rgba(239,68,68,0.05)' : 'rgba(255,255,255,0.02)',
                    border: s.alert ? '1px solid rgba(239,68,68,0.2)' : '1px solid rgba(255,255,255,0.04)',
                    borderRadius: 8,
                  }}>
                    <div style={{ fontSize: 14, color: s.alert ? '#ef4444' : '#e2e8f0', fontWeight: 800 }}>
                      {s.icon} {s.value}
                    </div>
                    <div style={{ fontSize: 10, color: '#475569', marginTop: 2 }}>{s.label}</div>
                  </div>
                ))}
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
