"""
ATF Lab - 关卡注册表装载入口

⚠️ 仅供教学演示（EDUCATIONAL USE ONLY）
"""

from .base import registry, Level, flag_digest, check_flag
from . import web, crypto, forensics, network, misc, finale_level

_loaded = False


def load_all() -> None:
    """装载全部关卡（幂等）。"""
    global _loaded
    if _loaded:
        return
    web.register()
    crypto.register()
    forensics.register()
    network.register()
    misc.register()
    finale_level.register()      # L37 压轴关
    _loaded = True


__all__ = ["registry", "Level", "flag_digest", "check_flag", "load_all"]
