"""
ATF Lab - 压轴关 L37「REAPER 行动」

⚠️⚠️ 仅供教学演示（CONTROLLED SIMULATION — EDUCATIONAL USE ONLY）⚠️⚠️

本关是一条完整的 6 阶段模拟攻击链，剧情为"白帽清除危险数据"。
但请注意实现层面的**硬性安全边界**：

  阶段              剧情表现                  实际实现
  ----------------  ------------------------  ----------------------------------
  1 员工名录泄露    废弃接口返回员工表         内存中的静态字典
  2 SQL 注入绕过    拼接 SQL 导致认证绕过      模式匹配 + 预置会话 token
  3 JWT 伪造提权    弱密钥签出 admin token     独立弱密钥 + 独立 audience，
                                               只对本关模拟接口有效，
                                               与平台真实 JWT 体系完全隔离
  4 SSRF 探测内网   读取内部档案服务           白名单内置端点，零出站请求
  5 XXE 读取索引    外部实体展开文件           正则识别 + 预置文本，无真实 XML 解析
  6 销毁档案        删除 PROJECT_REAPER        UPDATE sim_archive_records
                                               表中 status 字段（虚构数据）

关键隔离设计：
  - FINALE_SECRET 与 settings.SECRET_KEY 不同，且 audience 不同
  - 伪造出的 token 无法通过平台 /api/v1/auth/me 的校验
  - "销毁"只改 simulation 表的 status，不删除任何行、不触碰真实数据
"""

import hashlib
import hmac
import re
import time
import warnings

import jwt

from ..database import query, query_one, execute, tx
from ..responses import Code, ApiError

# ⚠️ 仅供教学演示：本关刻意使用弱密钥，PyJWT 会发出 InsecureKeyLengthWarning。
# 这正是我们要演示的漏洞本身，因此在该模块内静音，避免污染日志。
warnings.filterwarnings("ignore", message=".*InsecureKeyLength.*")

# ==================================================================
# ⚠️ 仅供教学演示：本关专用的弱密钥。
# 刻意与 settings.SECRET_KEY 分离 —— 这是安全边界的关键。
# 即使玩家伪造出本关的 admin token，也无法用于平台任何真实权限。
# ==================================================================
FINALE_SECRET = "helios-dev-secret"
FINALE_AUDIENCE = "helios-portal-sim"
FINALE_ISSUER = "helios-portal"

STAGES = {
    1: "员工名录泄露",
    2: "SQL 注入绕过登录",
    3: "JWT 弱密钥提权",
    4: "SSRF 探测内网",
    5: "XXE 读取档案索引",
    6: "销毁 REAPER 档案",
}

# ==================================================================
# 阶段 1：废弃接口泄露员工名录（静态字典）
# ⚠️ 仅供教学演示：数据为内存中的虚构常量
# ==================================================================

_EMPLOYEE_DIRECTORY = [
    {"id": 1, "username": "m.chen", "employee_id": "HX-2291",
     "email": "m.chen@helios-sim.invalid", "role": "employee", "department": "R&D"},
    {"id": 2, "username": "r.okafor", "employee_id": "HX-2317",
     "email": "r.okafor@helios-sim.invalid", "role": "employee", "department": "QA"},
    {"id": 3, "username": "portal_admin", "employee_id": "HX-0001",
     "email": "admin@helios-sim.invalid", "role": "admin", "department": "IT"},
]


def stage1_directory() -> dict:
    """阶段 1：返回虚构员工名录。"""
    return {
        "stage": 1,
        "title": STAGES[1],
        "endpoint": "/api/v1/finale/legacy/employees",
        "note": "这是门户改版后忘记下线的旧接口，返回了完整员工名录。",
        "employees": _EMPLOYEE_DIRECTORY,
        "leads_to": "拿到 m.chen 的工号 HX-2291，用它作为登录用户名进入阶段 2。",
    }


# ==================================================================
# 阶段 2：SQL 注入绕过登录
# ⚠️ 仅供教学演示：不拼接真实 SQL、不连接数据库。
# ==================================================================

_SQLI_PATTERNS = [
    re.compile(r"'\s*or\s+'?\d+'?\s*=\s*'?\d+", re.I),
    re.compile(r"'\s*or\s+1\s*=\s*1", re.I),
    re.compile(r"\bor\s+1\s*=\s*1", re.I),
    re.compile(r"'\s*--"),
    re.compile(r"--\s*$"),
    re.compile(r"\bunion\s+select\b", re.I),
    re.compile(r"'\s*or\s*'", re.I),
]

_SESSION_TOKEN = "hl-sess-8f2a41c9d7e3"


def stage2_login(username: str, password: str) -> dict:
    """阶段 2：模拟登录。注入 payload 命中则发会话 token。"""
    injected = any(p.search(username or "") or p.search(password or "")
                   for p in _SQLI_PATTERNS)
    if not injected:
        raise ApiError(Code.UNAUTHORIZED, "用户名或密码错误（提示：这个接口存在注入）")

    return {
        "stage": 2,
        "title": STAGES[2],
        "injected": True,
        "query_template": ("SELECT id, username, role FROM portal_users "
                           "WHERE username = '<input>' AND password = '<input>'"),
        "session_token": _SESSION_TOKEN,
        "role": "employee",
        "note": "注入使 WHERE 条件恒真，返回了第一条记录并签发员工会话。",
        "leads_to": "员工会话可访问门户，但管理员面板在 /api/v1/finale/admin，需要 admin 身份。",
    }


# ==================================================================
# 阶段 3：JWT 弱密钥伪造
# ⚠️ 仅供教学演示：使用独立弱密钥 + 独立 audience。
#    该 token 只对本关模拟接口有效，无法提权平台。
# ==================================================================

def issue_employee_jwt() -> str:
    """签发给玩家的员工 token（弱密钥，可被爆破/伪造）。"""
    now = int(time.time())
    return jwt.encode(
        {
            "sub": "2",
            "username": "m.chen",
            "role": "employee",
            "iat": now,
            "exp": now + 3600,
            "aud": FINALE_AUDIENCE,
            "iss": FINALE_ISSUER,
        },
        FINALE_SECRET,
        algorithm="HS256",
    )


def verify_finale_jwt(token: str):
    """
    ⚠️ 仅供教学演示：校验本关模拟 token。
    注意 audience / issuer 都限定在本关，平台 token 不会通过，
    本关 token 也不会通过平台校验 —— 双向隔离。
    """
    try:
        return jwt.decode(
            token,
            FINALE_SECRET,
            algorithms=["HS256"],
            audience=FINALE_AUDIENCE,
            issuer=FINALE_ISSUER,
        )
    except Exception:
        return None


def stage3_admin_check(token: str) -> dict:
    """阶段 3：用伪造的 JWT 访问管理员面板。"""
    payload = verify_finale_jwt(token)
    if payload is None:
        raise ApiError(Code.UNAUTHORIZED,
                       "token 无效（提示：密钥很弱，而且服务端只认 HS256）")
    if payload.get("role") != "admin":
        raise ApiError(Code.FORBIDDEN,
                       "当前身份是 %s，需要 admin（提示：payload 里的 role 可以改）"
                       % payload.get("role"))

    return {
        "stage": 3,
        "title": STAGES[3],
        "admin_granted": True,
        "panel": "Helios 内部档案管理面板",
        "features": ["服务健康检查", "档案检索", "档案销毁"],
        "leads_to": "健康检查功能存在 SSRF，可用它探测内部档案服务。",
    }


# ==================================================================
# 阶段 4：SSRF 探测内部服务
# ⚠️ 仅供教学演示：零出站请求，只允许内置 mock 端点。
# ==================================================================

_ALLOWED_TARGETS = {
    "http://internal.helios-sim.invalid/archive": "archive-index",
    "http://127.0.0.1:8899/api/v1/finale/mock/archive": "archive-index",
}

_MOCK_ARCHIVE_INDEX = {
    "service": "Helios Internal Archive",
    "version": "3.4.1-sim",
    "records": [
        {"codename": "PROJECT_REAPER", "classification": "TOP-SECRET",
         "path": "/archive/reaper", "consent_forms": "41/47 缺失"},
        {"codename": "PROJECT_ORCHID", "classification": "CONFIDENTIAL",
         "path": "/archive/orchid", "consent_forms": "完整"},
        {"codename": "PROJECT_ATLAS", "classification": "INTERNAL",
         "path": "/archive/atlas", "consent_forms": "完整"},
    ],
    "archive_key": "HL-ARCHIVE-KEY-7f3a91",
}


def stage4_ssrf(url: str) -> dict:
    """阶段 4：模拟 SSRF。"""
    target = (url or "").strip()
    if target not in _ALLOWED_TARGETS:
        raise ApiError(
            Code.BAD_PARAM,
            "教学沙箱限制：仅允许访问内置模拟端点，不代理任何外部连接",
            data={"allowed_targets": sorted(_ALLOWED_TARGETS)},
        )
    return {
        "stage": 4,
        "title": STAGES[4],
        "url": target,
        "fetched": True,
        "status": 200,
        "body": _MOCK_ARCHIVE_INDEX,
        "note": "目标为应用内置模拟端点，未发起真实网络请求。",
        "leads_to": "拿到 archive_key，可调用档案检索接口（阶段 5）。",
    }


# ==================================================================
# 阶段 5：XXE 读取档案索引
# ⚠️ 仅供教学演示：不使用真实 XML 解析器，正则识别 + 预置文本。
# ==================================================================

_XXE_ENTITY = re.compile(r"<!ENTITY\s+(\w+)\s+SYSTEM\s+[\"']([^\"']+)[\"']", re.I)

_ENTITY_TARGETS = {
    "file:///etc/helios/archive.conf": (
        "archive_root=/srv/archive\n"
        "reaper_index=/archive/reaper/manifest.xml\n"
    ),
    "/srv/archive/reaper/manifest.xml": (
        "<manifest project=\"PROJECT_REAPER\" records=\"47\" consent=\"6\"/>"
    ),
}


def stage5_xxe(xml: str, archive_key: str) -> dict:
    """阶段 5：模拟 XXE 读取档案清单。"""
    if archive_key != _MOCK_ARCHIVE_INDEX["archive_key"]:
        raise ApiError(Code.FORBIDDEN, "archive_key 无效（先完成阶段 4 拿到它）")

    entities = _XXE_ENTITY.findall(xml or "")
    if not entities:
        raise ApiError(Code.BAD_PARAM,
                       "未检测到外部实体声明（提示：需要 DOCTYPE 加 ENTITY SYSTEM）")

    expanded = {}
    for name, target in entities:
        expanded[name] = _ENTITY_TARGETS.get(
            target.strip(),
            "⚠️ 模拟：实体 %s 的目标已被教学沙箱拦截（%s）" % (name, target),
        )

    return {
        "stage": 5,
        "title": STAGES[5],
        "entities": [{"name": n, "system": t} for n, t in entities],
        "entity_values": expanded,
        "manifest": {
            "project": "PROJECT_REAPER",
            "codename": "REAPER",
            "records_total": 47,
            "consent_missing": 41,
            "classification": "TOP-SECRET",
        },
        "destruction_token": _destruction_token(),
        "note": "以上为预置文本，未读取任何真实文件。",
        "leads_to": "档案确认存在，material 齐全。用 destruction_token 执行销毁。",
    }


def _destruction_token() -> str:
    """销毁令牌 —— 绑定到当前日期，避免长期有效。"""
    day = time.strftime("%Y%m%d")
    raw = "REAPER::%s::%s" % (day, FINALE_SECRET)
    return "DESTROY-" + hashlib.sha256(raw.encode()).hexdigest()[:16]


# ==================================================================
# 阶段 6：销毁档案（压轴高潮）
# ⚠️⚠️ 仅供教学演示：只 UPDATE sim_archive_records 的 status 字段。
#     不删除任何行、不触碰真实数据、不影响平台其他任何部分。
# ==================================================================

CONFIRM_PHRASE = "CONFIRM DESTRUCTION"


def stage6_preview() -> dict:
    """销毁前预览：展示将被标记的记录。"""
    rows = query(
        "SELECT id, project, codename, classification, status "
        "FROM sim_archive_records WHERE project = 'HELIOS' ORDER BY id"
    )
    return {
        "stage": 6,
        "title": STAGES[6],
        "warning": (
            "此操作将把 PROJECT_REAPER 档案标记为已销毁。"
            "本次操作作用于教学模拟数据表 sim_archive_records。"
        ),
        "confirm_phrase": CONFIRM_PHRASE,
        "records": [dict(r) for r in rows],
    }


def stage6_destroy(user_id: int, destruction_token: str, confirm: str) -> dict:
    """阶段 6：执行销毁（写入模拟表）。"""
    if confirm != CONFIRM_PHRASE:
        raise ApiError(Code.BAD_PARAM,
                       "确认短语不正确，需要输入：%s" % CONFIRM_PHRASE)
    if destruction_token != _destruction_token():
        raise ApiError(Code.FORBIDDEN,
                       "destruction_token 无效或已过期（每日轮换，先完成阶段 5）")

    row = query_one(
        "SELECT id, status FROM sim_archive_records WHERE codename = 'PROJECT_REAPER'"
    )
    if row is None:
        raise ApiError(Code.NOT_FOUND, "模拟档案记录不存在")

    already = row["status"] == "DESTROYED"
    if not already:
        # ⚠️ 仅供教学演示：这是本关唯一的"写操作"，作用于模拟表。
        execute(
            "UPDATE sim_archive_records SET status = 'DESTROYED', destroyed_at = ? "
            "WHERE codename = 'PROJECT_REAPER'",
            (time.time(),),
        )

    return {
        "stage": 6,
        "title": STAGES[6],
        "destroyed": True,
        "already_destroyed": already,
        "target": "PROJECT_REAPER",
        "simulated": True,
        "note": (
            "PROJECT_REAPER 已在教学模拟数据表中被标记为 DESTROYED。"
            "此操作仅影响 sim_archive_records 表，未删除任何真实数据。"
        ),
    }


def restore_sim_archive() -> None:
    """重置模拟档案状态（供管理后台或自测使用）。"""
    execute(
        "UPDATE sim_archive_records SET status = 'ACTIVE', destroyed_at = NULL "
        "WHERE codename = 'PROJECT_REAPER'"
    )


# ==================================================================
# 阶段进度记录
# ==================================================================

def record_stage(user_id: int, stage: int, detail: str = "") -> None:
    """记录玩家到达的阶段（幂等）。"""
    existing = query_one(
        "SELECT id FROM sim_reaper_progress WHERE user_id = ? AND stage = ?",
        (user_id, stage),
    )
    if existing:
        return
    execute(
        "INSERT INTO sim_reaper_progress (user_id, stage, detail, reached_at) "
        "VALUES (?, ?, ?, ?)",
        (user_id, stage, detail, time.time()),
    )


def get_progress(user_id: int) -> dict:
    """返回该玩家的阶段进度。"""
    rows = query(
        "SELECT stage, reached_at FROM sim_reaper_progress "
        "WHERE user_id = ? ORDER BY stage",
        (user_id,),
    )
    reached = {r["stage"]: r["reached_at"] for r in rows}
    return {
        "stages": [
            {
                "stage": n,
                "title": STAGES[n],
                "reached": n in reached,
                "reached_at": reached.get(n),
            }
            for n in sorted(STAGES)
        ],
        "completed_stages": len(reached),
        "total_stages": len(STAGES),
        "destroyed": _is_destroyed(),
    }


def _is_destroyed() -> bool:
    row = query_one(
        "SELECT status FROM sim_archive_records WHERE codename = 'PROJECT_REAPER'"
    )
    return bool(row and row["status"] == "DESTROYED")
