"""
ATF Lab - 取证分析赛道（L22-L26）

⚠️ 仅供教学演示（EDUCATIONAL USE ONLY）
所有素材均为程序生成的虚构数据，不含任何真实文件或流量。
"""

from .base import Level, registry
from . import sandbox as sb

CAT = "取证分析"


def register() -> None:
    L = [
        Level(
            id="L22", name="图片里的碎语", category=CAT, difficulty=2, points=80,
            objective="一张 PNG 图片的末尾追加了一段文本，提取出其中的 flag。",
            hints=[
                "文件末尾追加数据不会影响图片正常显示。",
                "可以用 strings 命令直接搜可打印字符。",
                "或者用 tail 或 dd 查看文件最后几百字节。",
            ],
            writeup="""文件尾附加数据（Appended Data）是隐写的最简单形式。PNG 以 IEND 块结束，之后的字节被读取器忽略，但数据仍在文件里。

**常用手段**：

- `strings image.png | grep -i flag`
- `binwalk -e image.png` 分析嵌入结构
- foremost 或 scalpel 按文件头切分
- 十六进制编辑器直接看尾部

**防御**：上传图片时重新编码（re-encode），这会丢弃所有非图像数据。""",
            flag="flag{png_appended_data}",
            tags=["隐写", "文件结构"],
            handler=lambda ctx: sb.sim({
                "file": "helios_badge.png",
                "size_bytes": 40960,
                "tail_hex_preview": "49 45 4E 44 AE 42 60 82 ... 66 6C 61 67 7B ...",
                "extracted_text": "IEND 之后附带了 HTML 注释，内容含 flag{png_appended_data}",
            }),
        ),
        Level(
            id="L23", name="元数据不会骗人", category=CAT, difficulty=2, points=80,
            objective="一张照片的 EXIF 元数据里记录了拍摄设备与坐标，flag 藏在其中。",
            hints=[
                "EXIF 是相机写入图片的元数据，包含设备、时间、GPS 等信息。",
                "命令行工具：exiftool、identify -verbose。",
                "留意 UserComment 和 ImageDescription 字段。",
            ],
            writeup="""EXIF（Exchangeable Image File Format）由相机自动写入，常包含：

- 设备型号与序列号
- 拍摄时间
- **GPS 经纬度**（最危险的泄露）
- 编辑软件与原始路径

**真实风险**：有人上传照片到社交平台，EXIF 里的 GPS 直接暴露了家庭住址；记者与活动人士因 EXIF 泄露位置而陷入危险。

**防御**：上传前剥离 EXIF；平台侧自动清理元数据。""",
            flag="flag{exif_gps_leak}",
            tags=["EXIF", "元数据"],
            handler=lambda ctx: sb.sim({
                "file": "site_photo.jpg",
                "exif": {
                    "Make": "HeliosSIM",
                    "Model": "FieldCam X200",
                    "Software": "helios-desktop 2.1",
                    "ImageDescription": "flag{exif_gps_leak}",
                    "UserComment": "internal-use-only",
                    "GPSLatitude": "39.9042 N",
                    "GPSLongitude": "116.4074 E",
                    "DateTimeOriginal": "2024:03:12 09:14:02",
                },
            }),
        ),
        Level(
            id="L24", name="流量的低语", category=CAT, difficulty=3, points=120,
            objective="一份 pcap 抓包文件里，有一个请求以明文传输了凭据。找出 flag。",
            hints=[
                "用 Wireshark 打开，或用 tshark 命令行分析。",
                "过滤 HTTP 请求：http.request。",
                "留意 POST 请求的 body，以及 Authorization 头。",
            ],
            writeup="""流量分析是应急响应与取证的核心技能。常见切入点：

- **明文协议**：HTTP、FTP、Telnet、SMTP 的凭据与内容完全可见
- **TLS**：需要私钥才能解密（或利用已知漏洞）
- **DNS 隧道**：异常的域名长度与查询频率
- **文件传输**：用 Wireshark 的导出对象功能还原文件

**防御**：全站 HTTPS（配合 HSTS）；内部服务同样加密；避免在 URL 里放敏感参数（会进日志与 Referer）。""",
            flag="flag{cleartext_credentials_pcap}",
            tags=["流量分析", "Wireshark"],
            handler=lambda ctx: sb.sim({
                "file": "capture_20240312.pcap",
                "packets": [
                    {"no": 1, "src": "10.0.3.14", "dst": "10.0.3.80", "proto": "TCP",
                     "info": "54321 -> 80 [SYN]"},
                    {"no": 4, "src": "10.0.3.14", "dst": "10.0.3.80", "proto": "HTTP",
                     "info": "POST /helios/portal/login HTTP/1.1"},
                    {"no": 5, "src": "10.0.3.80", "dst": "10.0.3.14", "proto": "HTTP",
                     "info": "HTTP/1.1 302 Found"},
                ],
                "reassembled_request": (
                    "POST /helios/portal/login HTTP/1.1\r\n"
                    "Host: portal.helios-sim.invalid\r\n"
                    "Content-Type: application/x-www-form-urlencoded\r\n"
                    "Authorization: Basic c2ltdWxhdGVkOmZsYWd7Y2xlYXJ0ZXh0X2NyZWRlbnRpYWxzX3BjYXB9\r\n"
                    "\r\n"
                    "username=portal_admin&password=SimulatedOnly123"
                ),
                "decode_hint": "Authorization 头里的 Base64 解码后即为凭据。",
            }),
        ),
        Level(
            id="L25", name="日志中的脚印", category=CAT, difficulty=3, points=120,
            objective="从一份 Web 访问日志中找出攻击者的探测行为，定位 flag 所在的请求。",
            hints=[
                "关注异常的状态码组合：大量 404 后突然出现 200。",
                "留意可疑的 User-Agent 和异常的 URL 路径。",
                "攻击者最后成功访问的那个路径里含有 flag。",
            ],
            writeup="""日志审计要点：

- **扫描探测**：短时间内大量 404 或 403，路径有规律（目录爆破）
- **注入尝试**：URL 里出现引号、union、上级目录符号、script 标签
- **异常 UA**：sqlmap、nikto、nmap 的默认特征
- **时间异常**：非工作时间的访问
- **成功入侵**：扫描后出现的 200 加可疑路径

**实践建议**：把日志接入 SIEM 做关联告警；对关键路径设置专门的审计规则。""",
            flag="flag{log_forensics_found}",
            tags=["日志审计", "应急响应"],
            handler=lambda ctx: sb.sim({
                "file": "access.log",
                "entries": [
                    '10.0.3.14 - - [12/Mar/2024:09:14:02] "GET /helios/portal HTTP/1.1" 200',
                    '10.0.3.14 - - [12/Mar/2024:09:15:41] "POST /helios/portal/login HTTP/1.1" 401',
                    '203.0.113.9 - - [12/Mar/2024:09:20:11] "GET /admin.php HTTP/1.1" 404',
                    '203.0.113.9 - - [12/Mar/2024:09:20:12] "GET /backup.zip HTTP/1.1" 404',
                    '203.0.113.9 - - [12/Mar/2024:09:20:13] "GET /.git/config HTTP/1.1" 404',
                    '203.0.113.9 - - [12/Mar/2024:09:21:07] "GET /helios/portal/admin HTTP/1.1" 302',
                    '203.0.113.9 - - [12/Mar/2024:09:21:55] "GET /helios/portal/archive?key=SIMULATED HTTP/1.1" 200',
                    '203.0.113.9 - - [12/Mar/2024:09:22:30] "GET /helios/portal/flag/flag{log_forensics_found} HTTP/1.1" 200',
                ],
                "note": "以上为虚构日志，IP 使用保留测试网段（RFC 5737）。",
            }),
        ),
        Level(
            id="L26", name="藏在字节末尾", category=CAT, difficulty=4, points=150,
            objective="图片使用 LSB（最低有效位）隐写藏入了文本。提取出 flag。",
            hints=[
                "LSB 隐写把数据藏在每个像素颜色值的最低 1 位。",
                "肉眼完全看不出差异，因为改动量只有 1/255。",
                "常用工具：zsteg、stegsolve。也可以自己写脚本读最低位。",
            ],
            writeup="""LSB（Least Significant Bit）隐写的原理：

RGB 每个通道是 0-255，改动最低位只让颜色变化 1 个单位，肉眼不可辨。把每个通道的最低位拼起来，就能还原出隐藏数据。

一个 1920x1080 的图片有约 620 万个色彩通道，每位藏 1 bit 就能藏约 777 KB 数据。

**检测方法**：

- `zsteg image.png`（专治 PNG 与 BMP 的 LSB）
- 卡方分析（LSB 替换会破坏自然图像的统计特征）
- 目视检查最低位平面（stegsolve 的 bit plane 视图）

**防御**：有损压缩（JPEG）会破坏 LSB 数据；平台侧统一重新编码可清除隐写。""",
            flag="flag{lsb_steganography_bits}",
            tags=["隐写", "LSB"],
            handler=lambda ctx: sb.sim({
                "file": "helios_logo.png",
                "resolution": "800x600",
                "channels": "RGB",
                "lsb_capacity_bytes": 180000,
                "method_hint": "按 R,G,B,R,G,B 顺序取每个通道最低位，每 8 位组成一个字节。",
                "extracted_preview": "flag{lsb_steganography_bits}",
            }),
        ),
    ]
    for lv in L:
        registry.add(lv)
