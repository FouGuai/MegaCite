import socketserver
import http.server
import os
import threading
from services.static_gen import StaticSiteGenerator
from services.watcher import DBWatcher
from services.db import create_connection

PID_FILE = "server.pid"
WEB_ROOT = "public"

class ReuseAddrTCPServer(socketserver.TCPServer):
    allow_reuse_address = True

def server_start(port: int) -> None:
    # 1. 检查数据库连接
    try:
        conn = create_connection()
        conn.ping()
        conn.close()
    except Exception as e:
        print(f"[-] Database connection failed: {e}")
        return

    # 2. 写入 PID
    with open(PID_FILE, "w") as f:
        f.write(str(os.getpid()))

    # 3. 初始化组件 (指向 public 目录)
    gen = StaticSiteGenerator(WEB_ROOT)
    watcher = DBWatcher(gen)
    
    # 4. 后台启动 Watcher
    t_watcher = threading.Thread(target=watcher.start, args=(3,), daemon=True)
    t_watcher.start()

    # 5. 启动 HTTP Server
    abs_root = os.path.abspath(WEB_ROOT)
    if not os.path.exists(abs_root):
        os.makedirs(abs_root)

    class Handler(http.server.SimpleHTTPRequestHandler):
        def __init__(self, *args, **kwargs):
            # 严格服务于 public 目录
            super().__init__(*args, directory=abs_root, **kwargs)
        
        def log_message(self, format, *args):
            pass # 静默模式

    print(f"[+] Server started on port {port}.")
    print(f"[+] Root: {abs_root}")
    print(f"[+] Example: http://localhost:{port}/<username>/index.html")
    print("[*] Press Ctrl+C to stop.")

    try:
        with ReuseAddrTCPServer(("0.0.0.0", port), Handler) as httpd:
            httpd.serve_forever()
    except KeyboardInterrupt:
        print("\n[*] Stopping server...")
    finally:
        watcher.stop()
        if os.path.exists(PID_FILE):
            os.remove(PID_FILE)