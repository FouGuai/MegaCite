from datetime import date
from core.auth import verify_token
from core.post import post_create, post_update
from crawler.fetcher import fetch_html
from crawler.ai_converter import convert_html_to_markdown

def migrate_post_from_url(token: str, url: str) -> str:
    """执行迁移：下载 -> 转换 -> 入库"""
    # 1. 验证权限
    verify_token(token)

    # 2. 获取源码
    print(f"[*] Fetching {url}...")
    html = fetch_html(url)

    # 3. AI 转换
    print(f"[*] Analyzing with AI...")
    data = convert_html_to_markdown(html)

    # 4. 创建文章
    cid = post_create(token)
    
    # 5. 更新字段
    try:
        # 按照需求：不让 AI 分析 category 和 date，使用默认值
        title = data.get("title", f"Imported-{cid}")
        cat = "Imported"  # 固定默认分类
        desc = data.get("description", "Imported from URL")
        dt = str(date.today()) # 使用当前日期
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