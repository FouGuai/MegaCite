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
from dao.post_dao import MySQLPostDAO
from dao.user_dao import MySQLUserDAO
from dao.url_map_dao import MySQLUrlMapDAO
from core.auth import user_login, user_register, change_password, verify_token
from core.post import post_create, post_delete, post_get_full, post_update_content
from crawler.service import migrate_post_from_url
from verification import manager as verify_manager

PID_FILE = "server.pid"
WEB_ROOT = "public"

# [Global Generator Instance]
SERVER_GEN = None

class ThreadingHTTPServer(socketserver.ThreadingMixIn, http.server.HTTPServer):
    daemon_threads = True

def force_sync_post(cid: str, user_id: int):
    """
    [同步渲染逻辑 - 更新/新增]
    """
    if not SERVER_GEN: return

    conn = create_connection()
    try:
        post_dao = MySQLPostDAO(conn)
        title = post_dao.get_field(cid, "title")
        category = post_dao.get_field(cid, "category")
        date = post_dao.get_field(cid, "date")
        context = post_dao.get_field(cid, "context")
        desc = post_dao.get_field(cid, "description")
        
        post_data = {
            "cid": cid,
            "title": title,
            "category": category,
            "date": str(date),
            "context": context,
            "description": desc
        }
        
        user_dao = MySQLUserDAO(conn)
        user = user_dao.get_user_by_id(user_id)
        if not user: return
        username = user.username
        
        print(f"[Sync] Force generating files for {cid}...")
        SERVER_GEN.sync_post_file(post_data, username)
        SERVER_GEN.sync_user_index(user_id)
        print(f"[Sync] Done.")
    finally:
        conn.close()

def force_sync_delete(cid: str, user_id: int):
    """
    [同步渲染逻辑 - 删除]
    移除对应的静态文件并重建用户索引页。
    """
    if not SERVER_GEN: return
    
    print(f"[Sync] Force removing files for {cid}...")
    # 1. 物理删除文章 HTML
    SERVER_GEN.remove_post_file(cid)
    
    # 2. 刷新索引页
    SERVER_GEN.sync_user_index(user_id)
    print(f"[Sync] Delete Done.")


def server_start(port: int) -> None:
    global SERVER_GEN
    
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
    
    # 初始化全局 Generator
    SERVER_GEN = StaticSiteGenerator(WEB_ROOT)
    watcher = DBWatcher(SERVER_GEN)
    
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

        def _get_token(self):
            token = self.headers.get('Authorization')
            if not token and "Cookie" in self.headers:
                cookie = http.cookies.SimpleCookie(self.headers["Cookie"])
                if "mc_token" in cookie:
                    token = cookie["mc_token"].value
            return token

        def do_GET(self):
            # 拦截 settings.html 和 edit.html，未登录直接返回 404
            if self.path.startswith('/settings.html') or self.path.startswith('/edit.html'):
                if not self._check_auth_cookie():
                    self.send_error(404, "Not Found")
                    return

            parsed_path = urllib.parse.urlparse(self.path)
            query_params = urllib.parse.parse_qs(parsed_path.query)
            
            if parsed_path.path == '/api/auth/bindings':
                try:
                    token = self._get_token()
                    user_id = verify_token(token)
                    conn = create_connection()
                    dao = MySQLAuthDAO(conn)
                    platforms = dao.list_platform_auths(user_id)
                    conn.close()
                    self._send_json({'bindings': platforms})
                except Exception:
                    self._send_json({'bindings': []})
            
            elif parsed_path.path == '/api/auth/watch':
                try:
                    session_id = query_params.get('session_id', [None])[0]
                    if not session_id:
                        self.send_error(400, "Missing session_id")
                        return

                    self.send_response(200)
                    self.send_header('Content-Type', 'text/event-stream')
                    self.send_header('Cache-Control', 'no-cache')
                    self.send_header('Connection', 'keep-alive')
                    self.send_header('Access-Control-Allow-Origin', '*')
                    self.end_headers()

                    status = verify_manager.session_wait(session_id, timeout=120)
                    
                    payload = json.dumps(status)
                    self.wfile.write(f"data: {payload}\n\n".encode('utf-8'))
                    self.wfile.flush()
                    return

                except Exception as e:
                    print(f"SSE Error: {e}")

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
            
            elif parsed_path.path == '/api/post/detail':
                try:
                    token = self._get_token()
                    cid = query_params.get('cid', [None])[0]
                    if not cid:
                        self.send_error(400, "Missing cid")
                        return
                    
                    data = post_get_full(token, cid)
                    self._send_json(data)
                except Exception as e:
                    self.send_error(400, str(e))

            elif parsed_path.path == '/api/categories':
                try:
                    conn = create_connection()
                    dao = MySQLPostDAO(conn)
                    cats = dao.get_all_categories()
                    conn.close()
                    self._send_json({'categories': cats})
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
                    try:
                        user_id = verify_token(token)
                        if SERVER_GEN:
                            print(f"[*] Login Sync: Generating index for user {user_id}")
                            SERVER_GEN.sync_user_index(user_id)
                    except Exception as e:
                        print(f"[-] Login Sync Failed: {e}")

                    self._send_json({'token': token})
                
                elif self.path == '/api/register':
                    uid = user_register(data.get('username'), data.get('password'))
                    try:
                        if SERVER_GEN:
                            SERVER_GEN.sync_user_index(uid)
                    except Exception:
                        pass
                    self._send_json({'status': 'ok'})
                
                elif self.path == '/api/change_password':
                    try:
                        token = self._get_token()
                        change_password(token, data.get('old_password'), data.get('new_password'))
                        self._send_json({'status': 'ok'})
                    except ValueError as ve:
                        self.send_response(400)
                        self.send_header('Content-type', 'application/json')
                        self.end_headers()
                        self.wfile.write(json.dumps({'error': str(ve)}).encode())
                        return

                elif self.path == '/api/post/create':
                    try:
                        token = self._get_token()
                        user_id = verify_token(token)
                        cid = post_create(token)
                        force_sync_post(cid, user_id)
                        self._send_json({'status': 'ok', 'cid': cid})
                    except Exception as e:
                         self.send_error(400, str(e))
                
                elif self.path == '/api/post/update':
                    try:
                        token = self._get_token()
                        user_id = verify_token(token)
                        
                        cid = data.get('cid')
                        title = data.get('title')
                        category = data.get('category')
                        context = data.get('context')
                        description = data.get('description') # [新增] 读取摘要
                        
                        if post_update_content(token, cid, title, category, context, description):
                            force_sync_post(cid, user_id)
                            
                            # 获取文章的最新 URL 返回给前端跳转
                            target_url = None
                            conn = create_connection()
                            try:
                                map_dao = MySQLUrlMapDAO(conn)
                                target_url = map_dao.get_url_by_cid(cid)
                            finally:
                                conn.close()
                                
                            self._send_json({'status': 'ok', 'url': target_url})
                        else:
                            self.send_error(400, "Update failed")
                    except Exception as e:
                        self.send_error(400, str(e))

                elif self.path == '/api/post/delete':
                    try:
                        token = self._get_token()
                        user_id = verify_token(token)
                        cid = data.get('cid')
                        
                        if post_delete(token, cid):
                            force_sync_delete(cid, user_id)
                            self._send_json({'status': 'ok'})
                        else:
                            self.send_error(400, "Delete failed")
                    except Exception as e:
                        self.send_error(400, str(e))

                elif self.path == '/api/post/migrate':
                    try:
                        token = self._get_token()
                        user_id = verify_token(token)
                        url = data.get('url')
                        
                        self.send_response(200)
                        self.send_header('Content-Type', 'text/event-stream')
                        self.send_header('Cache-Control', 'no-cache')
                        self.send_header('Connection', 'keep-alive')
                        self.end_headers()

                        def progress_callback(msg):
                            try:
                                payload = json.dumps({'step': msg})
                                self.wfile.write(f"data: {payload}\n\n".encode('utf-8'))
                                self.wfile.flush()
                            except Exception:
                                pass

                        try:
                            cid = migrate_post_from_url(token, url, progress_callback)
                            
                            progress_callback("[*] Finalizing: Generating static pages...")
                            force_sync_post(cid, user_id)
                            
                            success_payload = json.dumps({'success': True, 'cid': cid})
                            self.wfile.write(f"data: {success_payload}\n\n".encode('utf-8'))
                        except Exception as e:
                            error_payload = json.dumps({'error': str(e)})
                            self.wfile.write(f"data: {error_payload}\n\n".encode('utf-8'))
                        
                        self.wfile.flush()
                        return

                    except Exception as e:
                        self.send_error(400, str(e))
                        return
                
                # --- 验证会话 APIs ---
                elif self.path == '/api/auth/init':
                    token = self._get_token()
                    user_id = verify_token(token)
                    platform = data.get('platform')
                    session_id = verify_manager.session_init(user_id, platform)
                    if session_id:
                        self._send_json({'session_id': session_id, 'status': 'initialized'})
                    else:
                        self.send_error(400, "Failed")
                
                elif self.path == '/api/auth/save_cookies':
                    session_id = data.get('session_id')
                    cookies = data.get('cookies', [])
                    if verify_manager.session_save_cookies(session_id, cookies):
                        self._send_json({'status': 'ok'})
                    else:
                        self.send_error(400, "Failed")
                
                elif self.path == '/api/auth/save_error':
                    session_id = data.get('session_id')
                    error_msg = data.get('error')
                    verify_manager.session_save_error(session_id, error_msg)
                    self._send_json({'status': 'ok'})
                
                elif self.path == '/api/auth/cancel':
                    session_id = data.get('session_id')
                    verify_manager.session_close(session_id)
                    self._send_json({'status': 'cancelled'})

                elif self.path == '/api/auth/unbind':
                    token = self._get_token()
                    user_id = verify_token(token)
                    platform = data.get('platform')
                    conn = create_connection()
                    dao = MySQLAuthDAO(conn)
                    dao.remove_platform_auth(user_id, platform)
                    conn.close()
                    self._send_json({'status': 'ok'})

                else:
                    self.send_error(404)
            except Exception as e:
                print(f"Server Error: {e}")
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