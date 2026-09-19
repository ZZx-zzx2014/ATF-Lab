"""
ATF Lab - netlab 仿真服务验证

⚠️ 仅供教学演示：验证仿真服务只回预置静态文本。
"""
import socket
import sys


def talk(port, payload=None, wait=1.2):
    try:
        s = socket.create_connection(("127.0.0.1", port), timeout=4)
    except OSError as e:
        return "CONNECT_FAIL %s" % e
    s.settimeout(wait)
    data = b""
    try:
        while True:
            chunk = s.recv(2048)
            if not chunk:
                break
            data += chunk
            if payload:
                break
    except socket.timeout:
        pass
    if payload:
        try:
            s.sendall(payload.encode())
            s.settimeout(wait)
            while True:
                chunk = s.recv(2048)
                if not chunk:
                    break
                data += chunk
        except socket.timeout:
            pass
    s.close()
    return data.decode("utf-8", "replace")


def main():
    out = []

    out.append("=== FTP 2121 (banner) ===")
    out.append(talk(2121)[:300])

    out.append("\n=== Redis 16379: INFO ===")
    out.append(talk(16379, "INFO\r\n")[:400])

    out.append("\n=== Redis 16379: KEYS * ===")
    out.append(talk(16379, "KEYS *\r\n")[:300])

    out.append("\n=== Redis 16379: GET helios:flag:readonly ===")
    out.append(talk(16379, "GET helios:flag:readonly\r\n")[:300])

    out.append("\n=== Redis 16379: 未知命令（应回 ERR 且不执行）===")
    out.append(talk(16379, "SHUTDOWN NOSAVE\r\n")[:200])

    out.append("\n=== Redis 16379: CONFIG GET dir ===")
    out.append(talk(16379, "CONFIG GET dir\r\n")[:300])

    out.append("\n=== Debug 31337: CONFIG ===")
    out.append(talk(31337, "CONFIG\r\n")[:400])

    out.append("\n=== Debug 31337: ENV ===")
    out.append(talk(31337, "ENV\r\n")[:300])

    out.append("\n=== Debug 31337: 危险命令（应被拒绝）===")
    out.append(talk(31337, "EXEC rm -rf /\r\n")[:200])

    out.append("\n=== MySQL 13306 (handshake) ===")
    out.append(repr(talk(13306)[:200]))

    # 安全边界自查
    out.append("\n=== 安全边界自查 ===")
    src = open("netlab/services.py", encoding="utf-8").read()
    banned = ["subprocess", "os.system", "os.popen", "eval(", "exec(",
              "connect((", "requests.", "urllib.request", "open("]
    for b in banned:
        # connect(( 是允许的（服务端 accept），这里只查客户端连接
        pass
    checks = {
        "无 subprocess": "subprocess" not in src,
        "无 os.system": "os.system" not in src,
        "无 eval/exec": ("eval(" not in src and "exec(" not in src),
        "无出站连接 socket.connect": "socket.create_connection" not in src
                                    and ".connect(" not in src,
        "无文件写入": "'w'" not in src and '"w"' not in src,
        "仅绑定回环": 'bind(("127.0.0.1"' in src,
    }
    for k, v in checks.items():
        out.append("%s %s" % ("PASS" if v else "FAIL", k))

    txt = "\n".join(out)
    open("netlab_result.txt", "w", encoding="utf-8").write(txt)
    print("netlab verification written to netlab_result.txt")


if __name__ == "__main__":
    sys.exit(main())
