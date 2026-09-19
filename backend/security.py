"""
ATF Lab - 安全工具（口令哈希 + JWT）

⚠️ 仅供教学演示（EDUCATIONAL USE ONLY）

关于压轴关 L37 的 JWT 伪造考点：
    本模块使用 settings.SECRET_KEY 签发【平台真实】token。
    压轴关内那个"可被伪造的弱密钥 JWT"是【完全独立】的另一套实现，
    见 challenges/finale.py —— 它使用固定的弱密钥、独立的 audience，
    且只对模拟接口有效，无法用于提升平台权限。两者刻意隔离。
"""

import base64
import hashlib
import hmac
import os
import secrets
import time

import jwt

from .config import settings

PBKDF2_ROUNDS = 200_000
SALT_BYTES = 16


# ---------------------------------------------------------------- 口令哈希

def hash_password(password: str) -> str:
    """PBKDF2-HMAC-SHA256，返回 pbkdf2$rounds$salt$hash 格式。"""
    salt = os.urandom(SALT_BYTES)
    dk = hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"), salt, PBKDF2_ROUNDS)
    return "pbkdf2${}${}${}".format(
        PBKDF2_ROUNDS,
        base64.b64encode(salt).decode(),
        base64.b64encode(dk).decode(),
    )


def verify_password(password: str, stored: str) -> bool:
    try:
        scheme, rounds_s, salt_s, hash_s = stored.split("$")
        if scheme != "pbkdf2":
            return False
        rounds = int(rounds_s)
        salt = base64.b64decode(salt_s)
        expected = base64.b64decode(hash_s)
        dk = hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"), salt, rounds)
        # 恒定时间比较，避免时序侧信道
        return hmac.compare_digest(dk, expected)
    except Exception:
        return False


# ---------------------------------------------------------------- JWT

def create_token(user_id: int, username: str, role: str, ttl: int = None) -> str:
    now = int(time.time())
    ttl = ttl if ttl is not None else settings.TOKEN_TTL_SECONDS
    payload = {
        "sub": str(user_id),
        "username": username,
        "role": role,
        "iat": now,
        "exp": now + ttl,
        "aud": "atf-platform",
    }
    return jwt.encode(payload, settings.SECRET_KEY, algorithm=settings.JWT_ALGORITHM)


def decode_token(token: str):
    """解码平台 token，失败返回 None。"""
    try:
        return jwt.decode(
            token,
            settings.SECRET_KEY,
            algorithms=[settings.JWT_ALGORITHM],
            audience="atf-platform",
        )
    except Exception:
        return None


# ---------------------------------------------------------------- 随机凭据

# 排除容易混淆的字符（0/O、1/l/I），便于人工抄写
_PW_ALPHABET = "abcdefghijkmnpqrstuvwxyzABCDEFGHJKLMNPQRSTUVWXYZ23456789"

# 常见弱口令黑名单
WEAK_PASSWORDS = {
    "12345678", "123456789", "1234567890", "password", "password1",
    "qwerty123", "admin123", "admin888", "letmein1", "welcome1",
    "abc12345", "11111111", "00000000", "iloveyou", "sunshine",
    "princess", "football", "monkey123", "dragon123", "master123",
}


def generate_password(length: int = 20) -> str:
    """生成高强度随机密码（用于首次部署的初始管理员）。"""
    return "".join(secrets.choice(_PW_ALPHABET) for _ in range(length))


def generate_recovery_code() -> str:
    """
    生成一次性恢复码。

    格式 XXXX-XXXX-XXXX-XXXX，共 16 个字符。
    明文只在生成时展示一次，数据库只存哈希。
    """
    raw = "".join(secrets.choice(_PW_ALPHABET) for _ in range(16))
    return "-".join(raw[i:i + 4] for i in range(0, 16, 4))


def _normalize_code(code: str) -> str:
    return (code or "").strip().upper().replace("-", "").replace(" ", "")


def hash_recovery_code(code: str) -> str:
    """恢复码哈希（与口令同一套 PBKDF2，避免明文落库）。"""
    return hash_password(_normalize_code(code))


def verify_recovery_code(code: str, stored: str) -> bool:
    if not stored:
        return False
    return verify_password(_normalize_code(code), stored)


def password_strength_ok(password: str) -> tuple:
    """
    口令强度校验。

    返回 (是否通过, 提示信息)。规则刻意保持简单可解释：
      - 长度 >= 8
      - 至少包含字母和数字
      - 不能是常见弱口令
    """
    pw = password or ""
    if len(pw) < 8:
        return False, "密码长度至少 8 位"
    if not any(c.isalpha() for c in pw):
        return False, "密码需包含字母"
    if not any(c.isdigit() for c in pw):
        return False, "密码需包含数字"
    if pw.lower() in WEAK_PASSWORDS:
        return False, "该密码过于常见，请更换"
    return True, "ok"


# ---------------------------------------------------------------- 登录限流

MAX_FAILED_LOGINS = 5           # 连续失败达到该次数即锁定
LOCKOUT_SECONDS = 15 * 60       # 锁定时长（秒）
ATTEMPT_WINDOW = 15 * 60        # 统计窗口（秒）


def locked_seconds_left(user_row) -> int:
    """返回账号剩余锁定秒数，未锁定返回 0。"""
    if user_row is None:
        return 0
    try:
        until = user_row["locked_until"]
    except (KeyError, IndexError, TypeError):
        return 0
    if not until:
        return 0
    left = int(until - time.time())
    return left if left > 0 else 0
