"""
routes/users.py — User management endpoints (Admin only).
"""
from fastapi import APIRouter, HTTPException, status, Depends, Query
from datetime import datetime, timezone
from bson import ObjectId
from typing import Optional

from database import get_users_collection
from models.user import UserResponse, UserUpdateRequest, UserListResponse
from middleware.auth import get_current_user, require_analyst_or_admin, require_admin

router = APIRouter()


def _serialize_user(user: dict) -> dict:
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


@router.get("/", response_model=UserListResponse)
async def list_users(
    page: int = Query(1, ge=1),
    per_page: int = Query(20, ge=1, le=100),
    role: Optional[str] = None,
    department: Optional[str] = None,
    search: Optional[str] = None,
    current_user: dict = Depends(require_analyst_or_admin),
):
    """List all users with pagination and filtering (Analyst/Admin only)."""
    users_col = get_users_collection()

    query = {}
    if role:
        query["role"] = role
    if department:
        query["department"] = department
    if search:
        query["$or"] = [
            {"username": {"$regex": search, "$options": "i"}},
            {"full_name": {"$regex": search, "$options": "i"}},
            {"email": {"$regex": search, "$options": "i"}},
        ]

    total = await users_col.count_documents(query)
    skip = (page - 1) * per_page

    cursor = (
        users_col.find(query)
        .sort("risk_score", -1)
        .skip(skip)
        .limit(per_page)
    )
    users = await cursor.to_list(length=per_page)

    return UserListResponse(
        users=[UserResponse(**_serialize_user(u)) for u in users],
        total=total,
        page=page,
        per_page=per_page,
    )


@router.get("/{user_id}", response_model=UserResponse)
async def get_user(
    user_id: str,
    current_user: dict = Depends(require_analyst_or_admin),
):
    """Get a specific user by ID."""
    users_col = get_users_collection()
    try:
        user = await users_col.find_one({"_id": ObjectId(user_id)})
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid user ID")

    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    return UserResponse(**_serialize_user(user))


@router.patch("/{user_id}", response_model=UserResponse)
async def update_user(
    user_id: str,
    payload: UserUpdateRequest,
    current_user: dict = Depends(require_admin),
):
    """Update user profile (Admin only)."""
    users_col = get_users_collection()

    update_data = {k: v for k, v in payload.model_dump().items() if v is not None}
    if not update_data:
        raise HTTPException(status_code=400, detail="No fields to update")

    try:
        result = await users_col.find_one_and_update(
            {"_id": ObjectId(user_id)},
            {"$set": {**update_data, "updated_at": datetime.now(timezone.utc)}},
            return_document=True,
        )
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid user ID")

    if not result:
        raise HTTPException(status_code=404, detail="User not found")

    return UserResponse(**_serialize_user(result))


@router.delete("/{user_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_user(
    user_id: str,
    current_user: dict = Depends(require_admin),
):
    """Soft-delete (deactivate) a user (Admin only)."""
    users_col = get_users_collection()

    if user_id == str(current_user["_id"]):
        raise HTTPException(status_code=400, detail="Cannot delete yourself")

    try:
        result = await users_col.update_one(
            {"_id": ObjectId(user_id)},
            {"$set": {"is_active": False}},
        )
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid user ID")

    if result.modified_count == 0:
        raise HTTPException(status_code=404, detail="User not found")


@router.get("/stats/overview", response_model=dict)
async def user_stats(current_user: dict = Depends(require_analyst_or_admin)):
    """Get overall user statistics for the dashboard."""
    users_col = get_users_collection()

    total = await users_col.count_documents({})
    active = await users_col.count_documents({"is_active": True})
    high_risk = await users_col.count_documents({"risk_level": "HIGH"})
    medium_risk = await users_col.count_documents({"risk_level": "MEDIUM"})

    # Role breakdown
    admins = await users_col.count_documents({"role": "admin"})
    analysts = await users_col.count_documents({"role": "analyst"})
    employees = await users_col.count_documents({"role": "employee"})

    return {
        "total_users": total,
        "active_users": active,
        "inactive_users": total - active,
        "high_risk_users": high_risk,
        "medium_risk_users": medium_risk,
        "low_risk_users": total - high_risk - medium_risk,
        "role_breakdown": {
            "admin": admins,
            "analyst": analysts,
            "employee": employees,
        },
    }
