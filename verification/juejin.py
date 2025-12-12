import re
import time
from playwright.sync_api import sync_playwright
from client.cookie_store import save_cookies, load_cookies
from verification.interface import PlatformVerifier

class JuejinVerifier(PlatformVerifier):
    def login(self) -> bool:
        print("[*] Launching browser for Juejin login...")
        try:
            with sync_playwright() as p:
                browser = p.chromium.launch(headless=False)
                context = browser.new_context()
                
                # 初始页面
                main_page = context.new_page()

                try:
                    main_page.goto("https://juejin.cn/login")
                    print("[*] Please log in within 120 seconds...")

                    deadline = time.time() + 120
                    
                    while time.time() < deadline:
                        for page in list(context.pages):
                            try:
                                if page.is_closed():
                                    continue
                                
                                url = page.url
                                
                                # 判定标准：掘金域名，且 Cookie 中包含 sessionid
                                if "juejin.cn" in url and "login" not in url:
                                    cookies = context.cookies()
                                    has_session = any(c['name'] == 'sessionid' for c in cookies)
                                    
                                    if has_session:
                                        print(f"[*] Detected login success on page: {url}")
                                        page.wait_for_timeout(2000) # 等待 Cookie 写全
                                        
                                        cookies = context.cookies()
                                        save_cookies("juejin", cookies)
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
        cookies_list = load_cookies("juejin")
        if not cookies_list:
            print("[-] No Juejin cookies found. Run 'mc auth add juejin'.")
            return False

        print(f"[*] Verifying ownership for: {url}")
        
        try:
            with sync_playwright() as p:
                browser = p.chromium.launch(headless=True)
                # 使用真实 UA，防止被拦截
                context = browser.new_context(
                    user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
                    viewport={"width": 1920, "height": 1080}
                )
                context.add_cookies(cookies_list)
                
                page = context.new_page()
                try:
                    # 1. 访问文章页
                    page.goto(url, timeout=30000, wait_until="domcontentloaded")
                    page.wait_for_timeout(2000) # 等待 hydration
                    
                    # 2. 检查 Cookie 是否失效 (检测右上角是否显示“登录”)
                    # 掘金未登录时右上角会有“登录 | 注册”按钮
                    if page.locator(".login-button").is_visible():
                        print("[-] Cookie expired (Login button detected).")
                        return False

                    # 3. 【核心策略】数据比对法
                    # 从 window.__NUXT__ 提取当前登录用户 ID 和 文章作者 ID
                    
                    ids = page.evaluate("""() => {
                        try {
                            // 尝试从 Nuxt 状态获取
                            if (window.__NUXT__ && window.__NUXT__.state) {
                                const state = window.__NUXT__.state;
                                
                                // 获取当前登录用户 ID
                                let currentUserId = null;
                                if (state.user && state.user.authUser) {
                                    currentUserId = state.user.authUser.user_id;
                                } else if (state.auth && state.auth.user) {
                                    // 兼容不同版本的 store 结构
                                    currentUserId = state.auth.user.user_id;
                                }
                                
                                // 获取文章作者 ID
                                let authorId = null;
                                // 路径1: state.view.column.entry (旧版/专栏)
                                if (state.view && state.view.column && state.view.column.entry) {
                                    authorId = state.view.column.entry.author_user_info.user_id;
                                }
                                // 路径2: state.view.content (新版)
                                else if (state.view && state.view.content) {
                                     authorId = state.view.content.author_user_info.user_id;
                                }
                                
                                return { current: currentUserId, author: authorId, source: 'nuxt' };
                            }
                        } catch (e) {}
                        
                        // 备选 DOM 提取方案
                        try {
                            // 提取头像链接中的 ID
                            // 当前用户头像 (右上角)
                            const avatarLink = document.querySelector('.avatar-wrapper a[href^="/user/"]');
                            const current = avatarLink ? avatarLink.getAttribute('href').split('/user/')[1] : null;
                            
                            // 文章作者头像
                            const authorLink = document.querySelector('.author-info-box a[href^="/user/"]');
                            const author = authorLink ? authorLink.getAttribute('href').split('/user/')[1] : null;
                            
                            return { current: current, author: author, source: 'dom' };
                        } catch(e) {
                            return { error: e.toString() };
                        }
                    }""")
                    
                    current_uid = str(ids.get('current', '')).strip()
                    author_uid = str(ids.get('author', '')).strip()
                    
                    print(f"[*] Identity Check: LoginUser={current_uid}, Author={author_uid} (Source: {ids.get('source')})")
                    
                    if current_uid and author_uid and current_uid != 'None' and author_uid != 'None':
                        if current_uid == author_uid:
                            return True
                        else:
                            print(f"[-] Ownership Mismatch: {current_uid} != {author_uid}")
                            return False

                    # 4. 【兜底策略】UI 特征检测
                    # 只有作者能看到的 "编辑" 按钮
                    if page.locator(".edit-btn").is_visible() or \
                       page.locator("a:has-text('编辑')").count() > 0:
                        return True

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