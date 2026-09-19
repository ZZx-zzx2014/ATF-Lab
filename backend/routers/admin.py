"""
ATF Lab - 管理后台路由（关卡管理 / 答题统计）

⚠️ 仅供教学演示（EDUCATIONAL USE ONLY）
需要管理员身份（首个注册用户自动成为管理员）。
"""

import json
import time

from fastapi import APIRouter, Depends
from pydantic import BaseModel, Field

from ..challenges import registry
from ..challenges.base import Level
from ..database import query, query_one, execute, audit
from ..deps import admin_user
from ..responses import Code, ApiError, ok

router = APIRouter(prefix="/api/v1/admin", tags=["管理后台"])


class LevelIn(BaseModel):
    id: str = Field(..., min_length=2, max_length=16)
    name: str = Field(..., min_length=1, max_length=80)
    category: str = Field(..., min_length=1, max_length=40)
    difficulty: int = Field(default=1, ge=1, le=5)
    objective: str = Field(..., min_length=1, max_length=1000)
    writeup: str = Field(default="", max_length=8000)
    flag: str = Field(..., min_length=1, max_length=200)
    points: int = Field(default=100, ge=0, le=10000)
    tags: list = Field(default_factory=list)
    hints: list = Field(default_factory=list)


@router.get("/stats", summary="答题统计")
def stats(admin: dict = Depends(admin_user)):
    total_users = query_one("SELECT COUNT(*) AS c FROM users")["c"]
    total_solves = query_one("SELECT COUNT(*) AS c FROM solves")["c"]
    total_subs = query_one("SELECT COUNT(*) AS c FROM submissions")["c"]
    correct_subs = query_one(
        "SELECT COUNT(*) AS c FROM submissions WHERE correct = 1")["c"]

    per_level = []
    for lv in registry.all():
        row = query_one(
            "SELECT COUNT(*) AS c FROM solves WHERE level_id = ?", (lv.id,)
        )
        subs = query_one(
            "SELECT COUNT(*) AS c FROM submissions WHERE level_id = ?", (lv.id,)
        )
        per_level.append({
            "level_id": lv.id,
            "name": lv.name,
            "category": lv.category,
            "difficulty": lv.difficulty,
            "points": lv.points,
            "solve_count": row["c"] if row else 0,
            "submit_count": subs["c"] if subs else 0,
        })

    recent = query(
        "SELECT s.level_id, s.solved_at, u.username FROM solves s "
        "JOIN users u ON u.id = s.user_id ORDER BY s.solved_at DESC LIMIT 20"
    )
    return ok({
        "total_users": total_users,
        "total_solves": total_solves,
        "total_submissions": total_subs,
        "correct_submissions": correct_subs,
        "accuracy": round(correct_subs / total_subs * 100, 1) if total_subs else 0.0,
        "total_levels": len(registry.all()),
        "per_level": per_level,
        "recent_solves": [
            {"level_id": r["level_id"], "username": r["username"],
             "solved_at": r["solved_at"]}
            for r in recent
        ],
    })


@router.get("/levels", summary="关卡列表（含答案，仅管理员）")
def admin_levels(admin: dict = Depends(admin_user)):
    return ok({
        "levels": [
            {
                "id": lv.id, "name": lv.name, "category": lv.category,
                "difficulty": lv.difficulty, "points": lv.points,
                "objective": lv.objective, "flag": lv.flag,
                "hint_count": len(lv.hints), "tags": lv.tags,
                "simulated": lv.simulated, "special": lv.special,
                "builtin": not lv.id.startswith("C"),
            }
            for lv in registry.all()
        ]
    })


@router.post("/levels", summary="新增或更新关卡")
def upsert_level(body: LevelIn, admin: dict = Depends(admin_user)):
    if len(body.hints) < 3:
        raise ApiError(Code.BAD_PARAM, "每关至少需要 3 条提示")

    lv = Level(
        id=body.id,
        name=body.name,
        category=body.category,
        difficulty=body.difficulty,
        objective=body.objective,
        hints=[str(h) for h in body.hints],
        writeup=body.writeup or "（管理员未填写原理讲解）",
        flag=body.flag,
        points=body.points,
        tags=[str(t) for t in body.tags],
        simulated=True,
        special=None,
    )
    registry.replace(lv)

    execute(
        "INSERT INTO level_overrides (level_id, payload, updated_at) VALUES (?, ?, ?) "
        "ON CONFLICT(level_id) DO UPDATE SET payload = excluded.payload, "
        "updated_at = excluded.updated_at",
        (lv.id, json.dumps(body.model_dump(), ensure_ascii=False), time.time()),
    )
    audit(admin["id"], "admin_upsert_level", lv.id)
    return ok({"level_id": lv.id}, message="关卡已保存")


@router.delete("/levels/{level_id}", summary="删除自定义关卡")
def delete_level(level_id: str, admin: dict = Depends(admin_user)):
    lv = registry.get(level_id)
    if lv is None:
        raise ApiError(Code.NOT_FOUND, "关卡不存在")
    if not level_id.startswith("C"):
        raise ApiError(Code.FORBIDDEN, "内置关卡不允许删除（可通过更新覆盖）")

    registry.remove(level_id)
    execute("DELETE FROM level_overrides WHERE level_id = ?", (level_id,))
    audit(admin["id"], "admin_delete_level", level_id)
    return ok({"level_id": level_id}, message="关卡已删除")


@router.get("/users", summary="用户列表")
def admin_users(admin: dict = Depends(admin_user)):
    rows = query(
        "SELECT u.id, u.username, u.email, u.role, u.created_at, u.last_login_at, "
        "       COUNT(s.id) AS solved_count, COALESCE(SUM(s.points),0) AS points "
        "FROM users u LEFT JOIN solves s ON s.user_id = u.id "
        "GROUP BY u.id ORDER BY points DESC"
    )
    return ok({
        "users": [
            {
                "id": r["id"], "username": r["username"], "email": r["email"],
                "role": r["role"], "created_at": r["created_at"],
                "last_login_at": r["last_login_at"],
                "solved_count": r["solved_count"], "points": r["points"],
            }
            for r in rows
        ]
    })


def load_overrides() -> None:
    """启动时把数据库中保存的自定义关卡载入注册表。"""
    try:
        rows = query("SELECT level_id, payload FROM level_overrides")
    except Exception:
        return
    for r in rows:
        try:
            d = json.loads(r["payload"])
            registry.replace(Level(
                id=d["id"], name=d["name"], category=d["category"],
                difficulty=int(d.get("difficulty", 1)),
                objective=d["objective"],
                hints=[str(h) for h in d.get("hints", [])] or ["提示 1", "提示 2", "提示 3"],
                writeup=d.get("writeup") or "（管理员未填写原理讲解）",
                flag=d["flag"], points=int(d.get("points", 100)),
                tags=[str(t) for t in d.get("tags", [])],
            ))
        except Exception:
            continue
