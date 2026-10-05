/**
 * pages/UserManagement.jsx — Admin user management page.
 */
import { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { usersAPI } from '../api/axios';
import { useAuth } from '../context/AuthContext';
import toast from 'react-hot-toast';

const RISK_COLOR = { HIGH: '#ef4444', MEDIUM: '#f59e0b', LOW: '#10b981' };
const ROLE_BADGE = {
  admin: { bg: 'rgba(99,102,241,0.15)', color: '#818cf8', label: 'Admin' },
  analyst: { bg: 'rgba(6,182,212,0.15)', color: '#22d3ee', label: 'Analyst' },
  employee: { bg: 'rgba(255,255,255,0.08)', color: '#94a3b8', label: 'Employee' },
};

export default function UserManagement() {
  const { isAdmin } = useAuth();
  const navigate = useNavigate();
  const [users, setUsers] = useState([]);
  const [stats, setStats] = useState({});
  const [loading, setLoading] = useState(true);
  const [search, setSearch] = useState('');
  const [roleFilter, setRoleFilter] = useState('');
  const [page, setPage] = useState(1);
  const [total, setTotal] = useState(0);
  const [editingUser, setEditingUser] = useState(null);
  const [editForm, setEditForm] = useState({});
  const PER_PAGE = 15;

  useEffect(() => {
    fetchData();
  }, [search, roleFilter, page]);

  const fetchData = async () => {
    setLoading(true);
    try {
      const params = { page, per_page: PER_PAGE };
      if (search) params.search = search;
      if (roleFilter) params.role = roleFilter;

      const [usersRes, statsRes] = await Promise.all([
        usersAPI.list(params),
        usersAPI.stats(),
      ]);
      setUsers(usersRes.data.users || []);
      setTotal(usersRes.data.total || 0);
      setStats(statsRes.data);
    } catch {
      toast.error('Failed to load users');
    } finally {
      setLoading(false);
    }
  };

  const handleToggleActive = async (userId, currentStatus) => {
    if (!isAdmin) { toast.error('Admin access required'); return; }
    try {
      await usersAPI.update(userId, { is_active: !currentStatus });
      toast.success(`User ${currentStatus ? 'disabled' : 'enabled'}`);
      fetchData();
    } catch { toast.error('Update failed'); }
  };

  const handleRoleChange = async (userId, newRole) => {
    if (!isAdmin) { toast.error('Admin access required'); return; }
    try {
      await usersAPI.update(userId, { role: newRole });
      toast.success(`Role updated to ${newRole}`);
      fetchData();
    } catch { toast.error('Role update failed'); }
  };

  const handleDelete = async (userId) => {
    if (!isAdmin) { toast.error('Admin access required'); return; }
    if (!window.confirm('Deactivate this user account?')) return;
    try {
      await usersAPI.delete(userId);
      toast.success('User deactivated');
      fetchData();
    } catch { toast.error('Delete failed'); }
  };

  return (
    <div style={{ animation: 'fadeInUp 0.4s ease forwards' }}>
      {/* Header */}
      <div className="page-header">
        <div>
          <h1 className="page-title">👥 User Management</h1>
          <p className="page-subtitle">{total} total users · {stats.active_users || 0} active · {stats.high_risk_users || 0} high risk</p>
        </div>
      </div>

      {/* Stats */}
      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(4, 1fr)', gap: 14, marginBottom: 20 }}>
        {[
          { label: 'Total Users', value: stats.total_users || 0, color: '#6366f1' },
          { label: 'Active', value: stats.active_users || 0, color: '#10b981' },
          { label: 'High Risk', value: stats.high_risk_users || 0, color: '#ef4444' },
          { label: 'Admins', value: stats.role_breakdown?.admin || 0, color: '#818cf8' },
        ].map((s, i) => (
          <div key={i} style={{
            background: 'var(--bg-card)', border: '1px solid rgba(255,255,255,0.06)',
            borderRadius: 10, padding: '14px 18px', display: 'flex', alignItems: 'center', gap: 12,
          }}>
            <div style={{ fontSize: 20, fontWeight: 900, color: s.color }}>{s.value}</div>
            <div style={{ fontSize: 11, color: '#475569', textTransform: 'uppercase', letterSpacing: '0.05em' }}>{s.label}</div>
          </div>
        ))}
      </div>

      {/* Filters */}
      <div style={{
        display: 'flex', gap: 12, marginBottom: 16, background: 'var(--bg-card)',
        padding: '14px', borderRadius: 10, border: '1px solid rgba(255,255,255,0.06)',
      }}>
        <input
          className="input"
          style={{ flex: 1, maxWidth: 300 }}
          placeholder="🔍 Search by name, username, or email..."
          value={search}
          onChange={(e) => { setSearch(e.target.value); setPage(1); }}
        />
        <select
          className="input"
          style={{ width: 'auto', minWidth: 140 }}
          value={roleFilter}
          onChange={(e) => { setRoleFilter(e.target.value); setPage(1); }}
        >
          <option value="">All Roles</option>
          <option value="admin">Admin</option>
          <option value="analyst">Analyst</option>
          <option value="employee">Employee</option>
        </select>
        <button className="btn btn-secondary btn-sm" onClick={() => { setSearch(''); setRoleFilter(''); setPage(1); }}>
          ✕ Clear
        </button>
      </div>

      {/* Table */}
      <div className="card" style={{ padding: 0, overflow: 'hidden' }}>
        {loading ? (
          <div style={{ display: 'flex', justifyContent: 'center', padding: 40 }}>
            <div className="spinner" style={{ width: 32, height: 32 }} />
          </div>
        ) : users.length === 0 ? (
          <div className="empty-state"><div className="empty-state-icon">👤</div><div className="empty-state-text">No users found</div></div>
        ) : (
          <table className="data-table">
            <thead>
              <tr>
                <th>User</th>
                <th>Department</th>
                <th>Role</th>
                <th>Risk Level</th>
                <th>Status</th>
                <th>Last Login</th>
                <th>Actions</th>
              </tr>
            </thead>
            <tbody>
              {users.map((u) => {
                const roleBadge = ROLE_BADGE[u.role] || ROLE_BADGE.employee;
                const rColor = RISK_COLOR[u.risk_level] || '#10b981';
                return (
                  <tr key={u.id}>
                    <td>
                      <div style={{ display: 'flex', alignItems: 'center', gap: 10 }}>
                        <div style={{
                          width: 32, height: 32,
                          background: 'linear-gradient(135deg, #6366f1, #4f46e5)',
                          borderRadius: '50%',
                          display: 'flex', alignItems: 'center', justifyContent: 'center',
                          fontSize: 12, fontWeight: 700, color: '#fff', flexShrink: 0,
                        }}>
                          {u.full_name?.[0] || '?'}
                        </div>
                        <div>
                          <div style={{ fontSize: 13, fontWeight: 600, color: '#e2e8f0' }}>{u.full_name}</div>
                          <div style={{ fontSize: 11, color: '#475569' }}>@{u.username}</div>
                        </div>
                      </div>
                    </td>
                    <td style={{ fontSize: 12, color: '#64748b' }}>{u.department}</td>
                    <td>
                      <select
                        style={{
                          background: roleBadge.bg, color: roleBadge.color,
                          border: 'none', borderRadius: 20, padding: '3px 10px',
                          fontSize: 11, fontWeight: 700, cursor: isAdmin ? 'pointer' : 'default',
                          fontFamily: 'var(--font-primary)',
                        }}
                        value={u.role}
                        onChange={(e) => handleRoleChange(u.id, e.target.value)}
                        disabled={!isAdmin}
                      >
                        <option value="admin">Admin</option>
                        <option value="analyst">Analyst</option>
                        <option value="employee">Employee</option>
                      </select>
                    </td>
                    <td>
                      <div style={{ display: 'flex', alignItems: 'center', gap: 6 }}>
                        <div style={{ width: 8, height: 8, borderRadius: '50%', background: rColor, boxShadow: `0 0 6px ${rColor}` }} />
                        <span style={{ fontSize: 12, fontWeight: 700, color: rColor }}>{u.risk_level}</span>
                        <span style={{ fontSize: 11, color: '#475569' }}>({u.risk_score?.toFixed(0)})</span>
                      </div>
                    </td>
                    <td>
                      <span style={{
                        fontSize: 11, fontWeight: 600, padding: '2px 10px', borderRadius: 20,
                        background: u.is_active ? 'rgba(16,185,129,0.15)' : 'rgba(239,68,68,0.15)',
                        color: u.is_active ? '#34d399' : '#f87171',
                      }}>
                        {u.is_active ? '● Active' : '○ Disabled'}
                      </span>
                    </td>
                    <td style={{ fontSize: 11, color: '#475569' }}>
                      {u.last_login ? new Date(u.last_login).toLocaleDateString() : 'Never'}
                    </td>
                    <td>
                      <div style={{ display: 'flex', gap: 6 }}>
                        <button
                          className="btn btn-secondary btn-sm"
                          onClick={() => navigate(`/investigation/${u.id}`)}
                          title="Investigate"
                        >🔍</button>
                        {isAdmin && (
                          <>
                            <button
                              className="btn btn-secondary btn-sm"
                              onClick={() => handleToggleActive(u.id, u.is_active)}
                              style={{ color: u.is_active ? '#f87171' : '#34d399' }}
                              title={u.is_active ? 'Disable' : 'Enable'}
                            >
                              {u.is_active ? '🚫' : '✅'}
                            </button>
                          </>
                        )}
                      </div>
                    </td>
                  </tr>
                );
              })}
            </tbody>
          </table>
        )}
      </div>

      {/* Pagination */}
      {total > PER_PAGE && (
        <div style={{ display: 'flex', justifyContent: 'center', alignItems: 'center', gap: 12, marginTop: 16 }}>
          <button className="btn btn-secondary btn-sm" disabled={page === 1} onClick={() => setPage((p) => p - 1)}>← Previous</button>
          <span style={{ color: '#64748b', fontSize: 13 }}>Page {page} of {Math.ceil(total / PER_PAGE)}</span>
          <button className="btn btn-secondary btn-sm" disabled={page >= Math.ceil(total / PER_PAGE)} onClick={() => setPage((p) => p + 1)}>Next →</button>
        </div>
      )}
    </div>
  );
}
