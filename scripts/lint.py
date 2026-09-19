"""
ATF Lab - 源码静态检查

写关卡文案时容易把中文引号误写成 ASCII 双引号，导致字符串被提前截断。
本脚本用于提交前自检。判定以 **编译器为准**，避免正则误报。

检查项：
  1. 每个 .py 文件能否 compile（这是唯一权威判定）
  2. 报告编译失败的具体行，便于定位
"""
import io
import sys
from pathlib import Path


def check_file(path):
    src = io.open(path, encoding="utf-8").read()
    try:
        compile(src, str(path), "exec")
        return None
    except SyntaxError as e:
        lines = src.split("\n")
        ctx = []
        lo = max(0, (e.lineno or 1) - 3)
        hi = min(len(lines), (e.lineno or 1) + 2)
        for i in range(lo, hi):
            ctx.append("      %4d| %s" % (i + 1, lines[i]))
        return "  line %s: %s\n%s" % (e.lineno, e.msg, "\n".join(ctx))


def main():
    root = Path(sys.argv[1]) if len(sys.argv) > 1 else Path(".")
    files = [f for f in sorted(root.rglob("*.py")) if "__pycache__" not in str(f)]
    out = []
    bad = 0
    for f in files:
        msg = check_file(f)
        if msg:
            bad += 1
            out.append("FAIL %s\n%s" % (f, msg))
    out.append("checked %d file(s), %d failed" % (len(files), bad))
    # 写入文件，避免控制台编码问题
    io.open(Path(root) / ".lint_result.txt", "w", encoding="utf-8").write(
        "\n".join(out))
    sys.stdout.write("checked %d file(s), %d failed\n" % (len(files), bad))
    return 1 if bad else 0


if __name__ == "__main__":
    sys.exit(main())
