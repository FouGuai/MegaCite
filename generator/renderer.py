import os
import markdown
from core.url_manager import URLManager
from generator.markdown_extensions import CiteReferenceExtension
from generator.content_updater import update_post_content_in_db, update_post_references_in_db

class HTMLRenderer:
    """渲染 HTML 内容"""

    def __init__(self):
        self.url_mgr = URLManager()
        
        # base_dir = os.path.dirname(__file__)
                
        # with open(os.path.join(base_dir, "index.html"), "r", encoding="utf-8") as f:
        #     self.template_index = f.read()
            
        # with open(os.path.join(base_dir, "post.html"), "r", encoding="utf-8") as f:
        #     self.template_post = f.read()

        current_dir = os.path.dirname(__file__)
        project_root = os.path.dirname(current_dir)
        template_dir = os.path.join(project_root, "templates")

        with open(os.path.join(template_dir, "index.html"), "r", encoding="utf-8") as f:
            self.template_index = f.read()
    
        with open(os.path.join(template_dir, "post.html"), "r", encoding="utf-8") as f:
            self.template_post = f.read()

    def render_user_index(self, username: str, categorized_posts: dict) -> str:
        parts = []
        for category in sorted(categorized_posts.keys()):
            posts = categorized_posts[category]
            items = []
            for p in posts:
                items.append(f'<li><span class="post-date">{p["date"]}</span><a href="{p["filename"]}">{p["title"]}</a></li>')
            list_html = "\n".join(items) if items else "<li class='empty'>No posts.</li>"
            parts.append(f'<section class="category-section"><h2>{category}</h2><ul class="post-list">{list_html}</ul></section>')
        
        return self.template_index.format(
            username=username,
            content="\n".join(parts) or "<p class='empty'>No posts found.</p>"
        )

    def render_post(self, post_data: dict, author_name: str, cid: str) -> str:
        
        raw_content = str(post_data.get("context", "") or "")
        
        desc_text = post_data.get("description", "")
        
        if desc_text and desc_text.strip():
            description_html = f'<blockquote class="description">{desc_text}</blockquote>'
        else:
            description_html = ""
        
        found_refs = set()

        def processor_callback(old_str, new_str, target_cid):
            if target_cid: found_refs.add(target_cid)
            if old_str and new_str:
                update_post_content_in_db(cid, old_str, new_str)

        md = markdown.Markdown(extensions=[
            'fenced_code', 'tables',
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