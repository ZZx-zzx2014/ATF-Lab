"""
ATF Lab - 数据库层（SQLite / 标准库 sqlite3）

⚠️ 仅供教学演示（EDUCATIONAL USE ONLY）
- 全部查询使用参数化绑定，不做字符串拼接
- 压轴关的"数据销毁"只作用于 sim_archive_records（模拟档案表），
  不涉及任何真实数据，详见 challenges/finale.py
"""

import sqlite3
import threading
import time
from contextlib import contextmanager
from pathlib import Path

from .config import settings

_local = threading.local()

SCHEMA = """
CREATE TABLE IF NOT EXISTS users (
    id            INTEGER PRIMARY KEY AUTOINCREMENT,
    username      TEXT    NOT NULL UNIQUE,
    email         TEXT,
    password_hash TEXT    NOT NULL,
    role          TEXT    NOT NULL DEFAULT 'user',
    created_at    REAL    NOT NULL,
    last_login_at REAL
);

CREATE TABLE IF NOT EXISTS solves (
    id         INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id    INTEGER NOT NULL,
    level_id   TEXT    NOT NULL,
    points     INTEGER NOT NULL DEFAULT 0,
    solved_at  REAL    NOT NULL,
    UNIQUE(user_id, level_id),
    FOREIGN KEY(user_id) REFERENCES users(id) ON DELETE CASCADE
);
CREATE INDEX IF NOT EXISTS idx_solves_user  ON solves(user_id);
CREATE INDEX IF NOT EXISTS idx_solves_level ON solves(level_id);

CREATE TABLE IF NOT EXISTS hint_unlocks (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id     INTEGER NOT NULL,
    level_id    TEXT    NOT NULL,
    hint_index  INTEGER NOT NULL,
    unlocked_at REAL    NOT NULL,
    UNIQUE(user_id, level_id, hint_index),
    FOREIGN KEY(user_id) REFERENCES users(id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS submissions (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id     INTEGER NOT NULL,
    level_id    TEXT    NOT NULL,
    correct     INTEGER NOT NULL,
    submitted_at REAL   NOT NULL,
    FOREIGN KEY(user_id) REFERENCES users(id) ON DELETE CASCADE
);
CREATE INDEX IF NOT EXISTS idx_sub_user ON submissions(user_id);

-- 管理后台可编辑的关卡覆盖表（内置关卡 + 后台自定义关卡）
CREATE TABLE IF NOT EXISTS level_overrides (
    level_id   TEXT PRIMARY KEY,
    payload    TEXT NOT NULL,
    updated_at REAL NOT NULL
);

-- ============================================================
-- 压轴关 L37 专用：模拟档案表
-- ⚠️ 仅供教学演示：表名以 sim_ 前缀强制标识为模拟数据。
--    "销毁档案"仅 UPDATE 本表的 status 字段，不触碰任何真实数据。
-- ============================================================
CREATE TABLE IF NOT EXISTS sim_archive_records (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    project     TEXT NOT NULL,
    codename    TEXT NOT NULL,
    classification TEXT NOT NULL,
    summary     TEXT NOT NULL,
    status      TEXT NOT NULL DEFAULT 'ACTIVE',
    destroyed_at REAL
);

-- 压轴关进度（每阶段检查点）
CREATE TABLE IF NOT EXISTS sim_reaper_progress (
    id         INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id    INTEGER NOT NULL,
    stage      INTEGER NOT NULL,
    detail     TEXT,
    reached_at REAL NOT NULL,
    UNIQUE(user_id, stage),
    FOREIGN KEY(user_id) REFERENCES users(id) ON DELETE CASCADE
);

-- 审计日志
CREATE TABLE IF NOT EXISTS audit_log (
    id         INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id    INTEGER,
    action     TEXT NOT NULL,
    detail     TEXT,
    created_at REAL NOT NULL
);
"""

# 压轴关用的虚构档案数据（干净、可重复初始化）
SIM_ARCHIVE_SEED = [
    ("HELIOS", "PROJECT_REAPER", "TOP-SECRET",
     "代号 REAPER 的生物样本试验项目。档案显示 2019-2023 年间共有 47 名受试者参与，"
     "其中 41 份知情同意书缺失。项目于 2024 年 3 月被内部合规部门标记为待销毁。", "ACTIVE"),
    ("HELIOS", "PROJECT_ORCHID", "CONFIDENTIAL",
     "对照组研究档案，材料完整。", "ACTIVE"),
    ("HELIOS", "PROJECT_ATLAS", "INTERNAL",
     "基础设施迁移记录，无敏感内容。", "ACTIVE"),
    ("HELIOS", "PROJECT_NULLSET", "CONFIDENTIAL",
     "已归档的失败项目，材料完整。", "ACTIVE"),
]


def _connect() -> sqlite3.Connection:
    Path(settings.DB_PATH).parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(settings.DB_PATH, check_same_thread=False, timeout=10)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("PRAGMA foreign_keys=ON")
    return conn


def get_conn() -> sqlite3.Connection:
    """每线程一个连接。"""
    conn = getattr(_local, "conn", None)
    if conn is None:
        conn = _connect()
        _local.conn = conn
    return conn


@contextmanager
def tx():
    """事务上下文：异常自动回滚。"""
    conn = get_conn()
    try:
        yield conn
        conn.commit()
    except Exception:
        conn.rollback()
        raise


def query(sql: str, params: tuple = ()) -> list:
    return get_conn().execute(sql, params).fetchall()


def query_one(sql: str, params: tuple = ()):
    return get_conn().execute(sql, params).fetchone()


def execute(sql: str, params: tuple = ()) -> int:
    with tx() as conn:
        cur = conn.execute(sql, params)
        return cur.lastrowid


def init_db() -> None:
    conn = get_conn()
    conn.executescript(SCHEMA)
    conn.commit()
    _seed_sim_archive()
    _seed_admin()


def _seed_sim_archive() -> None:
    """初始化模拟档案表（幂等）。"""
    row = query_one("SELECT COUNT(*) AS c FROM sim_archive_records")
    if row and row["c"] == 0:
        with tx() as conn:
            conn.executemany(
                "INSERT INTO sim_archive_records "
                "(project, codename, classification, summary, status) "
                "VALUES (?, ?, ?, ?, ?)",
                SIM_ARCHIVE_SEED,
            )


def _seed_admin() -> None:
    """按环境变量预置管理员。"""
    if not settings.ADMIN_USER or not settings.ADMIN_PASSWORD:
        return
    from .security import hash_password

    existing = query_one("SELECT id FROM users WHERE username = ?", (settings.ADMIN_USER,))
    if existing:
        return
    execute(
        "INSERT INTO users (username, email, password_hash, role, created_at) "
        "VALUES (?, ?, ?, 'admin', ?)",
        (settings.ADMIN_USER, None, hash_password(settings.ADMIN_PASSWORD), time.time()),
    )


def audit(user_id, action: str, detail: str = "") -> None:
    try:
        execute(
            "INSERT INTO audit_log (user_id, action, detail, created_at) VALUES (?, ?, ?, ?)",
            (user_id, action, detail, time.time()),
        )
    except Exception:
        pass
