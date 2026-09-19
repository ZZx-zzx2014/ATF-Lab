"""
ATF Lab - 依赖注入（当前用户 / 管理员校验）

⚠️ 仅供教学演示（EDUCATIONAL USE ONLY）
"""

from typing import Optional

from fastapi import Header

from .database import query_one
from .responses import Code, ApiError
from .security import decode_token


def _user_from_token(authorization: Optional[str]):
    if not authorization:
        return None
    parts = authorization.split()
    if len(parts) != 2 or parts[0].lower() != "bearer":
        return None
    payload = decode_token(parts[1])
    if not payload:
        return None
    row = query_one(
        "SELECT id, username, email, role, created_at, last_login_at, "
        "       must_change_password, password_changed_at, is_demo "
        "FROM users WHERE id = ?",
        (int(payload["sub"]),),
    )
    return dict(row) if row else None


def current_user_optional(authorization: Optional[str] = Header(default=None)):
    """可选认证：未登录返回 None。"""
    return _user_from_token(authorization)


def current_user(authorization: Optional[str] = Header(default=None)) -> dict:
    """强制认证。"""
    user = _user_from_token(authorization)
    if user is None:
        raise ApiError(Code.UNAUTHORIZED, "未登录或登录已过期")
    return user


def admin_user(authorization: Optional[str] = Header(default=None)) -> dict:
    """管理员校验。"""
    user = _user_from_token(authorization)
    if user is None:
        raise ApiError(Code.UNAUTHORIZED, "未登录或登录已过期")
    if user["role"] != "admin":
        raise ApiError(Code.FORBIDDEN, "需要管理员权限")
    return user
