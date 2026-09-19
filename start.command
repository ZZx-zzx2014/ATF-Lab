#!/usr/bin/env bash
# ============================================================
# ATF Lab - 一键启动（macOS 双击运行）
#
# ⚠️ 仅供教学演示（EDUCATIONAL USE ONLY）
#   请勿在互联网上公开发布、部署或传播。
#
# 说明：
#   本文件是 start.sh 的 macOS 图形化包装。
#   双击后会在「终端」中打开，执行完毕后保持窗口不关闭，
#   方便查看运行日志。
# ============================================================

cd "$(dirname "$0")" || exit 1

# 双击 .command 时 PATH 往往不含 Homebrew，这里主动补上
export PATH="/opt/homebrew/bin:/usr/local/bin:/usr/bin:/bin:$PATH"

if [ ! -x "./start.sh" ]; then
  chmod +x ./start.sh 2>/dev/null || true
fi

./start.sh "$@"
status=$?

echo
if [ $status -ne 0 ]; then
  echo "✗ 启动失败（退出码 $status）"
else
  echo "✓ 服务已停止"
fi
echo
echo "按回车键关闭此窗口…"
read -r _
