"""
middleware/auth.py — JWT authentication middleware and dependency injections.
Provides current_user dependency with RBAC role checking.
"""
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from database import get_users_collection
from utils.jwt_utils import verify_token
from bson import ObjectId

security = HTTPBearer()


async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
):
    """
    Dependency: Extracts and validates JWT token.
    Returns the authenticated user document from MongoDB.
    """
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )

    token = credentials.credentials
    payload = verify_token(token, token_type="access")
    if not payload:
        raise credentials_exception

    user_id: str = payload.get("sub")
    if not user_id:
        raise credentials_exception

    users_col = get_users_collection()
    try:
        user = await users_col.find_one({"_id": ObjectId(user_id)})
    except Exception:
        raise credentials_exception

    if not user:
        raise credentials_exception

    if not user.get("is_active", True):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Account is disabled",
        )

    return user


def require_roles(*allowed_roles: str):
    """
    Role-Based Access Control (RBAC) dependency factory.
    Usage: Depends(require_roles("admin", "analyst"))
    """

    async def role_checker(current_user: dict = Depends(get_current_user)):
        user_role = current_user.get("role", "employee")
        if user_role not in allowed_roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Access denied. Required roles: {allowed_roles}",
            )
        return current_user

    return role_checker


# Convenience role dependencies
require_admin = require_roles("admin")
require_analyst_or_admin = require_roles("admin", "analyst")
