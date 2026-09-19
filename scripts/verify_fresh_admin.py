"""在全新数据库上验证管理员初始化行为。"""
import io
import os
import sys

# 指向一个临时的干净库
tmp = r"D:\deepseek-harness\ATF_sever\.tmp_verify"
os.makedirs(tmp, exist_ok=True)
os.environ["ATF_DB_PATH"] = os.path.join(tmp, "atf.db")

sys.path.insert(0, r"D:\deepseek-harness\ATF_sever")
from backend.database import init_db, query_one  # noqa: E402

init_db()
r = query_one("SELECT username, must_change_password, "
              "recovery_code_hash IS NOT NULL AS rc "
              "FROM users WHERE role = 'admin'")

lines = [
    "全新数据库初始化验证",
    "=" * 50,
    "用户名           : %s" % r["username"],
    "must_change_password : %s  (期望 1)" % r["must_change_password"],
    "有恢复码         : %s" % r["rc"],
    "",
    "结论             : %s" % (
        "正确 - 初始管理员被标记为需改密" if r["must_change_password"] == 1
        else "错误"),
]
io.open(os.path.join(tmp, "result.txt"), "w", encoding="utf-8").write(
    "\n".join(lines))
print("done")
