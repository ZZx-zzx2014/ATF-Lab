"""
导出全部关卡的解题信息（flag / 目标 / 提示 / 考点），
供人工核对与编写题解文档。

输出写入 levels_export.txt（UTF-8），避免控制台编码干扰。
"""
import io
import sys

sys.path.insert(0, r"D:\deepseek-harness\ATF_sever")
from backend.challenges import load_all, registry

load_all()
levels = registry.all()

lines = []
lines.append("ATF Lab 全部关卡解题信息")
lines.append("=" * 78)
lines.append("共 %d 关" % len(levels))
lines.append("")

cur_cat = None
for lv in levels:
    if lv.category != cur_cat:
        cur_cat = lv.category
        lines.append("")
        lines.append("#" * 78)
        lines.append("# 分类：%s" % cur_cat)
        lines.append("#" * 78)

    lines.append("")
    lines.append("-" * 78)
    lines.append("[%s] %s   (难度 %d/5, %d 分)" % (
        lv.id, lv.name, lv.difficulty, lv.points))
    lines.append("-" * 78)
    lines.append("目标   : %s" % lv.objective)
    lines.append("标签   : %s" % ", ".join(lv.tags))
    lines.append("FLAG   : %s" % lv.flag)
    lines.append("")
    lines.append("提示：")
    for i, h in enumerate(lv.hints):
        lines.append("  %d) %s" % (i + 1, h))
    lines.append("")
    lines.append("原理讲解：")
    for line in lv.writeup.split("\n"):
        lines.append("  " + line)

io.open(r"D:\deepseek-harness\ATF_sever\levels_export.txt", "w",
        encoding="utf-8").write("\n".join(lines))
print("exported %d levels" % len(levels))
