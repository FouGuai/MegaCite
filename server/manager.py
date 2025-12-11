import socketserver
import http.server
import os
import threading
import json
from generator.builder import StaticSiteGenerator
from generator.watcher import DBWatcher
from dao.factory import create_connection
from core.auth import user_login, user_register, change_password
from verification import manager as verify_manager

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
                        self.send_error(400, "Start failed. check console.")
                
                elif self.path == '/api/auth/interact':
                    # 转发前端的点击/输入事件
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

        def do_GET(self):
            if self.path == '/api/auth/screenshot':
                b64 = verify_manager.session_get_screenshot()
                self._send_json({'image': b64})
            elif self.path == '/api/auth/status':
                is_success = verify_manager.session_check_status()
                self._send_json({'status': 'success' if is_success else 'waiting'})
            else:
                super().do_GET()

        def _send_json(self, data):
            self.send_response(200)
            self.send_header('Content-type', 'application/json')
            self.end_headers()
            self.wfile.write(json.dumps(data).encode())

    print(f"[+] Server started on port {port}.")
    try:
        with ReuseAddrTCPServer(("0.0.0.0", port), Handler) as httpd:
            httpd.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        watcher.stop()
        if os.path.exists(PID_FILE): os.remove(PID_FILE)