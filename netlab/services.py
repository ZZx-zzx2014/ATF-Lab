"""
ATF Lab - 仿真网络服务（netlab）

⚠️⚠️ 仅供教学演示（CONTROLLED SIMULATION）⚠️⚠️

本模块监听多个端口，模拟常见服务的 banner 与响应，供玩家练习
nmap / nc / redis-cli 等工具的使用。

【硬性安全边界】
  - 只返回**预置的静态文本**，不做任何协议解析后的动态行为
  - **绝不建立任何出站连接**（不连接数据库、不代理、不做端口转发）
  - **绝不读写任何文件**（不实现 Redis 的 RDB/AOF 落盘）
  - **绝不执行任何命令**
  - 仅监听 127.0.0.1（默认），不对外暴露

端口分配：
  2121  仿 FTP
  3306  仿 MySQL
  6379  仿 Redis
  31337 仿调试服务
"""

import socket
import threading
import time

from backend.config import settings

# ==================================================================
# 预置响应文本 —— 全部为静态常量
# ==================================================================

FTP_BANNER = (
    "220 Helios-FTP (vsFTPd 3.0.3-sim) ready.\r\n"
    "230 Login successful (anonymous).\r\n"
    "⚠️ 仿真服务：以上为预置文本，不存在真实文件系统。\r\n"
)

MYSQL_BANNER = (
    "\x4a\x00\x00\x00\x0a"          # 协议版本 + 服务版本长度（模拟握手前缀）
    "5.7.42-sim\x00"
    "\x0b\x00\x00\x00" "3f2a1b4c\x00"
    "mysql_native_password\x00"
    "⚠️ 仿真 MySQL 握手包：预置文本，不接受任何认证。\r\n"
)

REDIS_INFO = (
    "# Server\r\n"
    "redis_version:6.2.6-sim\r\n"
    "redis_mode:standalone\r\n"
    "os:Linux 5.15.0-sim x86_64\r\n"
    "arch_bits:64\r\n"
    "process_id:1337\r\n"
    "tcp_port:6379\r\n"
    "uptime_in_seconds:86400\r\n"
    "# Clients\r\n"
    "connected_clients:1\r\n"
    "# Stats\r\n"
    "total_connections_received:42\r\n"
    "# Replication\r\n"
    "role:master\r\n"
    "# Keyspace\r\n"
    "db0:keys=1,expires=0,avg_ttl=0\r\n"
    "⚠️ 仿真 Redis：以上为预置文本，无真实数据。\r\n"
)

REDIS_KEYS = (
    "*1\r\n"
    "$20\r\n"
    "helios:flag:readonly\r\n"
    "⚠️ 仿真 Redis：此 key 为教学占位，值为虚构 flag。\r\n"
)

REDIS_GET = (
    "$33\r\n"
    "flag{redis_unauthorized_access}\r\n"
    "⚠️ 仿真 Redis：以上为预置文本。\r\n"
)

REDIS_CONFIG = (
    "*6\r\n"
    "$3\r\n" "dir\r\n" "$15\r\n" "/var/lib/redis\r\n"
    "$8\r\n" "dbfilename\r\n" "$9\r\n" "dump.rdb\r\n"
    "⚠️ 仿真 Redis：仅回显预置配置，不接受任何写入。\r\n"
)

REDIS_PROTECTED = (
    "-NOAUTH Authentication required.\r\n"
    "⚠️ 仿真 Redis：本服务不实现真实认证，此响应为教学演示。\r\n"
)

DEBUG_BANNER = (
    "Helios Debug Service v3.4.1-sim\r\n"
    "=================================\r\n"
    "WARNING: debug endpoint exposed (simulated)\r\n"
    "\r\n"
    "Available commands:\r\n"
    "  HELP    显示帮助\r\n"
    "  CONFIG  显示服务配置\r\n"
    "  ENV     显示环境变量\r\n"
    "  STATUS  显示运行状态\r\n"
    "  QUIT    断开连接\r\n"
    "\r\n"
    "⚠️ 仿真服务：所有响应均为预置文本，不执行任何真实操作。\r\n"
)

DEBUG_CONFIG = (
    "--- service config (simulated) ---\r\n"
    "debug_mode       = true\r\n"
    "expose_internals = true\r\n"
    "admin_endpoint   = /helios/portal/admin\r\n"
    "archive_service  = http://internal.helios-sim.invalid/archive\r\n"
    "internal_note    = flag{debug_service_misconfig}\r\n"
    "⚠️ 以上为预置文本，不含任何真实凭据。\r\n"
)

DEBUG_ENV = (
    "--- environment (simulated) ---\r\n"
    "APP_ENV      = production\r\n"
    "DEBUG        = true\r\n"
    "DB_HOST      = 127.0.0.1\r\n"
    "DB_PASSWORD  = SIMULATED_NOT_A_REAL_PASSWORD\r\n"
    "⚠️ 以上为预置文本，不含任何真实凭据。\r\n"
)

DEBUG_STATUS = (
    "status      = running\r\n"
    "uptime      = 86400s\r\n"
    "connections = 7\r\n"
    "version     = 3.4.1-sim\r\n"
    "⚠️ 以上为预置文本。\r\n"
)


# ==================================================================
# 通用服务实现
# ==================================================================

class _Service(threading.Thread):
    """⚠️ 仅供教学演示：一个只回静态文本的 TCP 服务。

    设计上刻意保持"哑"：不接受参数、不解析协议、不产生副作用。
    """

    def __init__(self, name: str, port: int, banner: str, handler=None,
                 fallback_ports=()):
        super().__init__(daemon=True, name="netlab-%s" % name)
        self.svc_name = name
        self.port = port
        self.requested_port = port
        self.fallback_ports = list(fallback_ports)
        self.banner = banner
        self.handler = handler
        self.sock = None
        self.ready = threading.Event()
        self.error = None

    def _try_bind(self, port: int):
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        # ⚠️ 仅绑定回环地址：不对外网暴露，也不接受任何外部连接
        s.bind(("127.0.0.1", port))
        s.listen(16)
        return s

    def run(self):
        candidates = [self.requested_port] + self.fallback_ports
        last_err = None
        for port in candidates:
            try:
                self.sock = self._try_bind(port)
                self.port = port
                self.error = None
                self.ready.set()
                break
            except OSError as e:
                last_err = "port %d: %s" % (port, e.strerror or e)
                continue

        if self.sock is None:
            self.error = last_err or "无法绑定任何候选端口"
            self.ready.set()
            return

        while True:
            try:
                conn, _addr = s_accept(self.sock)
            except OSError:
                break
            threading.Thread(target=self._serve, args=(conn,), daemon=True).start()

    def _serve(self, conn: socket.socket):
        try:
            conn.settimeout(10)
            if self.banner:
                conn.sendall(self.banner.encode("utf-8", "replace"))
            if self.handler is None:
                # 无交互服务：发完 banner 稍候即关闭
                time.sleep(0.4)
                return
            buf = b""
            while True:
                try:
                    chunk = conn.recv(1024)
                except socket.timeout:
                    break
                if not chunk:
                    break
                buf += chunk
                line = buf.decode("utf-8", "replace").strip()
                reply = self.handler(line)
                if reply is None:
                    break
                conn.sendall(reply.encode("utf-8", "replace"))
                buf = b""
        except Exception:
            pass
        finally:
            try:
                conn.close()
            except Exception:
                pass

    def stop(self):
        if self.sock:
            try:
                self.sock.close()
            except Exception:
                pass


# ==================================================================
# Redis 仿真交互（⚠️ 纯字符串匹配，无真实数据操作）
# ==================================================================

def _redis_handler(line: str):
    up = line.upper()
    if not up:
        return None
    if up.startswith("QUIT"):
        return None
    if up.startswith("INFO"):
        return REDIS_INFO
    if up.startswith("KEYS"):
        return REDIS_KEYS
    if up.startswith("GET"):
        return REDIS_GET
    if up.startswith("CONFIG"):
        return REDIS_CONFIG
    if up.startswith("PING"):
        return "+PONG\r\n"
    if up.startswith("AUTH"):
        return REDIS_PROTECTED
    if up in ("COMMAND DOCS", "COMMAND"):
        return "*0\r\n"
    return ("-ERR unknown command '%s' (simulated)\r\n"
            "⚠️ 仿真 Redis：仅支持少量只读命令。\r\n" % line[:32])


# ==================================================================
# 调试服务仿真交互（⚠️ 只回预置常量，不执行任何操作）
# ==================================================================

def _debug_handler(line: str):
    up = line.upper()
    if not up:
        return None
    if up.startswith("QUIT") or up.startswith("EXIT"):
        return None
    if up.startswith("HELP"):
        return DEBUG_BANNER
    if up.startswith("CONFIG"):
        return DEBUG_CONFIG
    if up.startswith("ENV"):
        return DEBUG_ENV
    if up.startswith("STATUS"):
        return DEBUG_STATUS
    return ("unknown command: %s\r\n"
            "⚠️ 仿真服务：不执行任何真实操作。\r\n" % line[:32])


# ==================================================================
# 启动 / 停止
# ==================================================================

_services: list = []


def s_accept(sock):
    """薄封装：便于集中管理 accept 行为。"""
    return sock.accept()


def start_all() -> list:
    """
    启动全部仿真服务，返回状态列表。

    注意：某些系统（尤其是启用了 Hyper-V / WSL 的 Windows）会保留或
    拒绝绑定 3306、6379 这类常用端口。因此每个服务都配置了备用端口，
    最终实际监听的端口会在 status_all() 中如实上报，前端据此展示。
    """
    global _services
    if _services:
        return status_all()

    specs = [
        # name, 首选端口, 备用端口, banner, handler
        ("ftp", settings.NETLAB_FTP_PORT, (2021,), FTP_BANNER, None),
        ("mysql", settings.NETLAB_MYSQL_PORT, (13306, 33306), MYSQL_BANNER, None),
        ("redis", settings.NETLAB_REDIS_PORT, (16379, 26379), "", _redis_handler),
        ("debug", settings.NETLAB_DEBUG_PORT, (31338,), DEBUG_BANNER, _debug_handler),
    ]
    for name, port, fallbacks, banner, handler in specs:
        svc = _Service(name, port, banner, handler, fallback_ports=fallbacks)
        svc.start()
        _services.append(svc)

    for svc in _services:
        svc.ready.wait(timeout=3)
    return status_all()


def status_all() -> list:
    out = []
    for svc in _services:
        running = svc.is_alive() and svc.error is None
        out.append({
            "name": svc.svc_name,
            "port": svc.port,
            "requested_port": svc.requested_port,
            "fell_back": running and svc.port != svc.requested_port,
            "running": running,
            "error": svc.error,
            "host": "127.0.0.1",
        })
    return out


def stop_all() -> None:
    global _services
    for svc in _services:
        svc.stop()
    _services = []
