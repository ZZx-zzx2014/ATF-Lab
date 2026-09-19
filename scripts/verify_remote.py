"""验证 GitHub 远程仓库内容与本地一致。"""
import base64
import io
import json
import subprocess

GH = r"C:\Program Files\GitHub CLI\gh.exe"
REPO = "ZZx-zzx2014/ATF-Lab"

_lines = []


def out(s=""):
    _lines.append(str(s))


def gh_api(path):
    o = subprocess.run([GH, "api", path], capture_output=True)
    if o.returncode != 0:
        return None
    return json.loads(o.stdout.decode("utf-8"))


out("=" * 66)
out("GitHub 远程仓库验证: " + REPO)
out("=" * 66)

# 1) 仓库元信息
info = gh_api("repos/" + REPO)
out("")
out("[仓库信息]")
out("  名称        : " + info["name"])
out("  可见性      : " + info["visibility"])
out("  URL         : " + info["html_url"])
out("  默认分支    : " + info["default_branch"])
out("  Description : " + (info["description"] or "(空!)"))

# 2) 远程文件树
tree = gh_api("repos/%s/git/trees/%s?recursive=1" % (REPO, info["default_branch"]))
blobs = [t for t in tree["tree"] if t["type"] == "blob"]
out("")
out("[文件统计]")
out("  远程文件数  : %d" % len(blobs))

local = subprocess.run(["git", "ls-files"], capture_output=True,
                       cwd=r"D:\deepseek-harness\ATF_sever")
local_files = set(local.stdout.decode().split())
remote_files = {t["path"] for t in blobs}
out("  本地文件数  : %d" % len(local_files))
out("  完全一致    : %s" % (local_files == remote_files))
if local_files != remote_files:
    out("  仅本地有    : %s" % sorted(local_files - remote_files)[:10])
    out("  仅远程有    : %s" % sorted(remote_files - local_files)[:10])

# 3) README 顶部内容
out("")
out("[README 顶部 15 行 - 验证免责声明在显著位置]")
readme = gh_api("repos/%s/readme" % REPO)
if readme:
    raw = base64.b64decode(readme["content"]).decode("utf-8")
    for i, line in enumerate(raw.split("\n")[:15], 1):
        out("  %2d | %s" % (i, line))

# 4) 敏感文件检查
out("")
out("[敏感文件检查]")
for f in [".env", "data/atf.db", "frontend/node_modules/package.json",
          "frontend/dist/index.html"]:
    r = gh_api("repos/%s/contents/%s" % (REPO, f))
    out("  %-38s %s" % (f, "!! 已上传" if r else "OK 未上传"))

# 5) 提交历史
out("")
out("[提交历史]")
commits = gh_api("repos/%s/commits?per_page=10" % REPO)
for c in commits:
    au = c["commit"]["author"]
    out("  %s  %-16s %s" % (c["sha"][:7], au["name"],
                           c["commit"]["message"].split("\n")[0][:52]))

out("")
out("=" * 66)
out("仓库地址: https://github.com/" + REPO)
out("=" * 66)

report = "\n".join(_lines)
io.open("remote_verify_result.txt", "w", encoding="utf-8").write(report)
print("remote verification written to remote_verify_result.txt")

