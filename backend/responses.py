"""
ATF Lab - 统一响应格式与错误码

⚠️ 仅供教学演示（EDUCATIONAL USE ONLY）

所有 /api/v1/* 接口统一返回：
    { "code": 0, "message": "ok", "data": {...} }
前端只需判断 code 是否为 0。
"""

from typing import Any

from fastapi.responses import JSONResponse


class Code:
    OK = 0
    BAD_PARAM = 1001          # 参数校验失败
    UNAUTHORIZED = 1002       # 未登录 / token 无效
    FORBIDDEN = 1003          # 无权限
    NOT_FOUND = 1004          # 资源不存在
    CONFLICT = 1005           # 冲突（用户名已占用等）
    RATE_LIMITED = 1006       # 请求过于频繁
    WRONG_FLAG = 1007         # flag 错误（业务失败，非 HTTP 错误）
    LOCKED = 1008             # 关卡未解锁
    INTERNAL = 5000


_CODE_HTTP = {
    Code.OK: 200,
    Code.BAD_PARAM: 400,
    Code.UNAUTHORIZED: 401,
    Code.FORBIDDEN: 403,
    Code.NOT_FOUND: 404,
    Code.CONFLICT: 409,
    Code.RATE_LIMITED: 429,
    Code.WRONG_FLAG: 200,
    Code.LOCKED: 403,
    Code.INTERNAL: 500,
}


def ok(data: Any = None, message: str = "ok") -> dict:
    return {"code": Code.OK, "message": message, "data": data}


def fail(code: int, message: str, data: Any = None) -> JSONResponse:
    return JSONResponse(
        status_code=_CODE_HTTP.get(code, 400),
        content={"code": code, "message": message, "data": data},
    )


class ApiError(Exception):
    """业务异常，由全局处理器转成统一格式。"""

    def __init__(self, code: int, message: str, data: Any = None):
        self.code = code
        self.message = message
        self.data = data
        super().__init__(message)
