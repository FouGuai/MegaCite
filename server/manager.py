import socketserver
import http.server
import http.cookies
import os
import threading
import json
from generator.builder import StaticSiteGenerator
from generator.watcher import DBWatcher
from dao.factory import create_connection
from dao.auth_dao import MySQLAuthDAO
from core.auth import user_login, user_register, change_password, verify_token
from verification import manager as verify_manager

PID_FILE = "server.pid"
WEB_ROOT = "public"

# [核心修复] 使用 ThreadingMixIn 实现多线程并发 HTTP 服务器
# 这彻底解决了前端在轮询截图时，后续的点击交互请求被阻塞的问题
class ThreadingHTTPServer(socketserver.ThreadingMixIn, http.server.HTTPServer):
    daemon_threads = True

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

    os.makedirs(WEB_ROOT, exist_ok=True)
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

        def _check_auth_cookie(self):
            """检查 HTTP Cookie 中的 Token 是否有效"""
            if "Cookie" not in self.headers:
                return False
            try:
                cookie = http.cookies.SimpleCookie(self.headers["Cookie"])
                if "mc_token" in cookie:
                    token = cookie["mc_token"].value
                    verify_token(token) # 验证失败会抛出异常
                    return True
            except Exception:
                pass
            return False

        def do_GET(self):
            # [需求] 拦截 settings.html，未登录直接返回 404 Not Found
            # 防止用户通过 URL 直接访问设置页
            if self.path == '/settings.html' or self.path.startswith('/settings.html?'):
                if not self._check_auth_cookie():
                    self.send_error(404, "Not Found")
                    return

            # API: 获取远程浏览器截图流
            if self.path == '/api/auth/screenshot':
                b64 = verify_manager.session_get_screenshot()
                self._send_json({'image': b64})
            
            # API: 获取会话状态 (是否登录成功)
            elif self.path == '/api/auth/status':
                is_success = verify_manager.session_check_status()
                self._send_json({'status': 'success' if is_success else 'waiting'})
            
            # API: 获取当前用户的绑定列表 (用于前端渲染按钮状态：绑定 vs 重新绑定)
            elif self.path == '/api/auth/bindings':
                try:
                    # 优先尝试从 Header 获取 Token
                    token = self.headers.get('Authorization')
                    # 如果 Header 没有，尝试从 Cookie 获取 (兼容页面直接刷新)
                    if not token and "Cookie" in self.headers:
                        cookie = http.cookies.SimpleCookie(self.headers["Cookie"])
                        if "mc_token" in cookie:
                            token = cookie["mc_token"].value
                            
                    user_id = verify_token(token)
                    conn = create_connection()
                    dao = MySQLAuthDAO(conn)
                    platforms = dao.list_platform_auths(user_id)
                    conn.close()
                    self._send_json({'bindings': platforms})
                except Exception:
                    self._send_json({'bindings': []})
            
            else:
                super().do_GET()

        def do_POST(self):
            content_length = int(self.headers.get('Content-Length', 0))
            body = self.rfile.read(content_length)
            
            try:
                data = json.loads(body) if body else {}
                
                if self.path == '/api/login':
                    token = user_login(data.get('username'), data.get('password'))
                    self._send_json({'token': token})
                elif self.path == '/api/register':
                    user_register(data.get('username'), data.get('password'))
                    self._send_json({'status': 'ok'})
                elif self.path == '/api/change_password':
                    token = self.headers.get('Authorization')
                    change_password(token, data.get('old_password'), data.get('new_password'))
                    self._send_json({'status': 'ok'})
                
                # --- Auth Session APIs ---
                elif self.path == '/api/auth/init':
                    if verify_manager.session_start(data.get('platform')):
                        self._send_json({'status': 'started'})
                    else:
                        self.send_error(400, "Start failed. Check logs.")
                
                elif self.path == '/api/auth/interact':
                    verify_manager.session_handle_interaction(
                        data.get('type'), data
                    )
                    self._send_json({'status': 'ok'})

                elif self.path == '/api/auth/cancel':
                    verify_manager.session_close()
                    self._send_json({'status': 'cancelled'})
                else:
                    self.send_error(404)
            except Exception as e:
                self.send_response(400)
                self.wfile.write(json.dumps({'error': str(e)}).encode())

        def _send_json(self, data):
            self.send_response(200)
            self.send_header('Content-type', 'application/json')
            self.end_headers()
            self.wfile.write(json.dumps(data).encode())

    print(f"[+] Server started on port {port} (Multi-threaded).")
    try:
        # 使用 ThreadingHTTPServer 启动
        with ThreadingHTTPServer(("0.0.0.0", port), Handler) as httpd:
            httpd.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        watcher.stop()
        if os.path.exists(PID_FILE): os.remove(PID_FILE)