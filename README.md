# 🛡️ AI-Powered Explainable Insider Threat Intelligence Platform

<div align="center">

![ThreatSight AI Banner](https://img.shields.io/badge/ThreatSight-AI_Platform-6366f1?style=for-the-badge&logo=shield&logoColor=white)
![Python](https://img.shields.io/badge/Python-3.11-3776AB?style=for-the-badge&logo=python&logoColor=white)
![FastAPI](https://img.shields.io/badge/FastAPI-0.111-009688?style=for-the-badge&logo=fastapi&logoColor=white)
![React](https://img.shields.io/badge/React-18-61DAFB?style=for-the-badge&logo=react&logoColor=black)
![MongoDB](https://img.shields.io/badge/MongoDB-7.0-47A248?style=for-the-badge&logo=mongodb&logoColor=white)
![Docker](https://img.shields.io/badge/Docker-Ready-2496ED?style=for-the-badge&logo=docker&logoColor=white)

**Enterprise-grade AI-powered insider threat detection with UEBA, ML/DL, and SHAP explainability**

[🚀 Quick Start](#-quick-start) · [📖 Documentation](#-documentation) · [🤖 ML Models](#-ml-models) · [🔌 API Reference](#-api-reference)

</div>

---

## 📋 Overview

**ThreatSight AI** is a complete, production-ready academic-grade platform for detecting malicious insider activities within organizations using:

- **User Behavior Analytics (UEBA)** — Real-time behavioral profiling
- **Machine Learning** — Random Forest + XGBoost ensemble classification
- **Deep Learning** — Bidirectional LSTM for sequential pattern analysis
- **Anomaly Detection** — Isolation Forest for unsupervised threat detection
- **Explainable AI (SHAP)** — Human-readable threat explanations
- **Dynamic Risk Scoring** — Weighted real-time risk assessment
- **SOC Dashboard** — Enterprise-grade security operations center UI
- **PDF Reporting** — Automated incident investigation reports

Inspired by: **Splunk UEBA · Microsoft Defender Insider Risk · Exabeam · CrowdStrike Falcon**

---

## 🏗️ Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                      Nginx Reverse Proxy                     │
│                         (Port 80)                           │
└──────────────────┬───────────────────┬──────────────────────┘
                   │                   │
         ┌─────────▼──────┐   ┌───────▼────────┐
         │  React Frontend │   │  FastAPI Backend│
         │  (Vite + Tailwind│   │  (Python 3.11) │
         │   Recharts +    │   │  JWT Auth + RBAC│
         │   Framer Motion)│   │  REST APIs     │
         └─────────────────┘   └───────┬────────┘
                                       │
                          ┌────────────┴────────────┐
                          │                         │
               ┌──────────▼──────┐      ┌──────────▼──────┐
               │    MongoDB      │      │    ML Engine     │
               │  (Motor async)  │      │  RF + XGBoost   │
               │  Users, Alerts  │      │  Isolation Forest│
               │  Activities,    │      │  LSTM + SHAP    │
               │  Risk Scores    │      │  Risk Engine    │
               └─────────────────┘      └────────────────┘
```

---

## 🛠️ Tech Stack

| Layer | Technology |
|-------|-----------|
| **Frontend** | React 18, Vite, Tailwind CSS, Recharts, Framer Motion, React Router |
| **Backend** | FastAPI (Python 3.11), Pydantic v2, Uvicorn, SlowAPI |
| **Database** | MongoDB 7.0 (Motor async driver) |
| **Auth** | JWT (python-jose), bcrypt (passlib), RBAC |
| **ML/AI** | scikit-learn, XGBoost, TensorFlow/Keras, SHAP, Pandas, NumPy |
| **Reporting** | ReportLab (PDF generation) |
| **DevOps** | Docker, Docker Compose, Nginx, GitHub Actions |

---

## 🚀 Quick Start

### Option 1 — Docker Compose (Recommended)

```bash
# 1. Clone the repository
git clone https://github.com/yourusername/insider-threat-platform.git
cd insider-threat-platform

# 2. Configure environment
cp .env.example .env
# Edit .env and set a strong JWT_SECRET_KEY

# 3. Start all services
docker-compose up --build -d

# 4. Access the platform
# Frontend: http://localhost
# API Docs: http://localhost/api/docs
```

### Option 2 — Local Development

#### Prerequisites
- Python 3.11+
- Node.js 20+
- MongoDB 7.0 (local or Atlas)

#### Backend Setup

```bash
cd backend

# Create virtual environment
python -m venv venv
# Windows:
venv\Scripts\activate
# Linux/Mac:
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Copy and configure environment
cp ../.env.example .env
# Set MONGO_URL=mongodb://localhost:27017

# Start the API server
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

#### Frontend Setup

```bash
cd frontend

# Install dependencies
npm install

# Start development server
npm run dev
# Open: http://localhost:5173
```

---

## 🤖 ML Models

### Training Pipeline

```bash
# Step 1: Generate synthetic dataset (CERT-like)
cd dataset
python generate_synthetic.py
# Generates: dataset/synthetic_insider_threat.csv (2000 records)

# Step 2: Train ALL models at once
cd backend
python -m ml.train_all

# Or train individual models:
python -m ml.train_rf          # Random Forest
python -m ml.train_xgboost     # XGBoost
python -m ml.train_isolation_forest  # Anomaly Detection
python -m ml.train_lstm        # Bidirectional LSTM (requires TensorFlow)
```

### Model Architecture

| Model | Task | Algorithm | Metric |
|-------|------|-----------|--------|
| Random Forest | Classification | 200 trees, balanced | ROC-AUC ~0.95 |
| XGBoost | Classification | Gradient Boosting | F1 ~0.92 |
| Isolation Forest | Anomaly Detection | 200 estimators | Unsupervised |
| Bi-LSTM | Sequential Analysis | 128+64 units | AUC ~0.91 |

### Behavioral Features

| Feature | Description | Risk Weight |
|---------|-------------|-------------|
| `login_frequency` | Login attempts per day | Baseline |
| `late_night_logins` | Logins between 10PM–6AM | High |
| `failed_login_count` | Authentication failures | +10 each |
| `file_download_volume` | MB downloaded | Scaled |
| `usb_transfer_count` | USB device transfers | +25 each |
| `suspicious_url_count` | High-risk URL visits | +10 each |
| `external_transfers` | Data sent externally | +30 |
| `after_hours_events` | Off-hours activity | +15 |

---

## 📊 Risk Scoring

Dynamic weighted scoring engine:

```
Risk Score = Σ(weight × events) with logarithmic decay

Risk Levels:
  LOW:    0–30   ✅ Normal behavior
  MEDIUM: 31–70  ⚠️  Elevated risk, increased monitoring
  HIGH:   71–100 🚨 Immediate investigation required
```

Alert triggers:
- Risk score > 70 → CRITICAL alert
- Risk score > 40 → HIGH alert
- Single high-risk event (USB transfer, bulk download) → Immediate alert

---

## 🔌 API Reference

Base URL: `http://localhost:8000/api`
Interactive Docs: `http://localhost:8000/api/docs`

### Authentication
| Endpoint | Method | Description |
|----------|--------|-------------|
| `/auth/register` | POST | Register new user |
| `/auth/login` | POST | Get JWT tokens |
| `/auth/refresh` | POST | Refresh access token |
| `/auth/profile` | GET | Get current user profile |

### Activity Monitoring
| Endpoint | Method | Description |
|----------|--------|-------------|
| `/activity/log` | POST | Log user activity event |
| `/activity/user/{id}` | GET | Get user activity history |
| `/activity/all` | GET | Get all platform activities |
| `/activity/summary/{id}` | GET | Behavioral summary |
| `/activity/timeline/{id}` | GET | Daily activity timeline |

### Alerts & Threats
| Endpoint | Method | Description |
|----------|--------|-------------|
| `/alerts/` | GET | List alerts (filtered) |
| `/alerts/stats` | GET | Alert statistics |
| `/alerts/threats` | GET | Threat trend data |
| `/alerts/{id}` | PATCH | Update alert status |
| `/alerts/mark-all-read` | POST | Mark all as read |

### Risk & ML
| Endpoint | Method | Description |
|----------|--------|-------------|
| `/risk/score/{id}` | GET | Current risk score |
| `/risk/history/{id}` | GET | Risk score history |
| `/risk/leaderboard` | GET | Highest risk users |
| `/predict/predict` | POST | ML threat classification |
| `/predict/anomaly-detect` | POST | Isolation Forest anomaly |
| `/explain/explain/{id}` | GET | SHAP explanation |
| `/explain/global-importance` | GET | Global feature importance |
| `/reports/generate/{id}` | GET | Download PDF report |

---

## 👤 RBAC Roles

| Role | Permissions |
|------|-------------|
| `admin` | Full access: user management, all data, model info |
| `analyst` | View all users, alerts, activities, generate reports |
| `employee` | View own profile and risk score only |

---

## 📂 Project Structure

```
insider-threat-platform/
├── backend/                    # FastAPI Python backend
│   ├── main.py                 # App entry point
│   ├── config.py               # Settings (Pydantic)
│   ├── database.py             # MongoDB connection
│   ├── requirements.txt        # Python dependencies
│   ├── Dockerfile              # Backend container
│   ├── models/                 # Pydantic schemas
│   │   ├── user.py
│   │   ├── activity.py
│   │   ├── alert.py
│   │   └── risk.py
│   ├── routes/                 # API route handlers
│   │   ├── auth.py             # JWT auth
│   │   ├── users.py            # User management
│   │   ├── activity.py         # Activity monitoring
│   │   ├── alerts.py           # Alert management
│   │   ├── risk.py             # Risk scoring
│   │   ├── predict.py          # ML inference
│   │   ├── explain.py          # SHAP explainability
│   │   └── reports.py          # PDF generation
│   ├── middleware/
│   │   └── auth.py             # JWT + RBAC
│   ├── utils/
│   │   ├── jwt_utils.py        # Token management
│   │   └── password.py         # bcrypt hashing
│   └── ml/                     # AI/ML engine
│       ├── risk_engine.py      # Dynamic risk scorer
│       ├── preprocessing.py    # Data pipeline
│       ├── train_rf.py         # Random Forest
│       ├── train_xgboost.py    # XGBoost
│       ├── train_isolation_forest.py
│       ├── train_lstm.py       # Bidirectional LSTM
│       ├── train_all.py        # Master training script
│       ├── predict.py          # Unified inference
│       └── shap_explainer.py   # SHAP explanations
├── frontend/                   # React + Vite frontend
│   ├── src/
│   │   ├── api/axios.js        # API client
│   │   ├── context/AuthContext.jsx
│   │   ├── components/
│   │   │   └── Sidebar.jsx
│   │   └── pages/
│   │       ├── Login.jsx
│   │       ├── Register.jsx
│   │       ├── Dashboard.jsx   # SOC overview
│   │       ├── Alerts.jsx      # Alert management
│   │       ├── Investigation.jsx # User deep-dive
│   │       ├── Analytics.jsx   # Risk analytics
│   │       ├── UserManagement.jsx
│   │       └── Profile.jsx
│   └── Dockerfile
├── dataset/
│   └── generate_synthetic.py  # CERT-like data generator
├── nginx/
│   └── nginx.conf             # Reverse proxy config
├── .github/workflows/
│   └── ci-cd.yml              # GitHub Actions pipeline
├── docker-compose.yml         # Full-stack orchestration
├── .env.example               # Environment template
└── README.md                  # This file
```

---

## 🔐 Security Features

- ✅ JWT access + refresh tokens
- ✅ bcrypt password hashing
- ✅ Role-Based Access Control (RBAC)
- ✅ Rate limiting (SlowAPI: 30 req/min)
- ✅ CORS protection
- ✅ Input validation (Pydantic)
- ✅ Security headers (Nginx)
- ✅ Environment variable management
- ✅ MongoDB injection prevention (Motor)

---

## 🧪 Demo Data

After starting the platform, create an admin user:

```bash
curl -X POST http://localhost:8000/api/auth/register \
  -H "Content-Type: application/json" \
  -d '{
    "username": "admin",
    "email": "admin@threatsight.ai",
    "password": "Admin@123456",
    "full_name": "System Administrator",
    "department": "IT Security",
    "role": "admin"
  }'
```

Then simulate activity using the `/api/activity/log` endpoint or the interactive Swagger docs at `/api/docs`.

---

## 📈 Future Roadmap

- [ ] Real-time WebSocket alerts
- [ ] Email/Slack notifications
- [ ] SIEM integration (Splunk, Elastic)
- [ ] Network traffic analysis
- [ ] Multi-tenant support
- [ ] Mobile app (React Native)
- [ ] MITRE ATT&CK mapping
- [ ] Graph-based anomaly detection (GNN)

---

## 📚 References

- CERT Insider Threat Dataset (CMU SEI)
- SHAP: Lundberg & Lee (2017) — *A Unified Approach to Interpreting Model Predictions*
- Isolation Forest: Liu et al. (2008)
- XGBoost: Chen & Guestrin (2016)
- NIST SP 800-53 — Security Controls
- MITRE ATT&CK for Enterprise

---

## 📄 License

MIT License — Academic and Research use. See [LICENSE](LICENSE).

---

<div align="center">
Built with ❤️ for academic research | AI-Powered Cybersecurity
</div>
