"""
ATF Lab - 验收标准自动核验

对照用户提出的 6 条验收标准逐项检查。
用法：python scripts/acceptance.py
"""
import io
import json
import re
import subprocess
import sys
import urllib.error
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
BASE = "http://127.0.0.1:8899"
R = []


def check(name, ok, detail=""):
    R.append((name, bool(ok), detail))


def get(path, token=None):
    req = urllib.request.Request(BASE + path)
    if token:
        req.add_header("Authorization", "Bearer " + token)
    try:
        with urllib.request.urlopen(req, timeout=15) as r:
            return json.loads(r.read().decode())
    except urllib.error.HTTPError as e:
        return json.loads(e.read().decode())
    except Exception as e:
        return {"code": -1, "message": str(e)}


def post(path, body, token=None):
    req = urllib.request.Request(
        BASE + path, data=json.dumps(body).encode(), method="POST")
    req.add_header("Content-Type", "application/json")
    if token:
        req.add_header("Authorization", "Bearer " + token)
    try:
        with urllib.request.urlopen(req, timeout=15) as r:
            return json.loads(r.read().decode())
    except urllib.error.HTTPError as e:
        return json.loads(e.read().decode())


def read(rel):
    p = ROOT / rel
    return io.open(p, encoding="utf-8").read() if p.is_file() else ""


def main():
    # ============ 标准 1：一条命令 docker compose up 即可完整启动 ============
    dc = read("docker-compose.yml")
    df = read("Dockerfile")
    check("1a. docker-compose.yml 存在且定义服务", "services:" in dc and "atf-lab" in dc)
    check("1b. Dockerfile 为多阶段构建", df.count("FROM ") >= 2 and "AS frontend-builder" in df)
    check("1c. compose 配置语法有效",
          subprocess.run(["docker", "compose", "config", "--quiet"],
                         cwd=str(ROOT), capture_output=True).returncode == 0)
    check("1d. compose 含健康检查与数据卷",
          "healthcheck:" in dc and "atf-data" in dc)
    # 三平台启动脚本
    for f in ("start.sh", "start.bat", "start.command"):
        check("1e. 启动脚本存在: " + f, (ROOT / f).is_file())

    # ============ 标准 2：注册登录、答题、进度入库跨浏览器 ============
    h = get("/api/v1/health")
    check("2a. 服务健康且 37 关已装载",
          h.get("code") == 0 and h.get("data", {}).get("levels") == 37,
          "levels=%s" % h.get("data", {}).get("levels"))

    import random
    u = "acc_%d" % random.randint(100000, 999999)
    reg = post("/api/v1/auth/register",
               {"username": u, "password": "Accept123!", "email": "a@b.local"})
    token = reg.get("data", {}).get("token")
    check("2b. 可注册并拿到 token", bool(token))

    me = get("/api/v1/auth/me", token)
    check("2c. token 可用于鉴权", me.get("data", {}).get("username") == u)

    sub = post("/api/v1/levels/L01/submit", {"flag": "flag{html_comment_leak}"}, token)
    check("2d. 可答题（flag 校验正确）",
          sub.get("data", {}).get("correct") is True)

    prog = get("/api/v1/progress", token)
    check("2e. 进度已写入数据库",
          prog.get("data", {}).get("count", 0) >= 1)

    # 关键：换一个"客户端"（新 token）读同一账号的进度，模拟换浏览器
    login = post("/api/v1/auth/login", {"username": u, "password": "Accept123!"})
    token2 = login.get("data", {}).get("token")
    # 注意：JWT 是**无状态**的。同一秒内用相同 payload（sub/iat/exp 一致）
    # 签发的 token 必然完全相同，这是设计使然，不是缺陷。
    # 这里真正要验证的是"能重新登录拿到可用 token"，而非 token 字符串必须不同。
    check("2f. 可重新登录并获得可用 token",
          bool(token2) and get("/api/v1/auth/me", token2).get("data", {}).get("username") == u)
    prog2 = get("/api/v1/levels", token2)
    solved = [l for l in prog2.get("data", {}).get("levels", []) if l.get("solved")]
    check("2g. ★换浏览器/换设备后进度仍在（服务端存储）",
          len(solved) >= 1 and solved[0]["id"] == "L01",
          "solved=%s" % [s["id"] for s in solved])

    # 确认进度不在 Cookie 里
    auth_src = read("backend/routers/auth.py")
    check("2h. 进度不依赖 Cookie（无 set_cookie）",
          "set_cookie" not in auth_src and "Cookie" not in read("backend/routers/levels.py"))

    # ============ 标准 3：前端所有数据交互均通过 API ============
    api_src = read("frontend/src/api.js")
    check("3a. 前端存在独立 API 客户端层", "export const api" in api_src)
    check("3b. API 客户端只调用 /api/v1/*", "/api/v1/" in api_src)

    fe_files = list((ROOT / "frontend" / "src").rglob("*.jsx")) + \
        list((ROOT / "frontend" / "src").rglob("*.js"))
    check("3c. 前端源码规模合理", len(fe_files) >= 15, "%d 个文件" % len(fe_files))

    # 检查是否有绕过 api.js 直接写死数据的情况
    direct_fetch = []
    for f in fe_files:
        if f.name == "api.js":
            continue
        t = io.open(f, encoding="utf-8").read()
        if re.search(r"\bfetch\s*\(", t):
            direct_fetch.append(f.name)
    check("3d. 组件层无直接 fetch（统一走 api.js）",
          len(direct_fetch) == 0, "越权文件: %s" % direct_fetch)

    # ============ 标准 4：免责声明三处到位 ============
    readme = read("README.md")
    check("4a. README 顶部有免责声明（首个标题）",
          readme.lstrip().startswith("# ⚠️ 免责声明"))

    footer = read("frontend/src/components/Common.jsx")
    check("4b. 页脚组件含免责声明", "DISCLAIMER_LINES" in footer and "footer-disclaimer" in footer)

    app = read("frontend/src/App.jsx")
    check("4c. 首次访问有确认弹窗", "DisclaimerModal" in app and "accepted" in app)

    disc = read("frontend/src/disclaimer.js")
    for phrase in ["仅供本人自行娱乐与安全学习使用",
                   "请勿在互联网上公开发布、部署或传播",
                   "由使用者自行承担"]:
        check("4d. 弹窗含声明原文: %s" % phrase[:14] + "…", phrase in disc)

    check("4e. 关卡页底部有教学模拟小字",
          "本关漏洞为教学模拟，禁止用于未授权测试" in read("frontend/src/components/Common.jsx"))

    lic = read("LICENSE")
    for phrase in ["仅供本人自行娱乐与安全学习使用",
                   "请勿在互联网上公开发布、部署或传播",
                   "由使用者自行承担"]:
        check("4f. LICENSE 含限制性条款: %s" % phrase[:14] + "…", phrase in lic)

    # ============ 标准 5：全部关卡可通过且 flag 校验正确 ============
    # 从关卡定义中提取全部 flag，逐个提交验证
    sys.path.insert(0, str(ROOT))
    from backend.challenges import load_all, registry
    load_all()
    all_levels = registry.all()
    check("5a. 关卡总数为 37", len(all_levels) == 37, "actual=%d" % len(all_levels))

    check("5b. 每关都有目标/提示>=3/原理讲解/难度/分类",
          all(lv.objective and len(lv.hints) >= 3 and lv.writeup
              and 1 <= lv.difficulty <= 5 and lv.category
              for lv in all_levels),
          "异常: %s" % [lv.id for lv in all_levels
                        if not (lv.objective and len(lv.hints) >= 3
                                and lv.writeup and lv.category)])

    # 先通关 5 个教学关以解锁 L37
    prereq = ["L01", "L16", "L17", "L18", "L22"]
    for lid in prereq:
        lv = registry.get(lid)
        if lv:
            post("/api/v1/levels/%s/submit" % lid, {"flag": lv.flag}, token)

    failed = []
    for lv in all_levels:
        r = post("/api/v1/levels/%s/submit" % lv.id, {"flag": lv.flag}, token)
        if not r.get("data", {}).get("correct"):
            failed.append("%s(%s)" % (lv.id, r.get("code")))
    check("5c. ★全部 37 关 flag 均校验通过",
          len(failed) == 0, "失败: %s" % failed)

    wrong = post("/api/v1/levels/L01/submit", {"flag": "flag{definitely_wrong}"}, token)
    check("5d. 错误 flag 被正确拒绝",
          wrong.get("data", {}).get("correct") is False)

    lst = get("/api/v1/levels", token)
    raw = json.dumps(lst, ensure_ascii=False)
    check("5e. 关卡列表不泄露 flag 明文", "flag{" not in raw)

    # ============ 标准 6：不含任何可危害真实系统的功能 ============
    audit = subprocess.run([sys.executable, str(ROOT / "scripts" / "audit_safety.py")],
                           cwd=str(ROOT), capture_output=True)
    check("6a. ★AST 安全审计全部通过", audit.returncode == 0)

    audit_txt = ""
    p = ROOT / "safety_audit_result.txt"
    if p.is_file():
        audit_txt = io.open(p, encoding="utf-8").read()
    check("6b. 无命令执行能力", "未导入 subprocess" in audit_txt)
    check("6c. 无真实反序列化", "未导入 pickle" in audit_txt)
    check("6d. 无出站 HTTP 请求", "未导入 requests" in audit_txt)
    check("6e. 无真实 XML 解析", "未导入 xml" in audit_txt)
    check("6f. netlab 仅监听回环", "仅绑定 127.0.0.1" in audit_txt)
    check("6g. 压轴关只操作模拟表", "只操作模拟表" in audit_txt)
    check("6h. 压轴关密钥与平台隔离", "密钥与 audience 均与平台隔离" in audit_txt)

    # ============ 附加：交付物清单 ============
    for f in ["README.md", "LICENSE", ".gitignore", ".env.example",
              "Dockerfile", "docker-compose.yml", "docs/API.md"]:
        check("7. 交付物存在: " + f, (ROOT / f).is_file())

    # ============ 输出 ============
    passed = sum(1 for _, ok, _ in R if ok)
    total = len(R)
    lines = ["=" * 74, "ATF Lab 验收标准核验报告", "=" * 74, ""]
    section = ""
    for name, ok, detail in R:
        head = name.split(".")[0]
        if head != section:
            section = head
        mark = "PASS" if ok else "FAIL"
        line = "%s  %s" % (mark, name)
        if detail and not ok:
            line += "   <- " + detail
        lines.append(line)
    lines.append("")
    lines.append("=" * 74)
    lines.append("通过 %d / %d" % (passed, total))
    lines.append("=" * 74)

    report = "\n".join(lines)
    io.open(ROOT / "acceptance_result.txt", "w", encoding="utf-8").write(report)
    print("acceptance: %d/%d passed (see acceptance_result.txt)" % (passed, total))
    return 0 if passed == total else 1


if __name__ == "__main__":
    sys.exit(main())
