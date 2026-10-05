/**
 * pages/Investigation.jsx — User investigation and activity timeline page.
 */
import { useState, useEffect } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import {
  BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip,
  ResponsiveContainer, LineChart, Line,
} from 'recharts';
import { usersAPI, activityAPI, riskAPI, explainAPI, reportsAPI } from '../api/axios';
import toast from 'react-hot-toast';

const EVENT_ICONS = {
  login: '🔑', logout: '🚪', file_access: '📁', file_download: '⬇️',
  file_upload: '⬆️', file_delete: '🗑️', usb_connect: '🔌', usb_transfer: '💾',
  web_browse: '🌐', email_send: '📧', email_attachment: '📎',
  remote_access: '🖥️', print_document: '🖨️', suspicious_process: '⚠️',
};

const SENSITIVITY_STYLES = {
  low: { color: '#10b981', bg: 'rgba(16,185,129,0.12)' },
  medium: { color: '#f59e0b', bg: 'rgba(245,158,11,0.12)' },
  high: { color: '#f97316', bg: 'rgba(249,115,22,0.12)' },
  critical: { color: '#ef4444', bg: 'rgba(239,68,68,0.12)' },
};

export default function Investigation() {
  const { userId } = useParams();
  const navigate = useNavigate();
  const [selectedUserId, setSelectedUserId] = useState(userId || '');
  const [users, setUsers] = useState([]);
  const [user, setUser] = useState(null);
  const [activities, setActivities] = useState([]);
  const [timeline, setTimeline] = useState([]);
  const [summary, setSummary] = useState(null);
  const [riskScore, setRiskScore] = useState(null);
  const [explanation, setExplanation] = useState(null);
  const [activeTab, setActiveTab] = useState('timeline');
  const [loading, setLoading] = useState(false);
  const [loadingReport, setLoadingReport] = useState(false);

  useEffect(() => {
    fetchUsers();
  }, []);

  useEffect(() => {
    if (selectedUserId) {
      fetchUserData(selectedUserId);
    }
  }, [selectedUserId]);

  const fetchUsers = async () => {
    try {
      const res = await usersAPI.list({ per_page: 100 });
      setUsers(res.data.users || []);
    } catch {}
  };

  const fetchUserData = async (uid) => {
    setLoading(true);
    try {
      const [userRes, activitiesRes, timelineRes, summaryRes] = await Promise.allSettled([
        usersAPI.get(uid),
        activityAPI.getUserActivities(uid, { per_page: 50, days: 30 }),
        activityAPI.getTimeline(uid, { days: 14 }),
        activityAPI.getSummary(uid, { days: 30 }),
      ]);

      if (userRes.status === 'fulfilled') setUser(userRes.value.data);
      if (activitiesRes.status === 'fulfilled') setActivities(activitiesRes.value.data.activities || []);
      if (timelineRes.status === 'fulfilled') setTimeline(timelineRes.value.data.timeline || []);
      if (summaryRes.status === 'fulfilled') setSummary(summaryRes.value.data);

      // Fetch risk score and SHAP explanation
      const [riskRes, explainRes] = await Promise.allSettled([
        riskAPI.getScore(uid),
        explainAPI.getExplanation(uid),
      ]);
      if (riskRes.status === 'fulfilled') setRiskScore(riskRes.value.data);
      if (explainRes.status === 'fulfilled') setExplanation(explainRes.value.data);
    } catch (err) {
      toast.error('Failed to load investigation data');
    } finally {
      setLoading(false);
    }
  };

  const handleGenerateReport = async () => {
    if (!selectedUserId) return;
    setLoadingReport(true);
    try {
      const res = await reportsAPI.generate(selectedUserId);
      const url = window.URL.createObjectURL(new Blob([res.data]));
      const link = document.createElement('a');
      link.href = url;
      link.download = `incident_report_${user?.username}_${new Date().toISOString().slice(0, 10)}.pdf`;
      link.click();
      window.URL.revokeObjectURL(url);
      toast.success('PDF incident report downloaded!');
    } catch {
      toast.error('Failed to generate report');
    } finally {
      setLoadingReport(false);
    }
  };

  const riskLevel = riskScore?.risk_level || user?.risk_level || 'LOW';
  const riskScoreVal = riskScore?.risk_score ?? user?.risk_score ?? 0;
  const riskColor = riskLevel === 'HIGH' ? '#ef4444' : riskLevel === 'MEDIUM' ? '#f59e0b' : '#10b981';

  return (
    <div style={{ animation: 'fadeInUp 0.4s ease forwards' }}>
      {/* ─── Header ─────────────────────────────────────── */}
      <div className="page-header">
        <div>
          <h1 className="page-title">🔍 Investigation</h1>
          <p className="page-subtitle">Deep-dive user behavior analysis & threat correlation</p>
        </div>
        <div style={{ display: 'flex', gap: 10 }}>
          <select
            className="input"
            style={{ minWidth: 220 }}
            value={selectedUserId}
            onChange={(e) => {
              setSelectedUserId(e.target.value);
              navigate(`/investigation/${e.target.value}`);
            }}
          >
            <option value="">— Select User —</option>
            {users.map((u) => (
              <option key={u.id} value={u.id}>
                {u.full_name} (@{u.username}) · {u.risk_level}
              </option>
            ))}
          </select>
          {selectedUserId && (
            <button
              className="btn btn-primary btn-sm"
              onClick={handleGenerateReport}
              disabled={loadingReport}
            >
              {loadingReport ? <><div className="spinner" style={{ width: 14, height: 14 }} /> Generating...</> : '📄 PDF Report'}
            </button>
          )}
        </div>
      </div>

      {!selectedUserId ? (
        <div className="empty-state" style={{ marginTop: 60 }}>
          <div className="empty-state-icon">🔍</div>
          <div className="empty-state-text">Select a user above to begin investigation</div>
        </div>
      ) : loading ? (
        <div style={{ display: 'flex', justifyContent: 'center', padding: 60 }}>
          <div className="spinner" style={{ width: 40, height: 40 }} />
        </div>
      ) : (
        <>
          {/* ─── User Profile Header Card ────────────────── */}
          {user && (
            <div style={{
              background: 'var(--bg-card)',
              border: `1px solid ${riskColor}30`,
              borderLeft: `4px solid ${riskColor}`,
              borderRadius: 'var(--radius-lg)',
              padding: '20px 24px',
              marginBottom: 20,
              display: 'flex', alignItems: 'center', gap: 20, flexWrap: 'wrap',
            }}>
              <div style={{
                width: 56, height: 56,
                background: 'linear-gradient(135deg, #6366f1, #4f46e5)',
                borderRadius: '50%',
                display: 'flex', alignItems: 'center', justifyContent: 'center',
                fontSize: 22, fontWeight: 800, color: '#fff', flexShrink: 0,
              }}>
                {user.full_name?.[0] || '?'}
              </div>
              <div style={{ flex: 1 }}>
                <div style={{ fontSize: 18, fontWeight: 800, color: '#e2e8f0' }}>{user.full_name}</div>
                <div style={{ fontSize: 13, color: '#64748b' }}>
                  @{user.username} · {user.email} · {user.department} · {user.role?.toUpperCase()}
                </div>
              </div>
              {/* Risk gauge */}
              <div style={{ textAlign: 'center' }}>
                <div style={{
                  fontSize: 36, fontWeight: 900, color: riskColor,
                  textShadow: `0 0 20px ${riskColor}60`,
                }}>
                  {riskScoreVal.toFixed(0)}
                </div>
                <div style={{
                  fontSize: 11, fontWeight: 700, color: riskColor,
                  background: `${riskColor}15`, padding: '2px 12px', borderRadius: 20,
                  textTransform: 'uppercase', letterSpacing: '0.08em',
                }}>
                  {riskLevel} RISK
                </div>
                <div style={{ fontSize: 10, color: '#475569', marginTop: 2 }}>Risk Score / 100</div>
              </div>

              {/* Summary stats */}
              {summary && (
                <div style={{ display: 'flex', gap: 16 }}>
                  {[
                    { label: 'Total Events', value: summary.total_events },
                    { label: 'Failed Logins', value: summary.failed_login_count, color: summary.failed_login_count > 3 ? '#ef4444' : undefined },
                    { label: 'USB Transfers', value: summary.usb_transfer_count, color: summary.usb_transfer_count > 2 ? '#f59e0b' : undefined },
                    { label: 'After Hours', value: summary.after_hours_events, color: summary.after_hours_events > 5 ? '#f97316' : undefined },
                  ].map((s, i) => (
                    <div key={i} style={{ textAlign: 'center' }}>
                      <div style={{ fontSize: 20, fontWeight: 800, color: s.color || '#94a3b8' }}>{s.value}</div>
                      <div style={{ fontSize: 10, color: '#475569', whiteSpace: 'nowrap' }}>{s.label}</div>
                    </div>
                  ))}
                </div>
              )}
            </div>
          )}

          {/* ─── Tabs ────────────────────────────────────── */}
          <div style={{ display: 'flex', gap: 4, marginBottom: 20, borderBottom: '1px solid rgba(255,255,255,0.06)', paddingBottom: 0 }}>
            {[
              { id: 'timeline', label: '📅 Activity Timeline' },
              { id: 'shap', label: '🧠 AI Explanation' },
              { id: 'risk', label: '⚠️ Risk Factors' },
            ].map((tab) => (
              <button
                key={tab.id}
                onClick={() => setActiveTab(tab.id)}
                style={{
                  padding: '10px 18px',
                  background: 'none',
                  border: 'none',
                  borderBottom: activeTab === tab.id ? '2px solid #6366f1' : '2px solid transparent',
                  color: activeTab === tab.id ? '#6366f1' : '#64748b',
                  fontWeight: activeTab === tab.id ? 700 : 500,
                  fontSize: 13,
                  cursor: 'pointer',
                  transition: 'all 0.2s',
                  fontFamily: 'var(--font-primary)',
                  marginBottom: -1,
                }}
              >
                {tab.label}
              </button>
            ))}
          </div>

          {/* ─── Tab Content ─────────────────────────────── */}
          {activeTab === 'timeline' && (
            <div>
              {/* Daily activity chart */}
              {timeline.length > 0 && (
                <div className="chart-container" style={{ marginBottom: 16 }}>
                  <div className="chart-title">📈 Daily Activity (14 Days)</div>
                  <ResponsiveContainer width="100%" height={180}>
                    <BarChart data={timeline}>
                      <CartesianGrid strokeDasharray="3 3" stroke="rgba(255,255,255,0.04)" />
                      <XAxis dataKey="date" tick={{ fontSize: 10, fill: '#475569' }} tickFormatter={(v) => v.slice(5)} />
                      <YAxis tick={{ fontSize: 10, fill: '#475569' }} />
                      <Tooltip contentStyle={{ background: '#0f1e36', border: '1px solid rgba(99,102,241,0.2)', borderRadius: 8, fontSize: 12 }} />
                      <Bar dataKey="count" fill="#6366f1" radius={[3, 3, 0, 0]} name="Events" />
                    </BarChart>
                  </ResponsiveContainer>
                </div>
              )}
              {/* Activity list */}
              <div className="card" style={{ padding: 0, overflow: 'hidden' }}>
                <div style={{ padding: '16px 20px', borderBottom: '1px solid rgba(255,255,255,0.06)', fontWeight: 700, fontSize: 14, color: '#e2e8f0' }}>
                  Recent Activity Events ({activities.length})
                </div>
                {activities.length === 0 ? (
                  <div className="empty-state"><div className="empty-state-icon">📭</div><div className="empty-state-text">No activity recorded</div></div>
                ) : (
                  <div style={{ maxHeight: 500, overflowY: 'auto' }}>
                    {activities.map((act, i) => {
                      const sensStyle = SENSITIVITY_STYLES[act.sensitivity_level] || SENSITIVITY_STYLES.low;
                      return (
                        <div key={i} style={{
                          display: 'flex', alignItems: 'flex-start', gap: 12,
                          padding: '12px 20px',
                          borderBottom: '1px solid rgba(255,255,255,0.03)',
                          transition: 'background 0.2s',
                        }}
                          onMouseEnter={(e) => e.currentTarget.style.background = 'rgba(99,102,241,0.04)'}
                          onMouseLeave={(e) => e.currentTarget.style.background = 'transparent'}
                        >
                          <span style={{ fontSize: 18, flexShrink: 0 }}>{EVENT_ICONS[act.event_type] || '📌'}</span>
                          <div style={{ flex: 1 }}>
                            <div style={{ display: 'flex', alignItems: 'center', gap: 8, flexWrap: 'wrap' }}>
                              <span style={{ fontSize: 13, fontWeight: 600, color: '#e2e8f0' }}>
                                {act.event_type.replace(/_/g, ' ').replace(/\b\w/g, (c) => c.toUpperCase())}
                              </span>
                              <span style={{
                                fontSize: 10, fontWeight: 600, padding: '1px 7px',
                                borderRadius: 8, background: sensStyle.bg, color: sensStyle.color,
                              }}>
                                {act.sensitivity_level?.toUpperCase()}
                              </span>
                              {act.is_after_hours && (
                                <span style={{ fontSize: 10, color: '#f59e0b', background: 'rgba(245,158,11,0.12)', padding: '1px 7px', borderRadius: 8, fontWeight: 600 }}>
                                  🌙 After Hours
                                </span>
                              )}
                              {act.risk_contribution > 0 && (
                                <span style={{ fontSize: 10, color: '#ef4444', marginLeft: 'auto' }}>+{act.risk_contribution} risk</span>
                              )}
                            </div>
                            <div style={{ fontSize: 11, color: '#475569', marginTop: 3, display: 'flex', gap: 10 }}>
                              <span>🕒 {new Date(act.timestamp).toLocaleString()}</span>
                              {act.ip_address && <span>🌐 {act.ip_address}</span>}
                              {act.file_name && <span>📄 {act.file_name}</span>}
                              {act.transfer_size_mb > 0 && <span>📦 {act.transfer_size_mb.toFixed(1)} MB</span>}
                            </div>
                          </div>
                        </div>
                      );
                    })}
                  </div>
                )}
              </div>
            </div>
          )}

          {activeTab === 'shap' && explanation && (
            <div>
              {/* Summary text */}
              <div style={{
                background: `${riskColor}10`,
                border: `1px solid ${riskColor}30`,
                borderRadius: 10, padding: '16px 20px', marginBottom: 16,
              }}>
                <div style={{ fontSize: 13, fontWeight: 700, color: riskColor, marginBottom: 6 }}>
                  🧠 AI Analysis: {explanation.prediction}
                </div>
                <div style={{ fontSize: 13, color: '#94a3b8', lineHeight: 1.6 }}>
                  {explanation.explanation_text}
                </div>
              </div>

              {/* SHAP Feature Importance Bars */}
              <div className="chart-container" style={{ marginBottom: 16 }}>
                <div className="chart-title">📊 SHAP Feature Impact (Top Contributors)</div>
                <div style={{ display: 'flex', flexDirection: 'column', gap: 10, marginTop: 8 }}>
                  {(explanation.top_features || []).map((feat, i) => {
                    const isPositive = feat.impact === 'positive';
                    const barColor = isPositive ? '#ef4444' : '#10b981';
                    const maxMag = Math.max(...(explanation.top_features || []).map((f) => f.magnitude));
                    const pct = maxMag > 0 ? (feat.magnitude / maxMag) * 100 : 0;
                    return (
                      <div key={i} style={{ display: 'flex', alignItems: 'center', gap: 12 }}>
                        <div style={{ width: 200, fontSize: 12, color: '#94a3b8', flexShrink: 0, textAlign: 'right' }}>
                          {feat.feature_name}
                        </div>
                        <div style={{
                          flex: 1, height: 20, background: 'rgba(255,255,255,0.04)',
                          borderRadius: 4, overflow: 'hidden',
                        }}>
                          <div style={{
                            height: '100%', width: `${pct}%`,
                            background: `linear-gradient(90deg, ${barColor}80, ${barColor})`,
                            borderRadius: 4,
                            transition: 'width 0.8s ease',
                          }} />
                        </div>
                        <div style={{ width: 80, fontSize: 12, color: isPositive ? '#f87171' : '#34d399', textAlign: 'right' }}>
                          {isPositive ? '+' : ''}{feat.shap_value.toFixed(3)}
                        </div>
                        <div style={{ width: 60, fontSize: 11, color: '#475569', textAlign: 'right' }}>
                          val: {feat.feature_value.toFixed(1)}
                        </div>
                      </div>
                    );
                  })}
                </div>
              </div>

              {/* Recommended Actions */}
              <div className="card">
                <div className="chart-title" style={{ marginBottom: 12 }}>🎯 Recommended Actions</div>
                <div style={{ display: 'flex', flexDirection: 'column', gap: 8 }}>
                  {(explanation.recommended_actions || []).map((action, i) => (
                    <div key={i} style={{
                      padding: '10px 14px',
                      background: 'rgba(255,255,255,0.03)',
                      borderRadius: 8,
                      border: '1px solid rgba(255,255,255,0.06)',
                      fontSize: 13, color: '#cbd5e1',
                    }}>
                      {action}
                    </div>
                  ))}
                </div>
              </div>
            </div>
          )}

          {activeTab === 'risk' && riskScore && (
            <div className="grid-2">
              {/* Score breakdown */}
              <div className="card">
                <div className="chart-title">⚖️ Risk Score Breakdown</div>
                <div style={{ display: 'flex', flexDirection: 'column', gap: 10 }}>
                  {Object.entries(riskScore.score_breakdown || {}).map(([key, val]) => {
                    const label = key.replace(/_/g, ' ').replace(/\b\w/g, (c) => c.toUpperCase());
                    const pct = Math.min((val / 40) * 100, 100);
                    const color = val >= 25 ? '#ef4444' : val >= 15 ? '#f59e0b' : '#10b981';
                    return (
                      <div key={key}>
                        <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: 12, marginBottom: 4 }}>
                          <span style={{ color: '#94a3b8' }}>{label}</span>
                          <span style={{ color, fontWeight: 700 }}>{val.toFixed(1)}</span>
                        </div>
                        <div style={{ height: 6, background: 'rgba(255,255,255,0.06)', borderRadius: 3, overflow: 'hidden' }}>
                          <div style={{ height: '100%', width: `${pct}%`, background: color, borderRadius: 3, transition: 'width 0.6s ease' }} />
                        </div>
                      </div>
                    );
                  })}
                </div>
                <div style={{ marginTop: 16, paddingTop: 16, borderTop: '1px solid rgba(255,255,255,0.06)', display: 'flex', justifyContent: 'space-between' }}>
                  <span style={{ fontSize: 13, color: '#64748b' }}>Total Risk Score</span>
                  <span style={{ fontSize: 20, fontWeight: 900, color: riskColor }}>{riskScoreVal.toFixed(1)}</span>
                </div>
              </div>

              {/* Top factors */}
              <div className="card">
                <div className="chart-title">🔑 Top Risk Factors</div>
                <div style={{ display: 'flex', flexDirection: 'column', gap: 10 }}>
                  {(riskScore.top_risk_factors || []).map((factor, i) => (
                    <div key={i} style={{
                      display: 'flex', alignItems: 'flex-start', gap: 10,
                      padding: '10px 12px',
                      background: 'rgba(239,68,68,0.05)',
                      border: '1px solid rgba(239,68,68,0.15)',
                      borderRadius: 8,
                    }}>
                      <span style={{ color: '#ef4444', flexShrink: 0 }}>⚠️</span>
                      <span style={{ fontSize: 13, color: '#cbd5e1' }}>{factor}</span>
                    </div>
                  ))}
                  {(riskScore.top_risk_factors || []).length === 0 && (
                    <div className="empty-state">
                      <div className="empty-state-icon">✅</div>
                      <div className="empty-state-text">No significant risk factors detected.</div>
                    </div>
                  )}
                </div>
              </div>
            </div>
          )}

          {activeTab === 'shap' && !explanation && (
            <div className="empty-state">
              <div className="empty-state-icon">🧠</div>
              <div className="empty-state-text">AI models not trained yet. Run training scripts to enable explainability.</div>
            </div>
          )}
        </>
      )}
    </div>
  );
}
