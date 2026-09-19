# ATF Lab 公网部署安全清单

> ⚠️ **免责声明**
> 本项目是一个 **API 调动的** 学习与演示项目，**仅供本人自行娱乐与安全学习使用**。
> **请勿在互联网上公开发布、部署或传播**。
> 若因违反本约定造成任何后果，由使用者自行承担。

---

## 重要：先读这一段

你在 README 第 1 行、网站每页页脚、首访弹窗、LICENSE 里都写了同一句话：

> **请勿在互联网上公开发布、部署或传播**

**公网部署与这条约定直接冲突。** 这份文档的存在不是鼓励你这么做，而是：
如果你确实要这么做，至少要知道必须做对哪些事，否则风险由你独自承担。

本文档列出**技术上必须完成**的加固项。跳过任何一项都可能让你和你的用户受损。

---

## 一、上线前必须完成（P0）

### 1. 设置强密钥

默认密钥是公开的（写在配置文件里），任何人都能用它伪造 JWT 冒充管理员。

```bash
# 生成
python -c "import secrets;print(secrets.token_hex(32))"
```

写入 `.env`：

```ini
ATF_SECRET_KEY=<粘贴生成的值>
```

**验证**：启动日志不应再出现 `⚠️ 安全警告：ATF_SECRET_KEY 使用了默认值`。

> 本项目会在启动时检查密钥强度并打印醒目警告，但那只是提醒，不会阻止启动。

### 2. 配置 CORS 白名单

```ini
# ❌ 不要留 *
ATF_CORS_ORIGINS=https://your-domain.com
```

### 3. 启用 HTTPS

本项目**只监听 HTTP**，TLS 必须由反向代理终止。

Nginx 示例：

```nginx
server {
    listen 443 ssl http2;
    server_name your-domain.com;

    ssl_certificate     /etc/letsencrypt/live/your-domain.com/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/your-domain.com/privkey.pem;
    ssl_protocols       TLSv1.2 TLSv1.3;

    # HSTS：确认 HTTPS 正常后再开启
    add_header Strict-Transport-Security "max-age=31536000; includeSubDomains" always;

    location / {
        proxy_pass http://127.0.0.1:8899;
        proxy_set_header Host              $host;
        proxy_set_header X-Real-IP         $remote_addr;
        # ⚠️ 关键：用 $remote_addr 覆盖，不要用 $proxy_add_x_forwarded_for
        #    后者会保留客户端伪造的前缀，导致 IP 伪造
        proxy_set_header X-Forwarded-For   $remote_addr;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}

server {
    listen 80;
    server_name your-domain.com;
    return 301 https://$host$request_uri;
}
```

### 4. 换掉初始管理员密码

首次启动会在日志里打印初始管理员账号。**登录后第一件事就是改密。**

未改密时，站内每页顶部都会显示红色警示横幅，改密后消失。

---

## 二、强烈建议（P1）

### 5. 只暴露 8899，不要映射仿真服务

`docker-compose.yml` 中四个仿真服务端口（FTP/MySQL/Redis/Debug）**建议整段注释掉**：

```yaml
ports:
  - "${ATF_BIND:-127.0.0.1}:8899:8899"
  # 公网部署：以下全部注释
  # - "${ATF_HOST_FTP_PORT:-12121}:2121"
  # - "${ATF_HOST_MYSQL_PORT:-13306}:3306"
  # - "${ATF_HOST_REDIS_PORT:-16379}:6379"
  # - "${ATF_HOST_DEBUG_PORT:-31337}:31337"
```

它们只返回预置静态文本，暴露出去无实际危害，但会：
- 让扫描器把你的站标记为「有可疑开放端口」
- 增加被误判为真实服务攻击面的概率

### 6. 限制注册

本项目默认开放注册。公网部署建议二选一：

- **关闭注册**：改 `backend/routers/auth.py` 的 `/register`，加邀请码校验
- **保持开放但限流**：在反向代理层对 `/api/v1/auth/register` 做 IP 限流

### 7. 反向代理层限流

应用层已有**账号级**登录锁定（连续 5 次失败锁 15 分钟），
但攻击者可以换账号名持续尝试。建议在 Nginx 加 IP 级限流：

```nginx
limit_req_zone $binary_remote_addr zone=login:10m rate=5r/m;
limit_req_zone $binary_remote_addr zone=api:10m   rate=30r/s;

location /api/v1/auth/login    { limit_req zone=login burst=3 nodelay; proxy_pass http://127.0.0.1:8899; }
location /api/v1/auth/register { limit_req zone=login burst=2 nodelay; proxy_pass http://127.0.0.1:8899; }
location /api/                 { limit_req zone=api   burst=60;        proxy_pass http://127.0.0.1:8899; }
```

### 8. 数据备份

SQLite 数据在 Docker 卷 `atf-data` 中。定期备份：

```bash
docker run --rm -v atf_sever_atf-data:/data -v $(pwd):/backup \
  alpine tar czf /backup/atf-backup-$(date +%F).tar.gz -C /data .
```

**同时妥善保管** `.env` 中的 `ATF_SECRET_KEY`——丢失后已签发的 JWT 全部失效，
且 flag 校验的 pepper 也会变化。

---

## 三、账号恢复机制（替代"后门密码"）

本项目**刻意不提供**任何通用后门密码。忘记密码时有两条正当途径：

### 途径 A：一次性恢复码（用户自助）

- 注册时自动生成，格式 `XXXX-XXXX-XXXX-XXXX`
- **只在生成时显示一次**，数据库只存 PBKDF2 哈希
- 在登录页「忘记密码」使用
- **用一次即失效**，重置后自动下发新码

### 途径 B：命令行工具（管理员本地操作）

需要**服务器 shell 权限**——这是天然的权限边界。

```bash
# 查看所有用户
python -m backend.admin list-users

# 重置某用户密码（随机生成）
python -m backend.admin reset-password --user admin

# 指定新密码
python -m backend.admin reset-password --user admin --password 'NewStrongPass123'

# 重新生成恢复码（旧的立即失效）
python -m backend.admin show-recovery --user admin

# 解除登录锁定
python -m backend.admin unlock --user admin

# 查看审计日志
python -m backend.admin audit --limit 50
```

Docker 环境：

```bash
docker compose exec atf-lab python -m backend.admin reset-password --user admin
```

---

## 四、安全检查清单

上线前逐项确认：

| # | 检查项 | 如何确认 |
|---|---|---|
| 1 | `ATF_SECRET_KEY` 已改为强随机值 | 启动日志无密钥警告 |
| 2 | `ATF_CORS_ORIGINS` 不是 `*` | 检查 `.env` |
| 3 | HTTPS 已启用 | 浏览器显示锁图标 |
| 4 | HSTS 已启用 | `curl -I https://域名` 有 `Strict-Transport-Security` |
| 5 | 初始管理员密码已修改 | 站内无红色警示横幅 |
| 6 | 仿真服务端口未暴露公网 | `nmap 域名` 只见 443/80 |
| 7 | 反向代理限流已配置 | 快速请求登录接口会被 503 |
| 8 | 数据备份已设置 | 手动跑一次备份命令 |
| 9 | 已阅读并接受免责声明 | —— |

### 自动核验

```bash
# 账号安全（32 项）
python scripts/test_auth.py

# 安全边界（AST 级扫描）
python scripts/audit_safety.py

# 全量验收（49 项）
python scripts/acceptance.py
```

---

## 五、本项目的安全设计（已实现）

这些是代码层面已经做好的，公网部署时无需额外配置：

| 项目 | 实现 |
|---|---|
| 口令存储 | PBKDF2-HMAC-SHA256，20 万轮 + 16 字节随机盐 |
| 口令比对 | `hmac.compare_digest` 恒定时间比较 |
| 登录防爆破 | 连续 5 次失败锁定账号 15 分钟 |
| 账号枚举防护 | 用户不存在与密码错误返回相同错误信息 |
| 密码强度 | 至少 8 位 + 含字母 + 含数字 + 弱口令黑名单 |
| 初始密码提醒 | `must_change_password` 标记 + 全站红色横幅 |
| 恢复码 | 一次性，仅存哈希，用后即失效并自动轮换 |
| 安全响应头 | CSP / X-Frame-Options / X-Content-Type-Options / Referrer-Policy / Permissions-Policy |
| 密钥强度检查 | 启动时检测默认密钥并打印警告 |
| 审计日志 | 登录、改密、恢复、管理员操作全部记录 |
| JWT | HS256 + `aud`/`iss`/`exp` 校验 |

---

## 六、明确不做的事

以下功能**本项目不提供，也不应被添加**：

| ❌ 不做 | 原因 |
|---|---|
| 通用"终极管理员密码" | 这是后门：绕过正常认证、用户不知情、泄露则全部实例沦陷 |
| 把用户密码回传到第三方服务器 | 凭据窃取，无论代码写得多干净 |
| 反取证 / 隐藏回传通道 | 让受害者无法察觉，性质更严重 |
| 真实命令执行 / 任意文件读写 | 见 README「安全边界」章节 |

如果你需要「忘记密码」的应急手段，用上面**第三节**的两条途径——
它们都需要服务器权限或一次性凭据，有边界、有审计、可追溯。

---

<div align="center">

**⚠️ 再次提醒：本项目仅供教学演示，公网部署风险自负。**

</div>
