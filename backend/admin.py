"""
ATF Lab - 管理员命令行工具

⚠️ 仅供教学演示（EDUCATIONAL USE ONLY）

用途：**在服务器本地**执行管理操作，无需通过网页登录。
这是「忘记密码」和「应急恢复」的正当实现方式 —— 需要服务器 shell 权限，
而不是一个藏在代码里的通用后门密码。

用法：
    python -m backend.admin list-users
    python -m backend.admin reset-password --user admin
    python -m backend.admin reset-password --user admin --password 'MyNewPass123'
    python -m backend.admin show-recovery --user admin
    python -m backend.admin unlock --user admin
    python -m backend.admin audit --limit 50

设计原则：
    1. 必须能访问服务器（物理/SSH），这是天然的权限边界
    2. 所有操作写入审计日志，可追溯
    3. 不提供任何网络可达的"万能密码"入口
"""

import argparse
import sys
import time

from .database import init_db, query, query_one, execute, audit
from .security import (
    hash_password, generate_password, generate_recovery_code,
    hash_recovery_code, password_strength_ok, LOCKOUT_SECONDS,
)


def _fmt_ts(ts):
    if not ts:
        return "-"
    return time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(ts))


def cmd_list_users(args):
    rows = query(
        "SELECT u.id, u.username, u.role, u.created_at, u.last_login_at, "
        "       u.must_change_password, u.locked_until, "
        "       (u.recovery_code_hash IS NOT NULL) AS has_recovery, "
        "       COUNT(s.id) AS solved "
        "FROM users u LEFT JOIN solves s ON s.user_id = u.id "
        "GROUP BY u.id ORDER BY u.id"
    )
    if not rows:
        print("（暂无用户）")
        return 0

    print("%-4s %-18s %-7s %-8s %-8s %-19s" %
          ("ID", "用户名", "角色", "通关数", "需改密", "最近登录"))
    print("-" * 74)
    for r in rows:
        print("%-4s %-18s %-7s %-8s %-8s %-19s" % (
            r["id"], r["username"], r["role"], r["solved"],
            "是" if r["must_change_password"] else "否",
            _fmt_ts(r["last_login_at"]),
        ))
        if r["locked_until"] and r["locked_until"] > time.time():
            left = int(r["locked_until"] - time.time())
            print("     └─ ⚠️ 账号锁定中，剩余 %d 分钟" % (left // 60 + 1))
    return 0


def cmd_reset_password(args):
    row = query_one("SELECT id, username FROM users WHERE username = ?",
                    (args.user,))
    if row is None:
        print("✗ 用户不存在: %s" % args.user, file=sys.stderr)
        return 1

    if args.password:
        new_pw = args.password
        ok, msg = password_strength_ok(new_pw)
        if not ok:
            print("✗ 密码强度不足: %s" % msg, file=sys.stderr)
            return 1
        generated = False
    else:
        new_pw = generate_password()
        generated = True

    execute(
        "UPDATE users SET password_hash = ?, must_change_password = 1, "
        "       password_changed_at = ?, failed_login_count = 0, locked_until = NULL "
        "WHERE id = ?",
        (hash_password(new_pw), time.time(), row["id"]),
    )
    audit(row["id"], "cli_reset_password", "by=cli generated=%s" % generated)

    print()
    print("=" * 62)
    print("  已重置用户 [%s] 的密码" % row["username"])
    print("=" * 62)
    print("  新密码 : %s%s" % (new_pw, "   （随机生成）" if generated else ""))
    print("  状态   : 已标记为「需要修改密码」，下次登录后会收到提醒")
    print("  审计   : 本次操作已记入 audit_log")
    print("=" * 62)
    print()
    return 0


def cmd_show_recovery(args):
    """重新生成恢复码（旧的立即失效）。"""
    row = query_one("SELECT id, username FROM users WHERE username = ?",
                    (args.user,))
    if row is None:
        print("✗ 用户不存在: %s" % args.user, file=sys.stderr)
        return 1

    code = generate_recovery_code()
    execute(
        "UPDATE users SET recovery_code_hash = ?, recovery_code_used_at = NULL "
        "WHERE id = ?",
        (hash_recovery_code(code), row["id"]),
    )
    audit(row["id"], "cli_regenerate_recovery", "by=cli")

    print()
    print("=" * 62)
    print("  已为用户 [%s] 重新生成恢复码" % row["username"])
    print("=" * 62)
    print("  恢复码 : %s" % code)
    print()
    print("  ⚠️ 此码只显示这一次，请立即妥善保存。")
    print("     旧恢复码已失效。用户可在登录页用「忘记密码」自助重置。")
    print("=" * 62)
    print()
    return 0


def cmd_unlock(args):
    row = query_one("SELECT id, username FROM users WHERE username = ?",
                    (args.user,))
    if row is None:
        print("✗ 用户不存在: %s" % args.user, file=sys.stderr)
        return 1
    execute(
        "UPDATE users SET failed_login_count = 0, locked_until = NULL WHERE id = ?",
        (row["id"],),
    )
    audit(row["id"], "cli_unlock", "by=cli")
    print("✓ 已解除用户 [%s] 的登录锁定" % row["username"])
    return 0


def cmd_audit(args):
    rows = query(
        "SELECT a.created_at, a.action, a.detail, u.username "
        "FROM audit_log a LEFT JOIN users u ON u.id = a.user_id "
        "ORDER BY a.created_at DESC LIMIT ?",
        (args.limit,),
    )
    if not rows:
        print("（暂无审计记录）")
        return 0
    print("%-19s %-24s %-16s %s" % ("时间", "操作", "用户", "详情"))
    print("-" * 84)
    for r in rows:
        print("%-19s %-24s %-16s %s" % (
            _fmt_ts(r["created_at"]), r["action"],
            r["username"] or "(系统)", (r["detail"] or "")[:30],
        ))
    return 0


def cmd_init(args):
    """显式初始化数据库（若尚无管理员会打印初始凭据）。"""
    init_db()
    print("✓ 数据库已初始化")
    rows = query("SELECT username, role FROM users WHERE role = 'admin'")
    if rows:
        print("  现有管理员: %s" % ", ".join(r["username"] for r in rows))
    return 0


def main(argv=None):
    parser = argparse.ArgumentParser(
        prog="python -m backend.admin",
        description="ATF Lab 管理命令行工具（需服务器本地执行）",
    )
    sub = parser.add_subparsers(dest="cmd", required=True)

    p = sub.add_parser("init", help="初始化数据库")
    p.set_defaults(func=cmd_init)

    p = sub.add_parser("list-users", help="列出所有用户")
    p.set_defaults(func=cmd_list_users)

    p = sub.add_parser("reset-password", help="重置某个用户的密码")
    p.add_argument("--user", required=True, help="用户名")
    p.add_argument("--password", help="指定新密码；不填则随机生成")
    p.set_defaults(func=cmd_reset_password)

    p = sub.add_parser("show-recovery", help="重新生成用户的一次性恢复码")
    p.add_argument("--user", required=True, help="用户名")
    p.set_defaults(func=cmd_show_recovery)

    p = sub.add_parser("unlock", help="解除用户的登录锁定")
    p.add_argument("--user", required=True, help="用户名")
    p.set_defaults(func=cmd_unlock)

    p = sub.add_parser("audit", help="查看审计日志")
    p.add_argument("--limit", type=int, default=50, help="显示条数")
    p.set_defaults(func=cmd_audit)

    args = parser.parse_args(argv)
    init_db()
    return args.func(args)


if __name__ == "__main__":
    sys.exit(main())
