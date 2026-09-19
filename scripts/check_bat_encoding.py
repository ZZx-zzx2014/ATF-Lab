"""
验证 start.bat 的编码与行尾（结果写入文件，避免控制台编码干扰）。
"""
import io
import os

ROOT = r"D:\deepseek-harness\ATF_sever"
bat = os.path.join(ROOT, "start.bat")
out = os.path.join(ROOT, "bat_check.txt")

b = open(bat, "rb").read()
lines = []

lines.append("start.bat 编码与行尾检查")
lines.append("=" * 50)
lines.append("文件大小 : %d 字节" % len(b))
lines.append("CRLF     : %d" % b.count(b"\r\n"))
lines.append("裸 LF    : %d" % (b.count(b"\n") - b.count(b"\r\n")))

try:
    b.decode("utf-8")
    lines.append("UTF-8 解码: 成功 -> 文件是 UTF-8（cmd 会乱码，不合格）")
except UnicodeDecodeError:
    lines.append("UTF-8 解码: 失败 -> 不是 UTF-8（正确）")

try:
    text = b.decode("gbk")
    lines.append("GBK 解码  : 成功 -> cmd.exe(代码页936) 可正确读取（正确）")
    lines.append("")
    lines.append("按 GBK 解码后的前 12 行（模拟 cmd 看到的内容）：")
    lines.append("-" * 50)
    for i, l in enumerate(text.split("\r\n")[:12], 1):
        lines.append("%3d | %s" % (i, l))
    lines.append("-" * 50)
except UnicodeDecodeError as e:
    lines.append("GBK 解码  : 失败 -> %s" % e)

io.open(out, "w", encoding="utf-8").write("\n".join(lines))
print("written to bat_check.txt")
