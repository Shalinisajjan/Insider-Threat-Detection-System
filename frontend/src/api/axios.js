/**
 * api/axios.js — Configured Axios instance with JWT interceptors.
 */
import axios from 'axios';

const API_BASE = import.meta.env.VITE_API_URL || '/api';

const api = axios.create({
  baseURL: API_BASE,
  timeout: 30000,
  headers: {
    'Content-Type': 'application/json',
  },
});

// ─── Request Interceptor ─────────────────────────────────────
api.interceptors.request.use(
  (config) => {
    const token = localStorage.getItem('access_token');
    if (token) {
      config.headers.Authorization = `Bearer ${token}`;
    }
    return config;
  },
  (error) => Promise.reject(error)
);

// ─── Response Interceptor ────────────────────────────────────
api.interceptors.response.use(
  (response) => response,
  async (error) => {
    const original = error.config;

    // If 401 and not already retrying — try refresh token
    if (error.response?.status === 401 && !original._retry) {
      original._retry = true;
      const refreshToken = localStorage.getItem('refresh_token');
      if (refreshToken) {
        try {
          const resp = await axios.post(`${API_BASE}/auth/refresh`, {
            refresh_token: refreshToken,
          });
          const newToken = resp.data.access_token;
          localStorage.setItem('access_token', newToken);
          original.headers.Authorization = `Bearer ${newToken}`;
          return api(original);
        } catch {
          // Refresh failed — clear tokens
          localStorage.removeItem('access_token');
          localStorage.removeItem('refresh_token');
          localStorage.removeItem('user');
          window.location.href = '/login';
        }
      } else {
        window.location.href = '/login';
      }
    }

    return Promise.reject(error);
  }
);

// ─── API service methods ─────────────────────────────────────

// Auth
export const authAPI = {
  register: (data) => api.post('/auth/register', data),
  login: (data) => api.post('/auth/login', data),
  getProfile: () => api.get('/auth/profile'),
  refresh: (refresh_token) => api.post('/auth/refresh', { refresh_token }),
};

// Users
export const usersAPI = {
  list: (params) => api.get('/users/', { params }),
  get: (id) => api.get(`/users/${id}`),
  update: (id, data) => api.patch(`/users/${id}`, data),
  delete: (id) => api.delete(`/users/${id}`),
  stats: () => api.get('/users/stats/overview'),
};

// Activity
export const activityAPI = {
  log: (data) => api.post('/activity/log', data),
  getUserActivities: (id, params) => api.get(`/activity/user/${id}`, { params }),
  getAll: (params) => api.get('/activity/all', { params }),
  getSummary: (id, params) => api.get(`/activity/summary/${id}`, { params }),
  getTimeline: (id, params) => api.get(`/activity/timeline/${id}`, { params }),
  getHeatmap: (id, params) => api.get(`/activity/heatmap/${id}`, { params }),
};

// Alerts
export const alertsAPI = {
  list: (params) => api.get('/alerts/', { params }),
  getStats: () => api.get('/alerts/stats'),
  getThreats: (params) => api.get('/alerts/threats', { params }),
  get: (id) => api.get(`/alerts/${id}`),
  update: (id, data) => api.patch(`/alerts/${id}`, data),
  markAllRead: () => api.post('/alerts/mark-all-read'),
};

// Risk
export const riskAPI = {
  getScore: (id) => api.get(`/risk/score/${id}`),
  getHistory: (id, params) => api.get(`/risk/history/${id}`, { params }),
  getLeaderboard: (params) => api.get('/risk/leaderboard', { params }),
  getOverview: () => api.get('/risk/analytics/overview'),
};

// Predictions
export const predictAPI = {
  predict: (data) => api.post('/predict/predict', data),
  detectAnomaly: (data) => api.post('/predict/anomaly-detect', data),
  getModelInfo: () => api.get('/predict/model-info'),
};

// Explain
export const explainAPI = {
  getExplanation: (id, params) => api.get(`/explain/explain/${id}`, { params }),
  getGlobalImportance: () => api.get('/explain/global-importance'),
};

// Reports
export const reportsAPI = {
  generate: (id) => api.get(`/reports/generate/${id}`, { responseType: 'blob' }),
  list: () => api.get('/reports/list'),
};

// Health
export const healthAPI = {
  check: () => api.get('/health'),
};

export default api;
