# ============================================================
# ATF Lab - 多阶段构建
#
# ⚠️ 仅供教学演示（EDUCATIONAL USE ONLY）
#   本项目是受控的安全教学靶场，禁止在互联网上公开发布或部署。
#
# 阶段 1：用 Node 构建前端静态产物
# 阶段 2：用轻量 Python 镜像运行后端并托管前端
# ============================================================

# ------------------------------------------------ 阶段 1：构建前端
FROM node:20-alpine AS frontend-builder

WORKDIR /build

# 先复制依赖清单，利用 Docker 层缓存
COPY frontend/package.json frontend/package-lock.json* ./

# 优先用 npm ci（有 lock 文件时），否则回退到 npm install
RUN if [ -f package-lock.json ]; then \
        npm ci --no-audit --no-fund; \
    else \
        npm install --no-audit --no-fund; \
    fi

COPY frontend/ ./
RUN npm run build


# ------------------------------------------------ 阶段 2：运行时
FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    ATF_HOST=0.0.0.0 \
    ATF_PORT=8899 \
    ATF_DB_PATH=/app/data/atf.db \
    ATF_FRONTEND_DIST=/app/frontend/dist \
    ATF_NETLAB_ENABLED=1

WORKDIR /app

# 只安装运行必需的依赖
COPY backend/requirements.txt /app/backend/requirements.txt
RUN pip install --no-cache-dir -r /app/backend/requirements.txt

# 复制后端代码
COPY backend/ /app/backend/
COPY netlab/ /app/netlab/

# 复制已构建好的前端产物
COPY --from=frontend-builder /build/dist /app/frontend/dist

# 数据目录（SQLite），通过 volume 持久化
RUN mkdir -p /app/data
VOLUME ["/app/data"]

# 仿真网络服务端口（仅用于本地教学演示）
EXPOSE 8899 2121 3306 6379 31337

# 健康检查：调用统一格式的 health 接口
HEALTHCHECK --interval=30s --timeout=5s --start-period=10s --retries=3 \
    CMD python -c "import urllib.request,sys; \
        sys.exit(0 if urllib.request.urlopen('http://127.0.0.1:8899/api/v1/health',timeout=4).status==200 else 1)"

CMD ["python", "-m", "uvicorn", "backend.main:app", "--host", "0.0.0.0", "--port", "8899"]
