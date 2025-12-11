import re
import time
from playwright.sync_api import sync_playwright
from client.cookie_store import save_cookies, load_cookies
from verification.interface import PlatformVerifier

class CNBlogsVerifier(PlatformVerifier):
    def login(self) -> bool:
        print("[*] Launching browser for CNBlogs login...")
        try:
            with sync_playwright() as p:
                browser = p.chromium.launch(headless=False)
                context = browser.new_context()
                page = context.new_page()

                try:
                    # 博客园登录页
                    page.goto("https://account.cnblogs.com/signin")
                    print("[*] Please log in within 120 seconds...")

                    # 判定标准：URL 跳转回主站域名且不包含 signin
                    page.wait_for_url(lambda u: "account.cnblogs.com/signin" not in u and "cnblogs.com" in u, timeout=120000)
                    
                    # 访问一下首页确保 Cookie 完整写入
                    page.goto("https://www.cnblogs.com/")
                    time.sleep(2) 

                    cookies = context.cookies()
                    if cookies:
                        save_cookies("cnblogs", cookies)
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
        cookies_list = load_cookies("cnblogs")
        if not cookies_list:
            print("[-] No CNBlogs cookies found. Run 'mc auth add cnblogs'.")
            return False
        
        # 1. 提取 Post ID (必须提取 ID 才能进行精确匹配)
        match = re.search(r"/p/(\d+)", url)
        if not match:
            match = re.search(r"(\d+)(?:\.html)?$", url)
        
        if not match:
            print("[-] Cannot extract Post ID from URL.")
            return False
            
        post_id = match.group(1)
        print(f"[*] Verifying ownership for Post ID: {post_id}")
        
        try:
            with sync_playwright() as p:
                browser = p.chromium.launch(headless=True)
                context = browser.new_context()
                context.add_cookies(cookies_list)
                
                page = context.new_page()
                try:
                    # 直接访问文章前台页面
                    page.goto(url, timeout=30000, wait_until="domcontentloaded")
                    
                    # 【核心方案 1】检查博客园全局变量 isBlogOwner
                    # 这是博客园前端系统硬编码的变量，不受皮肤影响，最为准确
                    # 必须确保它严格为 true
                    is_owner = page.evaluate("() => { return typeof isBlogOwner !== 'undefined' && isBlogOwner === true; }")
                    
                    if is_owner:
                        return True
                        
                    # 【核心方案 2】精确检查编辑链接
                    # 严禁泛匹配 EditPosts.aspx，否则会匹配到顶部导航栏的 "新随笔"
                    # 必须匹配包含 postid={post_id} 的链接
                    # 例如: https://i.cnblogs.com/EditPosts.aspx?postid=123456
                    
                    # 构造精确的选择器
                    edit_selector = f'a[href*="postid={post_id}"]'
                    
                    if page.locator(edit_selector).count() > 0:
                        # 再次确认链接文本包含 "编辑" 或 "Edit"，防止误判其他带 ID 的链接（虽然很少见）
                        # 大部分皮肤的编辑链接文本都是 "编辑"
                        return True

                    return False

                except Exception as e:
                    print(f"[-] Browser probe failed: {e}")
                    return False
                finally:
                    browser.close()

        except Exception as e:
            print(f"[-] Playwright verification failed: {e}")
            return False