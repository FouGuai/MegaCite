import os
import markdown
from core.url_manager import URLManager
from generator.markdown_extensions import CiteReferenceExtension
from generator.content_updater import update_post_content_in_db, update_post_references_in_db

class HTMLRenderer:
    """渲染 HTML 内容 - VitePress 风格"""

    def __init__(self):
        self.url_mgr = URLManager()
        
        current_dir = os.path.dirname(__file__)
        project_root = os.path.dirname(current_dir)
        template_dir = os.path.join(project_root, "templates")

        with open(os.path.join(template_dir, "index.html"), "r", encoding="utf-8") as f:
            self.template_index = f.read()
    
        with open(os.path.join(template_dir, "post.html"), "r", encoding="utf-8") as f:
            self.template_post = f.read()

        home_path = os.path.join(template_dir, "home.html")
        if os.path.exists(home_path):
            with open(home_path, "r", encoding="utf-8") as f:
                self.template_home = f.read()
        else:
            self.template_home = "<h1>Welcome</h1>"

        settings_path = os.path.join(template_dir, "settings.html")
        if os.path.exists(settings_path):
            with open(settings_path, "r", encoding="utf-8") as f:
                self.template_settings = f.read()
        else:
            self.template_settings = "<h1>Settings</h1>"

    def render_landing_page(self) -> str:
        return self.template_home

    def render_settings_page(self) -> str:
        return self.template_settings
        
    def render_admin_stub(self) -> str:
        return """
        <!DOCTYPE html>
        <html>
        <head><title>Admin Dashboard</title><link href="/style.css" rel="stylesheet"></head>
        <body style="padding: 40px; text-align:center;">
            <h1>Admin Dashboard</h1>
            <p>Welcome, Admin.</p>
            <a href="/" class="action-btn brand">Back Home</a>
        </body>
        </html>
        """

    def render_user_index(self, username: str, categorized_posts: dict) -> str:
        parts = []
        for category in sorted(categorized_posts.keys()):
            posts = categorized_posts[category]
            items = []
            for p in posts:
                # [修改] 重构 post-item 结构以支持删除按钮
                # 使用 div 包装，分离链接和按钮
                item_html = f"""
                <div class="post-item-container">
                    <a href="{p['filename']}" class="post-item-link">
                        <div class="post-item-title">{p['title']}</div>
                        <div class="post-item-meta">
                            <span>{p['date']}</span>
                            <span>Read more →</span>
                        </div>
                    </a>
                    <button class="btn-delete-post" data-cid="{p['cid']}" title="删除文章" style="display:none;">
                        <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><polyline points="3 6 5 6 21 6"></polyline><path d="M19 6v14a2 2 0 0 1-2 2H7a2 2 0 0 1-2-2V6m3 0V4a2 2 0 0 1 2-2h4a2 2 0 0 1 2 2v2"></path></svg>
                    </button>
                </div>
                """
                items.append(item_html)
            
            list_html = "\n".join(items) if items else "<div class='grey-text'>暂无内容</div>"
            
            section_html = f"""
            <div class="section">
                <h3 class="post-section-title">
                    <svg xmlns="http://www.w3.org/2000/svg" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" class="feather feather-folder"><path d="M22 19a2 2 0 0 1-2 2H4a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h5l2 3h9a2 2 0 0 1 2 2z"></path></svg>
                    {category}
                </h3>
                <div class="post-list">
                    {list_html}
                </div>
            </div>
            """
            parts.append(section_html)
        
        # 将 cid 传递给 render_post 方法没有用，这里是 index 页
        # 但是我们在 loop 中已经拿到了 p['cid'] (假设 sync_user_index 传了 cid)
        # 让我们确认一下 sync_user_index 的逻辑是否传了 cid。
        # builder.py -> sync_user_index: categorized[p_cat].append({ "title": ..., "cid": p_cid ... })
        # 我需要检查 builder.py 是否添加了 cid 到 dict 中。
        # 现在的 builder.py 代码中：
        # categorized[p_cat].append({ "title": p_title, "filename": link_href, "date": str(p_date) })
        # 缺少 cid。我必须修改 builder.py 或者在这里假设它有。
        # 由于我不能一次改所有文件，我会在 builder.py 中添加 cid。
        # 既然 builder.py 也在上下文中，我可以在思考中确认，或者我现在就修改 builder.py。
        # 看起来 builder.py 是在上一次上传的文件列表中。
        # 我将需要在本次回复中包含 builder.py 的修改。
        
        return self.template_index.format(
            username=username,
            content="\n".join(parts) or "<p style='text-align:center;color:var(--vp-c-text-3)'>空空如也</p>"
        )

    def render_post(self, post_data: dict, author_name: str, cid: str) -> str:
        
        raw_content = str(post_data.get("context", "") or "")
        desc_text = post_data.get("description", "")
        
        if desc_text and desc_text.strip():
            description_html = f"""
            <div class="custom-block info">
                <p class="custom-block-title">摘要</p>
                <p>{desc_text}</p>
            </div>
            """
        else:
            description_html = ""
        
        found_refs = set()

        def processor_callback(old_str, new_str, target_cid):
            if target_cid: found_refs.add(target_cid)
            if old_str and new_str:
                update_post_content_in_db(cid, old_str, new_str)

        md = markdown.Markdown(extensions=[
            'fenced_code', 'tables', 'toc',
            CiteReferenceExtension(url_mgr=self.url_mgr, db_callback=processor_callback)
        ])
        content = md.convert(raw_content)

        update_post_references_in_db(cid, found_refs)
        
        return self.template_post.format(
            title=post_data.get("title", "Untitled"),
            date=post_data.get("date", ""),
            author=author_name,
            category=post_data.get("category", "default") or "default",
            cid=cid,
            content=content,
            description_block=description_html
        )