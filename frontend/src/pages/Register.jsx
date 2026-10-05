/**
 * pages/Register.jsx — User registration page.
 */
import { useState } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';
import toast from 'react-hot-toast';

export default function Register() {
  const [form, setForm] = useState({
    username: '', email: '', password: '',
    full_name: '', department: 'General', role: 'employee',
  });
  const [loading, setLoading] = useState(false);
  const { register } = useAuth();
  const navigate = useNavigate();

  const handleSubmit = async (e) => {
    e.preventDefault();
    if (form.password.length < 8) {
      toast.error('Password must be at least 8 characters');
      return;
    }
    setLoading(true);
    try {
      await register(form);
      toast.success('Account created! Welcome to ThreatSight AI.');
      navigate('/dashboard');
    } catch (err) {
      const msg = err.response?.data?.detail || 'Registration failed.';
      toast.error(msg);
    } finally {
      setLoading(false);
    }
  };

  const departments = ['Engineering', 'Finance', 'HR', 'Legal', 'Sales', 'IT', 'Marketing', 'Operations'];

  return (
    <div style={{
      minHeight: '100vh',
      background: 'var(--bg-primary)',
      display: 'flex', alignItems: 'center', justifyContent: 'center',
      position: 'relative', overflow: 'hidden',
      padding: '20px',
    }}>
      <div style={{
        position: 'absolute', inset: 0,
        background: `
          radial-gradient(ellipse at 80% 50%, rgba(99,102,241,0.08) 0%, transparent 50%),
          radial-gradient(ellipse at 20% 80%, rgba(6,182,212,0.05) 0%, transparent 40%)
        `,
        pointerEvents: 'none',
      }} />

      <div style={{
        width: '100%', maxWidth: 480,
        position: 'relative', zIndex: 1,
        animation: 'fadeInUp 0.5s ease forwards',
      }}>
        {/* Header */}
        <div style={{ textAlign: 'center', marginBottom: 28 }}>
          <div style={{
            display: 'inline-flex', width: 56, height: 56,
            background: 'linear-gradient(135deg, #6366f1, #4f46e5)',
            borderRadius: 14, alignItems: 'center', justifyContent: 'center',
            fontSize: 24, boxShadow: '0 0 25px rgba(99,102,241,0.4)',
            marginBottom: 14,
          }}>
            🛡️
          </div>
          <h1 style={{
            fontSize: '1.5rem', fontWeight: 900,
            background: 'linear-gradient(135deg, #e2e8f0, #6366f1)',
            WebkitBackgroundClip: 'text', WebkitTextFillColor: 'transparent',
            marginBottom: 4,
          }}>Create Account</h1>
          <p style={{ color: '#475569', fontSize: 13 }}>Join the ThreatSight AI Platform</p>
        </div>

        <div style={{
          background: 'var(--bg-card)',
          border: '1px solid rgba(99,102,241,0.2)',
          borderRadius: 'var(--radius-xl)',
          padding: '28px',
          boxShadow: '0 20px 60px rgba(0,0,0,0.4)',
        }}>
          <form onSubmit={handleSubmit}>
            <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 12 }}>
              <div className="input-group">
                <label className="input-label">Full Name</label>
                <input
                  id="reg-full-name"
                  type="text"
                  className="input"
                  placeholder="John Doe"
                  value={form.full_name}
                  onChange={(e) => setForm({ ...form, full_name: e.target.value })}
                  required
                />
              </div>
              <div className="input-group">
                <label className="input-label">Username</label>
                <input
                  id="reg-username"
                  type="text"
                  className="input"
                  placeholder="jdoe"
                  value={form.username}
                  onChange={(e) => setForm({ ...form, username: e.target.value })}
                  required
                  minLength={3}
                />
              </div>
            </div>

            <div className="input-group">
              <label className="input-label">Email Address</label>
              <input
                id="reg-email"
                type="email"
                className="input"
                placeholder="john.doe@company.com"
                value={form.email}
                onChange={(e) => setForm({ ...form, email: e.target.value })}
                required
              />
            </div>

            <div className="input-group">
              <label className="input-label">Password (min 8 chars)</label>
              <input
                id="reg-password"
                type="password"
                className="input"
                placeholder="••••••••"
                value={form.password}
                onChange={(e) => setForm({ ...form, password: e.target.value })}
                required
                minLength={8}
              />
            </div>

            <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 12 }}>
              <div className="input-group">
                <label className="input-label">Department</label>
                <select
                  id="reg-department"
                  className="input"
                  value={form.department}
                  onChange={(e) => setForm({ ...form, department: e.target.value })}
                  style={{ cursor: 'pointer' }}
                >
                  {departments.map((d) => <option key={d}>{d}</option>)}
                </select>
              </div>
              <div className="input-group">
                <label className="input-label">Role</label>
                <select
                  id="reg-role"
                  className="input"
                  value={form.role}
                  onChange={(e) => setForm({ ...form, role: e.target.value })}
                  style={{ cursor: 'pointer' }}
                >
                  <option value="employee">Employee</option>
                  <option value="analyst">Security Analyst</option>
                  <option value="admin">Administrator</option>
                </select>
              </div>
            </div>

            <button
              id="reg-submit"
              type="submit"
              className="btn btn-primary"
              style={{ width: '100%', justifyContent: 'center', padding: '12px', marginTop: 8 }}
              disabled={loading}
            >
              {loading ? (
                <><div className="spinner" style={{ width: 18, height: 18 }} /> Creating Account...</>
              ) : '🚀 Create Account'}
            </button>
          </form>

          <div style={{ textAlign: 'center', marginTop: 16, fontSize: 13, color: '#475569' }}>
            Already have an account?{' '}
            <Link to="/login" style={{ color: '#6366f1', fontWeight: 600 }}>Sign In</Link>
          </div>
        </div>
      </div>
    </div>
  );
}
