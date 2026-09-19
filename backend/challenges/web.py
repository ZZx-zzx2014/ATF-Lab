"""
ATF Lab - Web 安全赛道（L01-L15）

⚠️ 仅供教学演示（EDUCATIONAL USE ONLY）
所有漏洞均为受控模拟，flag 均为虚构字符串，不可用于任何真实系统。
"""

from .base import Level, registry
from . import sandbox as sb

CAT = "Web 安全"


def register() -> None:
    L = [
        Level(
            id="L01", name="源码里的注释", category=CAT, difficulty=1, points=50,
            objective="开发者在页面源码中留下了一段注释，里面藏着本关 flag。找到它。",
            hints=[
                "浏览器右键 → 查看网页源代码，留意 HTML 注释。",
                "注释以 <!-- 开头，以 --> 结尾，不会被浏览器渲染出来。",
                "本关的模拟页面在 /api/v1/sim/level/L01/page，直接 GET 它就能看到原始 HTML。",
            ],
            writeup="""信息泄露是最常见的低危漏洞，却常常是渗透测试的突破口。

开发者在调试阶段习惯把测试凭据、内部路径、TODO 备注写进注释或 JS 变量里，上线时忘记清理。攻击者无需任何技术手段，只要查看源码即可获得情报。

**防御**：上线前做静态资源清理；使用构建流程剥离注释；不要把任何凭据写进前端代码。""",
            flag="flag{html_comment_leak}",
            tags=["信息泄露", "源码审计"],
            handler=lambda ctx: sb.sim({
                "html": (
                    "<!doctype html><html><head><title>Helios Portal</title></head><body>\n"
                    "<h1>员工门户</h1>\n"
                    "<!-- TODO: 上线前删掉测试标记 flag{html_comment_leak} -->\n"
                    "<!-- 运维备注：旧接口未下线 -->\n"
                    "</body></html>"
                )
            }),
        ),
        Level(
            id="L02", name="不只是 Base64", category=CAT, difficulty=1, points=50,
            objective="接口返回了一串编码后的字符串，逐层解开它，得到 flag。",
            hints=[
                "先观察字符串的字符集特征，判断可能是哪种编码。",
                "Base64 常见特征是结尾有等号、只含 A-Za-z0-9+/。",
                "解出来可能还是编码，需要重复几次。试试先 Base64 再反转字符串。",
            ],
            writeup="""编码不是加密。Base64 / Hex / URL 编码都只是**表示形式**的转换，没有任何密钥，任何人都能还原。

在 CTF 与真实渗透中，识别编码是基本功：看到 %3D 想到 URL 编码，看到 4a 6b 想到 Hex，看到等号结尾的长串想到 Base64。

**防御**：不要把敏感信息藏在编码里当作保护措施。""",
            flag="flag{encoding_is_not_encryption}",
            tags=["编码", "Base64"],
            handler=lambda ctx: sb.sim({
                "encoded": "fQ==",
                "hint": "先反转再 Base64 解码 —— 或者反过来，自己试。",
            }),
        ),
        Level(
            id="L03", name="响应头会说话", category=CAT, difficulty=2, points=80,
            objective="服务器在 HTTP 响应头里泄露了内部信息，其中包含 flag。",
            hints=[
                "用浏览器开发者工具的 Network 面板查看响应头。",
                "或者直接用命令行：curl -i 查看完整响应。",
                "除了常见的 Server / X-Powered-By，留意自定义的 X- 开头头部。",
            ],
            writeup="""HTTP 响应头经常泄露技术栈与内部信息：

- Server: nginx/1.18.0 → 具体版本，可查已知漏洞
- X-Powered-By: PHP/7.4 → 后端语言与版本
- 自定义头可能暴露内部主机名、调试标记、甚至凭据

**防御**：移除版本号与不必要的自定义头；用 server_tokens off 等配置收敛指纹。""",
            flag="flag{headers_leak_info}",
            tags=["HTTP", "信息泄露"],
            handler=lambda ctx: sb.sim({
                "headers": {
                    "Server": "nginx/1.18.0 (Ubuntu)",
                    "X-Powered-By": "PHP/7.4.3",
                    "X-Debug-Token": "flag{headers_leak_info}",
                    "X-Internal-Host": "helios-app-03.internal",
                }
            }),
        ),
        Level(
            id="L04", name="弱口令管理员", category=CAT, difficulty=2, points=80,
            objective="管理后台使用了一个非常常见的弱口令，猜出它即可登录拿到 flag。",
            hints=[
                "这是安全意识培训中最常被点名的密码。",
                "6 位数字，很多人用来当默认密码。",
                "是 123456 —— 但更重要的是理解为什么它危险。",
            ],
            writeup="""弱口令依旧是入侵的头号入口。常见弱口令：123456、password、admin、qwerty、letmein，以及「公司名+年份」式密码。

攻击者用字典加规则变形（如 P@ssw0rd）做在线/离线爆破，弱口令几乎瞬间被攻破。

**防御**：强制密码复杂度与最小长度；启用 MFA；限制登录尝试频率；对接撞库泄露库做黑名单校验。""",
            flag="flag{weak_password_123456}",
            tags=["弱口令", "认证"],
            handler=lambda ctx: sb.sim({
                "login_form": {"username": "admin", "password": "?"},
                "tip": "POST 到 /api/v1/sim/level/L04/login 试试常见口令。",
            }),
        ),
        Level(
            id="L05", name="登录框的谎言", category=CAT, difficulty=2, points=100,
            objective="登录接口把用户输入直接拼进了 SQL 语句。用注入绕过认证。",
            hints=[
                "在用户名输入框里试试一个单引号，观察报错。",
                "经典 payload 形如单引号 + OR + 恒真条件。",
                "注意闭合引号，并让条件恒真。POST 到 /api/v1/sim/level/L05/login。",
            ],
            writeup="""SQL 注入的成因是把用户输入当作 SQL 代码拼接：

```sql
SELECT * FROM users WHERE username = '$u' AND password = '$p'
```

当 $u 为 `' OR '1'='1` 时，WHERE 条件恒真，返回第一条记录，于是无需正确密码即可登录。

**防御**：使用参数化查询（预编译语句）—— 这是唯一根治手段；配合最小权限数据库账号、输入校验、WAF 兜底。

> ⚠️ 本关为教学模拟：后端用模式匹配判定 payload 并返回预置结果集，不连接任何真实数据库、不执行任何 SQL。""",
            flag="flag{sqli_auth_bypass}",
            tags=["SQL注入", "认证绕过"],
            handler=lambda ctx: sb.fake_sqli(ctx.get("username", "")),
        ),
        Level(
            id="L06", name="逐层向上", category=CAT, difficulty=2, points=100,
            objective="文件读取接口未过滤路径，用上级目录符号穿越读取敏感文件。",
            hints=[
                "参数看起来是文件名，试试传入 ../../etc/passwd。",
                "有时需要 URL 编码：%2e%2e%2f 表示 ../。",
                "目标文件是 /etc/passwd，flag 就在它的内容里。GET /api/v1/sim/level/L06/file?name=...",
            ],
            writeup="""路径穿越（Directory Traversal）源于服务端用用户输入拼接文件路径：

```python
open(BASE_DIR + user_input)   # 危险
```

当 user_input 为 `../../etc/passwd` 时，路径逃逸出预期目录。

**防御**：用 os.path.realpath() 归一化后校验前缀是否在白名单目录内；更稳妥的是用 ID 映射文件名，彻底不接受路径输入。

> ⚠️ 本关为教学模拟：读取的是内存中的虚拟文件树，不触碰真实文件系统。""",
            flag="flag{path_traversal_101}",
            tags=["路径穿越", "文件读取"],
            handler=lambda ctx: sb.vfs_list(ctx.get("name", "")),
        ),
        Level(
            id="L07", name="回显的代价", category=CAT, difficulty=3, points=120,
            objective="一个 ping 工具把用户输入拼进了系统命令。利用它执行额外命令。",
            hints=[
                "试试在 IP 后面加 ; 或 | 再接一条命令。",
                "Linux 下可以用分号、管道符、反引号、$() 分隔命令。",
                "试着执行 id 或 whoami。POST /api/v1/sim/level/L07/ping。",
            ],
            writeup="""命令注入发生在程序把用户输入拼进 shell 命令时：

```python
os.system("ping -c 1 " + user_ip)   # 危险
```

输入 `127.0.0.1; id` 就会额外执行 id。危害取决于服务进程权限 —— 若以 root 运行，等同于交出服务器。

**防御**：避免调用 shell，使用参数数组形式（subprocess.run 配合 shell=False）；对输入做严格白名单校验（如必须是合法 IP）；以最小权限运行服务。

> ⚠️ 本关为教学模拟：后端**不调用任何真实命令执行接口**，仅做模式识别并返回预置回显文本。这是刻意的安全边界。""",
            flag="flag{command_injection_sim}",
            tags=["命令注入", "RCE"],
            handler=lambda ctx: sb.fake_shell(ctx.get("ip", "")),
        ),
        Level(
            id="L08", name="换个身份进门", category=CAT, difficulty=3, points=120,
            objective="用户资料接口只靠 URL 里的 user_id 判断身份，越权读取管理员资料。",
            hints=[
                "先用自己的 ID 访问，看看返回什么结构。",
                "把 user_id 改成 1，观察是否返回了别人的资料。",
                "这叫 IDOR（不安全的直接对象引用）。GET /api/v1/sim/level/L08/profile?user_id=2",
            ],
            writeup="""越权分两类：

- **水平越权**：同级别用户互相访问数据（改 user_id 看别人订单）
- **垂直越权**：低权限用户执行高权限操作（普通用户调管理接口）

成因是服务端**只信任客户端提交的对象标识**，没有校验「这个资源是否属于当前用户」。

**防御**：服务端从会话中取当前用户身份，而不是从请求参数取；每次访问资源都做归属校验；管理接口独立做角色鉴权。

> ⚠️ 本关为教学模拟：数据来自内存中的虚构用户表。""",
            flag="flag{idor_vertical_escalation}",
            tags=["越权", "IDOR"],
            handler=lambda ctx: sb.sim({
                "requested_user_id": ctx.get("user_id"),
                "records": {
                    "1": {"username": "sysadmin", "role": "admin",
                          "secret": "flag{idor_vertical_escalation}"},
                    "2": {"username": "m.chen", "role": "employee", "secret": None},
                },
            }),
        ),
        Level(
            id="L09", name="反射的镜子", category=CAT, difficulty=3, points=120,
            objective="搜索接口把关键词原样输出到 HTML 里。构造 XSS 让脚本执行。",
            hints=[
                "试试搜索 <script>alert(1)</script>。",
                "如果被过滤，可以尝试 <img src=x onerror=alert(1)>。",
                "构造任意能触发 alert(1) 的 payload 即通过。GET /api/v1/sim/level/L09/search?q=...",
            ],
            writeup="""反射型 XSS 的成因是把用户输入未经转义地拼进 HTML：

```html
<div>你搜索了：<?= $q ?></div>   <!-- 危险 -->
```

攻击者构造带恶意脚本的链接，诱导受害者点击，脚本就在受害者浏览器中以该站点的身份执行 —— 可窃取 Cookie、发起 CSRF、篡改页面。

**防御**：输出编码（HTML/JS/URL 上下文各自转义）；配置 CSP 限制脚本来源；对 Cookie 设置 HttpOnly 防止脚本读取。

> ⚠️ 本关为教学模拟：后端只做字符串匹配检测 payload，**不会真的渲染或执行脚本**。""",
            flag="flag{reflected_xss_exec}",
            tags=["XSS", "注入"],
            handler=lambda ctx: sb.sim({
                "query": ctx.get("q", ""),
                "rendered_html": "<div>你搜索了：" + str(ctx.get("q", "")) + "</div>",
                "warning": "以上 HTML 由教学沙箱拼接后原样回显，但不会在真实浏览器执行。",
            }),
        ),
        Level(
            id="L10", name="借刀杀人", category=CAT, difficulty=4, points=150,
            objective="转账接口没有 CSRF token，构造一个自动提交的页面完成非授权转账。",
            hints=[
                "观察转账请求里有没有 CSRF token 或 Referer 校验。",
                "CSRF 利用的是浏览器自动携带 Cookie 的特性。",
                "构造一个自动提交的表单页面，或使用 GET 型接口更简单。POST /api/v1/sim/level/L10/transfer",
            ],
            writeup="""CSRF（跨站请求伪造）利用「浏览器会自动带上目标站 Cookie」这一特性：

1. 受害者已登录 bank.com
2. 受害者访问攻击者页面，页面里藏着自动提交到 bank.com 转账的表单
3. 浏览器自动附带 bank.com 的 Cookie，请求被当作合法操作

**防御**：

- 使用 CSRF Token 并校验（同步器令牌模式）
- 校验 Origin / Referer 头
- Cookie 设置 SameSite=Lax 或 Strict
- 敏感操作要求二次验证

> ⚠️ 本关为教学模拟：转账操作只记录到内存，不涉及任何真实资金或账户。""",
            flag="flag{csrf_token_missing}",
            tags=["CSRF", "逻辑漏洞"],
            handler=lambda ctx: sb.sim({
                "transfer_request": {
                    "to": ctx.get("to", ""),
                    "amount": ctx.get("amount", 0),
                    "csrf_token_present": False,
                },
                "result": "模拟转账已记录（无真实资金流动）",
                "csrf_verdict": "缺少 CSRF 防护，请求可被第三方页面伪造",
            }),
        ),
        Level(
            id="L11", name="让我替你访问", category=CAT, difficulty=4, points=150,
            objective="图片抓取接口可以访问任意 URL，用它探测内网服务获取 flag。",
            hints=[
                "接口参数是一个 URL，试试把外部地址换成内网地址。",
                "常见内网目标：127.0.0.1、169.254.169.254（云元数据）、内网域名。",
                "目标是 http://internal.helios-sim.invalid/archive。POST /api/v1/sim/level/L11/fetch",
            ],
            writeup="""SSRF（服务端请求伪造）让攻击者借服务器的身份发起请求，从而：

- 探测或访问内网服务（绕过防火墙）
- 读取云元数据窃取临时凭据（169.254.169.254）
- 扫描内网端口

**防御**：URL 白名单校验；解析后校验目标 IP 不在内网段（注意 DNS Rebinding）；禁用不必要的协议（file 与 gopher 等）；出网走独立代理并限制目标。

> ⚠️ 本关为教学模拟：**不发起任何真实网络请求**。只有内置的模拟内部端点会返回预置内容，外部地址一律拒绝。""",
            flag="flag{ssrf_internal_reach}",
            tags=["SSRF", "内网探测"],
            handler=lambda ctx: sb.fake_ssrf(ctx.get("url", "")),
        ),
        Level(
            id="L12", name="上传的黑名单", category=CAT, difficulty=4, points=150,
            objective="上传接口用黑名单过滤扩展名，绕过它上传一个可执行脚本。",
            hints=[
                "先判断它是黑名单还是白名单：黑名单可以找「没被列进去」的变体。",
                "PHP 的别名扩展名有 .phtml .php5 .php7 .phar。",
                "也可以试试大小写混写或尾部加点的方式绕过。POST /api/v1/sim/level/L12/upload",
            ],
            writeup="""文件上传漏洞的常见成因与绕过：

**黑名单绕过**：找等价扩展名（.phtml 也能被 PHP 解析）、大小写（.PHP）、尾部加点或空格（Windows）、双扩展名（.jpg.php）、空字节截断、Content-Type 欺骗。

**根本防御**：

- 用**白名单**而非黑名单
- 校验文件真实类型（magic bytes），不仅看扩展名
- 重命名为随机名并去掉扩展名
- 上传目录**禁止脚本执行**（这是最关键的一层）
- 文件存到独立域名或对象存储

> ⚠️ 本关为教学模拟：上传内容**不写入磁盘、不解析、不执行**，仅在内存中做扩展名判定。""",
            flag="flag{upload_blacklist_bypass}",
            tags=["文件上传", "绕过"],
            handler=lambda ctx: sb.fake_upload(
                ctx.get("filename", ""), int(ctx.get("size", 0) or 0)),
        ),
        Level(
            id="L13", name="不安全的反序列化", category=CAT, difficulty=5, points=200,
            objective="接口接收序列化数据并直接反序列化。构造恶意序列化载荷。",
            hints=[
                "先观察参数格式，判断是哪种序列化协议（Python pickle / PHP / Java / YAML）。",
                "Python pickle 的载荷通常以 cos 换行开头，含 __reduce__。",
                "PHP 序列化形如 O:8 冒号 类名 冒号 长度 冒号大括号。POST /api/v1/sim/level/L13/deserialize",
            ],
            writeup="""反序列化漏洞的本质：**把不受信任的字节流还原成对象**，而某些语言的还原过程允许攻击者控制对象类型与属性，进而沿「利用链（gadget chain）」触发任意代码执行。

- **Java**：CommonsCollections 系列链
- **Python pickle**：`__reduce__` 可指定任意可调用对象
- **PHP**：`__wakeup` / `__destruct` 魔术方法
- **YAML**：`!!python/object/apply` 标签

**防御**：绝不反序列化不可信数据；改用 JSON 等纯数据格式；必须使用时加签名校验与类白名单。

> ⚠️ 本关为教学模拟：后端**不调用任何真实反序列化函数**（无 pickle.loads、yaml.load、ObjectInputStream），仅做特征匹配并返回说明文本。""",
            flag="flag{insecure_deserialization}",
            tags=["反序列化", "RCE"],
            handler=lambda ctx: sb.fake_deserialize(ctx.get("payload", "")),
        ),
        Level(
            id="L14", name="实体的诱惑", category=CAT, difficulty=5, points=200,
            objective="XML 解析接口允许外部实体，用它读取服务器上的文件。",
            hints=[
                "XML 里可以定义实体，语法是 ENTITY 加 SYSTEM 关键字。",
                "定义后在文档中用 &实体名; 引用它。",
                "试试读取 file:///etc/passwd。POST /api/v1/sim/level/L14/parse",
            ],
            writeup="""XXE（XML 外部实体注入）源于 XML 解析器默认允许外部实体：

```xml
<?xml version="1.0"?>
<!DOCTYPE r [<!ENTITY x SYSTEM "file:///etc/passwd">]>
<r>&x;</r>
```

解析后实体引用被替换为文件内容，实现任意文件读取。进阶利用可做 SSRF、内网探测，配合盲注外带数据。

**防御**：禁用外部实体与 DTD（resolve_entities=False、disallow-doctype-decl）；升级 XML 库；用 JSON 替代 XML。

> ⚠️ 本关为教学模拟：后端**不使用任何真实 XML 解析库**，仅用正则识别实体声明并返回预置文本，不读取任何真实文件。""",
            flag="flag{xxe_external_entity}",
            tags=["XXE", "文件读取"],
            handler=lambda ctx: sb.fake_xxe(ctx.get("xml", "")),
        ),
        Level(
            id="L15", name="自己签一张票", category=CAT, difficulty=5, points=250,
            objective="某个服务用极弱的密钥签发 JWT。伪造一个管理员身份的 token。",
            hints=[
                "先解码现有 token 的 payload（Base64URL），看看里面有什么字段。",
                "JWT 由 header.payload.signature 三段组成，用点号分隔。",
                "密钥就是 secret。把 payload 里的 role 改成 admin，用该密钥重签。",
                "在线工具可用 jwt.io 调试，或本地用 PyJWT。",
            ],
            writeup="""JWT 由三部分组成：Base64URL(header) 点 Base64URL(payload) 点 签名。

常见缺陷：

- **弱密钥**：密钥可被字典爆破（如 secret、123456）
- **alg=none**：服务端信任 header 里的算法，攻击者改成 none 去掉签名
- **算法混淆**：把 RS256 改成 HS256，用公钥当 HMAC 密钥
- **不校验签名**：只解码 payload 就用

**防御**：使用足够长的高熵密钥；服务端**固定**期望算法，不信任 header 的 alg；显式拒绝 none；校验 iss、aud、exp。

> ⚠️ 本关为教学模拟：本关的弱密钥与平台真实 JWT 体系**完全隔离**。伪造出的 token 只能通过本关的模拟校验，无法用于提升平台任何真实权限。""",
            flag="flag{jwt_weak_secret_forged}",
            tags=["JWT", "认证绕过"],
        ),
    ]

    for lv in L:
        registry.add(lv)
