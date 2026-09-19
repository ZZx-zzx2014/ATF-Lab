"""
ATF Lab - 认证与账号安全测试

覆盖：注册恢复码 / 改密 / 密码恢复 / 登录限流 / 管理员初始化 /
      安全响应头 / 密钥强度校验

用法：python scripts/test_auth.py [base_url]
"""
import io
import json
import random
import sys
import time
import urllib.error
import urllib.request

BASE = sys.argv[1] if len(sys.argv) > 1 else "http://127.0.0.1:8899"
R = []


def call(method, path, body=None, token=None):
    req = urllib.request.Request(
        BASE + path,
        data=json.dumps(body).encode() if body is not None else None,
        method=method,
    )
    req.add_header("Content-Type", "application/json")
    if token:
        req.add_header("Authorization", "Bearer " + token)
    try:
        with urllib.request.urlopen(req, timeout=15) as r:
            return json.loads(r.read().decode()), dict(r.headers)
    except urllib.error.HTTPError as e:
        raw = e.read().decode()
        try:
            return json.loads(raw), dict(e.headers)
        except Exception:
            return {"code": -1, "message": raw[:120]}, dict(e.headers)
    except Exception as e:
        return {"code": -1, "message": str(e)}, {}


def check(name, cond, detail=""):
    R.append((name, bool(cond), detail))


def rnd(prefix="t"):
    return "%s_%d" % (prefix, random.randint(100000, 999999))


def main():
    # ============ 注册与恢复码 ============
    u = rnd("auth")
    d, _ = call("POST", "/api/v1/auth/register",
                {"username": u, "password": "InitialPass123", "email": ""})
    check("注册成功", d.get("code") == 0, d.get("message", "")[:50])
    tok = d.get("data", {}).get("token")
    rcode = d.get("data", {}).get("recovery_code")
    check("注册返回一次性恢复码", bool(rcode), "recovery_code=%s" % rcode)
    check("恢复码格式为 XXXX-XXXX-XXXX-XXXX",
          bool(rcode) and len(rcode) == 19 and rcode.count("-") == 3,
          rcode or "")
    check("注册响应含恢复码提示",
          "只显示这一次" in (d.get("data", {}).get("recovery_notice") or ""))

    # ============ 弱密码拒绝 ============
    d2, _ = call("POST", "/api/v1/auth/register",
                 {"username": rnd("weak"), "password": "12345678"})
    check("弱口令被拒绝(1001)", d2.get("code") == 1001, d2.get("message", "")[:40])
    d3, _ = call("POST", "/api/v1/auth/register",
                 {"username": rnd("weak2"), "password": "abcdefgh"})
    check("无数字口令被拒绝", d3.get("code") == 1001, d3.get("message", "")[:40])

    # ============ must_change_password 字段 ============
    me, _ = call("GET", "/api/v1/auth/me", token=tok)
    check("普通用户 must_change_password=false",
          me.get("data", {}).get("must_change_password") is False,
          str(me.get("data", {}).get("must_change_password")))

    # ============ 修改密码 ============
    cp, _ = call("POST", "/api/v1/auth/change-password",
                 {"old_password": "InitialPass123", "new_password": "NewPass456789"},
                 token=tok)
    check("修改密码成功", cp.get("code") == 0, cp.get("message", "")[:40])

    old_login, _ = call("POST", "/api/v1/auth/login",
                        {"username": u, "password": "InitialPass123"})
    check("旧密码已失效(1002)", old_login.get("code") == 1002)

    new_login, _ = call("POST", "/api/v1/auth/login",
                        {"username": u, "password": "NewPass456789"})
    check("新密码可登录", new_login.get("code") == 0)
    tok2 = new_login.get("data", {}).get("token")

    # 相同密码改密应被拒绝
    same, _ = call("POST", "/api/v1/auth/change-password",
                   {"old_password": "NewPass456789", "new_password": "NewPass456789"},
                   token=tok2)
    check("新旧密码相同被拒绝", same.get("code") == 1001, same.get("message", "")[:40])

    # 错误旧密码应被拒绝
    wrong_old, _ = call("POST", "/api/v1/auth/change-password",
                        {"old_password": "WrongOld123", "new_password": "Another12345"},
                        token=tok2)
    check("错误旧密码被拒绝(1002)", wrong_old.get("code") == 1002)

    # ============ 密码恢复（核心：替代后门密码） ============
    u2 = rnd("rec")
    reg2, _ = call("POST", "/api/v1/auth/register",
                   {"username": u2, "password": "OriginalPass1", "email": ""})
    code2 = reg2.get("data", {}).get("recovery_code")

    # 错误恢复码
    bad, _ = call("POST", "/api/v1/auth/recover",
                  {"username": u2, "recovery_code": "AAAA-BBBB-CCCC-DDDD",
                   "new_password": "RecoveredPass1"})
    check("错误恢复码被拒绝(1002)", bad.get("code") == 1002, bad.get("message", "")[:40])

    # 正确恢复码
    good, _ = call("POST", "/api/v1/auth/recover",
                   {"username": u2, "recovery_code": code2,
                    "new_password": "RecoveredPass1"})
    check("★使用恢复码成功重置密码", good.get("code") == 0, good.get("message", "")[:40])
    check("恢复后返回新的恢复码",
          bool(good.get("data", {}).get("recovery_code")))
    new_rc = good.get("data", {}).get("recovery_code")
    check("新恢复码与旧的不同", new_rc != code2)

    # 恢复后的密码可登录
    rl, _ = call("POST", "/api/v1/auth/login",
                 {"username": u2, "password": "RecoveredPass1"})
    check("恢复后的密码可登录", rl.get("code") == 0)

    # ★ 旧恢复码必须失效（一次性）
    reuse, _ = call("POST", "/api/v1/auth/recover",
                    {"username": u2, "recovery_code": code2,
                     "new_password": "Hacked12345"})
    check("★旧恢复码已失效（一次性）", reuse.get("code") == 1002,
          "code=%s" % reuse.get("code"))

    # 新恢复码仍可用
    reuse2, _ = call("POST", "/api/v1/auth/recover",
                     {"username": u2, "recovery_code": new_rc,
                      "new_password": "FinalPass12345"})
    check("新恢复码可用", reuse2.get("code") == 0)

    # ============ 重新生成恢复码（需登录） ============
    tok3 = reuse2.get("data", {}).get("token")
    rg, _ = call("POST", "/api/v1/auth/regenerate-recovery", {}, token=tok3)
    check("已登录用户可轮换恢复码", rg.get("code") == 0)
    check("轮换后的恢复码不同于旧的",
          rg.get("data", {}).get("recovery_code") != new_rc)

    # ============ 登录限流 ============
    u3 = rnd("lock")
    call("POST", "/api/v1/auth/register",
         {"username": u3, "password": "LockTest123", "email": ""})
    codes = []
    for i in range(6):
        r, _ = call("POST", "/api/v1/auth/login",
                    {"username": u3, "password": "DefinitelyWrong%d" % i})
        codes.append(r.get("code"))
    check("★连续失败触发账号锁定(1006)",
          1006 in codes, "codes=%s" % codes)
    # 锁定期内即使密码正确也应被拒
    locked_ok, _ = call("POST", "/api/v1/auth/login",
                        {"username": u3, "password": "LockTest123"})
    check("锁定期内正确密码也被拒绝", locked_ok.get("code") == 1006,
          "code=%s" % locked_ok.get("code"))

    # ============ 账号枚举防护 ============
    nonexist, _ = call("POST", "/api/v1/auth/login",
                       {"username": "no_such_user_xyz", "password": "whatever123"})
    check("不存在的用户也返回统一错误(1002)", nonexist.get("code") == 1002)

    # ============ 安全响应头 ============
    _, headers = call("GET", "/api/v1/health")
    hl = {k.lower(): v for k, v in headers.items()}
    check("含 X-Content-Type-Options", hl.get("x-content-type-options") == "nosniff")
    check("含 X-Frame-Options", hl.get("x-frame-options") == "DENY")
    check("含 Referrer-Policy", hl.get("referrer-policy") == "no-referrer")
    check("含 Content-Security-Policy", "content-security-policy" in hl)
    check("含 Permissions-Policy", "permissions-policy" in hl)

    # ============ 管理员初始化 ============
    # 直接查库确认（避免依赖 CLI 的中文控制台输出编码）
    import sqlite3
    db = r"D:\deepseek-harness\ATF_sever\data\atf.db"
    con = sqlite3.connect(db)
    con.row_factory = sqlite3.Row
    row = con.execute(
        "SELECT username, role, must_change_password, "
        "       (recovery_code_hash IS NOT NULL) AS has_rc "
        "FROM users WHERE role = 'admin' LIMIT 1"
    ).fetchone()
    con.close()
    check("存在自动创建的管理员账号",
          row is not None and row["username"] == "admin",
          "row=%s" % (dict(row) if row else None))
    check("★管理员被标记为需改密(must_change_password=1)",
          row is not None and row["must_change_password"] == 1,
          "must_change_password=%s" % (row["must_change_password"] if row else "N/A"))
    check("管理员有恢复码",
          row is not None and row["has_rc"] == 1)

    # ============ 输出 ============
    passed = sum(1 for _, ok, _ in R if ok)
    total = len(R)
    lines = ["=" * 72, "ATF Lab 认证与账号安全测试", "=" * 72, ""]
    for name, ok, detail in R:
        line = "%s  %s" % ("PASS" if ok else "FAIL", name)
        if detail and not ok:
            line += "   <- " + detail
        lines.append(line)
    lines.append("")
    lines.append("通过 %d / %d" % (passed, total))
    io.open("auth_test_result.txt", "w", encoding="utf-8").write("\n".join(lines))
    print("auth test: %d/%d passed (see auth_test_result.txt)" % (passed, total))
    return 0 if passed == total else 1


if __name__ == "__main__":
    sys.exit(main())
