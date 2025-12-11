import time
from playwright.sync_api import sync_playwright
from client.cookie_store import save_cookies, load_cookies
from verification.interface import PlatformVerifier

class YuqueVerifier(PlatformVerifier):
    def login(self) -> bool:
        print("[*] Launching browser for Yuque login...")
        try:
            with sync_playwright() as p:
                browser = p.chromium.launch(headless=False)
                context = browser.new_context()
                page = context.new_page()

                try:
                    page.goto("https://www.yuque.com/login")
                    print("[*] Please log in within 120 seconds...")

                    # 判定标准：URL 跳转至 dashboard 或 个人主页 (不包含 login)
                    page.wait_for_url(lambda u: "login" not in u and "yuque.com" in u, timeout=120000)
                    
                    # 等待页面完全加载，确保 Cookie 写入
                    page.wait_for_load_state("networkidle")
                    time.sleep(2)

                    cookies = context.cookies()
                    if cookies:
                        save_cookies("yuque", cookies)
                        print(f"[+] Login successful! Saved {len(cookies)} cookies.")
                        return True
                    return False
                finally:
                    browser.close()
        except Exception as e:
            if "Executable doesn't exist" in str(e):
                print("[-] Error: Playwright browsers are not installed. Run 'playwright install'.")
            else:
                print(f"[-] Login failed: {e}")
            return False

    def check_ownership(self, url: str) -> bool:
        cookies_list = load_cookies("yuque")
        if not cookies_list:
            print("[-] No Yuque cookies found. Run 'mc auth add yuque'.")
            return False

        print(f"[*] Verifying ownership for: {url}")
        
        try:
            with sync_playwright() as p:
                browser = p.chromium.launch(headless=True)
                context = browser.new_context(
                    user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
                    viewport={"width": 1920, "height": 1080}
                )
                context.add_cookies(cookies_list)
                
                page = context.new_page()
                try:
                    page.goto(url, timeout=30000)
                    page.wait_for_load_state("domcontentloaded")
                    page.wait_for_timeout(2000)

                    # 策略：检查页面是否存在只有作者可见的 "编辑" 按钮
                    # 语雀的 DOM 结构较复杂，通常会有 "编辑" 文本的按钮或链接
                    if page.locator('button:has-text("编辑")').count() > 0 or \
                       page.locator('a:has-text("编辑")').count() > 0 or \
                       page.locator('[aria-label="编辑"]').count() > 0:
                        return True
                    
                    return False

                except Exception as e:
                    print(f"[-] Verification failed: {e}")
                    return False
                finally:
                    browser.close()

        except Exception as e:
            print(f"[-] Playwright error: {e}")
            return False