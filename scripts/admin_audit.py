"""
检索管理员的全部活动记录。

输出内容：
  1. 数据库中与管理员相关的表及其行数
  2. 管理员账号本身的状态
  3. audit_log 审计日志全量导出

写入 admin_audit.txt（UTF-8），避免控制台编码干扰。
"""
import io
import os
import sqlite3
import time

ROOT = r"D:\deepseek-harness\ATF_sever"
db = os.path.join(ROOT, "data", "atf.db")
out = []


def ts(v):
    if not v:
        return "-"
    try:
        return time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(float(v)))
    except Exception:
        return str(v)


if not os.path.isfile(db):
    io.open(os.path.join(ROOT, "admin_audit.txt"), "w",
            encoding="utf-8").write("数据库不存在: %s" % db)
    print("no db")
    raise SystemExit(0)

con = sqlite3.connect(db)
con.row_factory = sqlite3.Row

# ---------------------------------------------------------- 表清单
out.append("=" * 78)
out.append("ATF Lab 管理员活动检索")
out.append("=" * 78)
out.append("")
out.append("[1] 数据库表及行数")
out.append("-" * 78)
tables = [r["name"] for r in con.execute(
    "SELECT name FROM sqlite_master WHERE type='table' ORDER BY name")]
for t in tables:
    n = con.execute("SELECT COUNT(*) AS c FROM %s" % t).fetchone()["c"]
    out.append("  %-24s %d 行" % (t, n))

# ---------------------------------------------------------- 用户
out.append("")
out.append("[2] 用户账号（role=admin 为管理员）")
out.append("-" * 78)
out.append("%-4s %-16s %-8s %-8s %-8s %-10s %s" % (
    "ID", "用户名", "角色", "需改密", "有恢复码", "失败次数", "锁定至"))
for r in con.execute(
        "SELECT id, username, role, must_change_password, "
        "       (recovery_code_hash IS NOT NULL) AS rc, "
        "       failed_login_count, locked_until "
        "FROM users ORDER BY id"):
    out.append("%-4s %-16s %-8s %-8s %-8s %-10s %s" % (
        r["id"], r["username"], r["role"],
        "是" if r["must_change_password"] else "否",
        "是" if r["rc"] else "否",
        r["failed_login_count"], ts(r["locked_until"])))

# ---------------------------------------------------------- 审计日志
out.append("")
out.append("[3] 审计日志（全部操作，按时间倒序）")
out.append("-" * 78)
rows = con.execute(
    "SELECT a.created_at, a.action, a.detail, a.user_id, u.username, u.role "
    "FROM audit_log a LEFT JOIN users u ON u.id = a.user_id "
    "ORDER BY a.created_at DESC").fetchall()
out.append("共 %d 条记录" % len(rows))
out.append("")
out.append("%-19s %-26s %-14s %-8s %s" % (
    "时间", "操作", "用户", "角色", "详情"))
out.append("-" * 78)
for r in rows:
    out.append("%-19s %-26s %-14s %-8s %s" % (
        ts(r["created_at"]), r["action"],
        r["username"] or "(系统/已删除)",
        r["role"] or "-",
        (r["detail"] or "")[:34]))

# ---------------------------------------------------------- 按类型统计
out.append("")
out.append("[4] 操作类型统计")
out.append("-" * 78)
for r in con.execute(
        "SELECT action, COUNT(*) AS c FROM audit_log "
        "GROUP BY action ORDER BY c DESC"):
    out.append("  %-28s %d 次" % (r["action"], r["c"]))

# ---------------------------------------------------------- 登录尝试
out.append("")
out.append("[5] 登录尝试记录（含失败）")
out.append("-" * 78)
try:
    n_ok = con.execute(
        "SELECT COUNT(*) AS c FROM login_attempts WHERE success=1").fetchone()["c"]
    n_bad = con.execute(
        "SELECT COUNT(*) AS c FROM login_attempts WHERE success=0").fetchone()["c"]
    out.append("  成功 %d 次，失败 %d 次" % (n_ok, n_bad))
    out.append("")
    out.append("%-19s %-18s %-16s %s" % ("时间", "用户名", "来源 IP", "结果"))
    out.append("-" * 78)
    for r in con.execute(
            "SELECT attempted_at, username, ip, success FROM login_attempts "
            "ORDER BY attempted_at DESC LIMIT 40"):
        out.append("%-19s %-18s %-16s %s" % (
            ts(r["attempted_at"]), r["username"], r["ip"] or "-",
            "成功" if r["success"] else "失败"))
except sqlite3.OperationalError as e:
    out.append("  （无 login_attempts 表: %s）" % e)

# ---------------------------------------------------------- 管理员相关操作
out.append("")
out.append("[6] 仅与管理员账号相关的记录")
out.append("-" * 78)
adm_rows = con.execute(
    "SELECT a.created_at, a.action, a.detail FROM audit_log a "
    "JOIN users u ON u.id = a.user_id "
    "WHERE u.role = 'admin' ORDER BY a.created_at DESC").fetchall()
if adm_rows:
    for r in adm_rows:
        out.append("  %-19s %-26s %s" % (
            ts(r["created_at"]), r["action"], (r["detail"] or "")[:30]))
else:
    out.append("  （无）")

con.close()

io.open(os.path.join(ROOT, "admin_audit.txt"), "w",
        encoding="utf-8").write("\n".join(out))
print("written to admin_audit.txt")
