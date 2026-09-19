"""
ATF Lab - 用户路由（排行榜 / 个人主页 / 成就徽章）

⚠️ 仅供教学演示（EDUCATIONAL USE ONLY）
"""

from fastapi import APIRouter, Depends, Query

from ..challenges import registry
from ..database import query, query_one
from ..deps import current_user, current_user_optional
from ..responses import ApiError, Code, ok

router = APIRouter(prefix="/api/v1", tags=["用户"])

# 成就徽章规则：(id, 名称, 说明, 判定函数(solved_ids, stats) -> bool)
BADGE_RULES = [
    ("first_blood", "初次交锋", "通关第一关",
     lambda s, st: len(s) >= 1),
    ("web_novice", "Web 新秀", "通关 5 个 Web 安全关卡",
     lambda s, st: len(s & st["by_cat"].get("Web 安全", set())) >= 5),
    ("web_master", "Web 大师", "通关全部 15 个 Web 安全关卡",
     lambda s, st: len(s & st["by_cat"].get("Web 安全", set())) >= 15),
    ("crypto_fan", "密码学徒", "通关 3 个密码学关卡",
     lambda s, st: len(s & st["by_cat"].get("密码学", set())) >= 3),
    ("forensics_eye", "取证之眼", "通关 3 个取证分析关卡",
     lambda s, st: len(s & st["by_cat"].get("取证分析", set())) >= 3),
    ("net_prober", "网络探针", "通关 3 个网络渗透关卡",
     lambda s, st: len(s & st["by_cat"].get("网络渗透", set())) >= 3),
    ("half_way", "过半征程", "通关一半以上的教学关",
     lambda s, st: len(s - st["finale_ids"]) >= (len(st["all_ids"] - st["finale_ids"]) // 2)),
    ("reaper", "清算者", "完成 REAPER 行动压轴关",
     lambda s, st: bool(s & st["finale_ids"])),
    ("completionist", "全境通关", "通关全部关卡",
     lambda s, st: len(s) >= len(st["all_ids"])),
]


def _stats():
    levels = registry.all()
    by_cat: dict = {}
    for lv in levels:
        by_cat.setdefault(lv.category, set()).add(lv.id)
    return {
        "all_ids": {lv.id for lv in levels},
        "by_cat": by_cat,
        "finale_ids": {lv.id for lv in levels if lv.special == "finale"},
        "level_map": {lv.id: lv for lv in levels},
    }


def _solved_ids(user_id: int) -> set:
    rows = query("SELECT level_id FROM solves WHERE user_id = ?", (user_id,))
    return {r["level_id"] for r in rows}


def _badges_for(solved: set) -> list:
    st = _stats()
    out = []
    for bid, name, desc, fn in BADGE_RULES:
        try:
            earned = bool(fn(solved, st))
        except Exception:
            earned = False
        out.append({"id": bid, "name": name, "description": desc, "earned": earned})
    return out


def _user_summary(row) -> dict:
    solved = _solved_ids(row["id"])
    st = _stats()
    total_points = sum(st["level_map"][i].points for i in solved if i in st["level_map"])
    return {
        "id": row["id"],
        "username": row["username"],
        "role": row["role"],
        "created_at": row["created_at"],
        "solved_count": len(solved),
        "total_count": len(st["all_ids"]),
        "points": total_points,
        "max_points": sum(lv.points for lv in st["level_map"].values()),
        "badges": [b for b in _badges_for(solved) if b["earned"]],
    }


@router.get("/leaderboard", summary="排行榜")
def leaderboard(limit: int = Query(default=50, ge=1, le=200),
                user=Depends(current_user_optional)):
    rows = query(
        "SELECT u.id, u.username, u.role, u.created_at, "
        "       COUNT(s.id) AS solved_count, COALESCE(SUM(s.points), 0) AS points, "
        "       MIN(s.solved_at) AS first_solve_at "
        "FROM users u LEFT JOIN solves s ON s.user_id = u.id "
        "GROUP BY u.id ORDER BY points DESC, first_solve_at ASC LIMIT ?",
        (limit,),
    )
    entries = []
    for i, r in enumerate(rows, 1):
        entries.append({
            "rank": i,
            "user_id": r["id"],
            "username": r["username"],
            "role": r["role"],
            "solved_count": r["solved_count"],
            "points": r["points"],
        })

    me_rank = None
    if user:
        for e in entries:
            if e["user_id"] == user["id"]:
                me_rank = e["rank"]
                break
    return ok({"entries": entries, "my_rank": me_rank, "total_players": len(rows)})


@router.get("/users/{username}", summary="查看某个用户的公开主页")
def user_profile(username: str):
    row = query_one(
        "SELECT id, username, role, created_at FROM users WHERE username = ?",
        (username,),
    )
    if row is None:
        raise ApiError(Code.NOT_FOUND, "用户不存在")

    solved = _solved_ids(row["id"])
    st = _stats()
    solved_levels = [
        {"id": lv.id, "name": lv.name, "category": lv.category,
         "difficulty": lv.difficulty, "points": lv.points}
        for lv in registry.all() if lv.id in solved
    ]
    summary = _user_summary(row)
    summary["solved_levels"] = solved_levels
    summary["progress_percent"] = round(
        len(solved) / max(1, len(st["all_ids"])) * 100, 1)
    return ok(summary)


@router.get("/me/profile", summary="我的个人主页（含徽章）")
def my_profile(user: dict = Depends(current_user)):
    row = query_one(
        "SELECT id, username, role, created_at FROM users WHERE id = ?", (user["id"],)
    )
    solved = _solved_ids(user["id"])
    st = _stats()
    summary = _user_summary(row)
    summary["solved_levels"] = [
        {"id": lv.id, "name": lv.name, "category": lv.category,
         "difficulty": lv.difficulty, "points": lv.points}
        for lv in registry.all() if lv.id in solved
    ]
    summary["progress_percent"] = round(
        len(solved) / max(1, len(st["all_ids"])) * 100, 1)
    summary["all_badges"] = _badges_for(solved)
    return ok(summary)


@router.get("/progress", summary="获取当前用户全部通关记录")
def progress(user: dict = Depends(current_user)):
    rows = query(
        "SELECT level_id, points, solved_at FROM solves "
        "WHERE user_id = ? ORDER BY solved_at",
        (user["id"],),
    )
    return ok({
        "solves": [
            {"level_id": r["level_id"], "points": r["points"], "solved_at": r["solved_at"]}
            for r in rows
        ],
        "count": len(rows),
    })
