"""
ATF Lab - FastAPI 应用入口

⚠️ 仅供教学演示（EDUCATIONAL USE ONLY）
本项目是受控的安全教学靶场。所有"漏洞"均为模拟实现，
不具备任何危害真实系统的能力。详见 README.md 顶部免责声明。

统一响应格式：{ "code": 0, "message": "ok", "data": {...} }
交互式 API 文档：/docs
"""

import logging
import time

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from pathlib import Path

from .challenges import load_all
from .config import settings
from .database import init_db
from .responses import Code, ApiError
from .routers import admin, auth, levels, sim, users

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
)
log = logging.getLogger("atf")

app = FastAPI(
    title="ATF Lab API",
    version=settings.APP_VERSION,
    description=(
        "⚠️ **仅供教学演示的安全靶场 API**\n\n"
        "本项目为受控模拟环境，所有漏洞均为教学构造，"
        "不具备危害真实系统的能力。请勿在互联网上公开发布或部署。\n\n"
        "统一响应格式：`{ code, message, data }`，`code == 0` 表示成功。"
    ),
    docs_url="/api/docs",
    redoc_url="/api/redoc",
    openapi_url="/api/openapi.json",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[o.strip() for o in settings.CORS_ORIGINS.split(",")] or ["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ================================================================
# 全局异常处理 —— 一律转换为统一响应格式
# ================================================================

@app.exception_handler(ApiError)
async def _api_error_handler(request: Request, exc: ApiError):
    from .responses import _CODE_HTTP
    return JSONResponse(
        status_code=_CODE_HTTP.get(exc.code, 400),
        content={"code": exc.code, "message": exc.message, "data": exc.data},
    )


@app.exception_handler(RequestValidationError)
async def _validation_handler(request: Request, exc: RequestValidationError):
    return JSONResponse(
        status_code=400,
        content={
            "code": Code.BAD_PARAM,
            "message": "参数校验失败",
            "data": {"errors": exc.errors()},
        },
    )


@app.exception_handler(Exception)
async def _unhandled_handler(request: Request, exc: Exception):
    log.exception("unhandled error on %s", request.url.path)
    return JSONResponse(
        status_code=500,
        content={"code": Code.INTERNAL, "message": "服务器内部错误", "data": None},
    )


# ================================================================
# 路由注册
# ================================================================

app.include_router(auth.router)
app.include_router(levels.router)
app.include_router(users.router)
app.include_router(admin.router)
app.include_router(sim.router)


@app.on_event("startup")
def _startup() -> None:
    init_db()
    load_all()
    admin.load_overrides()
    from .challenges import registry as _reg
    log.info("ATF Lab 启动完成：%d 个关卡已装载", len(_reg.all()))

    # ⚠️ 仅供教学演示：启动仿真网络服务（只回静态文本、仅监听回环、零出站）
    if settings.NETLAB_ENABLED:
        try:
            from netlab.services import start_all
            for s in start_all():
                if s["running"]:
                    log.info("netlab 仿真服务 %s 已监听 127.0.0.1:%s",
                             s["name"], s["port"])
                else:
                    log.warning("netlab 仿真服务 %s 未能启动: %s",
                                s["name"], s.get("error"))
        except Exception as e:  # 端口占用等不应影响主服务
            log.warning("netlab 启动失败（不影响主服务）: %s", e)

    log.info("⚠️  本项目仅供教学演示，禁止公网部署")


@app.on_event("shutdown")
def _shutdown() -> None:
    if settings.NETLAB_ENABLED:
        try:
            from netlab.services import stop_all
            stop_all()
        except Exception:
            pass


@app.get("/api/v1/health", tags=["系统"], summary="健康检查")
def health():
    from .challenges import registry
    from .database import query_one
    users = query_one("SELECT COUNT(*) AS c FROM users")
    netlab = []
    if settings.NETLAB_ENABLED:
        try:
            from netlab.services import status_all
            netlab = status_all()
        except Exception:
            netlab = []
    return {
        "code": Code.OK,
        "message": "ok",
        "data": {
            "status": "healthy",
            "app": settings.APP_NAME,
            "version": settings.APP_VERSION,
            "levels": len(registry.all()),
            "users": users["c"] if users else 0,
            "netlab": netlab,
            "server_time": time.time(),
            "disclaimer": (
                "本项目是一个 API 调动的学习与演示项目，仅供本人自行娱乐与安全学习使用。"
                "请勿在互联网上公开发布、部署或传播。"
            ),
        },
    }


# ================================================================
# 前端静态资源托管（同域部署模式）
# 若 frontend/dist 存在，则托管 SPA；否则仅提供 API。
#
# 注意：SPA 使用 BrowserRouter，像 /levels、/finale 这类前端路由
# 在刷新时也会打到后端。因此需要把「非 /api 且非静态文件」的请求
# 统一回退到 index.html，否则刷新深链接会 404。
# ================================================================

_dist = Path(settings.FRONTEND_DIST)
_INDEX = _dist / "index.html"

if _dist.is_dir() and _INDEX.is_file():

    # 静态资源（JS/CSS/图片等）直接由 StaticFiles 处理
    app.mount("/assets", StaticFiles(directory=str(_dist / "assets")), name="assets")

    @app.get("/{full_path:path}", include_in_schema=False)
    def spa_fallback(full_path: str):
        """SPA 路由回退：把前端路由交给 index.html 处理。"""
        # API 路径不应落到这里（已由上面的路由匹配）；双保险再挡一次
        if full_path.startswith("api/"):
            return JSONResponse(
                status_code=404,
                content={"code": Code.NOT_FOUND, "message": "接口不存在", "data": None},
            )
        # 真实存在的静态文件优先返回（如 favicon.ico、robots.txt）
        candidate = (_dist / full_path).resolve()
        try:
            candidate.relative_to(_dist.resolve())
        except ValueError:
            # 目录穿越企图，直接回退到 index
            return FileResponse(str(_INDEX))
        if full_path and candidate.is_file():
            return FileResponse(str(candidate))
        return FileResponse(str(_INDEX))

    log.info("已挂载前端 SPA: %s", _dist)
else:
    @app.get("/", tags=["系统"], summary="根路径（未构建前端时的提示）")
    def root():
        return {
            "code": Code.OK,
            "message": "ok",
            "data": {
                "hint": "前端尚未构建。请运行 npm run build，或直接访问 /api/docs 查看 API。",
                "docs": "/api/docs",
                "health": "/api/v1/health",
            },
        }
