"""
main.py — FastAPI application entry point.
Configures CORS, rate limiting, routers, and startup events.
"""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from contextlib import asynccontextmanager
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded

from config import get_settings
from database import create_indexes

# Import routers
from routes.auth import router as auth_router
from routes.activity import router as activity_router
from routes.alerts import router as alerts_router
from routes.risk import router as risk_router
from routes.predict import router as predict_router
from routes.explain import router as explain_router
from routes.reports import router as reports_router
from routes.users import router as users_router

settings = get_settings()

# Rate limiter
limiter = Limiter(key_func=get_remote_address)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application startup and shutdown events."""
    # Startup
    print("🚀 Starting AI Insider Threat Platform...")
    await create_indexes()
    print("✅ MongoDB indexes created.")
    yield
    # Shutdown
    print("🛑 Shutting down...")


# ─── FastAPI Application ──────────────────────────────────────────────────────
app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    description="""
## AI-Powered Explainable Insider Threat Intelligence Platform

### Features:
- 🔐 **JWT Authentication** with Role-Based Access Control
- 🎯 **User Behavior Analytics (UEBA)**
- 🤖 **ML-Powered Threat Detection** (RF, XGBoost, LSTM, Isolation Forest)
- 🔍 **Explainable AI** with SHAP values
- ⚡ **Dynamic Risk Scoring Engine**
- 🚨 **Real-time Alerting System**
- 📊 **Comprehensive Analytics Dashboard**
- 📄 **PDF Incident Reports**
    """,
    lifespan=lifespan,
    docs_url="/api/docs",
    redoc_url="/api/redoc",
)

# ─── Rate Limiting ────────────────────────────────────────────────────────────
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

# ─── CORS Middleware ──────────────────────────────────────────────────────────
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ─── Security Middleware ──────────────────────────────────────────────────────
app.add_middleware(
    TrustedHostMiddleware,
    allowed_hosts=["*"],  # Restrict in production
)

# ─── Routers ──────────────────────────────────────────────────────────────────
app.include_router(auth_router, prefix="/api/auth", tags=["Authentication"])
app.include_router(users_router, prefix="/api/users", tags=["User Management"])
app.include_router(activity_router, prefix="/api/activity", tags=["Activity Monitoring"])
app.include_router(alerts_router, prefix="/api/alerts", tags=["Alerts"])
app.include_router(risk_router, prefix="/api/risk", tags=["Risk Engine"])
app.include_router(predict_router, prefix="/api/predict", tags=["ML Inference"])
app.include_router(explain_router, prefix="/api/explain", tags=["Explainable AI"])
app.include_router(reports_router, prefix="/api/reports", tags=["Reports"])


# ─── Health Check ─────────────────────────────────────────────────────────────
@app.get("/api/health", tags=["Health"])
async def health_check():
    return {
        "status": "healthy",
        "app": settings.APP_NAME,
        "version": settings.APP_VERSION,
    }


@app.get("/", tags=["Root"])
async def root():
    return {
        "message": "AI Insider Threat Intelligence Platform API",
        "docs": "/api/docs",
        "health": "/api/health",
    }
