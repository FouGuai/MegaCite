import socketserver
import http.server
import os
import threading
from generator.builder import StaticSiteGenerator
from generator.watcher import DBWatcher
from dao.factory import create_connection

PID_FILE = "server.pid"
WEB_ROOT = "public"

class ReuseAddrTCPServer(socketserver.TCPServer):
    allow_reuse_address = True

def server_start(port: int) -> None:
    try:
        conn = create_connection()
        conn.ping()
        conn.close()
    except Exception as e:
        print(f"[-] Database connection failed: {e}")
        return

    with open(PID_FILE, "w") as f:
        f.write(str(os.getpid()))

    gen = StaticSiteGenerator(WEB_ROOT)
    watcher = DBWatcher(gen)
    
    t_watcher = threading.Thread(target=watcher.start, args=(3,), daemon=True)
    t_watcher.start()

    abs_root = os.path.abspath(WEB_ROOT)
    if not os.path.exists(abs_root):
        os.makedirs(abs_root)

    class Handler(http.server.SimpleHTTPRequestHandler):
        def __init__(self, *args, **kwargs):
            super().__init__(*args, directory=abs_root, **kwargs)
        
        def log_message(self, format, *args):
            pass

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