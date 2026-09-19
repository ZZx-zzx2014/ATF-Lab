"""
ATF Lab - 教学模拟路由

⚠️⚠️ 仅供教学演示（CONTROLLED SIMULATION）⚠️⚠️

本模块暴露两类端点：
  1. /api/v1/sim/level/{id}/...  —— 前 36 关的受控模拟交互
  2. /api/v1/finale/...          —— 压轴关 L37 的六阶段攻击链

所有端点都是**纯模拟**：不执行命令、不读写真实文件、不发外部请求。
每个响应都带 _simulation 标记，提醒使用者这不是真实漏洞。
"""

from fastapi import APIRouter, Depends, Query, Request
from pydantic import BaseModel

from ..challenges import registry
from ..challenges import sandbox as sb
from ..challenges import finale
from ..database import audit
from ..deps import current_user_optional, current_user
from ..responses import Code, ApiError, ok

router = APIRouter(tags=["教学模拟"])


# ==================================================================
# 通用关卡模拟入口
# ==================================================================

def _run(level_id: str, ctx: dict):
    """执行某关卡注册的模拟处理器。"""
    lv = registry.get(level_id)
    if lv is None:
        raise ApiError(Code.NOT_FOUND, "关卡不存在")
    if lv.handler is None:
        raise ApiError(Code.BAD_PARAM, "该关卡没有交互式模拟接口")
    result = lv.handler(ctx)
    return ok(result)


@router.get("/api/v1/sim/level/{level_id}/page", summary="获取关卡的模拟页面")
def sim_page(level_id: str):
    return _run(level_id, {})


@router.get("/api/v1/sim/level/{level_id}/file", summary="路径穿越模拟")
def sim_file(level_id: str, name: str = Query(default="")):
    return _run(level_id, {"name": name})


@router.get("/api/v1/sim/level/{level_id}/search", summary="XSS 反射模拟")
def sim_search(level_id: str, q: str = Query(default="")):
    return _run(level_id, {"q": q})


@router.get("/api/v1/sim/level/{level_id}/profile", summary="越权访问模拟")
def sim_profile(level_id: str, user_id: str = Query(default="2")):
    return _run(level_id, {"user_id": user_id})


class LoginBody(BaseModel):
    username: str = ""
    password: str = ""


@router.post("/api/v1/sim/level/{level_id}/login", summary="登录/注入模拟")
def sim_login(level_id: str, body: LoginBody):
    return _run(level_id, {"username": body.username, "password": body.password})


class PingBody(BaseModel):
    ip: str = ""


@router.post("/api/v1/sim/level/{level_id}/ping", summary="命令注入模拟")
def sim_ping(level_id: str, body: PingBody):
    return _run(level_id, {"ip": body.ip})


class UrlBody(BaseModel):
    url: str = ""


@router.post("/api/v1/sim/level/{level_id}/fetch", summary="SSRF 模拟")
def sim_fetch(level_id: str, body: UrlBody):
    return _run(level_id, {"url": body.url})


class UploadBody(BaseModel):
    filename: str = ""
    size: int = 0


@router.post("/api/v1/sim/level/{level_id}/upload", summary="文件上传模拟")
def sim_upload(level_id: str, body: UploadBody):
    return _run(level_id, {"filename": body.filename, "size": body.size})


class DeserializeBody(BaseModel):
    payload: str = ""


@router.post("/api/v1/sim/level/{level_id}/deserialize", summary="反序列化模拟")
def sim_deserialize(level_id: str, body: DeserializeBody):
    return _run(level_id, {"payload": body.payload})


class XmlBody(BaseModel):
    xml: str = ""


@router.post("/api/v1/sim/level/{level_id}/parse", summary="XXE 模拟")
def sim_parse(level_id: str, body: XmlBody):
    return _run(level_id, {"xml": body.xml})


class TransferBody(BaseModel):
    to: str = ""
    amount: float = 0


@router.post("/api/v1/sim/level/{level_id}/transfer", summary="CSRF 模拟")
def sim_transfer(level_id: str, body: TransferBody):
    return _run(level_id, {"to": body.to, "amount": body.amount})


# ==================================================================
# 压轴关 L37「REAPER 行动」
# ⚠️ 仅供教学演示：整条攻击链为受控模拟
# ==================================================================

@router.get("/api/v1/finale/briefing", summary="L37 任务简报")
def finale_briefing():
    return ok({
        "codename": "REAPER",
        "role": "白帽渗透测试员",
        "target": "Helios 生物科技 员工门户",
        "mission": (
            "内部档案 PROJECT_REAPER 缺少 41 份知情同意书，销毁期限在本周。"
            "你需要逐层穿透门户的六道防线，拿到管理员权限，销毁这份档案。"
        ),
        "stages": [{"stage": n, "title": t} for n, t in sorted(finale.STAGES.items())],
        "disclaimer": (
            "本关卡为教学模拟。所有漏洞均为后端刻意实现的教学逻辑，"
            "不存在真实缺陷；所有操作都在沙箱内完成，不触及真实系统。"
        ),
    })


@router.get("/api/v1/finale/progress", summary="L37 我的阶段进度")
def finale_progress(user=Depends(current_user_optional)):
    if user is None:
        return ok({
            "stages": [{"stage": n, "title": t, "reached": False, "reached_at": None}
                       for n, t in sorted(finale.STAGES.items())],
            "completed_stages": 0,
            "total_stages": len(finale.STAGES),
            "destroyed": finale._is_destroyed(),
            "logged_in": False,
        })
    data = finale.get_progress(user["id"])
    data["logged_in"] = True
    return ok(data)


@router.get("/api/v1/finale/legacy/employees", summary="阶段1：泄露的员工名录")
def finale_stage1(user=Depends(current_user_optional)):
    if user:
        finale.record_stage(user["id"], 1, "读取旧接口员工名录")
    return ok(finale.stage1_directory())


class FinaleLoginBody(BaseModel):
    username: str = ""
    password: str = ""


@router.post("/api/v1/finale/login", summary="阶段2：门户登录（存在注入）")
def finale_stage2(body: FinaleLoginBody, user=Depends(current_user_optional)):
    data = finale.stage2_login(body.username, body.password)
    data["employee_jwt"] = finale.issue_employee_jwt()
    data["jwt_hint"] = "拿去解码看看 payload，注意签名用的密钥很弱。"
    if user:
        finale.record_stage(user["id"], 2, "SQL 注入绕过登录")
    return ok(data)


@router.get("/api/v1/finale/admin", summary="阶段3：管理员面板（需 admin JWT）")
def finale_stage3(request: Request, token: str = Query(default=""),
                  user=Depends(current_user_optional)):
    """token 可通过 query 传入，或放在 Authorization: Bearer 里。"""
    raw = token
    if not raw:
        auth = request.headers.get("authorization", "")
        if auth.lower().startswith("bearer "):
            raw = auth[7:]
    data = finale.stage3_admin_check(raw)
    if user:
        finale.record_stage(user["id"], 3, "JWT 弱密钥提权")
    return ok(data)


class HealthCheckBody(BaseModel):
    url: str = ""


@router.post("/api/v1/finale/health-check", summary="阶段4：服务健康检查（SSRF）")
def finale_stage4(body: HealthCheckBody, user=Depends(current_user_optional)):
    data = finale.stage4_ssrf(body.url)
    if user:
        finale.record_stage(user["id"], 4, "SSRF 读取内部档案索引")
    return ok(data)


class ArchiveSearchBody(BaseModel):
    xml: str = ""
    archive_key: str = ""


@router.post("/api/v1/finale/archive/search", summary="阶段5：档案检索（XXE）")
def finale_stage5(body: ArchiveSearchBody, user=Depends(current_user_optional)):
    data = finale.stage5_xxe(body.xml, body.archive_key)
    if user:
        finale.record_stage(user["id"], 5, "XXE 获取销毁令牌")
    return ok(data)


@router.get("/api/v1/finale/archive/destroy/preview", summary="阶段6：销毁前预览")
def finale_preview():
    return ok(finale.stage6_preview())


class DestroyBody(BaseModel):
    destruction_token: str = ""
    confirm: str = ""


@router.post("/api/v1/finale/archive/destroy", summary="阶段6：销毁 REAPER 档案")
def finale_destroy(body: DestroyBody, user=Depends(current_user)):
    data = finale.stage6_destroy(user["id"], body.destruction_token, body.confirm)
    finale.record_stage(user["id"], 6, "销毁 PROJECT_REAPER 模拟档案")
    audit(user["id"], "finale_destroy", "simulated")
    return ok(data, message="REAPER 档案已在教学模拟数据中被标记销毁")


@router.get("/api/v1/finale/mock/archive", summary="内置模拟内部端点（SSRF 目标）")
def finale_mock_archive():
    """⚠️ 仅供教学演示：这是 SSRF 阶段的内置目标，返回静态内容。"""
    return ok({
        "service": "Helios Internal Archive (simulated endpoint)",
        "note": "这是应用内置的模拟端点，不代理任何外部服务。",
        "body": finale._MOCK_ARCHIVE_INDEX,
    })
