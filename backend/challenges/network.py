"""
ATF Lab - 网络渗透赛道（L27-L33）

⚠️ 仅供教学演示（EDUCATIONAL USE ONLY）
本模块的仿真服务只返回预置静态文本，不建立任何出站连接、不做端口转发。
"""

from .base import Level, registry
from . import sandbox as sb

CAT = "网络渗透"


def register() -> None:
    L = [
        Level(
            id="L27", name="端口在低语", category=CAT, difficulty=1, points=50,
            objective="对目标主机做端口扫描，找出开放的可疑端口，flag 在其中。",
            hints=[
                "nmap 是最常用的端口扫描工具。",
                "全端口扫描：nmap -p- 目标；快速扫描：nmap -F 目标。",
                "本靶场的仿真服务开在 2121 / 3306 / 6379 / 31337，试试 31337。",
            ],
            writeup="""端口扫描是渗透测试的第一步。常见扫描类型：

- **TCP connect（-sT）**：完整三次握手，无需特权，易被记录
- **TCP SYN（-sS）**：半开扫描，更快更隐蔽，需要 root
- **UDP（-sU）**：慢但能发现 DNS 与 SNMP 等服务

端口状态：open（有服务）、closed（无服务但可达）、filtered（被防火墙拦截）。

**防御**：最小化暴露面，只开必要端口；用防火墙限制来源；对外服务放在 DMZ。

> ⚠️ 本靶场的仿真服务仅返回静态文本，不对真实网络发起任何连接。请只对自己拥有授权的目标做扫描。""",
            flag="flag{port_31337_debug}",
            tags=["端口扫描", "nmap"],
        ),
        Level(
            id="L28", name="服务的指纹", category=CAT, difficulty=2, points=80,
            objective="对开放端口做服务版本识别，确认某端口上运行的服务及其版本。",
            hints=[
                "nmap -sV 会主动探测服务类型与版本。",
                "也可以直接用 nc 连接，看服务的欢迎横幅（banner）。",
                "nc 127.0.0.1 6379 然后发 INFO 命令看看。",
            ],
            writeup="""服务识别（Service Fingerprinting）确定端口上跑的是什么服务、什么版本。

**方法**：

- **Banner Grabbing**：连接后读取服务主动发送的欢迎信息
- **主动探测**：发送特定协议请求，观察响应特征
- **nmap -sV**：结合多种探测探针与特征库

拿到精确版本后，可查 CVE 找已知漏洞 —— 这是漏洞利用的前置步骤。

**防御**：隐藏或伪造 banner（如 SSH 的 DebianBanner no）；及时打补丁，不依赖「隐藏版本」作为安全措施。""",
            flag="flag{service_banner_redis}",
            tags=["服务识别", "Banner"],
        ),
        Level(
            id="L29", name="redis 没关门", category=CAT, difficulty=3, points=120,
            objective="一个 Redis 服务未设密码且暴露在公网。连接它并读取其中的 flag。",
            hints=[
                "redis-cli -h 目标 -p 6379 可以直接连接。",
                "未授权时无需 AUTH，试试 INFO 或 KEYS 星号。",
                "拿到 key 后用 GET 读取值。本靶场仿真服务在 6379 端口。",
            ],
            writeup="""Redis 未授权访问是极其常见的严重漏洞：

**成因**：Redis 默认无密码，且默认监听 0.0.0.0，很多部署直接暴露到公网。

**危害升级路径**：

1. 直接读写数据，窃取敏感信息
2. 写入 SSH 公钥到 authorized_keys → 直接登录服务器
3. 写 crontab 计划任务 → 反弹 shell
4. 写 WebShell 到网站目录 → 控制 Web 应用
5. 主从复制加模块加载 → 直接 RCE

**防御**：

- 设置强密码 requirepass
- bind 127.0.0.1 只监听本地，或严格限制来源 IP
- 重命名或禁用危险命令（CONFIG、FLUSHALL、EVAL）
- 以低权限用户运行，配合 rename-command

**真实案例**：多起大规模数据泄露源于暴露的 Redis、MongoDB、Elasticsearch。

> ⚠️ 本靶场的 6379 是仿真服务，只返回预置静态文本，不实现任何真实 Redis 协议。""",
            flag="flag{redis_unauthorized_access}",
            tags=["未授权", "Redis"],
        ),
        Level(
            id="L30", name="备份文件的疏忽", category=CAT, difficulty=2, points=100,
            objective="网站根目录下遗留了一个备份文件，下载并从中找到 flag。",
            hints=[
                "常见备份文件名：www.zip、backup.tar.gz、index.php.bak、.index.php.swp。",
                "可以用 dirsearch 或 gobuster 做目录爆破。",
                "本靶场模拟路径：/backup/helios_www.zip",
            ],
            writeup="""备份文件泄露是高频问题。常见命名规律：

- www.zip、web.tar.gz、site.rar
- index.php.bak、.bak、.old、.orig、.save
- .index.php.swp、.swo（Vim 交换文件）
- ~index.php（编辑器临时文件）
- .git/、.svn/、.DS_Store
- database.sql、dump.sql

**危害**：源码泄露暴露逻辑漏洞与硬编码凭据；SQL 备份直接暴露全部数据；.git 可还原完整源码历史。

**防御**：部署时清理临时文件；Web 服务器禁止访问备份扩展名；CI/CD 流程加入文件检查。""",
            flag="flag{backup_file_exposed}",
            tags=["信息泄露", "目录爆破"],
            handler=lambda ctx: sb.sim({
                "discovered": [
                    {"path": "/backup/helios_www.zip", "status": 200, "size": 2048576},
                    {"path": "/backup/db_dump.sql", "status": 403, "size": 0},
                    {"path": "/.git/config", "status": 404, "size": 0},
                ],
                "archive_listing": [
                    "index.php", "config/database.php", "README.md", "flag.txt",
                ],
                "flag_txt_content": "flag{backup_file_exposed}",
            }),
        ),
        Level(
            id="L31", name="请求头伪装", category=CAT, difficulty=3, points=120,
            objective="一个管理接口只允许内网访问，通过伪造请求头绕过限制。",
            hints=[
                "服务端判断来源时可能依赖 X-Forwarded-For 或 X-Real-IP。",
                "这些头部由客户端提供，完全可以伪造。",
                "试试添加 X-Forwarded-For: 127.0.0.1。",
            ],
            writeup="""基于请求头的访问控制是**不可靠的**，因为 HTTP 头完全由客户端控制。

常被滥用的头部：

- X-Forwarded-For、X-Real-IP、X-Client-IP
- X-Originating-IP、X-Remote-Addr
- Referer（用于「只能从本站访问」的判断）
- User-Agent（用于「只有手机客户端能访问」）

**正确做法**：

- 网络层控制：用防火墙、安全组或 VPN 限制来源
- 代理层控制：只在可信反向代理处设置并**剥离**客户端传入的同名头
- 应用层控制：基于认证与授权，而不是基于来源 IP

**注意**：反向代理配置不当（如 Nginx 用 proxy_add_x_forwarded_for 保留了客户端伪造的前缀）会导致应用取到错误的「真实 IP」。""",
            flag="flag{header_spoofing_bypass}",
            tags=["请求头伪造", "访问控制"],
            handler=lambda ctx: sb.sim({
                "access_control": "仅允许来自 127.0.0.1 的请求",
                "received_headers": {
                    "X-Forwarded-For": ctx.get("xff", "(未提供)"),
                    "X-Real-IP": ctx.get("xri", "(未提供)"),
                },
                "verdict": "服务端信任了客户端提供的头部",
                "granted": bool(ctx.get("xff") or ctx.get("xri")),
                "flag_on_success": "flag{header_spoofing_bypass}",
            }),
        ),
        Level(
            id="L32", name="Basic 认证的倔强", category=CAT, difficulty=4, points=150,
            objective="一个后台使用 HTTP Basic 认证且密码很弱，爆破它拿到 flag。",
            hints=[
                "Basic 认证格式是 Authorization 头加 Basic 加 base64(用户名:密码)。",
                "可以用 hydra 或 ffuf 做 HTTP Basic 爆破。",
                "用户名 admin，密码是常见弱口令之一。",
            ],
            writeup="""HTTP Basic 认证的问题：

1. **凭据只做 Base64**，不是加密 —— 明文等价，必须依赖 HTTPS
2. **每次请求都发送凭据**，容易在日志、代理、Referer 中泄露
3. **没有内置防爆破机制**，可无限次尝试
4. **无法单独登出**，除非关闭浏览器
5. **无 CSRF 防护**，浏览器会自动带上凭据

**爆破方法**：

```bash
hydra -l admin -P rockyou.txt target http-get /admin
ffuf -w pass.txt:PASS -u https://target/ -H "Authorization: Basic ..."
```

**防御**：改用基于会话或 Token 的认证；必须用 Basic 时强制 HTTPS 加强密码加登录频率限制加 MFA。

> ⚠️ 仅可用于你拥有明确授权的目标。未经授权的爆破在多数司法辖区构成违法。""",
            flag="flag{basic_auth_bruteforced}",
            tags=["认证爆破", "Basic"],
        ),
        Level(
            id="L33", name="配置错误的服务", category=CAT, difficulty=4, points=150,
            objective="一台服务器开放的调试端口暴露了内部配置，从中找到 flag。",
            hints=[
                "调试接口常常忘记在生产环境关闭。",
                "试试访问 /debug、/actuator、/__debug__、/console 等路径。",
                "本靶场仿真调试服务在 31337 端口，配置里有 flag。",
            ],
            writeup="""服务配置错误是最普遍的问题之一。常见类型：

- **调试模式开启**：Flask 或 Django 的 DEBUG=True 会暴露堆栈与交互式调试器；Spring Boot Actuator 未授权可读 /env、/heapdump
- **目录列表开启**：Nginx autoindex on 暴露全部文件
- **默认凭据未改**：admin/admin、tomcat/tomcat
- **CORS 配置过宽**：Access-Control-Allow-Origin 设为星号且允许凭据
- **错误页泄露**：详细堆栈暴露路径、框架版本、SQL 语句
- **云存储桶公开**：S3 或 OSS 权限设为 public-read

**防御**：生产环境关闭所有调试功能；建立配置基线并做自动化合规检查；使用容器镜像扫描与 CIS Benchmark 核查。""",
            flag="flag{debug_service_misconfig}",
            tags=["配置错误", "调试接口"],
        ),
    ]
    for lv in L:
        registry.add(lv)
