import http.server
import socketserver
import os
import threading
from services.static_gen import StaticSiteGenerator
from services.watcher import DBWatcher

def run_http_server(port: int, root_dir: str):
    """启动 HTTP 服务，阻塞运行"""
    # 切换当前工作目录到静态网站根目录，这样 handler 默认服务当前目录
    # 注意：这会改变整个进程的工作目录，需谨慎。
    # 更安全的方法是自定义 Handler 的 directory，但 Python 3.7+ 才支持 directory 参数
    # 这里假设 Python 环境较新
    
    abs_root = os.path.abspath(root_dir)
    
    class Handler(http.server.SimpleHTTPRequestHandler):
        def __init__(self, *args, **kwargs):
            super().__init__(*args, directory=abs_root, **kwargs)

    print(f"[*] Starting HTTP Server on port {port} serving {abs_root}")
    with socketserver.TCPServer(("0.0.0.0", port), Handler) as httpd:
        try:
            httpd.serve_forever()
        except KeyboardInterrupt:
            pass
        finally:
            httpd.server_close()

def start_full_service(port: int = 8080):
    """
    启动所有服务：Watcher 和 HTTP Server
    """
    gen = StaticSiteGenerator("www")
    watcher = DBWatcher(gen)
    
    # 在独立线程中启动 Watcher
    t_watcher = threading.Thread(target=watcher.start, args=(2,), daemon=True)
    t_watcher.start()
    
    # 主线程运行 HTTP Server
    run_http_server(port, "www")

if __name__ == "__main__":
    # 如果直接运行此文件
    start_full_service()