"""
ATF Lab - 压轴关 L37「REAPER 行动」关卡定义

⚠️ 仅供教学演示（EDUCATIONAL USE ONLY）
攻击链实现见 finale.py，本文件只负责关卡元数据与注册。
"""

from .base import Level, registry

CAT = "压轴行动"


def register() -> None:
    registry.add(Level(
        id="L37",
        name="REAPER 行动",
        category=CAT,
        difficulty=5,
        points=500,
        special="finale",
        objective=(
            "你是一名白帽。Helios 生物科技的内部档案 PROJECT_REAPER 缺少 41 份知情同意书，"
            "销毁期限就在本周。逐层穿透门户的六道防线，拿到管理员权限，销毁这份档案。"
        ),
        hints=[
            "阶段 1：门户改版后有个旧接口忘了下线，试着访问 /api/v1/finale/legacy/employees，"
            "它会返回完整员工名录。",
            "阶段 2：员工登录框存在 SQL 注入。用 OR 恒真条件绕过，"
            "POST /api/v1/finale/login。",
            "阶段 3：登录后你会拿到一个 JWT。它的签发密钥极弱（就是 secret 这个词），"
            "把 payload 里的 role 改成 admin 重新签名，再用它访问 /api/v1/finale/admin。",
            "阶段 4：管理员面板的『服务健康检查』存在 SSRF。"
            "目标是 http://internal.helios-sim.invalid/archive，"
            "POST /api/v1/finale/health-check。",
            "阶段 5：档案检索接口接受 XML 且允许外部实体。构造 DOCTYPE 加 ENTITY SYSTEM "
            "读取 file:///etc/helios/archive.conf，POST /api/v1/finale/archive/search，"
            "记得带上阶段 4 拿到的 archive_key。",
            "阶段 6：用阶段 5 返回的 destruction_token 调用 "
            "POST /api/v1/finale/archive/destroy，确认短语是 CONFIRM DESTRUCTION。",
        ],
        free_hints=1,
        writeup="""## REAPER 行动 —— 完整攻击链复盘

这是一条模拟的六阶段渗透链，把前面 36 关学到的技术在真实场景中串联起来。

### 阶段 1 · 信息泄露
门户改版后 API 路由未收敛，旧接口 `/legacy/employees` 仍然可达，直接返回员工名录。
**真实世界对应**：资产清点缺失、API 版本管理混乱。防御靠 API 网关统一收敛与下线流程。

### 阶段 2 · SQL 注入绕过认证
登录接口拼接 SQL，`' OR '1'='1` 使 WHERE 恒真。
**防御**：参数化查询。这是唯一根治手段。

### 阶段 3 · JWT 弱密钥提权
token 用 `secret` 这种字典词签名，且服务端从 payload 取 `role` 判断权限。
攻击者只需重签一个 `role: admin` 的 token。
**防御**：高熵密钥；服务端固定算法；权限不放在客户端可篡改的字段里。

### 阶段 4 · SSRF 探测内网
健康检查功能接受任意 URL，可探测内部服务。
**防御**：URL 白名单；解析后校验目标 IP；出网走受限代理。

### 阶段 5 · XXE 读取档案
XML 解析器允许外部实体，`ENTITY ... SYSTEM "file:///..."` 读取了服务端文件。
**防御**：禁用 DTD 与外部实体。

### 阶段 6 · 数据销毁
拿到管理员权限与销毁令牌后，执行了档案销毁。

---

> ⚠️ **重要说明**：本关的攻击链是**受控模拟**。
> - 所有"漏洞"都是后端刻意实现的教学逻辑，不存在真实缺陷
> - 阶段 3 的弱密钥与平台真实 JWT 体系**完全隔离**，伪造的 token 无法提权平台
> - 阶段 6 的"销毁"只更新 `sim_archive_records` 这张模拟表的 status 字段
> - 全程不执行任何系统命令、不读写真实文件、不发起外部网络请求
>
> 本关的教学价值在于**理解攻击链的串联逻辑**，以及每一环对应的防御措施。""",
        tags=["综合渗透", "攻击链", "模拟行动"],
        flag="flag{reaper_archive_destroyed}",
    ))
