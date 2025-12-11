from datetime import date
from core.auth import verify_token
from core.post import post_create, post_update
from crawler.fetcher import fetch_html
from crawler.converter import convert_html_to_markdown
# 引入验证管理器
from verification import manager as verify_manager

def migrate_post_from_url(token: str, url: str) -> str:
    """执行迁移：验证 -> 下载 -> 转换 -> 入库"""
    
    # 1. 执行严格的所有权验证 (先于 Token 验证)
    print(f"[*] Verifying ownership for {url}...")
    if not verify_manager.verify_url_owner(url):
        raise PermissionError("Ownership verification failed. Ensure you are logged in via 'mc auth add' and own this post.")
    print(f"[+] Ownership confirmed.")

    # 2. 验证系统 Token
    verify_token(token)

    # 3. 获取源码
    print(f"[*] Fetching {url}...")
    html = fetch_html(url)
    if not html:
        raise ValueError("Failed to fetch content.")

    # 4. AI 转换
    print(f"[*] Analyzing with AI...")
    data = convert_html_to_markdown(html)

    # 5. 创建文章
    cid = post_create(token)
    
    # 6. 更新字段
    try:
        title = data.get("title", f"Imported-{cid}")
        cat = "Imported"
        desc = data.get("description", "Imported from URL")
        dt = str(date.today())
        context = data.get("context", "")

        post_update(token, cid, "title", title)
        post_update(token, cid, "category", cat)
        post_update(token, cid, "description", desc)
        post_update(token, cid, "date", dt)
        post_update(token, cid, "context", context)
        
        return cid
    except Exception as e:
        print(f"[-] Warning: Partial update failed: {e}")
        return cid