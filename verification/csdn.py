import re
import time
import base64
from playwright.sync_api import sync_playwright
from client.cookie_store import save_cookies, load_cookies
from verification.interface import PlatformVerifier

class CSDNVerifier(PlatformVerifier):
    def __init__(self):
        self.playwright = None
        self.browser = None
        self.context = None
        self.page = None
        self._is_session_active = False

    def login(self) -> bool:
        print("[-] Please use the Web UI for CSDN login.")
        return False

    def start_login_session(self) -> None:
        print("[*] Starting CSDN headless session...")
        self.playwright = sync_playwright().start()
        self.browser = self.playwright.chromium.launch(headless=True)
        self.context = self.browser.new_context(viewport={'width': 1024, 'height': 768})
        self.page = self.context.new_page()
        
        try:
            self.page.goto("https://passport.csdn.net/login")
            self.page.wait_for_load_state("domcontentloaded")
            self._is_session_active = True
        except Exception as e:
            print(f"[-] Failed to load page: {e}")
            self.close_session()
            raise e

    def get_login_screenshot(self) -> str | None:
        if not self._is_session_active or not self.page: return None
        try:
            # 截取全屏以保证坐标对应准确
            png = self.page.screenshot()
            return base64.b64encode(png).decode("utf-8")
        except Exception:
            return None

    def handle_interaction(self, action: str, payload: dict) -> None:
        if not self._is_session_active or not self.page: return
        
        if action == 'click':
            # 坐标映射：前端图片尺寸 -> 后端视口尺寸
            try:
                view_size = self.page.viewport_size
                vw, vh = view_size['width'], view_size['height']
                
                img_w = payload.get('width', 1)
                img_h = payload.get('height', 1)
                
                # 防止除以零
                if img_w <= 0 or img_h <= 0: return

                req_x = payload.get('x', 0)
                req_y = payload.get('y', 0)

                target_x = req_x * (vw / img_w)
                target_y = req_y * (vh / img_h)
                
                print(f"[*] Click interaction: ({req_x}, {req_y}) -> ({target_x}, {target_y})")
                self.page.mouse.click(target_x, target_y)
            except Exception as e:
                print(f"[-] Interaction failed: {e}")

    def check_login_status(self) -> bool:
        if not self._is_session_active or not self.page: return False
        try:
            if "passport.csdn.net" not in self.page.url:
                print("[*] Login detected, extracting cookies...")
                self.page.goto("https://www.csdn.net")
                self.page.wait_for_load_state("networkidle")
                cookies = self.context.cookies()
                if cookies:
                    save_cookies("csdn", cookies)
                    print(f"[+] Saved {len(cookies)} cookies.")
                    return True
        except Exception:
            pass
        return False

    def close_session(self) -> None:
        self._is_session_active = False
        if self.page: self.page.close()
        if self.context: self.context.close()
        if self.browser: self.browser.close()
        if self.playwright: self.playwright.stop()
        self.page = None
        self.context = None
        self.browser = None
        self.playwright = None

    def check_ownership(self, url: str) -> bool:
        cookies = load_cookies("csdn")
        if not cookies: return False
        match = re.search(r"/article/details/(\d+)", url)
        if not match: return False
        article_id = match.group(1)
        probe = f"https://editor.csdn.net/md/?articleId={article_id}"
        
        try:
            with sync_playwright() as p:
                browser = p.chromium.launch(headless=True)
                context = browser.new_context()
                context.add_cookies(cookies)
                page = context.new_page()
                page.goto(probe, timeout=30000)
                page.wait_for_load_state("domcontentloaded")
                time.sleep(2)
                if ("editor.csdn.net" in page.url or "mp.csdn.net" in page.url) and "passport" not in page.url:
                    return True
                return False
        except Exception:
            return False