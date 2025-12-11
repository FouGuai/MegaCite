import re
import time
from playwright.sync_api import sync_playwright
from client.cookie_store import save_cookies, load_cookies
from verification.interface import PlatformVerifier

class CSDNVerifier(PlatformVerifier):
    def login(self) -> bool:
        print("[*] Launching browser for CSDN login...")
        try:
            with sync_playwright() as p:
                browser = p.chromium.launch(headless=False)
                context = browser.new_context()
                page = context.new_page()

                try:
                    page.goto("https://passport.csdn.net/login")
                    print("[*] Please log in within 120 seconds...")

                    # 判定标准：URL 不再包含 passport (跳转成功)
                    page.wait_for_url(lambda u: "passport.csdn.net" not in u, timeout=120000)
                    
                    # 额外跳转到首页，确保所有子域 Cookie 都已写入
                    print("[*] Syncing cookies...")
                    page.goto("https://www.csdn.net")
                    page.wait_for_load_state("networkidle")
                    
                    cookies = context.cookies()
                    if cookies:
                        save_cookies("csdn", cookies)
                        print(f"[+] Login successful! Saved {len(cookies)} cookies.")
                        return True
                    return False
                finally:
                    browser.close()
        except Exception as e:
            if "Executable doesn't exist" in str(e):
                print("[-] Error: Playwright browsers are not installed.")
                print("[-] Please run command: playwright install")
            else:
                print(f"[-] Login failed: {e}")
            return False

    def check_ownership(self, url: str) -> bool:
        cookies_list = load_cookies("csdn")
        if not cookies_list:
            print("[-] No CSDN cookies found. Run 'mc auth add csdn'.")
            return False

        # 1. 提取文章 ID
        match = re.search(r"/article/details/(\d+)", url)
        if not match:
            print("[-] Cannot extract article ID from URL.")
            return False
        article_id = match.group(1)
        
        # 2. 构造探针：编辑器 URL
        probe_url = f"https://editor.csdn.net/md/?articleId={article_id}"
        print(f"[*] Probing access (Headless): {probe_url}")
        
        try:
            with sync_playwright() as p:
                # 启动无头浏览器（后台运行）
                browser = p.chromium.launch(headless=True)
                context = browser.new_context()
                
                # 注入本地保存的 Cookie
                context.add_cookies(cookies_list)
                
                page = context.new_page()
                try:
                    # 访问编辑器
                    response = page.goto(probe_url, timeout=30000)
                    
                    # 等待重定向稳定（如果不是作者，CSDN 会重定向到首页或管理台）
                    page.wait_for_load_state("domcontentloaded")
                    time.sleep(2) 

                    final_url = page.url
                    content = page.content()

                    # 判定逻辑：
                    # 1. 如果还在 editor.csdn.net 或 mp.csdn.net (富文本编辑器)
                    # 2. 且没有出现“登录”或“无权访问”的提示
                    if "editor.csdn.net" in final_url or "mp.csdn.net" in final_url:
                        if "passport.csdn.net" not in final_url:
                            return True
                    
                    # 调试信息：如果失败，打印最终跳转到了哪里
                    # print(f"[-] Redirected to: {final_url}")
                    return False

                except Exception as e:
                    print(f"[-] Browser probe failed: {e}")
                    return False
                finally:
                    browser.close()

        except Exception as e:
            print(f"[-] Playwright error: {e}")
            return False