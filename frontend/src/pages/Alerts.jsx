/**
 * pages/Alerts.jsx — Real-time alert management page.
 */
import { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { alertsAPI } from '../api/axios';
import toast from 'react-hot-toast';

const SEVERITY_CONFIG = {
  critical: { color: '#ef4444', bg: 'rgba(239,68,68,0.12)', border: 'rgba(239,68,68,0.3)', icon: '🔴' },
  high: { color: '#f97316', bg: 'rgba(249,115,22,0.12)', border: 'rgba(249,115,22,0.3)', icon: '🟠' },
  medium: { color: '#f59e0b', bg: 'rgba(245,158,11,0.12)', border: 'rgba(245,158,11,0.3)', icon: '🟡' },
  low: { color: '#10b981', bg: 'rgba(16,185,129,0.12)', border: 'rgba(16,185,129,0.3)', icon: '🟢' },
};

const STATUS_LABELS = {
  open: { label: 'Open', color: '#ef4444' },
  investigating: { label: 'Investigating', color: '#f59e0b' },
  resolved: { label: 'Resolved', color: '#10b981' },
  false_positive: { label: 'False Positive', color: '#6366f1' },
};

export default function Alerts() {
  const navigate = useNavigate();
  const [alerts, setAlerts] = useState([]);
  const [stats, setStats] = useState({});
  const [loading, setLoading] = useState(true);
  const [filter, setFilter] = useState({ severity: '', status: 'open', days: 30 });
  const [page, setPage] = useState(1);
  const [total, setTotal] = useState(0);
  const PER_PAGE = 15;

  useEffect(() => {
    fetchAlerts();
  }, [filter, page]);

  const fetchAlerts = async () => {
    setLoading(true);
    try {
      const params = { page, per_page: PER_PAGE, days: filter.days };
      if (filter.severity) params.severity = filter.severity;
      if (filter.status) params.status = filter.status;

      const [alertsRes, statsRes] = await Promise.all([
        alertsAPI.list(params),
        alertsAPI.getStats(),
      ]);
      setAlerts(alertsRes.data.alerts || []);
      setTotal(alertsRes.data.total || 0);
      setStats(statsRes.data);
    } catch (err) {
      toast.error('Failed to load alerts');
    } finally {
      setLoading(false);
    }
  };

  const handleMarkRead = async (alertId, e) => {
    e.stopPropagation();
    try {
      await alertsAPI.update(alertId, { is_read: true });
      setAlerts((prev) => prev.map((a) => a.id === alertId ? { ...a, is_read: true } : a));
    } catch {}
  };

  const handleStatusChange = async (alertId, newStatus, e) => {
    e.stopPropagation();
    try {
      await alertsAPI.update(alertId, { status: newStatus });
      toast.success(`Alert marked as ${newStatus}`);
      fetchAlerts();
    } catch {
      toast.error('Failed to update alert');
    }
  };

  const handleMarkAllRead = async () => {
    try {
      const res = await alertsAPI.markAllRead();
      toast.success(`Marked ${res.data.marked_read} alerts as read`);
      fetchAlerts();
    } catch {
      toast.error('Failed to mark all as read');
    }
  };

  return (
    <div style={{ animation: 'fadeInUp 0.4s ease forwards' }}>
      {/* ─── Header ─────────────────────────────────────── */}
      <div className="page-header">
        <div>
          <h1 className="page-title">🚨 Security Alerts</h1>
          <p className="page-subtitle">
            {stats.open || 0} open · {stats.critical || 0} critical · {stats.today || 0} today
          </p>
        </div>
        <div style={{ display: 'flex', gap: 10 }}>
          <button className="btn btn-secondary btn-sm" onClick={handleMarkAllRead}>
            ✅ Mark All Read
          </button>
          <button className="btn btn-primary btn-sm" onClick={fetchAlerts}>
            🔄 Refresh
          </button>
        </div>
      </div>

      {/* ─── Stats Row ───────────────────────────────────── */}
      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(5, 1fr)', gap: 12, marginBottom: 20 }}>
        {[
          { label: 'Total', value: stats.total || 0, color: '#6366f1' },
          { label: 'Open', value: stats.open || 0, color: '#ef4444' },
          { label: 'Critical', value: stats.critical || 0, color: '#dc2626' },
          { label: 'Investigating', value: stats.investigating || 0, color: '#f59e0b' },
          { label: 'Resolved', value: stats.resolved || 0, color: '#10b981' },
        ].map((s, i) => (
          <div key={i} style={{
            background: 'var(--bg-card)',
            border: '1px solid rgba(255,255,255,0.06)',
            borderRadius: 10,
            padding: '14px 16px',
            textAlign: 'center',
          }}>
            <div style={{ fontSize: 22, fontWeight: 800, color: s.color }}>{s.value}</div>
            <div style={{ fontSize: 11, color: '#475569', textTransform: 'uppercase', letterSpacing: '0.05em' }}>{s.label}</div>
          </div>
        ))}
      </div>

      {/* ─── Filters ────────────────────────────────────── */}
      <div style={{
        display: 'flex', gap: 12, marginBottom: 20, flexWrap: 'wrap',
        background: 'var(--bg-card)', padding: '14px', borderRadius: 10,
        border: '1px solid rgba(255,255,255,0.06)',
      }}>
        <select
          className="input"
          style={{ width: 'auto', minWidth: 130 }}
          value={filter.status}
          onChange={(e) => { setFilter({ ...filter, status: e.target.value }); setPage(1); }}
        >
          <option value="">All Statuses</option>
          <option value="open">Open</option>
          <option value="investigating">Investigating</option>
          <option value="resolved">Resolved</option>
          <option value="false_positive">False Positive</option>
        </select>
        <select
          className="input"
          style={{ width: 'auto', minWidth: 130 }}
          value={filter.severity}
          onChange={(e) => { setFilter({ ...filter, severity: e.target.value }); setPage(1); }}
        >
          <option value="">All Severities</option>
          <option value="critical">Critical</option>
          <option value="high">High</option>
          <option value="medium">Medium</option>
          <option value="low">Low</option>
        </select>
        <select
          className="input"
          style={{ width: 'auto', minWidth: 120 }}
          value={filter.days}
          onChange={(e) => { setFilter({ ...filter, days: e.target.value }); setPage(1); }}
        >
          <option value={7}>Last 7 days</option>
          <option value={14}>Last 14 days</option>
          <option value={30}>Last 30 days</option>
          <option value={90}>Last 90 days</option>
        </select>
        <div style={{ color: '#475569', fontSize: 13, alignSelf: 'center', marginLeft: 'auto' }}>
          {total} alerts found
        </div>
      </div>

      {/* ─── Alert List ─────────────────────────────────── */}
      {loading ? (
        <div style={{ display: 'flex', justifyContent: 'center', padding: 40 }}>
          <div className="spinner" style={{ width: 32, height: 32 }} />
        </div>
      ) : alerts.length === 0 ? (
        <div className="empty-state">
          <div className="empty-state-icon">✅</div>
          <div className="empty-state-text">No alerts match your filters.</div>
        </div>
      ) : (
        <div style={{ display: 'flex', flexDirection: 'column', gap: 8 }}>
          {alerts.map((alert) => {
            const sev = SEVERITY_CONFIG[alert.severity] || SEVERITY_CONFIG.low;
            const status = STATUS_LABELS[alert.status] || STATUS_LABELS.open;
            return (
              <div
                key={alert.id}
                style={{
                  background: alert.is_read ? 'var(--bg-card)' : 'rgba(239,68,68,0.03)',
                  border: `1px solid ${alert.is_read ? 'rgba(255,255,255,0.06)' : sev.border}`,
                  borderLeft: `4px solid ${sev.color}`,
                  borderRadius: 10,
                  padding: '14px 16px',
                  cursor: 'pointer',
                  transition: 'all 0.2s',
                }}
                onClick={() => navigate(`/investigation/${alert.user_id}`)}
                onMouseEnter={(e) => e.currentTarget.style.background = 'rgba(99,102,241,0.06)'}
                onMouseLeave={(e) => e.currentTarget.style.background = alert.is_read ? 'var(--bg-card)' : 'rgba(239,68,68,0.03)'}
              >
                <div style={{ display: 'flex', alignItems: 'flex-start', gap: 12 }}>
                  <span style={{ fontSize: 20, flexShrink: 0 }}>{sev.icon}</span>
                  <div style={{ flex: 1, overflow: 'hidden' }}>
                    <div style={{ display: 'flex', alignItems: 'center', gap: 8, flexWrap: 'wrap' }}>
                      {!alert.is_read && (
                        <span style={{ width: 6, height: 6, borderRadius: '50%', background: '#ef4444', flexShrink: 0 }} />
                      )}
                      <span style={{ fontSize: 14, fontWeight: 700, color: '#e2e8f0' }}>{alert.title}</span>
                      <span className={`badge badge-${alert.severity}`}>{alert.severity}</span>
                      <span style={{
                        fontSize: 11, fontWeight: 600, color: status.color,
                        background: `${status.color}15`, padding: '2px 8px', borderRadius: 10,
                      }}>
                        {status.label}
                      </span>
                    </div>
                    <div style={{ fontSize: 12, color: '#64748b', marginTop: 4 }}>
                      {alert.description}
                    </div>
                    <div style={{ fontSize: 11, color: '#475569', marginTop: 6, display: 'flex', gap: 12, flexWrap: 'wrap' }}>
                      {alert.username && <span>👤 @{alert.username}</span>}
                      <span>🕒 {new Date(alert.timestamp).toLocaleString()}</span>
                      <span>⚡ Risk +{alert.risk_score?.toFixed(0)}</span>
                    </div>
                  </div>
                  {/* Actions */}
                  <div style={{ display: 'flex', gap: 6, flexShrink: 0 }} onClick={(e) => e.stopPropagation()}>
                    {!alert.is_read && (
                      <button
                        className="btn btn-secondary btn-sm"
                        onClick={(e) => handleMarkRead(alert.id, e)}
                        title="Mark as read"
                      >
                        ✓
                      </button>
                    )}
                    {alert.status === 'open' && (
                      <button
                        className="btn btn-secondary btn-sm"
                        onClick={(e) => handleStatusChange(alert.id, 'investigating', e)}
                        style={{ fontSize: 11 }}
                      >
                        Investigate
                      </button>
                    )}
                    {alert.status === 'investigating' && (
                      <button
                        className="btn btn-secondary btn-sm"
                        onClick={(e) => handleStatusChange(alert.id, 'resolved', e)}
                        style={{ fontSize: 11, color: '#10b981' }}
                      >
                        Resolve
                      </button>
                    )}
                  </div>
                </div>
              </div>
            );
          })}
        </div>
      )}

      {/* ─── Pagination ─────────────────────────────────── */}
      {total > PER_PAGE && (
        <div style={{ display: 'flex', justifyContent: 'center', alignItems: 'center', gap: 12, marginTop: 20 }}>
          <button
            className="btn btn-secondary btn-sm"
            disabled={page === 1}
            onClick={() => setPage((p) => p - 1)}
          >
            ← Previous
          </button>
          <span style={{ color: '#64748b', fontSize: 13 }}>
            Page {page} of {Math.ceil(total / PER_PAGE)}
          </span>
          <button
            className="btn btn-secondary btn-sm"
            disabled={page >= Math.ceil(total / PER_PAGE)}
            onClick={() => setPage((p) => p + 1)}
          >
            Next →
          </button>
        </div>
      )}
    </div>
  );
}
