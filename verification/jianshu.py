import re
import time
import json
from playwright.sync_api import sync_playwright
from client.cookie_store import save_cookies, load_cookies
from verification.interface import PlatformVerifier

class JianshuVerifier(PlatformVerifier):
    def login(self) -> bool:
        print("[*] Launching browser for Jianshu login...")
        try:
            with sync_playwright() as p:
                browser = p.chromium.launch(headless=False)
                context = browser.new_context()
                
                # 初始页面 (保持引用以维持事件循环)
                main_page = context.new_page()

                try:
                    main_page.goto("https://www.jianshu.com/sign_in")
                    print("[*] Please log in within 120 seconds...")

                    # 使用截止时间而非死循环
                    deadline = time.time() + 120
                    
                    while time.time() < deadline:
                        # 扫描上下文中的所有标签页 (包括新弹出的)
                        for page in list(context.pages):
                            try:
                                if page.is_closed():
                                    continue
                                
                                url = page.url
                                
                                # 判定标准：域名是简书，且不再是登录页，也不是空白页
                                # 排除微信回调页
                                if "jianshu.com" in url and "sign_in" not in url and "about:blank" not in url and "callback" not in url:
                                    print(f"[*] Detected login success on page: {url}")
                                    
                                    page.wait_for_timeout(3000) # 缓冲3秒确保Cookie写入

                                    cookies = context.cookies()
                                    if cookies:
                                        save_cookies("jianshu", cookies)
                                        print(f"[+] Login successful! Saved {len(cookies)} cookies.")
                                        
                                        try:
                                            page.close()
                                        except Exception:
                                            pass
                                        return True
                            except Exception:
                                pass
                        
                        main_page.wait_for_timeout(500)
                    
                    print("[-] Login timeout.")
                    return False
                finally:
                    try:
                        context.close()
                        browser.close()
                    except Exception:
                        pass

        except Exception as e:
            if "Executable doesn't exist" in str(e):
                print("[-] Error: Playwright browsers are not installed. Run 'playwright install'.")
            else:
                print(f"[-] Login failed: {e}")
            return False

    def check_ownership(self, url: str) -> bool:
        cookies_list = load_cookies("jianshu")
        if not cookies_list:
            print("[-] No Jianshu cookies found. Run 'mc auth add jianshu'.")
            return False

        print(f"[*] Verifying ownership for: {url}")
        
        try:
            with sync_playwright() as p:
                browser = p.chromium.launch(headless=True)
                # 使用真实 UA 和分辨率，减少被识别为 Bot 的概率
                context = browser.new_context(
                    user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
                    viewport={"width": 1920, "height": 1080}
                )
                context.add_cookies(cookies_list)
                
                page = context.new_page()
                try:
                    # 1. 验证登录态：尝试访问写文章页面
                    # 如果 Cookie 失效，这里会重定向到登录页
                    print("[*] Validating session...")
                    page.goto("https://www.jianshu.com/writer", timeout=20000)
                    page.wait_for_load_state("domcontentloaded")
                    
                    if "sign_in" in page.url:
                        print("[-] Cookie expired. Redirected to login page.")
                        return False
                        
                    # 2. 访问目标文章
                    print(f"[*] Accessing article...")
                    page.goto(url, timeout=30000)
                    page.wait_for_load_state("domcontentloaded")
                    page.wait_for_timeout(2000)

                    # 3. UI 判定 (最直观)
                    # 检查是否有 "编辑文章" 链接或跳转到 writer 的链接
                    if page.locator('a:has-text("编辑文章")').count() > 0:
                        return True
                    if page.locator('a[href*="/writer#/notebooks"]').count() > 0:
                        return True

                    # 4. 数据层判定 (__NEXT_DATA__)
                    # 简书现在大部分页面使用 Next.js，数据在 script 标签中
                    print("[*] Checking page data...")
                    next_data_loc = page.locator('#__NEXT_DATA__')
                    if next_data_loc.count() > 0:
                        try:
                            json_text = next_data_loc.first.inner_text()
                            data = json.loads(json_text)
                            
                            # 提取文章 ID
                            note = data.get('props', {}).get('pageProps', {}).get('note', {})
                            note_id = note.get('id')
                            
                            if note_id:
                                print(f"[*] Extracted Note ID: {note_id}. Probing API...")
                                # 调用只有作者能用的 API
                                api_url = f"https://www.jianshu.com/author/notes/{note_id}/content"
                                response = context.request.get(api_url)
                                
                                if response.status == 200:
                                    return True
                                else:
                                    print(f"[-] API probe status: {response.status}")
                        except Exception as e:
                            print(f"[-] Data parsing error: {e}")
                    else:
                        print("[-] __NEXT_DATA__ not found. Legacy page?")

                    return False

                except Exception as e:
                    print(f"[-] Verification failed: {e}")
                    return False
                finally:
                    try:
                        context.close()
                        browser.close()
                    except Exception:
                        pass

        except Exception as e:
            print(f"[-] Playwright error: {e}")
            return False