import os
import markdown
from core.url_manager import URLManager
from generator.markdown_extensions import CiteReferenceExtension
from generator.content_updater import update_post_content_in_db, update_post_references_in_db

class HTMLRenderer:
    """渲染 HTML 内容"""

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

    def render_landing_page(self) -> str:
        return self.template_home

    def render_user_index(self, username: str, categorized_posts: dict) -> str:
        parts = []
        for category in sorted(categorized_posts.keys()):
            posts = categorized_posts[category]
            items = []
            for p in posts:
                # 使用 Materialize 的 Collection 样式
                item_html = f"""
                <a href="{p['filename']}" class="collection-item avatar waves-effect">
                    <i class="material-icons circle blue lighten-3">article</i>
                    <span class="title black-text fw-500">{p['title']}</span>
                    <p class="grey-text small-text">{p['date']}</p>
                    <i class="material-icons secondary-content grey-text">arrow_forward</i>
                </a>
                """
                items.append(item_html)
            
            list_html = "\n".join(items) if items else "<div class='p-3 grey-text'>暂无内容</div>"
            
            # 分类块
            section_html = f"""
            <div class="section">
                <h5 class="category-title blue-text text-darken-2">
                    <i class="material-icons left">folder</i>{category}
                </h5>
                <div class="collection z-depth-1 hoverable border-radius-8">
                    {list_html}
                </div>
            </div>
            """
            parts.append(section_html)
        
        return self.template_index.format(
            username=username,
            content="\n".join(parts) or "<p class='center-align flow-text grey-text'>空空如也</p>"
        )

    def render_post(self, post_data: dict, author_name: str, cid: str) -> str:
        
        raw_content = str(post_data.get("context", "") or "")
        desc_text = post_data.get("description", "")
        
        # 描述块改为 Materialize 的 info card
        if desc_text and desc_text.strip():
            description_html = f"""
            <div class="card-panel blue lighten-5 z-depth-0">
                <span class="blue-text text-darken-3">
                    <i class="material-icons left tiny">info_outline</i>{desc_text}
                </span>
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