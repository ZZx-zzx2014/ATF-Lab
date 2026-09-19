"""
ATF Lab - 认证路由（注册 / 登录 / 我的信息）

⚠️ 仅供教学演示（EDUCATIONAL USE ONLY）
"""

import re
import time

from fastapi import APIRouter, Depends
from pydantic import BaseModel, Field

from ..database import query_one, execute, audit
from ..deps import current_user
from ..responses import Code, ApiError, ok
from ..security import hash_password, verify_password, create_token

router = APIRouter(prefix="/api/v1/auth", tags=["认证"])

USERNAME_RE = re.compile(r"^[A-Za-z0-9_\-]{3,24}$")


class RegisterIn(BaseModel):
    username: str = Field(..., min_length=3, max_length=24)
    password: str = Field(..., min_length=6, max_length=128)
    email: str = Field(default="", max_length=120)


class LoginIn(BaseModel):
    username: str
    password: str


def _public_user(row) -> dict:
    return {
        "id": row["id"],
        "username": row["username"],
        "email": row["email"],
        "role": row["role"],
        "created_at": row["created_at"],
    }


@router.post("/register", summary="注册新用户")
def register(body: RegisterIn):
    if not USERNAME_RE.match(body.username):
        raise ApiError(Code.BAD_PARAM, "用户名只能包含字母、数字、下划线、连字符，长度 3-24")

    exists = query_one("SELECT id FROM users WHERE username = ?", (body.username,))
    if exists:
        raise ApiError(Code.CONFLICT, "用户名已被占用")

    # 首个注册用户自动成为管理员，方便开箱体验管理后台
    count = query_one("SELECT COUNT(*) AS c FROM users")
    role = "admin" if count and count["c"] == 0 else "user"

    uid = execute(
        "INSERT INTO users (username, email, password_hash, role, created_at) "
        "VALUES (?, ?, ?, ?, ?)",
        (body.username, body.email or None, hash_password(body.password), role, time.time()),
    )
    audit(uid, "register", "role=%s" % role)

    row = query_one("SELECT * FROM users WHERE id = ?", (uid,))
    token = create_token(uid, body.username, role)
    return ok({
        "token": token,
        "user": _public_user(row),
        "is_first_user": role == "admin",
    }, message="注册成功")


@router.post("/login", summary="登录")
def login(body: LoginIn):
    row = query_one("SELECT * FROM users WHERE username = ?", (body.username,))
    # 恒定时间比较在 verify_password 内部处理；此处对不存在用户也返回同一错误
    if row is None or not verify_password(body.password, row["password_hash"]):
        raise ApiError(Code.UNAUTHORIZED, "用户名或密码错误")

    execute("UPDATE users SET last_login_at = ? WHERE id = ?", (time.time(), row["id"]))
    audit(row["id"], "login")

    token = create_token(row["id"], row["username"], row["role"])
    return ok({"token": token, "user": _public_user(row)}, message="登录成功")


@router.get("/me", summary="获取当前登录用户信息")
def me(user: dict = Depends(current_user)):
    return ok(_public_user(user))
