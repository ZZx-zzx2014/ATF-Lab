"""
ATF Lab - 数据库层（SQLite / 标准库 sqlite3）

⚠️ 仅供教学演示（EDUCATIONAL USE ONLY）
- 全部查询使用参数化绑定，不做字符串拼接
- 压轴关的"数据销毁"只作用于 sim_archive_records（模拟档案表），
  不涉及任何真实数据，详见 challenges/finale.py
"""

import logging
import sqlite3
import threading
import time
from contextlib import contextmanager
from pathlib import Path

from .config import settings

log = logging.getLogger("atf")

_local = threading.local()

SCHEMA = """
CREATE TABLE IF NOT EXISTS users (
    id            INTEGER PRIMARY KEY AUTOINCREMENT,
    username      TEXT    NOT NULL UNIQUE,
    email         TEXT,
    password_hash TEXT    NOT NULL,
    role          TEXT    NOT NULL DEFAULT 'user',
    created_at    REAL    NOT NULL,
    last_login_at REAL,
    -- 初始密码未修改时为 1，前端据此显示强制改密提醒
    must_change_password INTEGER NOT NULL DEFAULT 0,
    password_changed_at  REAL,
    -- 一次性恢复码：仅存哈希，明文只在生成时展示一次
    recovery_code_hash   TEXT,
    recovery_code_used_at REAL,
    -- 连续登录失败计数与锁定时间（防爆破）
    failed_login_count INTEGER NOT NULL DEFAULT 0,
    locked_until       REAL
);

CREATE TABLE IF NOT EXISTS login_attempts (
    id           INTEGER PRIMARY KEY AUTOINCREMENT,
    username     TEXT NOT NULL,
    ip           TEXT,
    success      INTEGER NOT NULL,
    attempted_at REAL NOT NULL
);
CREATE INDEX IF NOT EXISTS idx_login_attempts ON login_attempts(username, attempted_at);

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
    _migrate()
    _seed_sim_archive()
    _seed_admin()


def _migrate() -> None:
    """
    轻量迁移：为已存在的旧库补齐新增字段。

    SQLite 的 CREATE TABLE IF NOT EXISTS 不会修改已有表结构，
    因此升级时需要显式 ADD COLUMN。这里做成幂等的。
    """
    wanted = {
        "users": [
            ("must_change_password", "INTEGER NOT NULL DEFAULT 0"),
            ("password_changed_at", "REAL"),
            ("recovery_code_hash", "TEXT"),
            ("recovery_code_used_at", "REAL"),
            ("failed_login_count", "INTEGER NOT NULL DEFAULT 0"),
            ("locked_until", "REAL"),
        ],
    }
    for table, cols in wanted.items():
        existing = {r["name"] for r in query("PRAGMA table_info(%s)" % table)}
        for name, decl in cols:
            if name not in existing:
                try:
                    execute("ALTER TABLE %s ADD COLUMN %s %s" % (table, name, decl))
                except Exception:
                    pass



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
    """
    初始化管理员账号。

    规则：
      - 若用户表为空，则自动创建一个管理员账号（可公网部署的首次初始化流程）
      - 密码来源优先级：
          1. 环境变量 ATF_ADMIN_PASSWORD（推荐，你自己设定）
          2. 未设置时随机生成一个高强度密码，并打印到启动日志
      - 无论哪种方式，都标记 must_change_password=1，
        前端会持续提醒管理员修改初始密码。

    这样既可以做到"部署完自动有管理员"，又不会在代码里写死任何密码。
    """
    from .security import (
        hash_password, generate_password, generate_recovery_code,
        hash_recovery_code,
    )

    user_count = query_one("SELECT COUNT(*) AS c FROM users")
    has_users = bool(user_count and user_count["c"] > 0)
    if has_users:
        return

    username = settings.ADMIN_USER or "admin"
    generated = False
    password = settings.ADMIN_PASSWORD
    if not password:
        password = generate_password()
        generated = True

    recovery_plain = generate_recovery_code()
    uid = execute(
        "INSERT INTO users (username, email, password_hash, role, created_at, "
        "must_change_password, recovery_code_hash) "
        "VALUES (?, ?, ?, 'admin', ?, 1, ?)",
        (username, None, hash_password(password), time.time(),
         hash_recovery_code(recovery_plain)),
    )

    # 把初始凭据打印到启动日志（仅此一次，不落库明文）
    _log_banner(username, password, recovery_plain, generated)
    audit(uid, "bootstrap_admin", "generated=%s" % generated)


def _log_banner(username, password, recovery_code, generated):
    """在启动日志中醒目地输出初始管理员凭据。"""
    log = logging.getLogger("atf")
    bar = "=" * 68
    lines = [
        "",
        bar,
        "  ⚠️  首次初始化：已创建管理员账号",
        bar,
        "  用户名      : %s" % username,
        "  初始密码    : %s%s" % (password, "   （随机生成）" if generated else ""),
        "  恢复码      : %s" % recovery_code,
        "",
        "  请立即登录并修改初始密码。",
        "  恢复码用于忘记密码时自助重置，请妥善保存 —— 它只显示这一次。",
        bar,
        "",
    ]
    for line in lines:
        log.warning(line)



def audit(user_id, action: str, detail: str = "") -> None:
    try:
        execute(
            "INSERT INTO audit_log (user_id, action, detail, created_at) VALUES (?, ?, ?, ?)",
            (user_id, action, detail, time.time()),
        )
    except Exception:
        pass
