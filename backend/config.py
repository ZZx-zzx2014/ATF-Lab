"""
ATF Lab - 全局配置

⚠️ 仅供教学演示（EDUCATIONAL USE ONLY）
本项目是一个受控的安全教学靶场。所有"漏洞"均为模拟实现，
不具备任何危害真实系统的能力。详见 README.md 顶部免责声明。
"""

import os
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent


def _env(key: str, default: str) -> str:
    v = os.environ.get(key)
    return v if v not in (None, "") else default


def _env_int(key: str, default: int) -> int:
    try:
        return int(_env(key, str(default)))
    except ValueError:
        return default


class Settings:
    # ---- 服务 ----
    APP_NAME: str = "ATF Lab"
    APP_VERSION: str = "2.0.0-rc1"
    HOST: str = _env("ATF_HOST", "0.0.0.0")
    PORT: int = _env_int("ATF_PORT", 8899)
    DEBUG: bool = _env("ATF_DEBUG", "0").lower() in ("1", "true", "yes")

    # ---- 数据库 ----
    DB_PATH: str = _env("ATF_DB_PATH", str(BASE_DIR / "data" / "atf.db"))

    # ---- 密钥 ----
    # 生产部署请务必通过环境变量覆盖，否则每次重启会换密钥导致登录态失效
    SECRET_KEY: str = _env("ATF_SECRET_KEY", "atf-lab-dev-secret-change-me")
    JWT_ALGORITHM: str = "HS256"
    TOKEN_TTL_SECONDS: int = _env_int("ATF_TOKEN_TTL", 7 * 24 * 3600)

    # ---- 平台管理员 ----
    # 首个注册用户自动成为管理员；也可通过环境变量预置
    ADMIN_USER: str = _env("ATF_ADMIN_USER", "")
    ADMIN_PASSWORD: str = _env("ATF_ADMIN_PASSWORD", "")

    # ---- 跨域（前后端分离部署时使用） ----
    CORS_ORIGINS: str = _env("ATF_CORS_ORIGINS", "*")

    # ---- netlab 仿真服务 ----
    NETLAB_ENABLED: bool = _env("ATF_NETLAB_ENABLED", "1").lower() in ("1", "true", "yes")
    NETLAB_FTP_PORT: int = _env_int("ATF_NETLAB_FTP_PORT", 2121)
    NETLAB_MYSQL_PORT: int = _env_int("ATF_NETLAB_MYSQL_PORT", 3306)
    NETLAB_REDIS_PORT: int = _env_int("ATF_NETLAB_REDIS_PORT", 6379)
    NETLAB_DEBUG_PORT: int = _env_int("ATF_NETLAB_DEBUG_PORT", 31337)

    # ---- 前端静态资源（同域托管时使用） ----
    FRONTEND_DIST: str = _env("ATF_FRONTEND_DIST", str(BASE_DIR / "frontend" / "dist"))


settings = Settings()
