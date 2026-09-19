"""
ATF Lab - 逆向与杂项赛道（L34-L36）

⚠️ 仅供教学演示（EDUCATIONAL USE ONLY）
所有题目为教学构造，不包含任何真实恶意代码或成品攻击工具。
"""

from .base import Level, registry
from . import sandbox as sb

CAT = "逆向与杂项"


def register() -> None:
    L = [
        Level(
            id="L34", name="反汇编的第一眼", category=CAT, difficulty=3, points=120,
            objective="给定一段伪代码，分析其校验逻辑，推出正确的输入（即 flag）。",
            hints=[
                "先看程序做了什么比较，找到判断分支。",
                "注意字符串比较的每个字符，以及它们的变换方式。",
                "常见变换：字符加 1、异或固定值、逆序。",
            ],
            writeup="""逆向分析的基本流程：

1. **静态分析**：用 IDA、Ghidra、objdump 查看反汇编，识别函数、字符串引用、控制流
2. **动态分析**：用 gdb、x64dbg 下断点，观察运行时内存与寄存器
3. **定位关键逻辑**：搜索字符串、找比较指令、追踪输入的处理路径
4. **还原算法**：把汇编逻辑翻译成高级语言伪代码

**本关示例逻辑**：程序把输入每个字符加 1 后与目标串比较。逆运算就是把每个目标字符减 1 再反转。

> ⚠️ 本关提供的是**教学伪代码**，不包含任何真实二进制或恶意代码。""",
            flag="flag{reverse_me_please}",
            tags=["逆向", "伪代码分析"],
            handler=lambda ctx: sb.sim({
                "pseudo_code": (
                    "int check(char *input) {\n"
                    "    char target[] = \"gmbh|sfwf`nf|qmfbtf\";\n"
                    "    for (int i = 0; i < strlen(target); i++)\n"
                    "        if (input[i] + 1 != target[i]) return 0;\n"
                    "    return 1;\n"
                    "}"
                ),
                "note": "target 是逆序存放的，且每个字符加 1。先反转再减 1。",
            }),
        ),
        Level(
            id="L35", name="混淆的字符串", category=CAT, difficulty=4, points=150,
            objective="一段经过混淆的脚本，还原出它隐藏的 flag。",
            hints=[
                "混淆常用手法：字符串反转、字符编码转换、Base64、十六进制。",
                "注意脚本里可能有多个解码步骤串联。",
                "可以用 Python 逐步执行每一层解码。",
            ],
            writeup="""代码混淆（Obfuscation）的目的是增加阅读难度，但**不是加密**。

常见手法：

- **字符串编码**：Base64、Hex、Unicode 转义、String.fromCharCode
- **字符串拼接**：把关键字拆成多段再拼起来
- **控制流平坦化**：用 switch 加状态机打散执行顺序
- **变量名混淆**：_0x1a2b 这类无意义名称
- **动态执行**：eval 或 exec 运行时才生成代码

**还原方法**：

- 静态：手动逐层解码，或用 AST 工具反混淆
- 动态：把 eval 换成 print（或 hook eval）观察真实执行内容
- 工具：de4js、js-beautify、uncompyle6

**注意**：混淆常被恶意软件用于免杀。分析可疑样本请务必在**隔离的沙箱环境**中进行。""",
            flag="flag{deobfuscated_string}",
            tags=["混淆", "反混淆"],
            handler=lambda ctx: sb.sim({
                "obfuscated": (
                    "var _0x4f2a = ['fQ==', 'Z2Fs', 'Z19zdH']; "
                    "var s = _0x4f2a[1] + _0x4f2a[2] + _0x4f2a[0]; "
                    "// 拼接后再 Base64 解码"
                ),
                "steps": [
                    "拼接三个片段得到 Base64 串",
                    "Base64 解码后得到明文（注意补全花括号）",
                ],
                "note": "实际 flag 为 flag{deobfuscated_string}",
            }),
        ),
        Level(
            id="L36", name="这封邮件有问题", category=CAT, difficulty=2, points=100,
            objective="判断一封钓鱼邮件的可疑特征，找出其中伪造的发件人域名。",
            hints=[
                "仔细看发件人地址的域名拼写，是否与官方域名有细微差异。",
                "留意链接的真实目标（href）与显示文字是否一致。",
                "检查邮件头中的 SPF、DKIM、DMARC 验证结果。",
            ],
            writeup="""钓鱼邮件的识别要点：

**1. 发件人地址**

- 显示名伪装：显示为 Helios 客服，实际地址是 attacker@evil.com
- 相似域名：heli0s.com（数字 0 冒充字母 o）、helios-secure.com
- 子域欺骗：helios.com.evil.com

**2. 链接目标**

- 悬停查看真实 URL，与显示文字对比
- 短链（bit.ly）隐藏目标
- 同形异义字（Punycode）：用西里尔字母伪装拉丁字母

**3. 邮件头验证**

- SPF：发件 IP 是否被域名授权
- DKIM：邮件签名是否有效
- DMARC：策略与对齐检查
- Return-Path 与 From 是否一致

**4. 内容特征**

- 制造紧迫感（例如要求 24 小时内处理否则停用）
- 要求点击链接登录或提供凭据
- 附件为可执行文件或宏文档

**防御**：部署 DMARC 策略；员工安全意识培训；邮件网关做链接改写与沙箱检测。""",
            flag="flag{phishing_domain_heli0s}",
            tags=["社会工程", "钓鱼识别"],
            handler=lambda ctx: sb.sim({
                "email": {
                    "From": "Helios IT Support <it-support@heli0s-portal.com>",
                    "Reply-To": "no-reply@mail-relay.evil-sim.invalid",
                    "Return-Path": "bounce@mail-relay.evil-sim.invalid",
                    "Subject": "【紧急】您的账户将在 24 小时内被停用，请立即验证",
                    "Authentication-Results": (
                        "spf=fail (sender IP is not authorized) "
                        "dkim=none dmarc=fail"
                    ),
                    "body_display_link": "https://portal.helios-sim.invalid/verify",
                    "body_real_href": "http://heli0s-portal.com/login?token=SIMULATED",
                },
                "analysis_hints": [
                    "发件域名 heli0s-portal.com 使用了数字 0 冒充字母 o",
                    "SPF 与 DMARC 均为 fail",
                    "链接显示文字与真实目标不一致",
                ],
            }),
        ),
    ]
    for lv in L:
        registry.add(lv)
