import re
import time
import base64
from playwright.sync_api import sync_playwright
from client.cookie_store import save_cookies, load_cookies
from verification.interface import PlatformVerifier

class CNBlogsVerifier(PlatformVerifier):
    def __init__(self):
        self.playwright = None
        self.browser = None
        self.context = None
        self.page = None
        self._is_session_active = False

    def login(self) -> bool:
        return False

    def start_login_session(self) -> None:
        print("[*] Starting CNBlogs headless session...")
        self.playwright = sync_playwright().start()
        self.browser = self.playwright.chromium.launch(headless=True)
        self.context = self.browser.new_context(viewport={'width': 1024, 'height': 768})
        self.page = self.context.new_page()
        
        try:
            self.page.goto("https://account.cnblogs.com/signin")
            self.page.wait_for_load_state("domcontentloaded")
            self._is_session_active = True
        except Exception as e:
            self.close_session()
            raise e

    def get_login_screenshot(self) -> str | None:
        if not self._is_session_active or not self.page: return None
        try:
            png = self.page.screenshot()
            return base64.b64encode(png).decode("utf-8")
        except Exception:
            return None

    def handle_interaction(self, action: str, payload: dict) -> None:
        if not self._is_session_active or not self.page: return
        if action == 'click':
            try:
                view_size = self.page.viewport_size
                img_w = payload.get('width', 1)
                img_h = payload.get('height', 1)
                target_x = payload.get('x', 0) * (view_size['width'] / img_w)
                target_y = payload.get('y', 0) * (view_size['height'] / img_h)
                self.page.mouse.click(target_x, target_y)
            except Exception:
                pass

    def check_login_status(self) -> bool:
        if not self._is_session_active or not self.page: return False
        try:
            if "signin" not in self.page.url and "cnblogs.com" in self.page.url:
                cookies = self.context.cookies()
                if any(c['name'] == '.CNBlogsCookie' for c in cookies):
                    save_cookies("cnblogs", cookies)
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
        cookies = load_cookies("cnblogs")
        if not cookies: return False
        match = re.search(r"/p/(\d+)", url)
        if not match: match = re.search(r"(\d+)(?:\.html)?$", url)
        if not match: return False
        
        try:
            with sync_playwright() as p:
                browser = p.chromium.launch(headless=True)
                context = browser.new_context()
                context.add_cookies(cookies)
                page = context.new_page()
                page.goto(url, timeout=30000)
                is_owner = page.evaluate("() => { return typeof isBlogOwner !== 'undefined' && isBlogOwner === true; }")
                if is_owner: return True
                return False
        except Exception:
            return False