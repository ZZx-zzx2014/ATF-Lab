# ⚠️ 免责声明

> 本项目是一个 **API 调动的** 学习与演示项目，**仅供本人自行娱乐与安全学习使用**。
> **请勿在互联网上公开发布、部署或传播**。
> 若因违反本约定造成任何后果，由使用者自行承担。

<div align="center">

# 🛡️ ATF Lab

**一个 API 调动的安全学习靶场平台**

[![Python](https://img.shields.io/badge/Python-3.9%2B-3776ab?logo=python&logoColor=white)](https://www.python.org/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.110%2B-009688?logo=fastapi&logoColor=white)](https://fastapi.tiangolo.com/)
[![React](https://img.shields.io/badge/React-18-61dafb?logo=react&logoColor=black)](https://react.dev/)
[![SQLite](https://img.shields.io/badge/SQLite-3-003b57?logo=sqlite&logoColor=white)](https://www.sqlite.org/)
[![License](https://img.shields.io/badge/License-Educational%20Only-red)](#-许可与限制)

**37 个实战关卡 · 5 大技术方向 · 全受控模拟环境**

[快速开始](#-快速开始) · [关卡清单](#-关卡清单) · [API 文档](#-api-文档) · [架构说明](#-架构说明)

</div>

---

> [!CAUTION]
> **请勿将本项目部署到公网。**
> 本项目是安全教学靶场，所有"漏洞"均为**受控模拟**，不具备危害真实系统的能力。
> 但公开部署仍可能被误认为真实业务系统，并违反本项目的使用约定。
> **强烈建议使用私有仓库（`gh repo create --private`）。**

---

## 📌 版本状态

**当前版本：`v2.0.0-rc1`（候选版 / Release Candidate）**

功能已完整实现并通过自动化验证，但**尚未在所有部署路径上实测**，
因此暂标为候选版而非正式版。

### 已验证 ✅

| 验证项 | 结果 |
|---|---|
| 源码编译自检 | 25 / 25 文件通过 |
| 端到端冒烟测试 | 50 / 50 通过 |
| 安全边界审计（AST 级） | 全部通过 |
| 验收标准核验 | 49 / 49 通过 |
| 仿真网络服务 | 6 / 6 安全边界检查通过 |
| 前端 UI（Playwright） | 21 / 21 通过 |
| 全部 37 关 flag 校验 | 通过 |

验证环境：Windows 11 + Python 3.14.4 + Node 24.15.0

### 尚未实测 ⚠️

以下项目**代码已写好但未在真实环境执行过**，是 rc1 与正式版之间的差距：

| 项目 | 状态 | 说明 |
|---|---|---|
| `start.sh` (macOS/Linux) | ⚠️ 未实测 | 逻辑已实现，未在对应平台运行 |
| `start.command` (macOS) | ⚠️ 未实测 | 同上 |
| `start.bat` (Windows) | ⚠️ 未实测 | 逻辑已实现，未完整跑通 |
| Linux / macOS 运行 | ⚠️ 未实测 | 仅在 Windows 上验证过 |
| Python 3.9 – 3.12 | ⚠️ 未实测 | 仅在 Python 3.14 上验证过 |

### 已实测的部署路径 ✅

| 路径 | 结果 |
|---|---|
| `docker compose up --build` | ✅ **已实测通过**（Windows 11 + Docker Desktop 29.4.3 + WSL2） |
| 容器健康检查 | ✅ `Up (healthy)` |
| 容器内 37 关装载 | ✅ 通过 |
| 容器内全部 API | ✅ 冒烟 50/50、验收 49/49 |
| 容器内 4 个仿真服务 | ✅ 正常响应 |

> ⚠️ 但 Docker 模式下，宿主经端口映射访问**仿真服务的裸 TCP 端口**存在
> Docker Desktop 平台限制（连接被重置）。需要实操网络渗透关卡时请用本地运行方式。
> 详见 [已知限制](#已知限制宿主端口冲突与仿真服务转发)。

### 升级为正式版的条件

以下任一路径走通，即可将版本号提升为 `v2.0.0` 并打正式 tag：

1. ~~在启用虚拟化的机器上跑通 `docker compose up --build`~~ ✅ **已完成**
2. 在 macOS / Linux 上跑通 `./start.sh`，或
3. 在 Windows 上跑通 `start.bat`

> 💡 **已知环境问题**：若 `docker compose up` 报
> 「Virtualization support not detected」，说明 Windows 的
> **虚拟机平台**与 **Hyper-V** 功能未启用（与 CPU 是否支持无关）。
> 若启用时报 `0x8007371B`，需先执行
> `DISM /Online /Cleanup-Image /RestoreHealth` 修复组件存储。
> 详见 [部署](#-部署) 章节。

## 📖 目录

- [项目简介](#-项目简介)
- [账号与安全](#-账号与安全)
- [安全边界](#-安全边界重要)
- [核心特性](#-核心特性)
- [快速开始](#-快速开始)
- [关卡清单](#-关卡清单)
- [API 文档](#-api-文档)
- [架构说明](#-架构说明)
- [配置项](#-配置项)
- [部署](#-部署)
- [发布到 GitHub](#-发布到-github)
- [项目结构](#-项目结构)
- [许可与限制](#-许可与限制)

---

## 🎯 项目简介

**ATF Lab** 是一个面向安全学习者的实战靶场平台。它把 Web 安全、密码学、取证分析、
网络渗透、逆向与杂项五大方向的知识点，组织成 37 个循序渐进的可交互关卡，
外加一个串联多种技术的**压轴行动关卡**。

平台本身是一个完整的 Web 应用：

- **前端**：React + Vite 独立 SPA，所有数据经 REST API 获取
- **后端**：FastAPI，统一 JSON 响应格式，自动生成 OpenAPI 文档
- **存储**：SQLite，进度跨浏览器、跨设备同步
- **双模式**：展示模式（品牌落地页）与 CTF 靶场模式，可显式切换

### 双模式说明

| 模式 | 入口 | 内容 | 标识 |
|---|---|---|---|
| **展示模式** | `/` | 产品落地页、特性介绍、排行榜 | 顶部标注「教学靶场」，页脚含免责声明 |
| **CTF 靶场** | `/lab` | 37 个关卡、答题、进度 | 页面标题明确标注为靶场 |

> 两种模式**均明确标注为教学靶场**，不做任何"伪装成真实业务系统"的设计。
> 顶部导航提供显式模式切换器，当前模式一目了然。

---

## 👤 账号与安全

### 首次部署：自动创建管理员

首次启动时（用户表为空），系统会自动创建一个管理员账号，并在**启动日志**中
醒目地打印初始凭据：

```
====================================================================
  ⚠️  首次初始化：已创建管理员账号
====================================================================
  用户名      : admin
  初始密码    : FKWGCWiBG5EbvjWFY3XF   （随机生成）
  恢复码      : gHE4-w4gZ-6DUA-UD5P

  请立即登录并修改初始密码。
  恢复码用于忘记密码时自助重置，请妥善保存 —— 它只显示这一次。
====================================================================
```

密码来源有两种：

| 方式 | 行为 |
|---|---|
| 设置 `ATF_ADMIN_PASSWORD` | 使用你指定的密码 |
| 不设置 | 随机生成 20 位强密码并打印到日志 |

**两种方式都会标记 `must_change_password`**，在管理员改密之前，
站内**每页顶部**都会显示红色警示横幅：

> 🔐 安全提醒：你仍在使用初始密码，请立即修改后再使用平台。 [立即修改]

改密后横幅自动消失。

### 忘记密码：两条正当途径

本项目**刻意不提供任何通用后门密码**。忘记密码时有两套正规机制：

#### 途径 A：一次性恢复码（用户自助）

- 注册时自动生成，格式 `XXXX-XXXX-XXXX-XXXX`
- **只在生成时显示一次**，数据库中仅存 PBKDF2 哈希
- 在登录页「忘记密码」使用
- **用一次即失效**，重置成功后自动下发新的恢复码

#### 途径 B：命令行工具（需服务器权限）

```bash
python -m backend.admin list-users                        # 查看用户
python -m backend.admin reset-password --user admin       # 随机重置密码
python -m backend.admin show-recovery --user admin        # 重新生成恢复码
python -m backend.admin unlock --user admin               # 解除登录锁定
python -m backend.admin audit --limit 50                  # 查看审计日志
```

Docker 环境：

```bash
docker compose exec atf-lab python -m backend.admin reset-password --user admin
```

> 需要**服务器 shell 权限** —— 这是天然的权限边界，
> 而不是一个网络可达的"万能密码"。

### 已实现的安全措施

| 措施 | 说明 |
|---|---|
| 口令存储 | PBKDF2-HMAC-SHA256，20 万轮 + 16 字节随机盐 |
| 恒定时间比较 | `hmac.compare_digest`，避免时序侧信道 |
| **登录防爆破** | 连续 5 次失败锁定账号 15 分钟 |
| **账号枚举防护** | 用户不存在与密码错误返回**相同**错误信息 |
| **密码强度校验** | ≥8 位 + 含字母 + 含数字 + 弱口令黑名单 |
| **安全响应头** | CSP / X-Frame-Options / X-Content-Type-Options / Referrer-Policy / Permissions-Policy |
| **密钥强度检查** | 启动时检测默认密钥并打印醒目警告 |
| **审计日志** | 登录、改密、密码恢复、管理员操作全部记录 |
| JWT | HS256 + `aud` / `iss` / `exp` 校验 |

### 公网部署

⚠️ **本项目默认只绑定 `127.0.0.1`，不对外网暴露。**

如需公网部署，**必须先阅读** [`docs/PUBLIC_DEPLOY.md`](docs/PUBLIC_DEPLOY.md)，
其中包含 9 项上线检查清单、Nginx HTTPS 配置示例、反向代理限流规则。

最关键的几项：

```ini
# .env
ATF_SECRET_KEY=<用 secrets.token_hex(32) 生成>
ATF_CORS_ORIGINS=https://your-domain.com   # 不要留 *
ATF_BIND=0.0.0.0                           # 才对外监听
```

> ⚠️ 公网部署与 README 顶部的「请勿在互联网上公开发布、部署或传播」直接冲突。
> 这个决定归你，但风险自负。

### 明确不做的事

以下功能**本项目不提供，也不应被添加**：

| ❌ | 原因 |
|---|---|
| 通用"终极管理员密码" | 这是后门：绕过正常认证、用户不知情、一旦泄露则所有部署实例同时沦陷 |
| 把用户密码回传到第三方服务器 | 凭据窃取，无论代码写得多干净 |
| 反取证 / 隐藏回传通道 | 让受害者无法察觉，性质更严重 |

`scripts/acceptance.py` 中有专门的断言（`8d` / `8e`）持续校验这两点。

---

## 🔒 安全边界（重要）

这是本项目最核心的设计约束。**所有"漏洞"都是为教学设计而刻意实现的模拟逻辑**，
不是真实缺陷，也不具备任何真实攻击能力。

| 危险能力 | 本项目的实现方式 |
|---|---|
| 命令执行 | ❌ 无 `subprocess` / `os.system` / `os.popen`。命令注入关卡只做**模式匹配**并返回**硬编码**回显文本 |
| 任意文件读写 | ❌ 无真实文件系统操作。路径穿越作用于**内存中的虚拟文件树**（Python 字典） |
| 出站网络请求 | ❌ 无任何出站连接。SSRF 关卡只允许**内置的模拟端点**，外部地址一律拒绝 |
| 真实 SQL 执行 | ❌ 不连接任何数据库做查询。SQL 注入关卡用**正则匹配**判定 payload 并返回**预置结果集** |
| 反序列化 | ❌ 不调用 `pickle.loads` / `yaml.load` / `ObjectInputStream`。仅做**特征匹配**并返回说明文本 |
| 文件上传 | ❌ 不落盘、不解析、不执行。仅在**内存中**做扩展名判定 |
| XML 解析 | ❌ 不使用真实 XML 解析库。XXE 关卡用**正则识别**实体声明并返回**预置文本** |
| 反弹 shell / 端口转发 | ❌ 完全不实现 |
| 仿真网络服务 | ✅ 仅返回**预置静态文本**，**仅监听 127.0.0.1**，零出站连接 |
| 压轴关"数据销毁" | ✅ 只 `UPDATE` 模拟表 `sim_archive_records` 的 `status` 字段，**不删除任何行**、不影响任何真实数据 |

### 关键隔离设计

压轴关 L37 包含一个 **JWT 弱密钥伪造**考点。为避免这个教学漏洞影响平台本身：

- 关卡使用的弱密钥（`helios-dev-secret`）与平台真实密钥（`ATF_SECRET_KEY`）**完全分离**
- 关卡 token 的 `audience` 是 `helios-portal-sim`，平台 token 是 `atf-platform`，**互不承认**
- 用关卡弱密钥伪造的 `admin` token **无法通过平台任何真实接口的鉴权**

这一点有自动化测试覆盖（见 `scripts/smoke_test.py` 中的「★压轴关 JWT 无法提权平台」）。

### 代码中的标注

所有模拟点都有显著注释：

```python
# ⚠️ 仅供教学演示（CONTROLLED SIMULATION）
# 说明：此处不执行真实 XX，仅做 YY 并返回预置文本。
```

所有模拟响应体都带标记字段，防止使用者误判：

```json
{
  "result": "...",
  "_simulation": true,
  "_simulation_notice": "本响应由 ATF Lab 教学沙箱生成，为受控模拟数据，不对应任何真实系统。"
}
```

---

## ✨ 核心特性

<table>
<tr><td width="50%">

**🎯 37 个实战关卡**
覆盖 Web 安全（15）、密码学（6）、取证分析（5）、网络渗透（7）、逆向与杂项（3），外加压轴行动（1）

**🧪 全受控模拟**
每一个"漏洞"都有明确的安全边界，不产生任何真实副作用

**💡 分级提示**
每关至少 3 条递进提示，通关后解锁完整原理复盘与防御方案

</td><td width="50%">

**🔐 完整账号体系**
注册 / 登录 / JWT 鉴权，口令用 PBKDF2-HMAC-SHA256（20 万轮 + 随机盐）存储

**🏆 进度与排行**
进度入库跨设备同步，排行榜 + 9 种成就徽章

**⚙️ 管理后台**
关卡增删改、答题统计、用户列表（首个注册用户自动成为管理员）

</td></tr>
<tr><td>

**🎨 响应式 UI**
深浅色主题自动跟随系统并可手动切换，移动端适配

**🔍 筛选与搜索**
按分类、难度筛选，按关键词搜索关卡

</td><td>

**🖥️ 仿真网络服务**
仿 FTP（2121）/ MySQL（3306）/ Redis（6379）/ 调试服务（31337），
可练习 `nmap`、`nc`、`redis-cli`

**🐳 一键部署**
`docker compose up` 即可完整启动

</td></tr>
</table>

---

## 🚀 快速开始

### 方式一：Docker（推荐）

```bash
git clone <your-repo-url> ATF-Lab
cd ATF-Lab
docker compose up --build
```

打开 <http://127.0.0.1:8899> 即可。

### 方式二：本地运行

**前置要求**：Python 3.9+，Node.js 18+（可选，用于构建前端）

```bash
# macOS / Linux
chmod +x start.sh && ./start.sh

# Windows
start.bat
```

脚本会自动：创建虚拟环境 → 安装依赖 → 构建前端 → 启动服务。

**手动启动**：

```bash
python -m venv .venv
source .venv/bin/activate        # Windows: .venv\Scripts\activate
pip install -r backend/requirements.txt

cd frontend && npm install && npm run build && cd ..

cp .env.example .env             # 按需修改
python -m uvicorn backend.main:app --host 127.0.0.1 --port 8899
```

### 默认访问

| 地址 | 说明 |
|---|---|
| <http://127.0.0.1:8899> | 前端 SPA |
| <http://127.0.0.1:8899/api/docs> | Swagger UI（可在线调试） |
| <http://127.0.0.1:8899/api/redoc> | ReDoc |
| <http://127.0.0.1:8899/api/v1/health> | 健康检查 |

> 💡 **第一个注册的用户自动成为管理员**，可访问 `/admin` 管理后台。

### 验证部署

项目自带 5 个验证脚本，可逐项确认功能与安全边界：

```bash
# 1. 健康检查（应返回 code:0 且 levels:37）
curl http://127.0.0.1:8899/api/v1/health

# 2. 源码编译自检（25 个文件）
python scripts/lint.py backend
python scripts/lint.py netlab

# 3. 端到端冒烟测试（50 项：认证/关卡/flag/排行/管理/压轴关）
python scripts/smoke_test.py

# 4. 安全边界审计（AST 级扫描，确认无危险能力）
python scripts/audit_safety.py

# 5. 验收标准核验（49 项，逐条对照需求）
python scripts/acceptance.py

# 6. 仿真网络服务验证（需服务已启动）
python scripts/check_netlab.py
```

各脚本会在项目根目录生成对应的 `*_result.txt` 报告（已在 `.gitignore` 中排除）。

**当前验证状态**：

| 脚本 | 结果 |
|---|---|
| `lint.py` | ✅ 25/25 文件编译通过 |
| `smoke_test.py` | ✅ 50/50 通过 |
| `audit_safety.py` | ✅ 全部通过（无命令执行/无出站请求/无真实反序列化…） |
| `acceptance.py` | ✅ 49/49 通过 |
| `check_netlab.py` | ✅ 6/6 安全边界检查通过 |

> 前端 UI 另有 Playwright 脚本 `scripts/verify_ui.mjs`（21 项），
> 需在 `frontend/` 下安装 `playwright` 后运行。

---

## 📋 关卡清单

### 总览

| 分类 | 关卡数 | 编号范围 | 总分 |
|---|---:|---|---:|
| Web 安全 | 15 | L01 - L15 | 1900 |
| 密码学 | 6 | L16 - L21 | 660 |
| 取证分析 | 5 | L22 - L26 | 590 |
| 网络渗透 | 7 | L27 - L33 | 810 |
| 逆向与杂项 | 3 | L34 - L36 | 370 |
| 压轴行动 | 1 | L37 | 500 |
| **合计** | **37** | | **4830** |

### Web 安全（L01 - L15）

| 编号 | 名称 | 难度 | 分值 | 考点 | 提示要点 |
|---|---|---:|:--:|---|---|
| L01 | 源码里的注释 | ★ | 50 | 信息泄露 | 查看网页源代码，留意 HTML 注释 |
| L02 | 不只是 Base64 | ★ | 50 | 编码识别 | 识别字符集特征，可能需多层解码 |
| L03 | 响应头会说话 | ★★ | 80 | HTTP 头 | 用 Network 面板或 `curl -i` 看响应头 |
| L04 | 弱口令管理员 | ★★ | 80 | 暴力破解 | 安全意识培训最常点名的密码 |
| L05 | 登录框的谎言 | ★★ | 100 | SQL 注入 | 单引号探错，构造恒真条件绕过 |
| L06 | 逐层向上 | ★★ | 100 | 路径穿越 | 用 `../../` 逃逸目录，注意 URL 编码 |
| L07 | 回显的代价 | ★★★ | 120 | 命令注入 | 用 `;` `\|` 等分隔符追加命令 |
| L08 | 换个身份进门 | ★★★ | 120 | 越权 IDOR | 修改 `user_id` 参数访问他人资料 |
| L09 | 反射的镜子 | ★★★ | 120 | XSS | 搜索框输出未转义，构造脚本 payload |
| L10 | 借刀杀人 | ★★★★ | 150 | CSRF | 检查有无 CSRF token，构造自动提交表单 |
| L11 | 让我替你访问 | ★★★★ | 150 | SSRF | 把外网 URL 换成内网地址探测 |
| L12 | 上传的黑名单 | ★★★★ | 150 | 文件上传 | 找黑名单遗漏的等价扩展名 |
| L13 | 不安全的反序列化 | ★★★★★ | 200 | 反序列化 | 判断协议类型，构造利用链载荷 |
| L14 | 实体的诱惑 | ★★★★★ | 200 | XXE | 用 DOCTYPE + ENTITY SYSTEM 读文件 |
| L15 | 自己签一张票 | ★★★★★ | 250 | JWT 伪造 | 弱密钥可爆破，改 `role` 后重签 |

### 密码学（L16 - L21）

| 编号 | 名称 | 难度 | 分值 | 考点 | 提示要点 |
|---|---|---:|:--:|---|---|
| L16 | 凯撒的位移 | ★ | 50 | 古典密码 | 暴力枚举 1-25 位移 |
| L17 | 编码套娃 | ★★ | 80 | 多层编码 | Hex → Base64 → URL → 反转 |
| L18 | 撞出这个 MD5 | ★★ | 80 | 哈希破解 | 用彩虹表或在线库查常见值 |
| L19 | 时间就是答案 | ★★★ | 120 | 弱随机数 | 时间戳做种子则可复现序列 |
| L20 | 维吉尼亚之锁 | ★★★ | 120 | 多表替换 | 卡西斯基检验定密钥长度 |
| L21 | 异或的秘密 | ★★★★ | 150 | 密码分析 | 单字节异或仅 256 种，全枚举 |

### 取证分析（L22 - L26）

| 编号 | 名称 | 难度 | 分值 | 考点 | 提示要点 |
|---|---|---:|:--:|---|---|
| L22 | 图片里的碎语 | ★★ | 80 | 文件隐写 | 用 `strings` 或 `binwalk` 看文件尾部 |
| L23 | 元数据不会骗人 | ★★ | 80 | EXIF | `exiftool` 查看 GPS 与描述字段 |
| L24 | 流量的低语 | ★★★ | 120 | 流量分析 | Wireshark 过滤 HTTP，看 Authorization |
| L25 | 日志中的脚印 | ★★★ | 120 | 日志审计 | 大量 404 后突然 200 即入侵成功 |
| L26 | 藏在字节末尾 | ★★★★ | 150 | LSB 隐写 | 用 `zsteg` 或自写脚本读最低位 |

### 网络渗透（L27 - L33）

| 编号 | 名称 | 难度 | 分值 | 考点 | 提示要点 |
|---|---|---:|:--:|---|---|
| L27 | 端口在低语 | ★ | 50 | 端口扫描 | `nmap -p-` 扫全端口，注意 31337 |
| L28 | 服务的指纹 | ★★ | 80 | 服务识别 | `nmap -sV` 或 `nc` 抓 banner |
| L29 | redis 没关门 | ★★★ | 120 | 未授权访问 | `redis-cli` 无需 AUTH，`KEYS *` |
| L30 | 备份文件的疏忽 | ★★ | 100 | 备份泄露 | 目录爆破找 `www.zip` / `.bak` |
| L31 | 请求头伪装 | ★★★ | 120 | 头伪造 | 添加 `X-Forwarded-For: 127.0.0.1` |
| L32 | Basic 认证的倔强 | ★★★★ | 150 | 认证爆破 | `hydra` 或 `ffuf` 爆破 Basic |
| L33 | 配置错误的服务 | ★★★★ | 150 | 调试接口 | 访问 `/debug` `/actuator` 等路径 |

### 逆向与杂项（L34 - L36）

| 编号 | 名称 | 难度 | 分值 | 考点 | 提示要点 |
|---|---|---:|:--:|---|---|
| L34 | 反汇编的第一眼 | ★★★ | 120 | 伪代码分析 | 找比较分支，还原变换算法 |
| L35 | 混淆的字符串 | ★★★★ | 150 | 反混淆 | 逐层解码，注意拼接顺序 |
| L36 | 这封邮件有问题 | ★★ | 100 | 钓鱼识别 | 看域名拼写、链接目标、SPF/DKIM |

### 🎬 压轴行动（L37）

| 编号 | 名称 | 难度 | 分值 | 类型 |
|---|---|---:|:--:|---|
| **L37** | **REAPER 行动** | ★★★★★ | 500 | 综合攻击链 |

**解锁条件**：通关至少 **5 个**教学关。

**剧情**：你是一名白帽。Helios 生物科技的内部档案 `PROJECT_REAPER` 缺少 41 份知情同意书，
销毁期限就在本周。你需要逐层穿透门户的六道防线，拿到管理员权限，销毁这份档案。

**六阶段攻击链**：

| 阶段 | 名称 | 技术点 | 产出 |
|---:|---|---|---|
| 1 | 员工名录泄露 | 信息泄露（旧接口未下线） | 员工工号 |
| 2 | SQL 注入绕过 | SQL 注入 | 员工会话 JWT |
| 3 | JWT 弱密钥提权 | JWT 伪造 | 模拟 admin token |
| 4 | SSRF 探测内网 | SSRF | `archive_key` |
| 5 | XXE 读取档案 | XXE | `destruction_token` |
| 6 | 销毁 REAPER 档案 | 数据销毁（模拟） | 通关 |

> ⚠️ **再次强调**：阶段 3 的弱密钥与平台真实 JWT 体系完全隔离；
> 阶段 6 的"销毁"只更新模拟表 `sim_archive_records` 的 `status` 字段。

---

## 📡 API 文档

**统一响应格式**：

```json
{ "code": 0, "message": "ok", "data": { } }
```

`code === 0` 表示成功。完整交互式文档见 **`/api/docs`**（Swagger UI，可在线调试）。
详细的接口说明另见 [`docs/API.md`](docs/API.md)。

### 错误码

| code | 含义 | HTTP |
|---:|---|---:|
| 0 | 成功 | 200 |
| 1001 | 参数校验失败 | 400 |
| 1002 | 未登录 / token 无效 | 401 |
| 1003 | 无权限（非管理员） | 403 |
| 1004 | 资源不存在 | 404 |
| 1005 | 资源冲突（用户名已占用） | 409 |
| 1006 | 请求过于频繁 | 429 |
| 1007 | flag 错误（业务失败） | 200 |
| 1008 | 关卡未解锁 | 403 |
| 5000 | 服务器内部错误 | 500 |

### 接口速查

<details open>
<summary><b>系统</b></summary>

| 方法 | 路径 | 说明 | 认证 |
|---|---|---|---|
| GET | `/api/v1/health` | 健康检查（含关卡数、netlab 状态） | 否 |

</details>

<details open>
<summary><b>认证</b></summary>

| 方法 | 路径 | 说明 | 认证 |
|---|---|---|---|
| POST | `/api/v1/auth/register` | 注册（首个用户自动成为管理员） | 否 |
| POST | `/api/v1/auth/login` | 登录，返回 JWT | 否 |
| GET | `/api/v1/auth/me` | 当前用户信息 | 是 |

</details>

<details open>
<summary><b>关卡</b></summary>

| 方法 | 路径 | 说明 | 认证 |
|---|---|---|---|
| GET | `/api/v1/levels` | 关卡列表（`category`/`difficulty`/`keyword` 筛选） | 可选 |
| GET | `/api/v1/levels/{id}` | 关卡详情（含已解锁提示） | 可选 |
| POST | `/api/v1/levels/{id}/submit` | 提交 flag | 是 |
| POST | `/api/v1/levels/{id}/hint/{index}` | 解锁一条提示 | 是 |

</details>

<details open>
<summary><b>用户与排行</b></summary>

| 方法 | 路径 | 说明 | 认证 |
|---|---|---|---|
| GET | `/api/v1/leaderboard` | 排行榜 | 可选 |
| GET | `/api/v1/me/profile` | 我的主页（含徽章） | 是 |
| GET | `/api/v1/users/{username}` | 他人公开主页 | 否 |
| GET | `/api/v1/progress` | 我的通关记录 | 是 |

</details>

<details>
<summary><b>管理后台</b>（需管理员）</summary>

| 方法 | 路径 | 说明 |
|---|---|---|
| GET | `/api/v1/admin/stats` | 答题统计 |
| GET | `/api/v1/admin/levels` | 关卡列表（含 flag 明文） |
| POST | `/api/v1/admin/levels` | 新增/覆盖关卡 |
| DELETE | `/api/v1/admin/levels/{id}` | 删除自定义关卡 |
| GET | `/api/v1/admin/users` | 用户列表 |

</details>

<details>
<summary><b>压轴关 L37</b></summary>

| 方法 | 路径 | 说明 | 认证 |
|---|---|---|---|
| GET | `/api/v1/finale/briefing` | 任务简报 | 否 |
| GET | `/api/v1/finale/progress` | 我的阶段进度 | 可选 |
| GET | `/api/v1/finale/legacy/employees` | 阶段1：员工名录 | 可选 |
| POST | `/api/v1/finale/login` | 阶段2：门户登录（存在注入） | 可选 |
| GET | `/api/v1/finale/admin` | 阶段3：管理员面板 | 可选 |
| POST | `/api/v1/finale/health-check` | 阶段4：健康检查（SSRF） | 可选 |
| POST | `/api/v1/finale/archive/search` | 阶段5：档案检索（XXE） | 可选 |
| GET | `/api/v1/finale/archive/destroy/preview` | 阶段6：销毁预览 | 否 |
| POST | `/api/v1/finale/archive/destroy` | 阶段6：执行销毁 | 是 |

</details>

### 调用示例

```bash
BASE=http://127.0.0.1:8899

# 注册并保存 token
TOKEN=$(curl -s -X POST $BASE/api/v1/auth/register \
  -H 'Content-Type: application/json' \
  -d '{"username":"alice","password":"secret123"}' \
  | python -c "import sys,json;print(json.load(sys.stdin)['data']['token'])")

# 获取关卡列表
curl -s $BASE/api/v1/levels -H "Authorization: Bearer $TOKEN"

# 提交 flag
curl -s -X POST $BASE/api/v1/levels/L01/submit \
  -H "Authorization: Bearer $TOKEN" \
  -H 'Content-Type: application/json' \
  -d '{"flag":"flag{html_comment_leak}"}'
```

---

## 🏗️ 架构说明

### 前后端分离

```
┌──────────────────────────────────────────────────────────┐
│  浏览器                                                   │
│  ┌────────────────────────────────────────────────────┐  │
│  │  React SPA (Vite 构建)                              │  │
│  │  · BrowserRouter 客户端路由                         │  │
│  │  · fetch 调用 REST API（所有数据交互）              │  │
│  │  · JWT 存 localStorage，请求带 Authorization 头     │  │
│  └───────────────────────┬────────────────────────────┘  │
└──────────────────────────┼───────────────────────────────┘
                           │  JSON over HTTP
                           │  /api/v1/*
                           ▼
┌──────────────────────────────────────────────────────────┐
│  FastAPI 后端                                             │
│  ┌────────────────────────────────────────────────────┐  │
│  │  路由层  auth / levels / users / admin / sim        │  │
│  ├────────────────────────────────────────────────────┤  │
│  │  统一响应层  { code, message, data } + 全局异常处理 │  │
│  ├────────────────────────────────────────────────────┤  │
│  │  业务层  关卡注册表 · flag 校验(HMAC) · 计分 · 徽章  │  │
│  ├────────────────────────────────────────────────────┤  │
│  │  ⚠️ 模拟沙箱层（安全边界核心）                      │  │
│  │  虚拟文件树 · 假命令回显 · 假SQL结果集 · SSRF白名单 │  │
│  │  正则XXE · 假反序列化 · 内存上传                    │  │
│  ├────────────────────────────────────────────────────┤  │
│  │  数据层  SQLite（sqlite3 标准库，参数化查询）       │  │
│  └────────────────────────────────────────────────────┘  │
│                                                            │
│  netlab 仿真服务（可选，独立线程）                         │
│  FTP:2121 · MySQL:3306 · Redis:6379 · Debug:31337         │
│  ⚠️ 仅监听 127.0.0.1，只回预置静态文本，零出站连接         │
└──────────────────────────────────────────────────────────┘
```

### 部署模式

**同域部署（默认）**
前端构建产物由 FastAPI 托管，API 走相对路径 `/api/v1/...`，无跨域问题。

**分离部署**
前端设 `VITE_API_BASE=https://api.example.com` 后重新构建；
后端设 `ATF_CORS_ORIGINS` 允许前端域名。

### 安全设计要点

| 关注点 | 实现 |
|---|---|
| 口令存储 | PBKDF2-HMAC-SHA256，20 万轮，16 字节随机盐 |
| 口令比对 | `hmac.compare_digest` 恒定时间比较 |
| flag 存储 | 带 pepper 的 HMAC-SHA256 摘要，**明文绝不下发前端** |
| flag 校验 | `hmac.compare_digest` 恒定时间比较 |
| SQL | 全部参数化绑定，无字符串拼接 |
| Token | JWT（HS256），含 `aud` / `iss` / `exp` 校验 |
| 关卡解锁 | 服务端校验，不信任前端状态 |

---

## ⚙️ 配置项

所有配置通过环境变量注入，完整清单见 [`.env.example`](.env.example)。

| 变量 | 默认值 | 说明 |
|---|---|---|
| `ATF_HOST` | `0.0.0.0` | 监听地址（建议本地用 `127.0.0.1`） |
| `ATF_PORT` | `8899` | 服务端口 |
| `ATF_DEBUG` | `0` | 调试模式 |
| `ATF_DB_PATH` | `data/atf.db` | SQLite 路径 |
| `ATF_SECRET_KEY` | `atf-lab-dev-secret-change-me` | **JWT 密钥，生产务必修改** |
| `ATF_TOKEN_TTL` | `604800` | token 有效期（秒） |
| `ATF_ADMIN_USER` | 空 | 预置管理员用户名（可留空） |
| `ATF_ADMIN_PASSWORD` | 空 | 预置管理员密码（可留空） |
| `ATF_CORS_ORIGINS` | `*` | 允许的跨域来源，逗号分隔 |
| `ATF_FRONTEND_DIST` | `frontend/dist` | 前端产物目录 |
| `ATF_NETLAB_ENABLED` | `1` | 是否启用仿真网络服务 |
| `ATF_NETLAB_*_PORT` | 2121/3306/6379/31337 | 各仿真服务端口 |

生成安全密钥：

```bash
openssl rand -hex 32
# 或
python -c "import secrets;print(secrets.token_hex(32))"
```

> 💡 **端口回退**：若系统已占用 3306 / 6379（例如本机装了 MySQL / Redis），
> 仿真服务会自动回退到 13306 / 16379。实际端口可在 `/api/v1/health` 查看。

---

## 🐳 部署

### Docker Compose

```bash
docker compose up --build        # 前台运行
docker compose up --build -d     # 后台运行
docker compose logs -f           # 查看日志
docker compose down              # 停止
docker compose down -v           # 停止并删除数据卷
```

数据通过命名卷 `atf-data` 持久化，容器重建不丢进度。

### 环境变量覆盖

```bash
# 方式一：.env 文件（docker compose 自动读取）
cp .env.example .env
vim .env

# 方式二：命令行
ATF_SECRET_KEY=$(openssl rand -hex 32) docker compose up --build
```

### 安全提示

`docker-compose.yml` 中所有端口都绑定在 `127.0.0.1`，**不对外网暴露**。
这是刻意的设计，符合本项目「禁止公网部署」的约定。

### 常见问题：Docker 报「Virtualization support not detected」

Windows 上首次运行 Docker Desktop 时可能遇到：

```
Virtualization support not detected
Docker Desktop failed to start because virtualisation support wasn't detected.
```

**原因**：这不是 CPU 不支持虚拟化，而是 Windows 的**虚拟机平台**与 **Hyper-V** 功能未启用。

先确认 CPU 层面是否就绪（管理员 PowerShell）：

```powershell
Get-CimInstance Win32_Processor |
  Select-Object Name, VirtualizationFirmwareEnabled, VMMonitorModeExtensions
```

若两项均为 `True`，说明 CPU 没问题，只需启用 Windows 功能：

```powershell
# 管理员 PowerShell 执行
dism /online /enable-feature /featurename:VirtualMachinePlatform /all /norestart
dism /online /enable-feature /featurename:Microsoft-Hyper-V-All /all /norestart
```

检查功能状态（`InstallState` 为 `2` 表示已禁用）：

```powershell
Get-CimInstance Win32_OptionalFeature |
  Where-Object { $_.Name -match 'Hyper-V-All|VirtualMachinePlatform' } |
  Select-Object Name, InstallState
```

**然后必须重启电脑** —— 内核级功能不重启不生效。
重启后再确认 BIOS 中 `SVM Mode`（AMD）或 `Intel VT-x` 已开启。

### 替代方案：不用 Docker

若无法启用虚拟化，可直接本地运行（无需 Docker）：

```bash
# macOS / Linux
./start.sh

# Windows
start.bat
```

或手动启动：

```bash
pip install -r backend/requirements.txt
cd frontend && npm install && npm run build && cd ..
python -m uvicorn backend.main:app --host 127.0.0.1 --port 8899
```

> 本项目的所有自动化验证（冒烟测试 50 项、验收核验 49 项等）
> 都是在**不使用 Docker** 的情况下通过本地运行完成的，
> 因此即使 Docker 不可用，平台功能依然完整可用。

### 已知限制：宿主端口冲突与仿真服务转发

在 Windows + Docker Desktop（WSL2 后端）环境下实测发现两个问题，
**均不影响主服务与全部关卡功能**，但会影响仿真网络服务的宿主访问：

#### ① 宿主端口冲突

若本机已安装 MySQL / Redis，会占用 3306 / 6379，导致容器端口映射失败。
此外 Windows 启用 Hyper-V/WSL 后会保留部分端口段（如 `2061-2160`），
落在保留区间的端口无法绑定。

`docker-compose.yml` 已默认规避：

| 服务 | 容器内端口 | 宿主默认端口 | 原因 |
|---|---:|---:|---|
| 仿真 FTP | 2121 | **12121** | 2121 落在 Windows 保留区间 2061-2160 |
| 仿真 MySQL | 3306 | **13306** | 避开宿主真实 MySQL |
| 仿真 Redis | 6379 | **16379** | 避开宿主真实 Redis |
| 仿真调试 | 31337 | 31337 | 无冲突 |

查看本机保留端口段：

```powershell
netsh interface ipv4 show excludedportrange protocol=tcp
```

#### ② 仿真服务端口在宿主不可达（Docker Desktop 限制）

实测现象：容器内 4 个仿真服务**全部正常**，宿主 HTTP 主服务（8899）**正常**，
但宿主经端口映射访问裸 TCP 仿真端口时连接被立即重置（WinError 10053）。

这是 Docker Desktop for Windows 在 WSL2 后端下转发**非 HTTP 裸 TCP 长连接**
时的已知限制，与本项目代码无关。

**因此，如果你需要练习 `nmap` / `nc` / `redis-cli` 等工具连接仿真服务，
请使用本地运行方式而不是 Docker：**

```bash
./start.sh          # macOS / Linux
start.bat           # Windows
```

本地运行时仿真服务直接监听 `127.0.0.1`，`nmap 127.0.0.1`、
`nc 127.0.0.1 6379` 等均可正常工作。

> **Docker 模式适合**：快速体验平台、验证关卡逻辑、分享给他人。
> **本地模式适合**：网络渗透关卡（L27–L33）的实操练习。

### Docker 模式实测结果

| 项目 | 结果 |
|---|---|
| 镜像构建 | ✅ 通过（多阶段构建） |
| 容器启动 | ✅ `Up (healthy)` |
| 健康检查 | ✅ 通过 |
| SPA 全部路由 | ✅ 200 |
| 冒烟测试 50 项 | ✅ 通过 |
| 验收核验 49 项 | ✅ 通过 |
| 容器内 netlab 四服务 | ✅ 正常 |
| 宿主访问 netlab 裸 TCP | ⚠️ 连接被重置（Docker Desktop 限制，见上） |

---

## 🚀 发布到 GitHub

### 前置：安装 GitHub CLI

```bash
# macOS
brew install gh

# Windows
winget install --id GitHub.cli

# Linux
sudo apt install gh          # Debian/Ubuntu
```

登录：

```bash
gh auth login
```

### 首次发布

```bash
# 1. 初始化仓库
git init
git add .
git commit -m "feat: ATF Lab 安全教学靶场 v2.0.0-rc1

- 前后端分离架构：FastAPI 后端 + React SPA 前端
- 37 个关卡：Web安全15 / 密码学6 / 取证5 / 网络渗透7 / 逆向3 / 压轴1
- 完整账号体系：注册登录、JWT 鉴权、PBKDF2 口令哈希
- 进度入库跨设备同步、排行榜、9 种成就徽章
- 管理后台：关卡增删改、答题统计、用户列表
- 仿真网络服务：FTP/MySQL/Redis/Debug，仅回静态文本
- 压轴关 L37「REAPER 行动」六阶段模拟攻击链
- Docker 一键部署 + 三平台启动脚本
- 全部漏洞为受控模拟，无任何真实攻击能力"

# 2. 创建仓库并推送
gh repo create ATF-Lab --private --source=. --remote=origin --push
```

> [!IMPORTANT]
> **强烈建议使用 `--private`（私有仓库）。**
>
> 如果选择公开（`--public`），**必须**：
> 1. 在仓库 Description 中写明：`⚠️ 安全教学靶场，所有漏洞均为受控模拟，禁止公网部署`
> 2. 确认 README 顶部的免责声明未被删除
> 3. 确认没有把 `.env` 提交上去（`.gitignore` 已排除）
>
> 公开仓库命令：
> ```bash
> gh repo create ATF-Lab --public --source=. --remote=origin --push \
>   --description "⚠️ 安全教学靶场（受控模拟），禁止公网部署 | Educational CTF lab, simulations only, do NOT deploy publicly"
> ```

### 后续更新

```bash
git add .
git commit -m "feat: 描述本次改动"
git push
```

**规范提交信息格式**：

| 前缀 | 用途 | 示例 |
|---|---|---|
| `feat:` | 新功能 | `feat: 新增 5 个密码学关卡` |
| `fix:` | 修复缺陷 | `fix: 修正 L12 上传绕过的判定逻辑` |
| `docs:` | 文档变更 | `docs: 补充 API 文档示例` |
| `refactor:` | 重构 | `refactor: 抽取模拟沙箱为独立模块` |
| `style:` | 格式调整 | `style: 统一前端缩进` |
| `test:` | 测试相关 | `test: 补充冒烟测试用例` |
| `chore:` | 构建/工具 | `chore: 升级 FastAPI 依赖` |

---

## 📁 项目结构

```
ATF_sever/
├── README.md                    # 本文档（顶部含免责声明）
├── LICENSE                      # 含同等限制性条款
├── .gitignore
├── .env.example                 # 环境变量模板
├── Dockerfile                   # 多阶段构建
├── docker-compose.yml
├── start.sh / start.bat / start.command   # 三平台启动脚本
│
├── backend/                     # ── 后端 ──
│   ├── main.py                  # FastAPI 入口、统一响应、SPA 托管
│   ├── config.py                # 环境变量配置
│   ├── database.py              # SQLite 封装、建表、seed
│   ├── security.py              # PBKDF2 口令哈希 + JWT
│   ├── responses.py             # 统一响应格式与错误码
│   ├── deps.py                  # 依赖注入（当前用户/管理员）
│   ├── requirements.txt
│   │
│   ├── routers/                 # 路由层
│   │   ├── auth.py              #   注册/登录/me
│   │   ├── levels.py            #   关卡列表/详情/提交/提示
│   │   ├── users.py             #   排行榜/主页/徽章
│   │   ├── admin.py             #   管理后台
│   │   └── sim.py               #   模拟交互 + 压轴关
│   │
│   └── challenges/              # 关卡层
│       ├── base.py              #   Level 基类 + 注册表
│       ├── sandbox.py           #   ⚠️ 模拟沙箱（安全边界核心）
│       ├── web.py               #   L01-L15
│       ├── crypto.py            #   L16-L21
│       ├── forensics.py         #   L22-L26
│       ├── network.py           #   L27-L33
│       ├── misc.py              #   L34-L36
│       ├── finale.py            #   ⚠️ L37 六阶段攻击链
│       └── finale_level.py      #   L37 关卡定义
│
├── frontend/                    # ── 前端 ──
│   ├── package.json
│   ├── vite.config.js
│   ├── index.html
│   └── src/
│       ├── main.jsx  App.jsx  api.js  store.jsx
│       ├── theme.css            #   深浅色主题
│       ├── disclaimer.js        #   免责声明文本（单一来源）
│       ├── components/Common.jsx
│       └── pages/               #   Landing/Levels/LevelDetail/
│                                #   Finale/Login/Register/Profile/
│                                #   Leaderboard/Admin/About/ApiDocs/404
│
├── netlab/                      # ── 仿真网络服务 ──
│   └── services.py              #   ⚠️ 仅回静态文本、仅监听回环
│
├── docs/
│   └── API.md                   # 完整 API 文档
│
└── scripts/                     # ── 开发/测试脚本 ──
    ├── smoke_test.py            #   端到端冒烟测试（50 项）
    ├── check_netlab.py          #   仿真服务验证 + 安全边界自查
    └── lint.py                  #   源码编译自检
```

---

## 📄 许可与限制

本项目采用**限制性教学许可**，详见 [`LICENSE`](LICENSE)。

**核心限制**：

1. 仅供**本地环境下的安全学习、教学演示与技术研究**使用
2. **严禁**部署于可被公众访问的网络环境
3. **严禁**用于未经授权的渗透测试
4. **严禁**移除 LICENSE 与 README 中的限制性条款
5. **严禁**用于商业用途

---

<div align="center">

**⚠️ 再次提醒：本项目仅供教学演示，请勿在互联网上公开发布、部署或传播。**

Made with ❤️ for security learners

</div>
