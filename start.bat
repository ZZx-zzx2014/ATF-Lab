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
REM
REM 实现说明：
REM   本脚本刻意避免使用 if ( ... ) else ( ... ) 这类嵌套块。
REM   cmd 对块内的特殊字符（括号 && | 等）解析规则复杂且容易出错，
REM   因此统一改用 goto 标签跳转，行为可预测。
REM ============================================================
setlocal
cd /d "%~dp0"

echo.
echo ============================================================
echo   ATF Lab —— 安全教学靶场
echo   仅供教学演示，禁止公网部署
echo ============================================================
echo.

set USE_DOCKER=0
set FORCE_REBUILD=0

:parse_args
if "%~1"=="" goto args_done
if /i "%~1"=="--docker"  set USE_DOCKER=1
if /i "%~1"=="--rebuild" set FORCE_REBUILD=1
if /i "%~1"=="--help"    goto usage
if /i "%~1"=="-h"        goto usage
shift
goto parse_args
:args_done

if "%USE_DOCKER%"=="1" goto docker_mode

REM ============================================================
REM  本地模式
REM ============================================================

REM ---------------------------------------------------------- 查找 Python
REM 版本判断交给独立脚本，避免在 for 块里写含括号的 Python 代码
set PY=
for %%P in (python py) do call :try_python %%P
if not defined PY goto no_python
for /f "delims=" %%V in ('%PY% --version 2^>^&1') do echo [*] 使用 %%V
goto have_python

:try_python
if defined PY goto :eof
%1 "scripts\check_python.py" >nul 2>&1
if errorlevel 1 goto :eof
set PY=%1
goto :eof

:no_python
echo [错误] 未找到 Python 3.9+，请先安装
echo        下载：https://www.python.org/downloads/
exit /b 1

:have_python

REM ---------------------------------------------------------- 虚拟环境
if exist ".venv\Scripts\activate.bat" goto venv_ready
echo [*] 创建虚拟环境 .venv ...
%PY% -m venv .venv
if errorlevel 1 goto venv_fail

:venv_ready
call .venv\Scripts\activate.bat
if errorlevel 1 goto venv_fail

echo [*] 安装后端依赖...
python -m pip install --upgrade pip -q
python -m pip install -q -r backend\requirements.txt
if errorlevel 1 goto deps_fail

REM ---------------------------------------------------------- 前端构建
where node >nul 2>&1
if errorlevel 1 goto no_node

if "%FORCE_REBUILD%"=="1" goto build_frontend
if not exist "frontend\dist\index.html" goto build_frontend
echo [*] 前端产物已存在，跳过构建（用 --rebuild 强制重建）
goto frontend_done

:build_frontend
echo [*] 构建前端...
REM 把 npm 缓存指向项目内，避免全局缓存权限问题
set npm_config_cache=%CD%\.npm-cache
pushd frontend
call npm install --no-audit --no-fund
if errorlevel 1 goto npm_fail
call npm run build
if errorlevel 1 goto build_fail
popd
goto frontend_done

:npm_fail
echo [错误] npm install 失败
popd
exit /b 1

:build_fail
echo [错误] 前端构建失败
popd
exit /b 1

:no_node
echo [!] 未找到 node，跳过前端构建（仅提供 API，可访问 /api/docs）

:frontend_done

REM ---------------------------------------------------------- 环境变量
if exist ".env" goto env_ready
if not exist ".env.example" goto env_ready
copy /y ".env.example" ".env" >nul
echo [!] 已从 .env.example 生成 .env，请按需修改（尤其是 ATF_SECRET_KEY）

:env_ready
if defined ATF_PORT goto port_ready
set ATF_PORT=8899
:port_ready

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

REM ============================================================
REM  失败分支
REM ============================================================
:venv_fail
echo [错误] 创建或激活虚拟环境失败
exit /b 1

:deps_fail
echo [错误] 依赖安装失败
exit /b 1

REM ============================================================
REM  Docker 模式
REM ============================================================
:docker_mode
where docker >nul 2>&1
if errorlevel 1 goto no_docker

echo [*] 使用 docker compose 启动...
docker compose up --build -d
if errorlevel 1 goto docker_fail

echo [*] 等待服务就绪...
set /a WAIT_N=0
:wait_loop
set /a WAIT_N+=1
if %WAIT_N% GTR 30 goto docker_timeout
curl -fsS http://127.0.0.1:8899/api/v1/health >nul 2>&1
if not errorlevel 1 goto docker_ok
timeout /t 1 /nobreak >nul
goto wait_loop

:docker_ok
echo.
echo [OK] 已启动：http://127.0.0.1:8899
echo      查看日志：docker compose logs -f
echo      停止服务：docker compose down
exit /b 0

:docker_timeout
echo [!] 等待超时，请用 docker compose logs 查看日志
exit /b 1

:no_docker
echo [错误] 未找到 docker，请先安装 Docker Desktop
exit /b 1

:docker_fail
echo [错误] docker compose 启动失败
exit /b 1

REM ============================================================
:usage
echo 用法：
echo   start.bat            启动服务
echo   start.bat --rebuild  强制重建前端后启动
echo   start.bat --docker   使用 docker compose 启动
exit /b 0

:end
endlocal
