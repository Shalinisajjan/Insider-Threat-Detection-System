/**
 * components/Sidebar.jsx — Animated navigation sidebar.
 */
import { NavLink, useNavigate } from 'react-router-dom';
import { useState, useEffect } from 'react';
import { useAuth } from '../context/AuthContext';
import { alertsAPI } from '../api/axios';

const navItems = [
  { to: '/dashboard', icon: '⚡', label: 'Dashboard' },
  { to: '/alerts', icon: '🚨', label: 'Alerts', badge: true },
  { to: '/investigation', icon: '🔍', label: 'Investigation' },
  { to: '/analytics', icon: '📊', label: 'Analytics' },
  { to: '/models', icon: '🤖', label: 'ML Models' },
  { to: '/users', icon: '👥', label: 'Users', adminOnly: true },
  { to: '/profile', icon: '👤', label: 'Profile' },
];

export default function Sidebar() {
  const { user, logout, isAdmin } = useAuth();
  const navigate = useNavigate();
  const [unreadCount, setUnreadCount] = useState(0);
  const [collapsed, setCollapsed] = useState(false);

  useEffect(() => {
    const fetchAlertStats = async () => {
      try {
        const res = await alertsAPI.getStats();
        setUnreadCount(res.data.open || 0);
      } catch {}
    };
    fetchAlertStats();
    const interval = setInterval(fetchAlertStats, 30000);
    return () => clearInterval(interval);
  }, []);

  const handleLogout = () => {
    logout();
    navigate('/login');
  };

  const getRiskBadgeStyle = (level) => {
    if (level === 'HIGH') return { color: '#ef4444', background: 'rgba(239,68,68,0.15)' };
    if (level === 'MEDIUM') return { color: '#f59e0b', background: 'rgba(245,158,11,0.15)' };
    return { color: '#10b981', background: 'rgba(16,185,129,0.15)' };
  };

  return (
    <aside style={{
      position: 'fixed',
      top: 0, left: 0, bottom: 0,
      width: 'var(--sidebar-width)',
      background: 'var(--sidebar-bg)',
      borderRight: '1px solid rgba(255,255,255,0.06)',
      display: 'flex',
      flexDirection: 'column',
      zIndex: 100,
      transition: 'width 0.3s ease',
    }}>
      {/* ─── Logo ─────────────────────────────────────────── */}
      <div style={{
        padding: '20px 20px 16px',
        borderBottom: '1px solid rgba(255,255,255,0.06)',
      }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: 10 }}>
          <div style={{
            width: 36, height: 36,
            background: 'linear-gradient(135deg, #6366f1, #4f46e5)',
            borderRadius: 8,
            display: 'flex', alignItems: 'center', justifyContent: 'center',
            fontSize: 18,
            boxShadow: '0 0 15px rgba(99,102,241,0.4)',
            flexShrink: 0,
          }}>
            🛡️
          </div>
          <div>
            <div style={{ fontSize: 14, fontWeight: 800, color: '#e2e8f0', letterSpacing: '-0.01em' }}>
              ThreatSight
            </div>
            <div style={{ fontSize: 10, color: '#6366f1', fontWeight: 600, letterSpacing: '0.08em' }}>
              AI PLATFORM
            </div>
          </div>
        </div>
      </div>

      {/* ─── Nav Items ────────────────────────────────────── */}
      <nav style={{ padding: '12px 12px', flex: 1, overflow: 'auto' }}>
        <div style={{ fontSize: 10, color: '#475569', fontWeight: 700, letterSpacing: '0.08em', padding: '8px 8px 4px', textTransform: 'uppercase' }}>
          Navigation
        </div>
        {navItems
          .filter((item) => !item.adminOnly || isAdmin)
          .map((item) => (
            <NavLink
              key={item.to}
              to={item.to}
              style={({ isActive }) => ({
                display: 'flex',
                alignItems: 'center',
                gap: 10,
                padding: '10px 12px',
                borderRadius: 8,
                margin: '2px 0',
                fontSize: 14,
                fontWeight: 500,
                color: isActive ? '#e2e8f0' : '#94a3b8',
                background: isActive ? 'rgba(99,102,241,0.15)' : 'transparent',
                borderLeft: isActive ? '3px solid #6366f1' : '3px solid transparent',
                transition: 'all 0.2s',
                textDecoration: 'none',
                position: 'relative',
              })}
            >
              <span style={{ fontSize: 16 }}>{item.icon}</span>
              <span style={{ flex: 1 }}>{item.label}</span>
              {item.badge && unreadCount > 0 && (
                <span style={{
                  background: '#ef4444',
                  color: '#fff',
                  fontSize: 10,
                  fontWeight: 700,
                  padding: '1px 6px',
                  borderRadius: 10,
                  minWidth: 18,
                  textAlign: 'center',
                  animation: 'pulse-glow 2s infinite',
                }}>
                  {unreadCount > 99 ? '99+' : unreadCount}
                </span>
              )}
            </NavLink>
          ))}
      </nav>

      {/* ─── User info ─────────────────────────────────────── */}
      <div style={{
        padding: '16px',
        borderTop: '1px solid rgba(255,255,255,0.06)',
      }}>
        {user && (
          <div style={{
            background: 'rgba(255,255,255,0.03)',
            borderRadius: 10,
            padding: '12px',
            marginBottom: 10,
            border: '1px solid rgba(255,255,255,0.06)',
          }}>
            <div style={{ display: 'flex', alignItems: 'center', gap: 10, marginBottom: 8 }}>
              <div style={{
                width: 32, height: 32,
                background: 'linear-gradient(135deg, #6366f1, #4f46e5)',
                borderRadius: '50%',
                display: 'flex', alignItems: 'center', justifyContent: 'center',
                fontSize: 14, fontWeight: 700, color: '#fff',
                flexShrink: 0,
              }}>
                {user.full_name?.[0]?.toUpperCase() || 'U'}
              </div>
              <div style={{ overflow: 'hidden' }}>
                <div style={{ fontSize: 13, fontWeight: 600, color: '#e2e8f0', overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>
                  {user.full_name || user.username}
                </div>
                <div style={{ fontSize: 11, color: '#6366f1', fontWeight: 500 }}>
                  {user.role?.toUpperCase()}
                </div>
              </div>
            </div>
            {/* Risk score mini indicator */}
            <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
              <span style={{ fontSize: 11, color: '#475569' }}>Risk Score</span>
              <span style={{
                fontSize: 11, fontWeight: 700,
                padding: '1px 8px', borderRadius: 10,
                ...getRiskBadgeStyle(user.risk_level || 'LOW'),
              }}>
                {user.risk_score?.toFixed(0) || 0} — {user.risk_level || 'LOW'}
              </span>
            </div>
          </div>
        )}
        <button
          onClick={handleLogout}
          className="btn btn-secondary"
          style={{ width: '100%', justifyContent: 'center', fontSize: 13 }}
        >
          🚪 Sign Out
        </button>
      </div>
    </aside>
  );
}
