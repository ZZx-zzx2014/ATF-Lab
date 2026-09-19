"""
验证「全解锁体验账号」功能。

检查项：
  1. demo 账号可登录
  2. 角色是普通 user（不是 admin）
  3. 37 关全部解锁
  4. 能读取任意关卡的 writeup（含压轴关）
  5. 排行榜显示 is_demo 标识
  6. 不能访问管理后台
"""
import io
import json
import os
import sqlite3
import sys
import urllib.error
import urllib.request

BASE = "http://127.0.0.1:8899"
ROOT = r"D:\deepseek-harness\ATF_sever"
R = []


def call(method, path, body=None, token=None):
    req = urllib.request.Request(
        BASE + path,
        data=json.dumps(body).encode() if body is not None else None,
        method=method)
    req.add_header("Content-Type", "application/json")
    if token:
        req.add_header("Authorization", "Bearer " + token)
    try:
        with urllib.request.urlopen(req, timeout=15) as r:
            return json.loads(r.read().decode())
    except urllib.error.HTTPError as e:
        try:
            return json.loads(e.read().decode())
        except Exception:
            return {"code": -1, "message": "non-json"}
    except Exception as e:
        return {"code": -1, "message": str(e)}


def check(name, cond, detail=""):
    R.append((name, bool(cond), detail))


def main():
    # 从数据库取 demo 账号是否存在及其标记
    db = os.path.join(ROOT, "data", "atf.db")
    con = sqlite3.connect(db)
    con.row_factory = sqlite3.Row
    row = con.execute(
        "SELECT id, username, role, is_demo, must_change_password "
        "FROM users WHERE username = 'demo'").fetchone()
    n_solves = 0
    if row:
        n_solves = con.execute(
            "SELECT COUNT(*) AS c FROM solves WHERE user_id = ?",
            (row["id"],)).fetchone()["c"]
    con.close()

    check("demo 账号已创建", row is not None)
    if row is None:
        report()
        return 1

    check("★demo 角色为普通用户 user（非 admin）",
          row["role"] == "user", "role=%s" % row["role"])
    check("★demo 标记 is_demo=1", row["is_demo"] == 1,
          "is_demo=%s" % row["is_demo"])
    check("★demo 已解锁全部 37 关", n_solves == 37,
          "solves=%d" % n_solves)
    check("demo 不要求改密（体验账号直接可用）",
          row["must_change_password"] == 0)

    # 需要密码才能测登录，从文件读取
    pwfile = os.path.join(ROOT, "demo_password.txt")
    if not os.path.isfile(pwfile):
        check("找到 demo 密码文件", False, "缺少 demo_password.txt")
        report()
        return 1
    pw = io.open(pwfile, encoding="utf-8-sig").read().strip()

    # 登录
    lg = call("POST", "/api/v1/auth/login",
              {"username": "demo", "password": pw})
    check("★demo 账号可登录", lg.get("code") == 0, lg.get("message", "")[:50])
    tok = lg.get("data", {}).get("token")
    if not tok:
        report()
        return 1

    u = lg.get("data", {}).get("user", {})
    check("登录响应含 is_demo 字段", u.get("is_demo") is True,
          "is_demo=%s" % u.get("is_demo"))

    # 关卡列表：应全部 solved
    lst = call("GET", "/api/v1/levels", token=tok)
    levels = lst.get("data", {}).get("levels", [])
    solved = [l for l in levels if l.get("solved")]
    check("★关卡列表中全部显示已通关",
          len(solved) == len(levels) == 37,
          "solved=%d total=%d" % (len(solved), len(levels)))

    # writeup 应可见
    with_writeup = [l for l in levels if l.get("writeup")]
    check("★全部关卡 writeup 可见", len(with_writeup) == 37,
          "with_writeup=%d" % len(with_writeup))

    # 压轴关解锁状态
    l37 = call("GET", "/api/v1/levels/L37", token=tok)
    check("★压轴关 L37 已解锁",
          l37.get("data", {}).get("unlocked") is True,
          "unlocked=%s" % l37.get("data", {}).get("unlocked"))
    check("压轴关 writeup 可见",
          bool(l37.get("data", {}).get("writeup")))

    # 排行榜标识
    lb = call("GET", "/api/v1/leaderboard", token=tok)
    entries = lb.get("data", {}).get("entries", [])
    demo_e = [e for e in entries if e["username"] == "demo"]
    check("demo 出现在排行榜", len(demo_e) == 1)
    if demo_e:
        check("★排行榜中标示 is_demo=true",
              demo_e[0].get("is_demo") is True,
              "is_demo=%s" % demo_e[0].get("is_demo"))
        check("demo 得分为满分 4710",
              demo_e[0].get("points") == 4710,
              "points=%s" % demo_e[0].get("points"))

    # 权限边界：不能访问管理后台
    adm = call("GET", "/api/v1/admin/stats", token=tok)
    check("★demo 无法访问管理后台（1003）",
          adm.get("code") == 1003, "code=%s" % adm.get("code"))
    adm2 = call("GET", "/api/v1/admin/levels", token=tok)
    check("★demo 无法读取关卡 flag 明文（1003）",
          adm2.get("code") == 1003, "code=%s" % adm2.get("code"))

    # 个人主页
    prof = call("GET", "/api/v1/me/profile", token=tok)
    check("个人主页含 is_demo",
          prof.get("data", {}).get("is_demo") is True)
    check("个人主页徽章全部点亮",
          all(b["earned"] for b in prof.get("data", {}).get("all_badges", [])),
          "%d 个徽章" % len(prof.get("data", {}).get("all_badges", [])))

    return report()


def report():
    passed = sum(1 for _, ok, _ in R if ok)
    total = len(R)
    lines = ["=" * 70, "体验账号（demo）功能验证", "=" * 70, ""]
    for name, ok, detail in R:
        line = "%s  %s" % ("PASS" if ok else "FAIL", name)
        if detail and not ok:
            line += "   <- " + detail
        lines.append(line)
    lines.append("")
    lines.append("通过 %d / %d" % (passed, total))
    io.open(os.path.join(ROOT, "demo_test_result.txt"), "w",
            encoding="utf-8").write("\n".join(lines))
    print("demo test: %d/%d passed" % (passed, total))
    return 0 if passed == total else 1


if __name__ == "__main__":
    sys.exit(main())
