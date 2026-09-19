"""
ATF Lab - 关卡路由（列表 / 详情 / 提交 flag / 解锁提示）

⚠️ 仅供教学演示（EDUCATIONAL USE ONLY）
- flag 明文绝不下发，只返回 flag_hash 之外的公开字段
- 提交校验使用恒定时间比较
"""

import time
from collections import OrderedDict

from fastapi import APIRouter, Depends, Query
from pydantic import BaseModel

from ..challenges import registry, check_flag
from ..database import query, query_one, execute, audit
from ..deps import current_user, current_user_optional
from ..responses import Code, ApiError, ok

router = APIRouter(prefix="/api/v1/levels", tags=["关卡"])


class SubmitIn(BaseModel):
    flag: str


def _solved_ids(user_id: int) -> set:
    rows = query("SELECT level_id FROM solves WHERE user_id = ?", (user_id,))
    return {r["level_id"] for r in rows}


def _unlocked_hints(user_id: int, level_id: str) -> int:
    row = query_one(
        "SELECT COUNT(*) AS c FROM hint_unlocks WHERE user_id = ? AND level_id = ?",
        (user_id, level_id),
    )
    return row["c"] if row else 0


def _is_unlocked_for(user_id, level) -> bool:
    """
    压轴关解锁条件：至少通关 5 个教学关。
    其余关卡恒为解锁状态。
    """
    if level.special != "finale":
        return True
    if user_id is None:
        return False
    solved = query_one(
        "SELECT COUNT(*) AS c FROM solves WHERE user_id = ?", (user_id,)
    )
    return bool(solved and solved["c"] >= 5)


@router.get("", summary="获取关卡列表")
def list_levels(
    category: str = Query(default="", description="按分类筛选"),
    difficulty: int = Query(default=0, ge=0, le=5, description="按难度筛选，0 表示全部"),
    keyword: str = Query(default="", description="关键词搜索（名称/考点/标签）"),
    user=Depends(current_user_optional),
):
    uid = user["id"] if user else None
    solved = _solved_ids(uid) if uid else set()

    items = []
    for lv in registry.all():
        if category and lv.category != category:
            continue
        if difficulty and lv.difficulty != difficulty:
            continue
        if keyword:
            hay = " ".join([lv.name, lv.objective, lv.category] + lv.tags).lower()
            if keyword.lower() not in hay:
                continue
        pub = lv.public(solved=lv.id in solved,
                        unlocked_hints=_unlocked_hints(uid, lv.id) if uid else 0)
        pub["unlocked"] = _is_unlocked_for(uid, lv)
        items.append(pub)

    # 分类维度统计
    cats: "OrderedDict[str, dict]" = OrderedDict()
    for lv in registry.all():
        c = cats.setdefault(lv.category, {"category": lv.category, "total": 0,
                                          "solved": 0, "points": 0})
        c["total"] += 1
        c["points"] += lv.points
        if lv.id in solved:
            c["solved"] += 1

    return ok({
        "levels": items,
        "total": len(items),
        "categories": list(cats.values()),
        "solved_count": len(solved & {lv.id for lv in registry.all()}),
        "total_count": len(registry.all()),
        "total_points": sum(lv.points for lv in registry.all()),
        "earned_points": sum(lv.points for lv in registry.all() if lv.id in solved),
    })


@router.get("/{level_id}", summary="获取关卡详情")
def get_level(level_id: str, user=Depends(current_user_optional)):
    lv = registry.get(level_id)
    if lv is None:
        raise ApiError(Code.NOT_FOUND, "关卡不存在")

    uid = user["id"] if user else None
    solved = uid is not None and level_id in _solved_ids(uid)
    pub = lv.public(solved=solved,
                    unlocked_hints=_unlocked_hints(uid, level_id) if uid else 0)
    pub["unlocked"] = _is_unlocked_for(uid, lv)
    return ok(pub)


@router.post("/{level_id}/submit", summary="提交 flag")
def submit_flag(level_id: str, body: SubmitIn, user: dict = Depends(current_user)):
    lv = registry.get(level_id)
    if lv is None:
        raise ApiError(Code.NOT_FOUND, "关卡不存在")

    if not _is_unlocked_for(user["id"], lv):
        raise ApiError(Code.LOCKED, "该关卡尚未解锁（先通关至少 5 个教学关）")

    correct = check_flag(body.flag, lv.flag_hash)

    # 记录提交历史（无论对错，用于统计）
    execute(
        "INSERT INTO submissions (user_id, level_id, correct, submitted_at) "
        "VALUES (?, ?, ?, ?)",
        (user["id"], level_id, 1 if correct else 0, time.time()),
    )

    if not correct:
        return ok({"correct": False}, message="flag 不正确，再想想")

    already = query_one(
        "SELECT id FROM solves WHERE user_id = ? AND level_id = ?",
        (user["id"], level_id),
    )
    first_time = already is None
    if first_time:
        execute(
            "INSERT INTO solves (user_id, level_id, points, solved_at) "
            "VALUES (?, ?, ?, ?)",
            (user["id"], level_id, lv.points, time.time()),
        )
        audit(user["id"], "solve", level_id)

    solved_count = query_one(
        "SELECT COUNT(*) AS c FROM solves WHERE user_id = ?", (user["id"],)
    )["c"]

    return ok({
        "correct": True,
        "first_solve": first_time,
        "points_awarded": lv.points if first_time else 0,
        "solved_count": solved_count,
        "total_count": len(registry.all()),
        "writeup": lv.writeup,
        "all_cleared": solved_count >= len(registry.all()),
    }, message="正确！已记录通关" if first_time else "正确！（此前已通关，不重复计分）")


@router.post("/{level_id}/hint/{index}", summary="解锁一条提示")
def unlock_hint(level_id: str, index: int, user: dict = Depends(current_user)):
    lv = registry.get(level_id)
    if lv is None:
        raise ApiError(Code.NOT_FOUND, "关卡不存在")
    if index < 0 or index >= len(lv.hints):
        raise ApiError(Code.BAD_PARAM, "提示序号越界")

    already = query_one(
        "SELECT id FROM hint_unlocks WHERE user_id = ? AND level_id = ? AND hint_index = ?",
        (user["id"], level_id, index),
    )
    if not already:
        execute(
            "INSERT INTO hint_unlocks (user_id, level_id, hint_index, unlocked_at) "
            "VALUES (?, ?, ?, ?)",
            (user["id"], level_id, index, time.time()),
        )

    unlocked = _unlocked_hints(user["id"], level_id)
    return ok({
        "index": index,
        "text": lv.hints[index],
        "unlocked_hints": unlocked,
        "hint_count": len(lv.hints),
        "is_free": index < lv.free_hints,
    }, message="提示已解锁")
