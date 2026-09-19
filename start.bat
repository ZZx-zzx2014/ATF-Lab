@echo off
REM ============================================================
REM ATF Lab - 一键启动脚本（Windows）
REM
REM  仅供教学演示（EDUCATIONAL USE ONLY）
REM  请勿在互联网上公开发布、部署或传播。
REM
REM 用法：
REM   start.bat            启动服务
REM   start.bat --rebuild  强制重建前端后启动
REM   start.bat --docker   使用 docker compose 启动
REM ============================================================
setlocal enabledelayedexpansion
cd /d "%~dp0"

echo.
echo ============================================================
echo   ATF Lab —— 安全教学靶场
echo   仅供教学演示，禁止公网部署
echo ============================================================
echo.

set USE_DOCKER=0
set FORCE_REBUILD=0
:parse
if "%~1"=="" goto afterparse
if /i "%~1"=="--docker"  set USE_DOCKER=1
if /i "%~1"=="--rebuild" set FORCE_REBUILD=1
if /i "%~1"=="--help"    goto usage
shift
goto parse
:afterparse

REM ---------------------------------------------------------- Docker 模式
if "%USE_DOCKER%"=="1" (
  where docker >nul 2>&1
  if errorlevel 1 (
    echo [错误] 未找到 docker，请先安装 Docker Desktop
    exit /b 1
  )
  echo [*] 使用 docker compose 启动...
  docker compose up --build -d
  echo [*] 等待服务就绪...
  for /l %%i in (1,1,30) do (
    curl -fsS http://127.0.0.1:8899/api/v1/health >nul 2>&1 && goto dockerok
    timeout /t 1 /nobreak >nul
  )
  :dockerok
  echo.
  echo [OK] 已启动：http://127.0.0.1:8899
  echo      查看日志：docker compose logs -f
  echo      停止服务：docker compose down
  exit /b 0
)

REM ---------------------------------------------------------- 查找 Python
set PY=
for %%P in (python py) do (
  if not defined PY (
    %%P -c "import sys;sys.exit(0 if sys.version_info>=(3,9) else 1)" >nul 2>&1
    if not errorlevel 1 set PY=%%P
  )
)
if not defined PY (
  echo [错误] 未找到 Python 3.9+，请先安装
  echo        下载：https://www.python.org/downloads/
  exit /b 1
)
for /f "delims=" %%V in ('%PY% --version 2^>^&1') do echo [*] 使用 %%V

REM ---------------------------------------------------------- 虚拟环境
if not exist ".venv" (
  echo [*] 创建虚拟环境 .venv ...
  %PY% -m venv .venv
  if errorlevel 1 (
    echo [错误] 创建虚拟环境失败
    exit /b 1
  )
)
call .venv\Scripts\activate.bat

echo [*] 安装后端依赖...
python -m pip install --upgrade pip -q
python -m pip install -q -r backend\requirements.txt
if errorlevel 1 (
  echo [错误] 依赖安装失败
  exit /b 1
)

REM ---------------------------------------------------------- 前端构建
where node >nul 2>&1
if errorlevel 1 (
  echo [!] 未找到 node，跳过前端构建（仅提供 API，可访问 /api/docs）
) else (
  if "%FORCE_REBUILD%"=="1" goto buildfe
  if not exist "frontend\dist\index.html" goto buildfe
  echo [*] 前端产物已存在，跳过构建（用 --rebuild 强制重建）
  goto skipfe
  :buildfe
  echo [*] 构建前端...
  REM 把 npm 缓存指向项目内，避免全局缓存权限问题
  set npm_config_cache=%CD%\.npm-cache
  pushd frontend
  call npm install --no-audit --no-fund
  if errorlevel 1 (
    echo [错误] npm install 失败
    popd
    exit /b 1
  )
  call npm run build
  if errorlevel 1 (
    echo [错误] 前端构建失败
    popd
    exit /b 1
  )
  popd
  :skipfe
)

REM ---------------------------------------------------------- 环境变量
if not exist ".env" (
  if exist ".env.example" (
    copy /y ".env.example" ".env" >nul
    echo [!] 已从 .env.example 生成 .env，请按需修改（尤其是 ATF_SECRET_KEY）
  )
)

if not defined ATF_PORT set ATF_PORT=8899

echo.
echo ============================================================
echo   [OK] 启动中...
echo        访问地址：http://127.0.0.1:%ATF_PORT%
echo        API 文档：http://127.0.0.1:%ATF_PORT%/api/docs
echo        按 Ctrl+C 停止
echo ============================================================
echo.

python -m uvicorn backend.main:app --host 0.0.0.0 --port %ATF_PORT%
goto end

:usage
echo 用法：
echo   start.bat            启动服务
echo   start.bat --rebuild  强制重建前端后启动
echo   start.bat --docker   使用 docker compose 启动
exit /b 0

:end
endlocal
