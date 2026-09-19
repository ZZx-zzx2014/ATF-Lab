#!/usr/bin/env bash
# ============================================================
# ATF Lab - 一键启动脚本（macOS / Linux）
#
# ⚠️ 仅供教学演示（EDUCATIONAL USE ONLY）
#   请勿在互联网上公开发布、部署或传播。
#
# 用法：
#   ./start.sh            # 启动服务
#   ./start.sh --rebuild  # 强制重建前端后启动
#   ./start.sh --docker   # 使用 docker compose 启动
# ============================================================
set -euo pipefail

cd "$(dirname "$0")"

BOLD=$'\033[1m'; GREEN=$'\033[32m'; YELLOW=$'\033[33m'; RED=$'\033[31m'; NC=$'\033[0m'

info()  { printf '%s\n' "${GREEN}▸${NC} $*"; }
warn()  { printf '%s\n' "${YELLOW}!${NC} $*"; }
error() { printf '%s\n' "${RED}✗${NC} $*" >&2; }

printf '\n%s\n' "${BOLD}ATF Lab —— 安全教学靶场${NC}"
printf '%s\n\n' "⚠️  本项目仅供教学演示，禁止公网部署"

# ---------------------------------------------------------- 参数
USE_DOCKER=0
FORCE_REBUILD=0
for arg in "$@"; do
  case "$arg" in
    --docker)  USE_DOCKER=1 ;;
    --rebuild) FORCE_REBUILD=1 ;;
    -h|--help)
      sed -n '2,14p' "$0" | sed 's/^# \{0,1\}//'
      exit 0 ;;
  esac
done

# ---------------------------------------------------------- Docker 模式
if [ "$USE_DOCKER" -eq 1 ]; then
  if ! command -v docker >/dev/null 2>&1; then
    error "未找到 docker，请先安装 Docker Desktop"
    exit 1
  fi
  info "使用 docker compose 启动…"
  docker compose up --build -d
  info "等待服务就绪…"
  for _ in $(seq 1 30); do
    if curl -fsS http://127.0.0.1:8899/api/v1/health >/dev/null 2>&1; then
      break
    fi
    sleep 1
  done
  printf '\n%s\n' "${GREEN}✓ 已启动：http://127.0.0.1:8899${NC}"
  printf '%s\n' "  查看日志：docker compose logs -f"
  printf '%s\n\n' "  停止服务：docker compose down"
  exit 0
fi

# ---------------------------------------------------------- Python 检测
PY=""
for cand in python3.12 python3.11 python3 python; do
  if command -v "$cand" >/dev/null 2>&1; then
    ver=$("$cand" -c 'import sys;print("%d%d"%sys.version_info[:2])' 2>/dev/null || echo "0")
    if [ "$ver" -ge 39 ] 2>/dev/null; then PY="$cand"; break; fi
  fi
done
if [ -z "$PY" ]; then
  error "未找到 Python 3.9+，请先安装"
  exit 1
fi
info "使用 Python: $($PY --version 2>&1)"

# ---------------------------------------------------------- 虚拟环境
if [ ! -d ".venv" ]; then
  info "创建虚拟环境 .venv …"
  "$PY" -m venv .venv
fi
# shellcheck disable=SC1091
source .venv/bin/activate

info "安装后端依赖…"
python -m pip install --upgrade pip -q
python -m pip install -q -r backend/requirements.txt

# ---------------------------------------------------------- 前端构建
if command -v node >/dev/null 2>&1; then
  if [ "$FORCE_REBUILD" -eq 1 ] || [ ! -f "frontend/dist/index.html" ]; then
    info "构建前端…"
    # 把 npm 缓存指向项目内，避免全局缓存权限问题
    export npm_config_cache="$PWD/.npm-cache"
    ( cd frontend && npm install --no-audit --no-fund && npm run build )
  else
    info "前端产物已存在，跳过构建（用 --rebuild 强制重建）"
  fi
else
  warn "未找到 node，跳过前端构建。仅提供 API，可访问 /api/docs"
fi

# ---------------------------------------------------------- 环境变量
if [ ! -f ".env" ] && [ -f ".env.example" ]; then
  cp .env.example .env
  warn "已从 .env.example 生成 .env，请按需修改（尤其是 ATF_SECRET_KEY）"
fi

# ---------------------------------------------------------- 启动
PORT="${ATF_PORT:-8899}"
printf '\n%s\n' "${GREEN}✓ 启动中…${NC}"
printf '%s\n'   "  访问地址：http://127.0.0.1:${PORT}"
printf '%s\n'   "  API 文档：http://127.0.0.1:${PORT}/api/docs"
printf '%s\n\n' "  按 Ctrl+C 停止"

exec python -m uvicorn backend.main:app \
  --host "${ATF_HOST:-0.0.0.0}" \
  --port "$PORT"
