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
