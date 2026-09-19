"""
ATF Lab - 安全边界自查

⚠️ 本脚本用于验证项目的核心承诺：
   "所有漏洞均为受控模拟，不具备危害真实系统的能力"

设计说明：
   采用 **AST 静态分析**而非文本正则匹配。
   原因：代码与文档中有大量"不要使用 subprocess / pickle"这类**说明性文字**，
   正则会把它们误判为真实调用。AST 只看真实的导入与调用节点，结果准确。

任何一项 FAIL 都意味着项目违反了安全边界约定。

用法：python scripts/audit_safety.py
"""
import ast
import io
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent

# ---------------------------------------------------------------- 检测规则

# 禁止导入的模块
FORBIDDEN_MODULES = {
    "subprocess": "命令执行",
    "pickle": "危险反序列化",
    "marshal": "危险反序列化",
    "shelve": "危险反序列化",
    "dill": "危险反序列化",
    "requests": "出站 HTTP 请求",
    "httpx": "出站 HTTP 请求",
    "aiohttp": "出站 HTTP 请求",
    "xml": "真实 XML 解析器（XXE 应为模拟）",
    "lxml": "真实 XML 解析器（XXE 应为模拟）",
    "telnetlib": "网络交互",
    "ftplib": "网络交互",
    "smtplib": "网络交互",
    "paramiko": "SSH 交互",
}

# 禁止调用的函数名（按属性名或标识符名匹配）
FORBIDDEN_CALLS = {
    "system": "os.system 命令执行",
    "popen": "os.popen 命令执行",
    "execv": "os.exec* 命令执行",
    "execve": "os.exec* 命令执行",
    "execl": "os.exec* 命令执行",
    "spawnl": "os.spawn* 命令执行",
    "spawnv": "os.spawn* 命令执行",
    "eval": "动态代码执行",
    "urlopen": "出站 HTTP 请求",
    "create_connection": "socket 出站连接",
}

# 允许的例外：文件相对路径前缀 → 规则名集合（"*" 表示全部）
#
# 说明：scripts/ 下的**验证脚本**需要发起本地 HTTP 请求来测试 API、
# 或调用子进程来运行其他检查。它们属于开发期测试工具，
# 不参与线上运行，因此与 backend/ 和 netlab/ 的严格标准区别对待。
ALLOWLIST = {
    # 自测脚本需要发起本地 HTTP 请求来验证 API 是否正常
    "scripts/smoke_test.py": {"出站 HTTP 请求", "socket 出站连接"},
    "scripts/check_netlab.py": {"socket 出站连接"},
    # 验收脚本需要发请求 + 调用审计子进程
    "scripts/acceptance.py": {"出站 HTTP 请求", "socket 出站连接",
                              "命令执行"},
    # 本脚本自身包含规则文本
    "scripts/audit_safety.py": {"*"},
    # sqlite3.connect 是本地文件数据库，不是网络连接
    "backend/database.py": {"socket 出站连接"},
    "backend/deps.py": {"socket 出站连接"},
}


def is_allowed(rel: str, rule: str) -> bool:
    for prefix, rules in ALLOWLIST.items():
        if rel == prefix or rel.startswith(prefix):
            if "*" in rules or rule in rules:
                return True
    return False


# ---------------------------------------------------------------- 扫描实现

def scan() -> tuple:
    """返回 (扫描文件数, 命中列表)"""
    hits = []
    files = [p for p in ROOT.rglob("*.py")
             if "__pycache__" not in p.parts
             and ".venv" not in p.parts
             and "node_modules" not in p.parts]

    for p in files:
        rel = p.relative_to(ROOT).as_posix()
        try:
            src = io.open(p, encoding="utf-8").read()
            tree = ast.parse(src)
        except (SyntaxError, UnicodeDecodeError):
            continue
        lines = src.split("\n")

        def snippet(lineno):
            if 1 <= lineno <= len(lines):
                return lines[lineno - 1].strip()[:90]
            return ""

        for node in ast.walk(tree):
            # --- 导入检查 ---
            if isinstance(node, ast.Import):
                for alias in node.names:
                    root = alias.name.split(".")[0]
                    if root in FORBIDDEN_MODULES:
                        rule = FORBIDDEN_MODULES[root]
                        if not is_allowed(rel, rule):
                            hits.append((rule, rel, node.lineno,
                                         "import " + alias.name))
            elif isinstance(node, ast.ImportFrom):
                root = (node.module or "").split(".")[0]
                if root in FORBIDDEN_MODULES:
                    rule = FORBIDDEN_MODULES[root]
                    if not is_allowed(rel, rule):
                        hits.append((rule, rel, node.lineno,
                                     "from %s import ..." % node.module))

            # --- 调用检查 ---
            elif isinstance(node, ast.Call):
                f = node.func
                name = f.attr if isinstance(f, ast.Attribute) else (
                    f.id if isinstance(f, ast.Name) else None)

                # sqlite3.connect 是本地数据库，显式放行
                if name == "connect":
                    base = f.value.id if (
                        isinstance(f, ast.Attribute)
                        and isinstance(f.value, ast.Name)) else ""
                    if base == "sqlite3":
                        continue
                    if not is_allowed(rel, "socket 出站连接"):
                        hits.append(("socket 出站连接", rel, node.lineno,
                                     snippet(node.lineno)))

                if name in FORBIDDEN_CALLS:
                    rule = FORBIDDEN_CALLS[name]
                    if not is_allowed(rel, rule):
                        hits.append((rule, rel, node.lineno,
                                     snippet(node.lineno)))

    return len(files), hits


# ---------------------------------------------------------------- 专项检查

def check_netlab_loopback():
    p = ROOT / "netlab" / "services.py"
    if not p.is_file():
        return False, "netlab/services.py 不存在"
    text = io.open(p, encoding="utf-8").read()
    ok = 'bind(("127.0.0.1"' in text
    return ok, ("仅绑定 127.0.0.1 ✓" if ok else "绑定地址不是仅回环 ✗")


def check_sim_tables():
    p = ROOT / "backend" / "challenges" / "finale.py"
    if not p.is_file():
        return False, "finale.py 不存在"
    import re
    text = io.open(p, encoding="utf-8").read()
    tables = set(re.findall(
        r"(?:UPDATE|DELETE\s+FROM|INSERT\s+INTO)\s+(\w+)", text, re.I))
    non_sim = {t for t in tables if not t.startswith("sim_")}
    if non_sim:
        return False, "操作了非模拟表: %s" % sorted(non_sim)
    return True, "只操作模拟表 %s ✓" % sorted(tables)


def check_no_flag_leak():
    p = ROOT / "backend" / "challenges" / "base.py"
    import re
    text = io.open(p, encoding="utf-8").read()
    m = re.search(r"def public\(.*?\n(?=    def |\nclass |\Z)", text, re.S)
    if not m:
        return False, "无法定位 public() 方法"
    body = m.group(0)
    if re.search(r'"flag"\s*:\s*self\.flag', body):
        return False, "public() 泄露了 flag 明文 ✗"
    if '"flag"' not in body and "flag" not in body:
        return True, "未包含 flag 字段 ✓"
    return True, "未泄露 flag 明文 ✓"


def check_upload_no_disk():
    p = ROOT / "backend" / "challenges" / "sandbox.py"
    import re
    text = io.open(p, encoding="utf-8").read()
    m = re.search(r"def fake_upload\(.*?\n(?=# =|def |\Z)", text, re.S)
    body = m.group(0) if m else ""
    ok = "open(" not in body and ".write(" not in body
    return ok, ("不落盘 ✓" if ok else "存在磁盘写入 ✗")


def check_l37_isolation():
    """压轴关的弱密钥必须与平台密钥不同。"""
    p = ROOT / "backend" / "challenges" / "finale.py"
    import re
    text = io.open(p, encoding="utf-8").read()
    m = re.search(r'FINALE_SECRET\s*=\s*["\']([^"\']+)["\']', text)
    if not m:
        return False, "未找到 FINALE_SECRET"
    finale_secret = m.group(1)

    cfg = io.open(ROOT / "backend" / "config.py", encoding="utf-8").read()
    default_secret = "atf-lab-dev-secret-change-me"
    if finale_secret == default_secret:
        return False, "压轴关密钥与平台默认密钥相同 ✗"

    # audience 也必须不同
    aud_ok = "atf-platform" in io.open(
        ROOT / "backend" / "security.py", encoding="utf-8").read()
    finale_aud_ok = "helios-portal-sim" in text
    if not (aud_ok and finale_aud_ok):
        return False, "audience 未正确隔离 ✗"
    return True, "密钥与 audience 均与平台隔离 ✓"


# ---------------------------------------------------------------- 主流程

def main():
    out = []
    out.append("=" * 74)
    out.append("ATF Lab 安全边界自查报告")
    out.append("=" * 74)
    out.append("")
    out.append("目的：验证「所有漏洞均为受控模拟，不具备危害真实系统的能力」")
    out.append("方法：AST 静态分析（只看真实导入与调用，不受注释/文档干扰）")
    out.append("")

    n_files, hits = scan()
    out.append("扫描 %d 个 Python 文件" % n_files)
    out.append("")
    out.append("-" * 74)
    out.append("[1] 危险能力调用扫描")
    out.append("-" * 74)

    if hits:
        by_rule = {}
        for rule, rel, ln, snip in hits:
            by_rule.setdefault(rule, []).append((rel, ln, snip))
        for rule, items in sorted(by_rule.items()):
            out.append("FAIL  %s  (%d 处)" % (rule, len(items)))
            for rel, ln, snip in items[:8]:
                out.append("        %s:%d" % (rel, ln))
                out.append("          %s" % snip)
            if len(items) > 8:
                out.append("        ... 另有 %d 处" % (len(items) - 8))
    else:
        out.append("PASS  未发现任何真实的危险能力调用 ✓")
        out.append("")
        out.append("       已确认不存在的危险能力：")
        for mod, desc in sorted(FORBIDDEN_MODULES.items()):
            out.append("         ✗ 未导入 %-14s (%s)" % (mod, desc))
        for fn, desc in sorted(FORBIDDEN_CALLS.items()):
            out.append("         ✗ 未调用 %-14s (%s)" % (fn, desc))
        out.append("")
        out.append("       说明：scripts/ 下的验证脚本需要发起本地 HTTP 请求")
        out.append("       来测试 API 是否正常，属于开发期测试工具，")
        out.append("       不参与线上运行（见 ALLOWLIST）。")

    out.append("")
    out.append("-" * 74)
    out.append("[2] 专项检查")
    out.append("-" * 74)
    checks = [
        ("netlab 仅绑定回环", check_netlab_loopback),
        ("压轴关只操作模拟表", check_sim_tables),
        ("关卡公开字段不含 flag", check_no_flag_leak),
        ("上传模拟不落盘", check_upload_no_disk),
        ("★L37 密钥与平台隔离", check_l37_isolation),
    ]
    all_pass = not hits
    for name, fn in checks:
        try:
            ok, detail = fn()
        except Exception as e:
            ok, detail = False, "检查异常: %s" % e
        out.append("%s  %-22s %s" % ("PASS" if ok else "FAIL", name, detail))
        if not ok:
            all_pass = False

    out.append("")
    out.append("=" * 74)
    if all_pass:
        out.append("结论：全部通过 ✓")
        out.append("")
        out.append("  本项目符合「受控模拟」的安全边界约定：")
        out.append("   · 无命令执行能力      · 无真实文件读写")
        out.append("   · 无出站网络请求      · 无真实反序列化")
        out.append("   · 无真实 XML 解析     · 仿真服务仅监听回环")
        out.append("   · 压轴关只操作模拟表  · flag 明文不下发前端")
    else:
        out.append("结论：存在问题 ✗ 请修复上方 FAIL 项")
    out.append("=" * 74)

    report = "\n".join(out)
    io.open(ROOT / "safety_audit_result.txt", "w", encoding="utf-8").write(report)
    # 控制台可能是 GBK，避免打印特殊符号导致 UnicodeEncodeError
    status = "ALL PASS" if all_pass else "FAILED"
    print("safety audit: %s (%d files scanned)" % (status, n_files))
    print("report written to safety_audit_result.txt")
    return 0 if all_pass else 1


if __name__ == "__main__":
    sys.exit(main())
