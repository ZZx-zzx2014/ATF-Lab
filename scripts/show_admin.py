"""查询管理员账号状态（不显示密码，密码只存哈希）。"""
import io
import sqlite3

db = r"D:\deepseek-harness\ATF_sever\data\atf.db"
lines = []
try:
    con = sqlite3.connect(db)
    con.row_factory = sqlite3.Row
    rows = con.execute(
        "SELECT id, username, role, must_change_password, "
        "       (recovery_code_hash IS NOT NULL) AS has_rc, "
        "       (password_hash IS NOT NULL) AS has_pw, "
        "       password_changed_at, created_at "
        "FROM users ORDER BY id"
    ).fetchall()
    lines.append("数据库中的用户（共 %d 个）" % len(rows))
    lines.append("=" * 72)
    lines.append("%-4s %-16s %-7s %-10s %-8s %s" % (
        "ID", "用户名", "角色", "需改密", "有恢复码", "改密时间"))
    lines.append("-" * 72)
    for r in rows:
        lines.append("%-4s %-16s %-7s %-10s %-8s %s" % (
            r["id"], r["username"], r["role"],
            "是" if r["must_change_password"] else "否",
            "是" if r["has_rc"] else "否",
            r["password_changed_at"] or "-"))
    con.close()
except Exception as e:
    lines.append("读取失败: %s" % e)

lines.append("")
lines.append("说明：密码以 PBKDF2-HMAC-SHA256 哈希存储，无法反推明文。")

io.open(r"D:\deepseek-harness\ATF_sever\admin_info.txt", "w",
        encoding="utf-8").write("\n".join(lines))
print("written")
