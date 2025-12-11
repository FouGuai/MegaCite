import markdown
from core.url_manager import URLManager
from generator.markdown_extensions import CiteReferenceExtension
from generator.content_updater import update_post_content_in_db, update_post_references_in_db

class HTMLRenderer:
    """渲染 HTML 内容"""
    
    TEMPLATE_INDEX = """<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <title>{username}'s Blog</title>
</head>
<body>
    <h1>Articles by {username}</h1>
    <hr>
    {content}
</body>
</html>
"""
    TEMPLATE_POST = """<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <title>{title}</title>
</head>
<body>
    <h1>{title}</h1>
    <p>Date: {date} | Author: {author} | Category: {category} | CID: {cid}</p>
    <hr>
    <div>
        {content}
    </div>
    <hr>
    <a href="../index.html">Back to Index</a>
</body>
</html>
"""

    def __init__(self):
        self.url_mgr = URLManager()

    def render_user_index(self, username: str, categorized_posts: dict) -> str:
        parts = []
        for category in sorted(categorized_posts.keys()):
            posts = categorized_posts[category]
            items = []
            for p in posts:
                items.append(f'<li><a href="{p["filename"]}">{p["title"]}</a></li>')
            list_html = "\n".join(items) if items else "<li>No posts.</li>"
            parts.append(f"<h2>{category}</h2><ul>{list_html}</ul>")
        return self.TEMPLATE_INDEX.format(
            username=username,
            content="\n".join(parts) or "<p>No posts found.</p>"
        )

    def render_post(self, post_data: dict, author_name: str, cid: str) -> str:
        raw_content = str(post_data.get("context", "") or "")
        found_refs = set()

        def processor_callback(old_str, new_str, target_cid):
            if target_cid: found_refs.add(target_cid)
            if old_str and new_str:
                update_post_content_in_db(cid, old_str, new_str)

        md = markdown.Markdown(extensions=[
            CiteReferenceExtension(url_mgr=self.url_mgr, db_callback=processor_callback)
        ])
        content = md.convert(raw_content)

        update_post_references_in_db(cid, found_refs)
        
        return self.TEMPLATE_POST.format(
            title=post_data.get("title", "Untitled"),
            date=post_data.get("date", ""),
            author=author_name,
            category=post_data.get("category", "default") or "default",
            cid=cid,
            content=content
        )