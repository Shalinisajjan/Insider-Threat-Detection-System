/**
 * pages/Login.jsx — Cybersecurity-themed login page.
 */
import { useState } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';
import toast from 'react-hot-toast';

export default function Login() {
  const [form, setForm] = useState({ email: '', password: '' });
  const [loading, setLoading] = useState(false);
  const { login } = useAuth();
  const navigate = useNavigate();

  const handleSubmit = async (e) => {
    e.preventDefault();
    setLoading(true);
    try {
      await login(form.email, form.password);
      toast.success('Welcome back! Accessing SOC Dashboard...');
      navigate('/dashboard');
    } catch (err) {
      const msg = err.response?.data?.detail || 'Login failed. Check your credentials.';
      toast.error(msg);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div style={{
      minHeight: '100vh',
      background: 'var(--bg-primary)',
      display: 'flex',
      alignItems: 'center',
      justifyContent: 'center',
      position: 'relative',
      overflow: 'hidden',
    }}>
      {/* Animated background */}
      <div style={{
        position: 'absolute', inset: 0,
        background: `
          radial-gradient(ellipse at 20% 50%, rgba(99,102,241,0.08) 0%, transparent 50%),
          radial-gradient(ellipse at 80% 20%, rgba(6,182,212,0.05) 0%, transparent 40%)
        `,
        pointerEvents: 'none',
      }} />

      {/* Grid lines */}
      <div style={{
        position: 'absolute', inset: 0,
        backgroundImage: `
          linear-gradient(rgba(99,102,241,0.03) 1px, transparent 1px),
          linear-gradient(90deg, rgba(99,102,241,0.03) 1px, transparent 1px)
        `,
        backgroundSize: '60px 60px',
        pointerEvents: 'none',
      }} />

      <div style={{
        width: '100%', maxWidth: 420,
        padding: '0 20px',
        position: 'relative', zIndex: 1,
        animation: 'fadeInUp 0.5s ease forwards',
      }}>
        {/* Logo */}
        <div style={{ textAlign: 'center', marginBottom: 32 }}>
          <div style={{
            display: 'inline-flex',
            width: 64, height: 64,
            background: 'linear-gradient(135deg, #6366f1, #4f46e5)',
            borderRadius: 16,
            alignItems: 'center', justifyContent: 'center',
            fontSize: 28,
            boxShadow: '0 0 30px rgba(99,102,241,0.4)',
            marginBottom: 16,
            animation: 'float 3s ease-in-out infinite',
          }}>
            🛡️
          </div>
          <h1 style={{
            fontSize: '1.75rem',
            fontWeight: 900,
            background: 'linear-gradient(135deg, #e2e8f0, #6366f1)',
            WebkitBackgroundClip: 'text',
            WebkitTextFillColor: 'transparent',
            marginBottom: 6,
          }}>
            ThreatSight AI
          </h1>
          <p style={{ color: '#475569', fontSize: 14 }}>
            Insider Threat Intelligence Platform
          </p>
        </div>

        {/* Card */}
        <div style={{
          background: 'var(--bg-card)',
          border: '1px solid rgba(99,102,241,0.2)',
          borderRadius: 'var(--radius-xl)',
          padding: '32px',
          boxShadow: '0 20px 60px rgba(0,0,0,0.4)',
        }}>
          <h2 style={{ fontSize: '1.1rem', fontWeight: 700, color: '#e2e8f0', marginBottom: 24 }}>
            Sign In to SOC Dashboard
          </h2>

          <form onSubmit={handleSubmit}>
            <div className="input-group">
              <label className="input-label">Email Address</label>
              <input
                id="login-email"
                type="email"
                className="input"
                placeholder="analyst@company.com"
                value={form.email}
                onChange={(e) => setForm({ ...form, email: e.target.value })}
                required
                autoComplete="email"
              />
            </div>

            <div className="input-group">
              <label className="input-label">Password</label>
              <input
                id="login-password"
                type="password"
                className="input"
                placeholder="••••••••"
                value={form.password}
                onChange={(e) => setForm({ ...form, password: e.target.value })}
                required
                autoComplete="current-password"
              />
            </div>

            <button
              id="login-submit"
              type="submit"
              className="btn btn-primary"
              style={{ width: '100%', justifyContent: 'center', padding: '13px', fontSize: 15, marginTop: 8 }}
              disabled={loading}
            >
              {loading ? (
                <>
                  <div className="spinner" style={{ width: 18, height: 18 }} />
                  Authenticating...
                </>
              ) : (
                <>🔐 Sign In</>
              )}
            </button>
          </form>

          <div style={{ textAlign: 'center', marginTop: 20, fontSize: 13, color: '#475569' }}>
            No account?{' '}
            <Link to="/register" style={{ color: '#6366f1', fontWeight: 600 }}>
              Request Access
            </Link>
          </div>

          {/* Demo credentials */}
          <div style={{
            marginTop: 20,
            padding: '12px',
            background: 'rgba(99,102,241,0.06)',
            border: '1px solid rgba(99,102,241,0.15)',
            borderRadius: 8,
            fontSize: 12,
            color: '#64748b',
          }}>
            <div style={{ fontWeight: 700, color: '#818cf8', marginBottom: 4 }}>📋 Demo Credentials</div>
            <div>Email: <span style={{ fontFamily: 'monospace', color: '#94a3b8' }}>admin@threatsight.ai</span></div>
            <div>Password: <span style={{ fontFamily: 'monospace', color: '#94a3b8' }}>Admin@123456</span></div>
          </div>
        </div>

        {/* Version tag */}
        <div style={{ textAlign: 'center', marginTop: 16, fontSize: 12, color: '#334155' }}>
          ThreatSight AI v1.0 · Academic Research Edition
        </div>
      </div>
    </div>
  );
}
