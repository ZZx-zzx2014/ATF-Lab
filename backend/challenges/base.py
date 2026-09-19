"""
ATF Lab - 关卡基类与注册表

⚠️ 仅供教学演示（EDUCATIONAL USE ONLY）

设计要点：
- flag 以 HMAC 摘要形式存储，明文绝不下发到前端
- 校验使用 hmac.compare_digest（恒定时间）
- 每个关卡必须声明 category / difficulty / hints(>=3) / writeup
"""

import hashlib
import hmac
import os
from dataclasses import dataclass, field, asdict
from typing import Callable, List, Optional

from ..config import settings

# flag 校验用的独立密钥（与登录 token 分离）
_FLAG_PEPPER = os.environ.get("ATF_FLAG_PEPPER", settings.SECRET_KEY + "::flag")


def flag_digest(flag: str) -> str:
    """对 flag 明文做带 pepper 的 HMAC-SHA256。"""
    return hmac.new(
        _FLAG_PEPPER.encode("utf-8"),
        flag.strip().encode("utf-8"),
        hashlib.sha256,
    ).hexdigest()


def check_flag(flag: str, digest: str) -> bool:
    return hmac.compare_digest(flag_digest(flag), digest)


@dataclass
class Level:
    id: str
    name: str
    category: str
    difficulty: int                 # 1..5
    objective: str                  # 关卡目标
    hints: List[str]                # 分级提示，>=3 条
    writeup: str                    # 原理讲解
    flag: str                       # 明文（仅服务端持有，不下发）
    points: int = 100
    tags: List[str] = field(default_factory=list)
    free_hints: int = 1             # 前 N 条提示免费
    simulated: bool = True          # 全部为教学模拟
    special: Optional[str] = None   # 特殊关卡标记（如 "finale"）
    # 可选的交互处理器（受控模拟），签名见 handlers.py
    handler: Optional[Callable] = None

    @property
    def flag_hash(self) -> str:
        return flag_digest(self.flag)

    def public(self, solved: bool = False, unlocked_hints: int = 0) -> dict:
        """下发给前端的字段 —— 刻意不含 flag 明文。"""
        return {
            "id": self.id,
            "name": self.name,
            "category": self.category,
            "difficulty": self.difficulty,
            "objective": self.objective,
            "points": self.points,
            "tags": self.tags,
            "hint_count": len(self.hints),
            "free_hints": self.free_hints,
            "simulated": self.simulated,
            "special": self.special,
            "solved": solved,
            "unlocked_hints": unlocked_hints,
            # 只有已解锁的提示才下发内容
            "hints": [
                {"index": i, "text": self.hints[i], "unlocked": i < unlocked_hints}
                for i in range(len(self.hints))
            ],
            # 原理讲解通关后才可见
            "writeup": self.writeup if solved else None,
        }


class Registry:
    def __init__(self) -> None:
        self._levels: dict[str, Level] = {}
        self._order: list[str] = []

    def add(self, level: Level) -> None:
        if level.id in self._levels:
            raise ValueError(f"duplicate level id: {level.id}")
        if len(level.hints) < 3:
            raise ValueError(f"{level.id}: 每关至少需要 3 条提示")
        self._levels[level.id] = level
        self._order.append(level.id)

    def get(self, level_id: str) -> Optional[Level]:
        return self._levels.get(level_id)

    def all(self) -> List[Level]:
        return [self._levels[i] for i in self._order]

    def by_category(self) -> dict:
        out: dict[str, list] = {}
        for lv in self.all():
            out.setdefault(lv.category, []).append(lv)
        return out

    def replace(self, level: Level) -> None:
        """管理后台编辑时替换（保持顺序）。"""
        self._levels[level.id] = level
        if level.id not in self._order:
            self._order.append(level.id)

    def remove(self, level_id: str) -> bool:
        if level_id in self._levels:
            del self._levels[level_id]
            self._order.remove(level_id)
            return True
        return False


registry = Registry()
