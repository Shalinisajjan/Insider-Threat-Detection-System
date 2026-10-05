"""
routes/auth.py — Authentication endpoints: register, login, refresh, profile.
"""
from fastapi import APIRouter, HTTPException, status, Depends
from datetime import datetime, timezone
from bson import ObjectId

from database import get_users_collection
from models.user import (
    UserRegisterRequest,
    UserLoginRequest,
    UserResponse,
    TokenResponse,
    RefreshTokenRequest,
)
from utils.password import hash_password, verify_password
from utils.jwt_utils import create_access_token, create_refresh_token, verify_token
from middleware.auth import get_current_user

router = APIRouter()


def _serialize_user(user: dict) -> dict:
    """Convert MongoDB user document to response-friendly dict."""
    return {
        "id": str(user["_id"]),
        "username": user["username"],
        "email": user["email"],
        "full_name": user["full_name"],
        "department": user.get("department", "General"),
        "role": user["role"],
        "is_active": user.get("is_active", True),
        "created_at": user["created_at"],
        "last_login": user.get("last_login"),
        "risk_score": user.get("risk_score", 0.0),
        "risk_level": user.get("risk_level", "LOW"),
    }


@router.post("/register", response_model=TokenResponse, status_code=status.HTTP_201_CREATED)
async def register(payload: UserRegisterRequest):
    """Register a new user account."""
    users_col = get_users_collection()

    # Check if user already exists
    existing = await users_col.find_one(
        {"$or": [{"email": payload.email}, {"username": payload.username}]}
    )
    if existing:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="User with this email or username already exists",
        )

    # Create user document
    now = datetime.now(timezone.utc)
    user_doc = {
        "username": payload.username,
        "email": payload.email,
        "hashed_password": hash_password(payload.password),
        "full_name": payload.full_name,
        "department": payload.department or "General",
        "role": payload.role.value,
        "is_active": True,
        "created_at": now,
        "last_login": None,
        "risk_score": 0.0,
        "risk_level": "LOW",
    }

    result = await users_col.insert_one(user_doc)
    user_doc["_id"] = result.inserted_id

    # Generate tokens
    token_data = {"sub": str(result.inserted_id), "role": payload.role.value}
    access_token = create_access_token(token_data)
    refresh_token = create_refresh_token(token_data)

    return TokenResponse(
        access_token=access_token,
        refresh_token=refresh_token,
        user=UserResponse(**_serialize_user(user_doc)),
    )


@router.post("/login", response_model=TokenResponse)
async def login(payload: UserLoginRequest):
    """Authenticate user and return JWT tokens."""
    users_col = get_users_collection()

    user = await users_col.find_one({"email": payload.email})
    if not user or not verify_password(payload.password, user["hashed_password"]):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password",
        )

    if not user.get("is_active", True):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Account is disabled. Contact your administrator.",
        )

    # Update last login
    await users_col.update_one(
        {"_id": user["_id"]},
        {"$set": {"last_login": datetime.now(timezone.utc)}},
    )

    token_data = {"sub": str(user["_id"]), "role": user["role"]}
    access_token = create_access_token(token_data)
    refresh_token = create_refresh_token(token_data)

    return TokenResponse(
        access_token=access_token,
        refresh_token=refresh_token,
        user=UserResponse(**_serialize_user(user)),
    )


@router.post("/refresh", response_model=dict)
async def refresh_token(payload: RefreshTokenRequest):
    """Exchange a refresh token for a new access token."""
    token_payload = verify_token(payload.refresh_token, token_type="refresh")
    if not token_payload:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired refresh token",
        )

    new_access = create_access_token(
        {"sub": token_payload["sub"], "role": token_payload.get("role", "employee")}
    )
    return {"access_token": new_access, "token_type": "bearer"}


@router.get("/profile", response_model=UserResponse)
async def get_profile(current_user: dict = Depends(get_current_user)):
    """Get the authenticated user's profile."""
    return UserResponse(**_serialize_user(current_user))
