"""
ATF Lab - 受控模拟沙箱（安全边界核心）

⚠️⚠️ 仅供教学演示（CONTROLLED SIMULATION — EDUCATIONAL USE ONLY）⚠️⚠️

本模块是【整个项目安全边界的技术落地】。它刻意只提供"假的"能力：

    真实危险能力                    本模块提供的替代品
    ------------------------------  ----------------------------------
    subprocess / os.system          硬编码字符串回显（_fake_shell）
    open() 读写真实文件系统          内存字典构成的虚拟文件树（_VFS）
    出站 HTTP 请求                   仅允许内置 mock 端点（_ALLOWED_SSRF）
    pickle.loads / yaml.load         自定义安全解析器，绝不反序列化
    真实 SQL 拼接                    模式匹配判定，返回预置假结果集
    真实 socket 连接                 静态字节串（netlab）

红线：本文件不得引入 subprocess / os.system / eval / exec / socket 出站 /
      pickle / marshal / yaml.load / open(...,'w') 等任何真实危险调用。
"""

import re
from typing import Any

# 所有模拟响应都带上这个字段，防止使用者误判为真实漏洞
SIM_NOTICE = "本响应由 ATF Lab 教学沙箱生成，为受控模拟数据，不对应任何真实系统。"


def sim(data: Any) -> dict:
    """包装模拟响应。"""
    if isinstance(data, dict):
        return {**data, "_simulation": True, "_simulation_notice": SIM_NOTICE}
    return {"result": data, "_simulation": True, "_simulation_notice": SIM_NOTICE}


# ==================================================================
# 1. 虚拟文件系统（内存字典）
# ⚠️ 仅供教学演示：路径穿越只在字典键里解析，绝不触达真实磁盘。
# ==================================================================

_VFS: dict[str, str] = {
    "/": "drwxr-xr-x  root  root   var  etc  home  www",
    "/etc/passwd": (
        "root:x:0:0:root:/root:/bin/bash\n"
        "www-data:x:33:33:www-data:/var/www:/usr/sbin/nologin\n"
        "helios:x:1001:1001:Helios Service:/home/helios:/bin/bash"
    ),
    "/etc/hostname": "helios-portal",
    "/var/www/html/index.html": "<h1>Helios Biotech Portal</h1>",
    "/var/www/html/config.php": (
        "<?php\n"
        "// ⚠️ 教学模拟文件：这里的凭据是虚构的，不可用于任何真实系统\n"
        "$db_host = '127.0.0.1';\n"
        "$db_user = 'helios_app';\n"
        "$db_pass = 'SIMULATED_NOT_REAL';\n"
    ),
    "/home/helios/notes.txt": (
        "运维备忘（模拟）\n"
        "- 门户改版后旧接口 /api/legacy/employees 忘了下线\n"
        "- 管理员入口 /helios/portal/admin\n"
    ),
    "/var/log/helios/access.log": (
        '10.0.3.14 - - [12/Mar/2024:09:14:02] "GET /helios/portal HTTP/1.1" 200\n'
        '10.0.3.14 - - [12/Mar/2024:09:15:41] "POST /helios/portal/login HTTP/1.1" 401\n'
        '203.0.113.9 - - [12/Mar/2024:09:16:03] "GET /api/legacy/employees HTTP/1.1" 200\n'
        '203.0.113.9 - - [12/Mar/2024:09:16:55] "GET /helios/portal/admin HTTP/1.1" 302\n'
    ),
}

TRAVERSAL_MARKERS = ("../", "..\\", "%2e%2e", "....//", "..%2f")


def vfs_list(path: str) -> dict:
    """
    ⚠️ 仅供教学演示：虚拟文件读取，不触及真实文件系统。
    仅当路径字符串里出现穿越特征时"视为"穿越成功。
    """
    low = path.lower()
    if any(m in low for m in TRAVERSAL_MARKERS):
        # 归一化后仍限制在虚拟树内
        normalized = "/" + low.replace("..%2f", "../").replace("....//", "../")
        normalized = re.sub(r"/+", "/", normalized)
        parts = [p for p in normalized.split("/") if p not in ("", ".")]
        stack: list[str] = []
        for p in parts:
            if p == "..":
                if stack:
                    stack.pop()
            else:
                stack.append(p)
        resolved = "/" + "/".join(stack)
        if resolved in _VFS:
            return sim({"path": resolved, "content": _VFS[resolved], "traversal_detected": True})
        return sim({"path": resolved, "content": None, "traversal_detected": True,
                    "error": "虚拟文件系统中不存在该路径"})
    if path in _VFS:
        return sim({"path": path, "content": _VFS[path], "traversal_detected": False})
    return sim({"path": path, "content": None, "traversal_detected": False,
                "error": "虚拟文件系统中不存在该路径"})


# ==================================================================
# 2. 命令注入模拟
# ⚠️ 仅供教学演示：绝不调用 subprocess/os.system，只做模式识别 + 硬编码回显。
# ==================================================================

_SHELL_PATTERNS = [
    (re.compile(r"[;&|`$]|\|\||&&|\$\("), "命令分隔符"),
    (re.compile(r"\b(cat|ls|id|whoami|uname|curl|wget|nc|bash|sh)\b", re.I), "系统命令名"),
]

# 预置回显（完全硬编码）
_SHELL_ECHO = {
    "id": "uid=33(www-data) gid=33(www-data) groups=33(www-data)  [SIMULATED]",
    "whoami": "www-data  [SIMULATED]",
    "uname": "Linux helios-portal 5.15.0-sim #1 SMP x86_64 GNU/Linux  [SIMULATED]",
    "ls": "index.html  config.php  uploads  logs  [SIMULATED]",
    "cat": "⚠️ 模拟回显：真实文件内容已被沙箱拦截，此处返回占位文本。  [SIMULATED]",
    "default": "⚠️ 模拟回显：命令已被教学沙箱拦截，不产生任何真实执行。  [SIMULATED]",
}


def fake_shell(cmd: str) -> dict:
    """⚠️ 仅供教学演示：命令注入的受控模拟。不执行任何真实命令。"""
    hits = [name for pat, name in _SHELL_PATTERNS if pat.search(cmd)]
    if not hits:
        return sim({"input": cmd, "injected": False, "output": "未检测到注入特征"})
    low = cmd.lower()
    for key in ("id", "whoami", "uname", "ls", "cat"):
        if key in low:
            echo = _SHELL_ECHO[key]
            break
    else:
        echo = _SHELL_ECHO["default"]
    return sim({
        "input": cmd,
        "injected": True,
        "detected_by": hits,
        "output": echo,
        "note": "命令未被执行，以上为预置回显文本。",
    })


# ==================================================================
# 3. SQL 注入模拟
# ⚠️ 仅供教学演示：绝不拼接真实 SQL，绝不连接任何数据库。
# ==================================================================

_SQLI_PATTERNS = [
    re.compile(r"'\s*or\s+'?\d+'?\s*=\s*'?\d+", re.I),   # ' OR '1'='1
    re.compile(r"'\s*or\s+1\s*=\s*1", re.I),
    re.compile(r"\bor\s+1\s*=\s*1", re.I),
    re.compile(r"--\s*$"),
    re.compile(r"'\s*--"),
    re.compile(r"\bunion\s+select\b", re.I),
    re.compile(r"'\s*or\s*'", re.I),
]

# 预置的假结果集（完全虚构）
_FAKE_ROWS = [
    {"id": 1, "username": "m.chen", "role": "employee", "employee_id": "HX-2291",
     "email": "m.chen@helios-sim.invalid"},
    {"id": 2, "username": "r.okafor", "role": "employee", "employee_id": "HX-2317",
     "email": "r.okafor@helios-sim.invalid"},
    {"id": 3, "username": "portal_admin", "role": "admin", "employee_id": "HX-0001",
     "email": "admin@helios-sim.invalid"},
]


def fake_sqli(payload: str) -> dict:
    """⚠️ 仅供教学演示：SQL 注入的受控模拟。不访问任何真实数据库。"""
    matched = any(p.search(payload) for p in _SQLI_PATTERNS)
    if not matched:
        return sim({"payload": payload, "injected": False, "rows": [],
                    "authenticated": False})
    return sim({
        "payload": payload,
        "injected": True,
        "query_template": "SELECT * FROM users WHERE username = '<input>' AND password = '<input>'",
        "rows": _FAKE_ROWS,
        "authenticated": True,
        "note": "以上为预置的虚构结果集，未执行任何 SQL 语句。",
    })


# ==================================================================
# 4. SSRF 模拟
# ⚠️ 仅供教学演示：绝不发起出站请求。仅内置 mock 端点被允许。
# ==================================================================

_ALLOWED_SSRF = {
    "http://127.0.0.1:8899/api/v1/mock-internal/archive-index",
    "http://localhost:8899/api/v1/mock-internal/archive-index",
    "http://internal.helios-sim.invalid/archive",
    "http://169.254.169.254/latest/meta-data/",   # 云元数据地址（仅模拟响应）
}

_MOCK_INTERNAL = {
    "archive-index": {
        "service": "Helios Internal Archive",
        "records": [
            {"codename": "PROJECT_REAPER", "classification": "TOP-SECRET",
             "path": "/archive/reaper"},
            {"codename": "PROJECT_ORCHID", "classification": "CONFIDENTIAL",
             "path": "/archive/orchid"},
        ],
        "archive_key": "HL-ARCHIVE-KEY-7f3a91",
    },
    "meta-data": {
        "instance-id": "i-sim-0a1b2c3d",
        "iam": {"role": "helios-portal-role"},
        "note": "这是模拟的云元数据响应，不来自任何真实云环境。",
    },
}


def fake_ssrf(url: str) -> dict:
    """⚠️ 仅供教学演示：SSRF 的受控模拟。不产生任何网络连接。"""
    normalized = url.strip()
    if normalized in _ALLOWED_SSRF:
        if "meta-data" in normalized:
            body = _MOCK_INTERNAL["meta-data"]
        else:
            body = _MOCK_INTERNAL["archive-index"]
        return sim({"url": url, "fetched": True, "status": 200, "body": body,
                    "note": "目标为应用内置模拟端点，未发起真实网络请求。"})
    return sim({
        "url": url,
        "fetched": False,
        "status": 0,
        "error": "教学沙箱限制：仅允许访问内置的模拟内部端点，不代理任何外部连接。",
        "allowed_targets": sorted(_ALLOWED_SSRF),
    })


# ==================================================================
# 5. XXE 模拟
# ⚠️ 仅供教学演示：不使用任何真实 XML 解析库，不做实体展开。
# ==================================================================

_XXE_PATTERN = re.compile(r"<!ENTITY\s+(\w+)\s+SYSTEM\s+[\"']([^\"']+)[\"']", re.I)
_XXE_REF = re.compile(r"&(\w+);")

_ENTITY_FILES = {
    "file:///etc/passwd": (
        "root:x:0:0:root:/root:/bin/bash\n"
        "helios:x:1001:1001:Helios Service:/home/helios:/bin/bash"
    ),
    "/etc/passwd": "root:x:0:0:root:/root:/bin/bash",
    "file:///home/helios/notes.txt": "/home/helios/notes.txt 的内容（模拟）",
}


def fake_xxe(xml: str) -> dict:
    """⚠️ 仅供教学演示：XXE 的受控模拟。不使用真实 XML 解析器。"""
    entities = _XXE_PATTERN.findall(xml or "")
    if not entities:
        return sim({"entities": [], "expanded": False,
                    "message": "未检测到外部实体声明"})
    expanded = {}
    for name, target in entities:
        expanded[name] = _ENTITY_FILES.get(
            target.strip(),
            f"⚠️ 模拟：实体 {name} 的目标已被沙箱拦截（{target}）",
        )
    return sim({
        "entities": [{"name": n, "system": t} for n, t in entities],
        "expanded": True,
        "entity_values": expanded,
        "note": "以上为预置文本，未读取任何真实文件。",
    })


# ==================================================================
# 6. 反序列化（不安全）模拟
# ⚠️ 仅供教学演示：绝不调用 pickle/marshal/yaml.load。
# ==================================================================

_DESERIALIZE_MARKERS = [
    re.compile(r"\bcos\s*\n", re.I),          # python pickle 特征
    re.compile(r"__reduce__", re.I),
    re.compile(r"!!python/object", re.I),     # yaml 特征
    re.compile(r"O:\d+:\"", re.I),            # php 序列化特征
    re.compile(r"rO0AB", re.I),               # java 序列化 base64 头
]


def fake_deserialize(blob: str) -> dict:
    """⚠️ 仅供教学演示：反序列化漏洞的受控模拟。绝不真正反序列化。"""
    markers = [p.pattern for p in _DESERIALIZE_MARKERS if p.search(blob or "")]
    if not markers:
        return sim({"deserialized": False, "markers": [],
                    "message": "未检测到已知反序列化特征"})
    return sim({
        "deserialized": True,
        "markers": markers,
        "simulated_object": {
            "class": "SimulatedGadget",
            "chain": "教学演示链（无任何真实效果）",
            "result": "如果这是真实环境，此处可能导致任意代码执行。",
        },
        "note": "沙箱未执行任何反序列化操作，这里是预置说明文本。",
    })


# ==================================================================
# 7. 文件上传模拟
# ⚠️ 仅供教学演示：不落盘、不解析、不执行。仅检查扩展名并记录内存态。
# ==================================================================

_DANGEROUS_EXT = {".php", ".phtml", ".php5", ".jsp", ".asp", ".aspx", ".sh", ".exe"}
_uploaded_names: list[str] = []


def fake_upload(filename: str, size: int = 0) -> dict:
    """⚠️ 仅供教学演示：文件上传的受控模拟。文件不会写入磁盘。"""
    name = (filename or "").strip()
    ext = "." + name.rsplit(".", 1)[-1].lower() if "." in name else ""
    dangerous = ext in _DANGEROUS_EXT
    if name:
        _uploaded_names.append(name)
        del _uploaded_names[:-50]
    return sim({
        "filename": name,
        "extension": ext,
        "size": size,
        "bypassed": dangerous,
        "stored": False,
        "note": "教学沙箱不写入磁盘、不解析、不执行上传内容。",
    })


# ==================================================================
# 8. 弱随机数 / 哈希 / 编码工具
# ==================================================================

import hashlib  # noqa: E402
import base64  # noqa: E402
import random as _random  # noqa: E402

# ⚠️ 仅供教学演示：固定种子的弱随机数，用于演示"可预测随机数"的危害。
_weak_rng = _random.Random(1337)


def weak_random_token() -> str:
    """⚠️ 仅供教学演示：故意可预测的 token 生成（演示弱随机数风险）。"""
    return "".join(_weak_rng.choice("0123456789abcdef") for _ in range(16))


def md5_hex(s: str) -> str:
    return hashlib.md5(s.encode()).hexdigest()  # noqa: S324 - 教学演示弱哈希


def b64_decode(s: str) -> str:
    try:
        pad = "=" * (-len(s) % 4)
        return base64.b64decode(s + pad).decode("utf-8", "replace")
    except Exception:
        return ""


def b64_encode(s: str) -> str:
    return base64.b64encode(s.encode()).decode()
