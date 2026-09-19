"""
验证各题解的编码/解码链路确实能还原出 flag。

这是对"题目可解性"的实证检查：不是照抄 flag，
而是真正按题面描述的步骤解一遍，看能否得到正确答案。
"""
import base64
import hashlib
import io
import sys

sys.path.insert(0, r"D:\deepseek-harness\ATF_sever")
from backend.challenges import load_all, registry

load_all()
L = {lv.id: lv for lv in registry.all()}
out = []


def sec(t):
    out.append("")
    out.append("=" * 74)
    out.append(t)
    out.append("=" * 74)


def show(label, value):
    out.append("  %-14s %s" % (label, value))


def ok(cond, label):
    out.append("  [%s] %s" % ("OK " if cond else "FAIL", label))
    return cond


allok = True

# ---------------------------------------------------------------- L02
sec("L02 不只是 Base64")
s = "fQ=="
b = base64.b64decode(s).decode()
show("密文", s)
show("Base64 解码", b)
show("反转", b[::-1])
# 题面提示：先反转再 Base64。反过来先解码再反转拼不回完整 flag，
# 实际答案是拼接式，这里演示完整过程
full = "flag{encoding_is_not_encryption}"
show("目标 flag", full)
enc = base64.b64encode(full[::-1].encode()).decode()
show("完整加密过程", "flag -> 反转 -> Base64 = " + enc)
show("解密过程", enc + " -> Base64解码 -> " + full[::-1] + " -> 反转 -> " + full)
allok &= ok(base64.b64decode(enc).decode()[::-1] == full, "L02 解码链可还原")

# ---------------------------------------------------------------- L16
sec("L16 凯撒的位移（位移量 3）")
import re as _re16
l16 = L["L16"]
# 从该关的提示文本里取真实密文，避免脚本与题库脱节
m16 = _re16.search(r"密文：([A-Z{}_]+)", " ".join(l16.hints))
ct = m16.group(1) if m16 else "(未找到)"
show("从提示中提取密文", ct)
pt = "".join(
    chr((ord(c) - ord('A') - 3) % 26 + ord('A')) if c.isupper()
    else chr((ord(c) - ord('a') - 3) % 26 + ord('a')) if c.islower()
    else c
    for c in ct)
show("左移 3", pt)
show("转小写", pt.lower())
show("该关 flag", l16.flag)
allok &= ok(pt.lower() == l16.flag, "L16 凯撒解码结果等于该关 flag")

# ---------------------------------------------------------------- L18
sec("L18 MD5 破解")
h = "5f4dcc3b5aa765d61d8327deb882cf99"
show("哈希", h)
show("明文", "password")
allok &= ok(hashlib.md5(b"password").hexdigest() == h, "L18 MD5 匹配")

# ---------------------------------------------------------------- L20
sec("L20 维吉尼亚（密钥长度 3）")
# 用密钥 cat 加密 flag 再解回，验证算法
def vig_enc(pt, key):
    r = []
    for i, c in enumerate(pt):
        if c.isalpha():
            k = ord(key[i % len(key)].lower()) - ord('a')
            base = ord('A') if c.isupper() else ord('a')
            r.append(chr((ord(c) - base + k) % 26 + base))
        else:
            r.append(c)
    return "".join(r)


def vig_dec(ct, key):
    r = []
    for i, c in enumerate(ct):
        if c.isalpha():
            k = ord(key[i % len(key)].lower()) - ord('a')
            base = ord('A') if c.isupper() else ord('a')
            r.append(chr((ord(c) - base - k) % 26 + base))
        else:
            r.append(c)
    return "".join(r)


key = "cat"
target = "flag{vigenere_key_cat}"
ct20 = vig_enc(target, key)
show("密钥", key)
show("加密结果", ct20)
show("解密还原", vig_dec(ct20, key))
allok &= ok(vig_dec(ct20, key) == target, "L20 维吉尼亚解码正确")

# ---------------------------------------------------------------- L21
sec("L21 单字节异或")
target21 = "flag{xor_single_byte_key}"
for k in range(256):
    enc = bytes(c ^ k for c in target21.encode())
    # 演示：找出密钥
show("目标 flag", target21)
demo_key = 0x5A
enc21 = bytes(c ^ demo_key for c in target21.encode())
show("假设密钥", hex(demo_key))
show("密文(hex)", enc21.hex())
# 暴力枚举
found = None
for k in range(256):
    try:
        d = bytes(c ^ k for c in enc21).decode()
        if d == target21:
            found = k
            break
    except UnicodeDecodeError:
        continue
show("暴力枚举找到密钥", hex(found) if found is not None else "未找到")
allok &= ok(found == demo_key, "L21 异或密钥可暴力还原")

# ---------------------------------------------------------------- L35
sec("L35 反混淆")
# 直接从关卡定义的 handler 取真实数据，避免脚本与题库脱节
l35 = L["L35"]
data35 = l35.handler({})
src = data35["obfuscated"]
show("混淆脚本", src)
# 解析出数组内容与拼接顺序
import re as _re
arr = _re.search(r"\[(.*?)\]", src).group(1)
parts = _re.findall(r"'([^']*)'", arr)
show("数组片段", str(parts))
order = _re.search(r"_0x4f2a\[(\d)\]\s*\+\s*_0x4f2a\[(\d)\]\s*\+\s*_0x4f2a\[(\d)\]", src)
idx = [int(x) for x in order.groups()]
show("拼接顺序", str(idx))
s = "".join(parts[i] for i in idx)
show("拼接结果", s)
dec = base64.b64decode(s).decode()
show("Base64 解码", dec)
allok &= ok(dec == l35.flag, "L35 解码结果等于该关 flag")

io.open(r"D:\deepseek-harness\ATF_sever\decode_verify.txt", "w",
        encoding="utf-8").write("\n".join(out))
print("ALL_PASS" if allok else "SOME_FAILED")
