import socketserver
import http.server
import http.cookies
import os
import threading
import json
import urllib.parse
from generator.builder import StaticSiteGenerator
from generator.watcher import DBWatcher
from dao.factory import create_connection
from dao.auth_dao import MySQLAuthDAO
from core.auth import user_login, user_register, change_password, verify_token
from verification import manager as verify_manager

PID_FILE = "server.pid"
WEB_ROOT = "public"

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
                    verify_token(token)
                    return True
            except Exception:
                pass
            return False

        def do_GET(self):
            # 拦截 settings.html，未登录直接返回 404 Not Found
            if self.path == '/settings.html' or self.path.startswith('/settings.html?'):
                if not self._check_auth_cookie():
                    self.send_error(404, "Not Found")
                    return

            # 解析查询字符串
            parsed_path = urllib.parse.urlparse(self.path)
            query_params = urllib.parse.parse_qs(parsed_path.query)
            
            # API: 获取当前用户的绑定列表
            if parsed_path.path == '/api/auth/bindings':
                try:
                    token = self.headers.get('Authorization')
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
            
            # API: 查询验证会话状态
            elif parsed_path.path == '/api/auth/status':
                try:
                    session_id = query_params.get('session_id', [None])[0]
                    if not session_id:
                        self.send_error(400, "Missing session_id")
                        return
                    
                    status = verify_manager.session_get_status(session_id)
                    self._send_json(status)
                except Exception as e:
                    self.send_error(400, str(e))
            
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
                    # 注册并获取 UserID
                    uid = user_register(data.get('username'), data.get('password'))
                    
                    # [修复] 注册成功后立即生成用户首页
                    # 避免前端跳转时出现 404
                    try:
                        gen = StaticSiteGenerator(WEB_ROOT)
                        gen.sync_user_index(uid)
                        print(f"[*] Initial index generated for user {uid}")
                    except Exception as gen_err:
                        print(f"[-] Failed to generate initial index: {gen_err}")
                    
                    self._send_json({'status': 'ok'})
                
                elif self.path == '/api/change_password':
                    token = self.headers.get('Authorization')
                    change_password(token, data.get('old_password'), data.get('new_password'))
                    self._send_json({'status': 'ok'})
                
                # --- 验证会话 APIs ---
                elif self.path == '/api/auth/init':
                    """初始化验证会话"""
                    try:
                        token = self.headers.get('Authorization')
                        if not token and "Cookie" in self.headers:
                            cookie = http.cookies.SimpleCookie(self.headers["Cookie"])
                            if "mc_token" in cookie:
                                token = cookie["mc_token"].value
                        
                        user_id = verify_token(token)
                        platform = data.get('platform')
                        session_id = verify_manager.session_init(user_id, platform)
                        
                        if session_id:
                            self._send_json({
                                'session_id': session_id,
                                'status': 'initialized',
                                'platform': platform,
                            })
                        else:
                            self.send_error(400, "Failed to initialize session")
                    except Exception as e:
                        self.send_error(400, str(e))
                
                elif self.path == '/api/auth/save_cookies':
                    """本地客户端发送已验证的 Cookies"""
                    try:
                        session_id = data.get('session_id')
                        cookies = data.get('cookies', [])
                        
                        if verify_manager.session_save_cookies(session_id, cookies):
                            self._send_json({'status': 'ok'})
                        else:
                            self.send_error(400, "Failed to save cookies")
                    except Exception as e:
                        self.send_error(400, str(e))
                
                elif self.path == '/api/auth/save_error':
                    """本地客户端报告验证错误"""
                    try:
                        session_id = data.get('session_id')
                        error_msg = data.get('error')
                        
                        verify_manager.session_save_error(session_id, error_msg)
                        self._send_json({'status': 'ok'})
                    except Exception as e:
                        self.send_error(400, str(e))
                
                elif self.path == '/api/auth/cancel':
                    """取消验证会话"""
                    try:
                        session_id = data.get('session_id')
                        verify_manager.session_close(session_id)
                        self._send_json({'status': 'cancelled'})
                    except Exception as e:
                        self.send_error(400, str(e))

                elif self.path == '/api/auth/unbind':
                    """解除绑定"""
                    try:
                        token = self.headers.get('Authorization')
                        if not token and "Cookie" in self.headers:
                            cookie = http.cookies.SimpleCookie(self.headers["Cookie"])
                            if "mc_token" in cookie:
                                token = cookie["mc_token"].value
                        
                        user_id = verify_token(token)
                        platform = data.get('platform')
                        
                        conn = create_connection()
                        try:
                            dao = MySQLAuthDAO(conn)
                            dao.remove_platform_auth(user_id, platform)
                        finally:
                            conn.close()
                        
                        self._send_json({'status': 'ok'})
                    except Exception as e:
                        self.send_error(400, str(e))

                else:
                    self.send_error(404)
            except Exception as e:
                self.send_response(400)
                self.wfile.write(json.dumps({'error': str(e)}).encode())

        def _send_json(self, data):
            self.send_response(200)
            self.send_header('Content-type', 'application/json')
            self.send_header('Access-Control-Allow-Origin', '*')
            self.end_headers()
            self.wfile.write(json.dumps(data).encode())

    print(f"[+] Server started on port {port} (Multi-threaded).")
    try:
        with ThreadingHTTPServer(("0.0.0.0", port), Handler) as httpd:
            httpd.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        watcher.stop()
        if os.path.exists(PID_FILE): os.remove(PID_FILE)