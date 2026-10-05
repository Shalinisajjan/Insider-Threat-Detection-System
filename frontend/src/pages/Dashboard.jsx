/**
 * pages/Dashboard.jsx — Main SOC Overview Dashboard.
 * Real-time stats, threat trends, risk leaderboard, and recent alerts.
 */
import { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import {
  AreaChart, Area, LineChart, Line, BarChart, Bar,
  XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer,
  PieChart, Pie, Cell, Legend,
} from 'recharts';
import { usersAPI, alertsAPI, riskAPI, activityAPI } from '../api/axios';
import toast from 'react-hot-toast';
import ActivityHeatmap from '../components/charts/ActivityHeatmap';

// ─── Helpers ──────────────────────────────────────────────────
const getRiskColor = (level) => {
  if (level === 'HIGH') return '#ef4444';
  if (level === 'MEDIUM') return '#f59e0b';
  return '#10b981';
};

const SEVERITY_COLORS = {
  critical: '#ef4444', high: '#f97316', medium: '#f59e0b', low: '#10b981',
};

const CustomTooltip = ({ active, payload, label }) => {
  if (!active || !payload?.length) return null;
  return (
    <div style={{
      background: '#0f1e36', border: '1px solid rgba(99,102,241,0.3)',
      borderRadius: 8, padding: '10px 14px', fontSize: 12,
    }}>
      <div style={{ color: '#94a3b8', marginBottom: 4 }}>{label}</div>
      {payload.map((p, i) => (
        <div key={i} style={{ color: p.color, fontWeight: 600 }}>
          {p.name}: {p.value}
        </div>
      ))}
    </div>
  );
};

export default function Dashboard() {
  const navigate = useNavigate();
  const [loading, setLoading] = useState(true);
  const [stats, setStats] = useState({
    totalUsers: 0, activeAlerts: 0, highRiskUsers: 0, avgRiskScore: 0,
  });
  const [alertStats, setAlertStats] = useState({});
  const [userStats, setUserStats] = useState({});
  const [threatTrends, setThreatTrends] = useState([]);
  const [riskLeaderboard, setRiskLeaderboard] = useState([]);
  const [recentAlerts, setRecentAlerts] = useState([]);
  const [selectedHeatmapUser, setSelectedHeatmapUser] = useState(null);
  const [heatmapData, setHeatmapData] = useState({});
  const [heatmapLoading, setHeatmapLoading] = useState(false);

  useEffect(() => {
    fetchDashboardData();
  }, []);

  const fetchUserHeatmap = async (userId) => {
    setHeatmapLoading(true);
    try {
      const res = await activityAPI.getHeatmap(userId, { days: 30 });
      setHeatmapData(res.data.heatmap || {});
    } catch (err) {
      console.error('Error fetching heatmap:', err);
    } finally {
      setHeatmapLoading(false);
    }
  };

  const fetchDashboardData = async () => {
    try {
      const [alertStatsRes, userStatsRes, threatsRes, leaderboardRes, recentAlertsRes, riskOverviewRes] =
        await Promise.allSettled([
          alertsAPI.getStats(),
          usersAPI.stats(),
          alertsAPI.getThreats({ days: 14 }),
          riskAPI.getLeaderboard({ limit: 8 }),
          alertsAPI.list({ per_page: 6, days: 7 }),
          riskAPI.getOverview(),
        ]);

      if (alertStatsRes.status === 'fulfilled') setAlertStats(alertStatsRes.value.data);
      if (userStatsRes.status === 'fulfilled') setUserStats(userStatsRes.value.data);
      if (threatsRes.status === 'fulfilled') setThreatTrends(threatsRes.value.data.trends || []);
      
      let topUser = null;
      if (leaderboardRes.status === 'fulfilled') {
        const leaderboard = leaderboardRes.value.data.users || [];
        setRiskLeaderboard(leaderboard);
        if (leaderboard.length > 0) {
          topUser = leaderboard[0];
          setSelectedHeatmapUser(leaderboard[0]);
        }
      }
      
      if (recentAlertsRes.status === 'fulfilled') setRecentAlerts(recentAlertsRes.value.data.alerts || []);

      const aData = alertStatsRes.status === 'fulfilled' ? alertStatsRes.value.data : {};
      const uData = userStatsRes.status === 'fulfilled' ? userStatsRes.value.data : {};
      const rData = riskOverviewRes.status === 'fulfilled' ? riskOverviewRes.value.data : {};

      setStats({
        totalUsers: uData.total_users || 0,
        activeAlerts: aData.open || 0,
        highRiskUsers: uData.high_risk_users || 0,
        avgRiskScore: rData.average_risk_score || 0,
      });

      if (topUser) {
        await fetchUserHeatmap(topUser.user_id);
      }
    } catch (err) {
      console.error('Dashboard fetch error:', err);
    } finally {
      setLoading(false);
    }
  };

  // Stat cards config
  const statCards = [
    {
      label: 'Total Users', value: stats.totalUsers, icon: '👥',
      color: '#6366f1', bgColor: 'rgba(99,102,241,0.15)',
      sub: `${userStats.active_users || 0} active`,
    },
    {
      label: 'Active Alerts', value: stats.activeAlerts, icon: '🚨',
      color: '#ef4444', bgColor: 'rgba(239,68,68,0.15)',
      sub: `${alertStats.critical || 0} critical`,
      alert: stats.activeAlerts > 0,
    },
    {
      label: 'High Risk Users', value: stats.highRiskUsers, icon: '⚠️',
      color: '#f59e0b', bgColor: 'rgba(245,158,11,0.15)',
      sub: `${userStats.medium_risk_users || 0} medium risk`,
    },
    {
      label: 'Avg Risk Score', value: `${stats.avgRiskScore}`, icon: '📊',
      color: '#10b981', bgColor: 'rgba(16,185,129,0.15)',
      sub: 'Platform-wide average',
    },
  ];

  // Pie chart data for alert distribution
  const alertPieData = [
    { name: 'Critical', value: alertStats.critical || 0, color: '#ef4444' },
    { name: 'High', value: alertStats.high || 0, color: '#f97316' },
    { name: 'Medium', value: alertStats.medium || 0, color: '#f59e0b' },
    { name: 'Low', value: alertStats.low || 0, color: '#10b981' },
  ].filter((d) => d.value > 0);

  if (loading) {
    return (
      <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'center', height: '60vh' }}>
        <div style={{ textAlign: 'center' }}>
          <div className="spinner" style={{ width: 40, height: 40, margin: '0 auto 12px' }} />
          <div style={{ color: '#64748b', fontSize: 14 }}>Loading SOC Dashboard...</div>
        </div>
      </div>
    );
  }

  return (
    <div style={{ animation: 'fadeInUp 0.4s ease forwards' }}>
      {/* ─── Page Header ─────────────────────────────────── */}
      <div className="page-header">
        <div>
          <h1 className="page-title">🛡️ SOC Dashboard</h1>
          <p className="page-subtitle">Real-time insider threat monitoring · {new Date().toLocaleDateString('en-US', { weekday: 'long', year: 'numeric', month: 'long', day: 'numeric' })}</p>
        </div>
        <div style={{ display: 'flex', gap: 10 }}>
          <button className="btn btn-secondary btn-sm" onClick={fetchDashboardData}>
            🔄 Refresh
          </button>
          <button className="btn btn-primary btn-sm" onClick={() => navigate('/alerts')}>
            View All Alerts
          </button>
        </div>
      </div>

      {/* ─── Stat Cards ─────────────────────────────────── */}
      <div className="grid-4" style={{ marginBottom: 24 }}>
        {statCards.map((card, i) => (
          <div
            key={i}
            className="stat-card"
            style={{
              borderColor: card.alert ? 'rgba(239,68,68,0.4)' : 'rgba(255,255,255,0.06)',
              animation: card.alert ? 'pulse-danger 2s infinite' : 'none',
              animationDelay: `${i * 0.1}s`,
            }}
          >
            <div className="stat-icon" style={{ background: card.bgColor, color: card.color }}>
              {card.icon}
            </div>
            <div>
              <div className="stat-value" style={{ color: card.color, WebkitTextFillColor: card.color }}>
                {card.value}
              </div>
              <div className="stat-label">{card.label}</div>
              <div style={{ fontSize: 11, color: '#475569', marginTop: 2 }}>{card.sub}</div>
            </div>
          </div>
        ))}
      </div>

      {/* ─── Charts Row 1 ────────────────────────────────── */}
      <div className="grid-2" style={{ marginBottom: 24 }}>
        {/* Threat Trend Area Chart */}
        <div className="chart-container">
          <div className="chart-title">📈 Threat Trend (14 Days)</div>
          {threatTrends.length > 0 ? (
            <ResponsiveContainer width="100%" height={220}>
              <AreaChart data={threatTrends}>
                <defs>
                  <linearGradient id="criticalGrad" x1="0" y1="0" x2="0" y2="1">
                    <stop offset="5%" stopColor="#ef4444" stopOpacity={0.3} />
                    <stop offset="95%" stopColor="#ef4444" stopOpacity={0} />
                  </linearGradient>
                  <linearGradient id="highGrad" x1="0" y1="0" x2="0" y2="1">
                    <stop offset="5%" stopColor="#f97316" stopOpacity={0.2} />
                    <stop offset="95%" stopColor="#f97316" stopOpacity={0} />
                  </linearGradient>
                  <linearGradient id="medGrad" x1="0" y1="0" x2="0" y2="1">
                    <stop offset="5%" stopColor="#f59e0b" stopOpacity={0.15} />
                    <stop offset="95%" stopColor="#f59e0b" stopOpacity={0} />
                  </linearGradient>
                </defs>
                <CartesianGrid strokeDasharray="3 3" stroke="rgba(255,255,255,0.04)" />
                <XAxis dataKey="date" tick={{ fontSize: 10, fill: '#475569' }} tickFormatter={(v) => v.slice(5)} />
                <YAxis tick={{ fontSize: 10, fill: '#475569' }} />
                <Tooltip content={<CustomTooltip />} />
                <Area type="monotone" dataKey="critical" stroke="#ef4444" fill="url(#criticalGrad)" strokeWidth={2} name="Critical" />
                <Area type="monotone" dataKey="high" stroke="#f97316" fill="url(#highGrad)" strokeWidth={2} name="High" />
                <Area type="monotone" dataKey="medium" stroke="#f59e0b" fill="url(#medGrad)" strokeWidth={2} name="Medium" />
              </AreaChart>
            </ResponsiveContainer>
          ) : (
            <div className="empty-state">
              <div className="empty-state-icon">📊</div>
              <div className="empty-state-text">No threat data yet. System monitoring active.</div>
            </div>
          )}
        </div>

        {/* Alert Severity Pie Chart */}
        <div className="chart-container">
          <div className="chart-title">🎯 Alert Severity Distribution</div>
          {alertPieData.length > 0 ? (
            <ResponsiveContainer width="100%" height={220}>
              <PieChart>
                <Pie
                  data={alertPieData}
                  cx="50%" cy="50%"
                  innerRadius={60} outerRadius={90}
                  paddingAngle={3}
                  dataKey="value"
                >
                  {alertPieData.map((entry, i) => (
                    <Cell key={i} fill={entry.color} strokeWidth={0} />
                  ))}
                </Pie>
                <Legend
                  formatter={(value, entry) => (
                    <span style={{ color: '#94a3b8', fontSize: 12 }}>{value}: {entry.payload.value}</span>
                  )}
                />
                <Tooltip
                  formatter={(value, name) => [value, name]}
                  contentStyle={{ background: '#0f1e36', border: '1px solid rgba(99,102,241,0.2)', borderRadius: 8, fontSize: 12 }}
                />
              </PieChart>
            </ResponsiveContainer>
          ) : (
            <div className="empty-state">
              <div className="empty-state-icon">✅</div>
              <div className="empty-state-text">No active alerts. System is secure.</div>
            </div>
          )}
        </div>
      </div>

      {/* ─── Bottom Row ──────────────────────────────────── */}
      <div className="grid-2" style={{ marginBottom: 24 }}>
        {/* Risk Leaderboard */}
        <div className="card">
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 16 }}>
            <div className="chart-title" style={{ margin: 0 }}>⚠️ High Risk Users</div>
            <button className="btn btn-secondary btn-sm" onClick={() => navigate('/analytics')}>
              View All
            </button>
          </div>
          {riskLeaderboard.length > 0 ? (
            <div style={{ display: 'flex', flexDirection: 'column', gap: 8 }}>
              {riskLeaderboard.slice(0, 6).map((user, i) => (
                <div
                  key={i}
                  style={{
                    display: 'flex', alignItems: 'center', gap: 12,
                    padding: '10px 12px',
                    background: selectedHeatmapUser?.user_id === user.user_id ? 'rgba(99,102,241,0.12)' : 'rgba(255,255,255,0.02)',
                    borderRadius: 8,
                    border: selectedHeatmapUser?.user_id === user.user_id ? '1px solid rgba(99,102,241,0.3)' : '1px solid rgba(255,255,255,0.04)',
                    cursor: 'pointer',
                    transition: 'all 0.2s',
                  }}
                  onClick={() => {
                    setSelectedHeatmapUser(user);
                    fetchUserHeatmap(user.user_id);
                  }}
                >
                  <div style={{
                    width: 28, height: 28,
                    background: 'linear-gradient(135deg, #6366f1, #4f46e5)',
                    borderRadius: '50%',
                    display: 'flex', alignItems: 'center', justifyContent: 'center',
                    fontSize: 11, fontWeight: 700, color: '#fff', flexShrink: 0,
                  }}>
                    {user.full_name?.[0] || user.username?.[0] || '?'}
                  </div>
                  <div style={{ flex: 1, overflow: 'hidden' }}>
                    <div style={{ fontSize: 13, fontWeight: 600, color: '#e2e8f0', overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>
                      {user.full_name || user.username}
                    </div>
                    <div style={{ fontSize: 11, color: '#475569' }}>{user.department}</div>
                  </div>
                  <div style={{ display: 'flex', alignItems: 'center', gap: 10 }}>
                    <div style={{ textAlign: 'right' }}>
                      <div style={{
                        fontSize: 13, fontWeight: 800,
                        color: getRiskColor(user.risk_level),
                      }}>
                        {user.risk_score?.toFixed(0)}
                      </div>
                      <div style={{
                        fontSize: 10, fontWeight: 600,
                        color: getRiskColor(user.risk_level),
                        textTransform: 'uppercase',
                      }}>
                        {user.risk_level}
                      </div>
                    </div>
                    <button
                      className="btn btn-secondary btn-sm"
                      style={{ padding: '4px 8px', fontSize: 11 }}
                      onClick={(e) => {
                        e.stopPropagation();
                        navigate(`/investigation/${user.user_id}`);
                      }}
                    >
                      🔍
                    </button>
                  </div>
                </div>
              ))}
            </div>
          ) : (
            <div className="empty-state">
              <div className="empty-state-icon">✅</div>
              <div className="empty-state-text">No high-risk users detected.</div>
            </div>
          )}
        </div>

        {/* Recent Alerts */}
        <div className="card">
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 16 }}>
            <div className="chart-title" style={{ margin: 0 }}>🚨 Recent Alerts</div>
            <button className="btn btn-secondary btn-sm" onClick={() => navigate('/alerts')}>
              View All
            </button>
          </div>
          {recentAlerts.length > 0 ? (
            <div style={{ display: 'flex', flexDirection: 'column', gap: 8 }}>
              {recentAlerts.map((alert, i) => (
                <div
                  key={i}
                  style={{
                    padding: '10px 12px',
                    background: 'rgba(255,255,255,0.02)',
                    borderRadius: 8,
                    border: `1px solid ${alert.is_read ? 'rgba(255,255,255,0.04)' : 'rgba(239,68,68,0.2)'}`,
                    cursor: 'pointer',
                    transition: 'all 0.2s',
                    borderLeft: `3px solid ${SEVERITY_COLORS[alert.severity] || '#6366f1'}`,
                  }}
                  onClick={() => navigate('/alerts')}
                >
                  <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start' }}>
                    <div style={{ fontSize: 13, fontWeight: 600, color: '#e2e8f0', flex: 1 }}>
                      {!alert.is_read && <span style={{ color: '#ef4444', marginRight: 4 }}>●</span>}
                      {alert.title}
                    </div>
                    <span className={`badge badge-${alert.severity}`} style={{ marginLeft: 8, flexShrink: 0 }}>
                      {alert.severity}
                    </span>
                  </div>
                  <div style={{ fontSize: 11, color: '#475569', marginTop: 4 }}>
                    {alert.username && `@${alert.username} · `}
                    {new Date(alert.timestamp).toLocaleString()}
                  </div>
                </div>
              ))}
            </div>
          ) : (
            <div className="empty-state">
              <div className="empty-state-icon">✅</div>
              <div className="empty-state-text">No recent alerts.</div>
            </div>
          )}
        </div>
      </div>

      {/* ─── Heatmap Row ─────────────────────────────────── */}
      {selectedHeatmapUser && (
        <div className="card" style={{ marginBottom: 24, animation: 'fadeInUp 0.4s ease forwards' }}>
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 16 }}>
            <div>
              <h3 className="chart-title" style={{ margin: 0 }}>🕵️ User Behavior Heatmap — {selectedHeatmapUser.full_name || selectedHeatmapUser.username}</h3>
              <p style={{ fontSize: 12, color: '#64748b', margin: '4px 0 0' }}>
                Activity density by hour of day and day of week (past 30 days) · Department: {selectedHeatmapUser.department}
              </p>
            </div>
            <button className="btn btn-primary btn-sm" onClick={() => navigate(`/investigation/${selectedHeatmapUser.user_id}`)}>
              🔍 Open Investigation Profile
            </button>
          </div>
          <ActivityHeatmap heatmap={heatmapData} loading={heatmapLoading} />
        </div>
      )}
    </div>
  );
}
