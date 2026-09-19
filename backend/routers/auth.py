"""
ATF Lab - 认证路由（注册 / 登录 / 改密 / 密码恢复）

⚠️ 仅供教学演示（EDUCATIONAL USE ONLY）

安全设计说明：
  - 口令使用 PBKDF2-HMAC-SHA256（20 万轮 + 随机盐）存储
  - 登录失败达到阈值后锁定账号（防在线爆破）
  - 初始管理员标记 must_change_password，前端持续提醒改密
  - 密码恢复使用**一次性恢复码**，不提供任何通用后门密码
"""

import re
import time

from fastapi import APIRouter, Depends, Request
from pydantic import BaseModel, Field

from ..database import query_one, execute, audit
from ..deps import current_user
from ..responses import Code, ApiError, ok
from ..security import (
    hash_password, verify_password, create_token,
    generate_recovery_code, hash_recovery_code, verify_recovery_code,
    password_strength_ok, locked_seconds_left,
    MAX_FAILED_LOGINS, LOCKOUT_SECONDS, ATTEMPT_WINDOW,
)

router = APIRouter(prefix="/api/v1/auth", tags=["认证"])

USERNAME_RE = re.compile(r"^[A-Za-z0-9_\-]{3,24}$")


class RegisterIn(BaseModel):
    username: str = Field(..., min_length=3, max_length=24)
    password: str = Field(..., min_length=8, max_length=128)
    email: str = Field(default="", max_length=120)


class LoginIn(BaseModel):
    username: str
    password: str


class ChangePasswordIn(BaseModel):
    old_password: str
    new_password: str = Field(..., min_length=8, max_length=128)


class RecoverIn(BaseModel):
    username: str
    recovery_code: str
    new_password: str = Field(..., min_length=8, max_length=128)


def _public_user(row) -> dict:
    return {
        "id": row["id"],
        "username": row["username"],
        "email": row["email"],
        "role": row["role"],
        "created_at": row["created_at"],
        # 前端据此显示"请修改初始密码"的提醒横幅
        "must_change_password": bool(row["must_change_password"]),
        "password_changed_at": row["password_changed_at"],
    }


def _client_ip(request: Request) -> str:
    try:
        return request.client.host if request.client else ""
    except Exception:
        return ""


def _record_attempt(username: str, ip: str, success: bool) -> None:
    try:
        execute(
            "INSERT INTO login_attempts (username, ip, success, attempted_at) "
            "VALUES (?, ?, ?, ?)",
            (username, ip, 1 if success else 0, time.time()),
        )
        # 顺手清理过期记录，避免表无限增长
        execute("DELETE FROM login_attempts WHERE attempted_at < ?",
                (time.time() - ATTEMPT_WINDOW * 4,))
    except Exception:
        pass


# ================================================================ 注册

@router.post("/register", summary="注册新用户")
def register(body: RegisterIn, request: Request):
    if not USERNAME_RE.match(body.username):
        raise ApiError(Code.BAD_PARAM,
                       "用户名只能包含字母、数字、下划线、连字符，长度 3-24")

    okpw, msg = password_strength_ok(body.password)
    if not okpw:
        raise ApiError(Code.BAD_PARAM, msg)

    exists = query_one("SELECT id FROM users WHERE username = ?", (body.username,))
    if exists:
        raise ApiError(Code.CONFLICT, "用户名已被占用")

    count = query_one("SELECT COUNT(*) AS c FROM users")
    role = "admin" if count and count["c"] == 0 else "user"

    # 每个用户注册时生成一次性恢复码，明文只在本次响应中返回
    recovery_plain = generate_recovery_code()

    uid = execute(
        "INSERT INTO users (username, email, password_hash, role, created_at, "
        "must_change_password, recovery_code_hash) "
        "VALUES (?, ?, ?, ?, ?, 0, ?)",
        (body.username, body.email or None, hash_password(body.password),
         role, time.time(), hash_recovery_code(recovery_plain)),
    )
    audit(uid, "register", "role=%s" % role)

    row = query_one("SELECT * FROM users WHERE id = ?", (uid,))
    token = create_token(uid, body.username, role)
    return ok({
        "token": token,
        "user": _public_user(row),
        "is_first_user": role == "admin",
        # ⚠️ 恢复码只在此处返回一次，之后无法再取回明文
        "recovery_code": recovery_plain,
        "recovery_notice": "请立即保存此恢复码。它是忘记密码时自助重置的唯一凭据，只显示这一次。",
    }, message="注册成功")


# ================================================================ 登录

@router.post("/login", summary="登录")
def login(body: LoginIn, request: Request):
    ip = _client_ip(request)
    row = query_one("SELECT * FROM users WHERE username = ?", (body.username,))

    # 账号锁定检查
    left = locked_seconds_left(row)
    if left > 0:
        raise ApiError(
            Code.RATE_LIMITED,
            "账号因多次登录失败已被锁定，请 %d 分钟后再试" % (left // 60 + 1),
        )

    if row is None or not verify_password(body.password, row["password_hash"]):
        _record_attempt(body.username, ip, False)
        if row is not None:
            failed = (row["failed_login_count"] or 0) + 1
            if failed >= MAX_FAILED_LOGINS:
                execute(
                    "UPDATE users SET failed_login_count = ?, locked_until = ? "
                    "WHERE id = ?",
                    (failed, time.time() + LOCKOUT_SECONDS, row["id"]),
                )
                audit(row["id"], "account_locked",
                      "failed=%d ip=%s" % (failed, ip))
                raise ApiError(
                    Code.RATE_LIMITED,
                    "登录失败次数过多，账号已锁定 %d 分钟"
                    % (LOCKOUT_SECONDS // 60),
                )
            execute("UPDATE users SET failed_login_count = ? WHERE id = ?",
                    (failed, row["id"]))
        # 统一错误信息，避免账号枚举
        raise ApiError(Code.UNAUTHORIZED, "用户名或密码错误")

    # 登录成功：清除失败计数
    execute(
        "UPDATE users SET last_login_at = ?, failed_login_count = 0, "
        "locked_until = NULL WHERE id = ?",
        (time.time(), row["id"]),
    )
    _record_attempt(body.username, ip, True)
    audit(row["id"], "login", "ip=%s" % ip)

    token = create_token(row["id"], row["username"], row["role"])
    return ok({"token": token, "user": _public_user(row)}, message="登录成功")


@router.get("/me", summary="获取当前登录用户信息")
def me(user: dict = Depends(current_user)):
    return ok(_public_user(user))


# ================================================================ 修改密码

@router.post("/change-password", summary="修改自己的密码")
def change_password(body: ChangePasswordIn, user: dict = Depends(current_user)):
    row = query_one("SELECT * FROM users WHERE id = ?", (user["id"],))
    if row is None:
        raise ApiError(Code.UNAUTHORIZED, "用户不存在")

    if not verify_password(body.old_password, row["password_hash"]):
        audit(user["id"], "change_password_failed", "wrong_old_password")
        raise ApiError(Code.UNAUTHORIZED, "当前密码不正确")

    if verify_password(body.new_password, row["password_hash"]):
        raise ApiError(Code.BAD_PARAM, "新密码不能与当前密码相同")

    okpw, msg = password_strength_ok(body.new_password)
    if not okpw:
        raise ApiError(Code.BAD_PARAM, msg)

    execute(
        "UPDATE users SET password_hash = ?, must_change_password = 0, "
        "password_changed_at = ? WHERE id = ?",
        (hash_password(body.new_password), time.time(), user["id"]),
    )
    audit(user["id"], "change_password", "ok")

    fresh = query_one("SELECT * FROM users WHERE id = ?", (user["id"],))
    return ok({"user": _public_user(fresh)}, message="密码已更新")


# ================================================================ 密码恢复

@router.post("/recover", summary="使用一次性恢复码重置密码")
def recover(body: RecoverIn, request: Request):
    """
    忘记密码时的自助恢复。

    需要注册时生成的一次性恢复码。恢复码使用后立即失效。
    刻意不提供任何"通用管理密码"入口。
    """
    ip = _client_ip(request)
    row = query_one("SELECT * FROM users WHERE username = ?", (body.username,))

    left = locked_seconds_left(row)
    if left > 0:
        raise ApiError(Code.RATE_LIMITED,
                       "账号已锁定，请 %d 分钟后再试" % (left // 60 + 1))

    # 统一错误信息，避免账号枚举
    if row is None or not verify_recovery_code(
            body.recovery_code, row["recovery_code_hash"]):
        _record_attempt(body.username, ip, False)
        if row is not None:
            failed = (row["failed_login_count"] or 0) + 1
            if failed >= MAX_FAILED_LOGINS:
                execute(
                    "UPDATE users SET failed_login_count = ?, locked_until = ? "
                    "WHERE id = ?",
                    (failed, time.time() + LOCKOUT_SECONDS, row["id"]),
                )
            else:
                execute("UPDATE users SET failed_login_count = ? WHERE id = ?",
                        (failed, row["id"]))
        audit(row["id"] if row else None, "recover_failed", "ip=%s" % ip)
        raise ApiError(Code.UNAUTHORIZED, "用户名或恢复码不正确")

    okpw, msg = password_strength_ok(body.new_password)
    if not okpw:
        raise ApiError(Code.BAD_PARAM, msg)

    # 生成新的恢复码，旧的作废
    new_code = generate_recovery_code()
    execute(
        "UPDATE users SET password_hash = ?, must_change_password = 0, "
        "password_changed_at = ?, recovery_code_hash = ?, "
        "recovery_code_used_at = ?, failed_login_count = 0, locked_until = NULL "
        "WHERE id = ?",
        (hash_password(body.new_password), time.time(),
         hash_recovery_code(new_code), time.time(), row["id"]),
    )
    audit(row["id"], "password_recovered", "ip=%s" % ip)

    token = create_token(row["id"], row["username"], row["role"])
    fresh = query_one("SELECT * FROM users WHERE id = ?", (row["id"],))
    return ok({
        "token": token,
        "user": _public_user(fresh),
        "recovery_code": new_code,
        "recovery_notice": "密码已重置。这是你的新恢复码，旧码已失效，请立即保存。",
    }, message="密码已重置")


@router.post("/regenerate-recovery", summary="重新生成恢复码（需登录）")
def regenerate_recovery(body: dict = None, user: dict = Depends(current_user)):
    """已登录用户主动轮换恢复码（用于旧码可能泄露时）。"""
    code = generate_recovery_code()
    execute(
        "UPDATE users SET recovery_code_hash = ?, recovery_code_used_at = NULL "
        "WHERE id = ?",
        (hash_recovery_code(code), user["id"]),
    )
    audit(user["id"], "regenerate_recovery", "self_service")
    return ok({
        "recovery_code": code,
        "recovery_notice": "旧恢复码已失效。请立即保存新的恢复码，它只显示这一次。",
    }, message="恢复码已重新生成")
