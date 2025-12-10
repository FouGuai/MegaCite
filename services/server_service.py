import socketserver
import http.server
import os
import threading
import socket
from services.static_gen import StaticSiteGenerator
from services.watcher import DBWatcher
from services.db import create_connection

PID_FILE = "server.pid"

class ReuseAddrTCPServer(socketserver.TCPServer):
    allow_reuse_address = True

def server_start(port: int) -> None:
    """
    启动 HTTP 服务器和数据库监听器。
    此函数会阻塞主线程，直到收到中断信号。
    """
    # 1. 基础检查
    try:
        conn = create_connection()
        conn.ping()
        conn.close()
    except Exception as e:
        print(f"[-] Database connection failed: {e}")
        return

    # 2. 写入 PID 文件 (用于后续 stop 命令)
    with open(PID_FILE, "w") as f:
        f.write(str(os.getpid()))

    # 3. 初始化静态生成器和监听器
    root_dir = "public/"
    gen = StaticSiteGenerator(root_dir)
    watcher = DBWatcher(gen)
    
    # 4. 在后台线程启动 Watcher
    t_watcher = threading.Thread(target=watcher.start, args=(3,), daemon=True)
    t_watcher.start()

    # 5. 启动 HTTP Server
    abs_root = os.path.abspath(root_dir)
    
    class Handler(http.server.SimpleHTTPRequestHandler):
        def __init__(self, *args, **kwargs):
            # 指定目录为 www
            super().__init__(*args, directory=abs_root, **kwargs)
        
        def log_message(self, format, *args):
            # 简化日志输出，避免刷屏
            pass

    print(f"[+] Server started on port {port}. Web root: {abs_root}")
    print("[*] Press Ctrl+C to stop.")

    try:
        with ReuseAddrTCPServer(("0.0.0.0", port), Handler) as httpd:
            httpd.serve_forever()
    except KeyboardInterrupt:
        print("\n[*] Stopping server...")
    finally:
        if os.path.exists(PID_FILE):
            os.remove(PID_FILE)