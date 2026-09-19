"""
ATF Lab - 密码学赛道（L16-L21）

⚠️ 仅供教学演示（EDUCATIONAL USE ONLY）
所有密码学题目均为教学构造，flag 为虚构字符串。
"""

from .base import Level, registry
from . import sandbox as sb

CAT = "密码学"


def register() -> None:
    L = [
        Level(
            id="L16", name="凯撒的位移", category=CAT, difficulty=1, points=50,
            objective="一段密文使用了凯撒密码加密，还原出明文中的 flag。",
            hints=[
                "凯撒密码就是把字母表整体平移固定位数。",
                "试试暴力枚举 1 到 25 所有位移，找可读的英文。",
                "位移量是 3。密文：IODJ{NHDVDU_VKLIW_WKUHH}",
            ],
            writeup="""凯撒密码是最古老的替换密码：每个字母向后（或向前）平移固定位数。

因为密钥空间只有 25 种，**暴力枚举**就能破解。即使不知道位移量，也可以用频率分析（英文中 E 出现频率最高）来推断。

**教训**：密钥空间过小的古典密码在现代计算能力面前毫无安全性可言。""",
            flag="flag{caesar_shift_three}",
            tags=["古典密码", "凯撒"],
        ),
        Level(
            id="L17", name="编码套娃", category=CAT, difficulty=2, points=80,
            objective="密文被多层编码嵌套，逐层解开得到 flag。",
            hints=[
                "先看字符串长什么样：纯十六进制？还是 Base64 字符集？",
                "常见组合：Hex 转 Base64 转 URL 编码再反转字符串。",
                "善用命令行工具：xxd -r -p、base64 -d、python -c。",
            ],
            writeup="""多层编码是 CTF 的经典热身题。识别顺序的技巧：

- 全是 0-9a-f 且长度为偶数 → Hex
- 含 A-Za-z0-9+/ 且以等号结尾 → Base64
- 含 %XX → URL 编码
- 含 \\uXXXX → Unicode 转义

编码层层嵌套不等于安全，只是增加了人工识别的成本。""",
            flag="flag{nested_encoding_layers}",
            tags=["编码", "多层解码"],
        ),
        Level(
            id="L18", name="撞出这个 MD5", category=CAT, difficulty=2, points=80,
            objective="给定一个 MD5 哈希，还原出它对应的原始明文。",
            hints=[
                "MD5 是不可逆的，但可以用彩虹表或在线库查询常见值。",
                "这题的明文是一个很常见的英文单词，全部小写。",
                "提示：它是 password 这个词本身。哈希：5f4dcc3b5aa765d61d8327deb882cf99",
            ],
            writeup="""MD5 是单向散列函数，理论不可逆。但攻击者不需要逆推，而是**猜**：

- **字典攻击**：对字典中每个词算哈希，与目标比对
- **彩虹表**：预计算的哈希与明文对照表，以空间换时间
- **暴力破解**：枚举所有组合（短密码可行）

5f4dcc3b5aa765d61d8327deb882cf99 正是 password —— 世界上最常用的弱密码之一。

**防御**：口令存储必须加盐（salt）并使用慢哈希（bcrypt / scrypt / Argon2），绝不能直接用 MD5 或 SHA1。

> 本项目自己的用户口令就是用 PBKDF2-HMAC-SHA256（20 万轮加随机盐）存储的。""",
            flag="flag{md5_password_cracked}",
            tags=["哈希", "弱口令"],
        ),
        Level(
            id="L19", name="时间就是答案", category=CAT, difficulty=3, points=120,
            objective="某系统用时间戳作为随机数种子生成 token。预测出下一个 token。",
            hints=[
                "如果随机数种子是时间，那么给定时间就能复现序列。",
                "Python 里用时间戳做随机数种子后，生成的序列是可预测的。",
                "先找到种子被泄露的那个时间戳，再复现生成逻辑。",
            ],
            writeup="""弱随机数是真实世界中反复出现的漏洞：

- 用 time() 当种子 → 可枚举时间窗口复现
- 用 rand() 不播种 → 序列固定
- PHP 的 mt_rand 截断 → 可从输出反推内部状态
- 自己实现「随机」算法 → 几乎必然有偏

**真实案例**：某彩票网站用时间戳做种子，被预测出开奖号码；某加密工具用进程 ID 做种子，导致密钥可预测。

**防御**：密码学场景必须用 secrets、os.urandom 或 SecureRandom，绝不使用普通伪随机数生成器。

> ⚠️ 本关为教学模拟：演示用的是固定种子的伪随机数，不涉及任何真实系统。""",
            flag="flag{weak_random_seed_time}",
            tags=["弱随机数", "预测"],
            handler=lambda ctx: sb.sim({
                "observed_token": "a3f1c9d2e8b70456",
                "seed_hint": "种子为整数时间戳，初始种子 1337",
                "next_token_preview": sb.weak_random_token(),
            }),
        ),
        Level(
            id="L20", name="维吉尼亚之锁", category=CAT, difficulty=3, points=120,
            objective="密文使用维吉尼亚密码加密，密钥是一个常见英文单词。破解它。",
            hints=[
                "维吉尼亚是多表替换，相同明文字母会加密成不同密文。",
                "先确定密钥长度：可以看重复片段的间隔，或用卡西斯基检验。",
                "密钥长度是 3，猜测常见三字母单词。",
            ],
            writeup="""维吉尼亚密码用密钥决定每个位置的位移量，解决了凯撒密码「相同字母加密结果相同」的弱点，曾被称作不可破译的密码。

**破解方法**：

1. **卡西斯基检验**：找重复密文片段的间隔，取最大公约数猜密钥长度
2. **弗里德曼检验**：用重合指数估计密钥长度
3. 确定长度后，每个位置退化成独立的凯撒密码，用频率分析逐个破解

**教训**：只要密钥重复使用，多表替换依然可破。后来的一次性密码本（OTP）用不重复的随机密钥才真正不可破。""",
            flag="flag{vigenere_key_cat}",
            tags=["古典密码", "维吉尼亚"],
        ),
        Level(
            id="L21", name="异或的秘密", category=CAT, difficulty=4, points=150,
            objective="密文由明文与单字节密钥异或得到。恢复明文与密钥。",
            hints=[
                "单字节异或只有 256 种可能，可以全部试一遍。",
                "异或的性质：A 异或 B 再异或 B 等于 A，加密解密是同一个操作。",
                "观察试出来的结果中哪一个是可读的英文文本。",
            ],
            writeup="""异或（XOR）在密码学中极其重要，因为 A 异或 K 再异或 K 等于 A，同一个操作既是加密也是解密。

**单字节异或破解**：只有 256 种密钥，直接枚举即可。判断哪个是正确的，可以用**字符频率打分**（英文字母和空格占比高）。

**为什么流密码会出事**：如果密钥流重复使用（many-time pad），两份密文异或会消掉密钥，得到两份明文的异或，再用频率分析就能分别还原 —— 这就是 WEP 被攻破的原因之一。

**防御**：绝不重复使用密钥流；使用 AEAD 模式（如 AES-GCM）并确保 nonce 唯一。""",
            flag="flag{xor_single_byte_key}",
            tags=["异或", "密码分析"],
        ),
    ]
    for lv in L:
        registry.add(lv)
