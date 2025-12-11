import markdown
from markdown.inlinepatterns import InlineProcessor, AutolinkInlineProcessor
from markdown.extensions import Extension
from xml.etree import ElementTree
from core.url_manager import URLManager
from core.config import SERVER_CONFIG
from dao.factory import create_connection
from dao.post_dao import MySQLPostDAO
from dao.reference_dao import MySQLPostReferenceDAO

# 匹配 [text](url)
LINK_RE = r'\[([^\]]+)\]\(([^)]+)\)'
# 匹配 <http://...>
AUTOLINK_RE = r'<((?:http|https):[^>]+)>'
# 内部 CID 协议头
CID_SCHEME = "http://megacite.cid/"

class CiteLinkProcessor(InlineProcessor):
    """
    处理 [text](url)
    目标格式: [text](http://megacite.cid/<cid>)
    """
    def __init__(self, pattern, md, url_mgr, db_callback):
        super().__init__(pattern, md)
        self.url_mgr = url_mgr
        self.db_callback = db_callback

    def handleMatch(self, m, data):
        text = m.group(1)
        href = m.group(2)
        
        el = ElementTree.Element("a")
        el.text = text

        target_cid = None

        # 1. 识别内部引用 http://megacite.cid/<cid>
        if href.startswith(CID_SCHEME):
            target_cid = href[len(CID_SCHEME):]
        
        # 2. 识别外部链接并尝试转换
        else:
            target_cid = self.url_mgr.get_cid_from_external_url(href)
            if target_cid:
                # [DB Write] [text](url) -> [text](http://megacite.cid/<cid>)
                old_str = m.group(0)
                new_str = f"[{text}]({CID_SCHEME}{target_cid})"
                self.db_callback(old_str, new_str, target_cid)

        # 渲染逻辑
        if target_cid:
            # 记录引用 (如果是步骤1识别出的，需要手动触发引用记录，不传old/new_str代表不修改文本)
            if href.startswith(CID_SCHEME):
                self.db_callback(None, None, target_cid)

            real_path = self.url_mgr.get_url_by_cid(target_cid)
            el.set("href", real_path if real_path else "#unknown-cid")
            return el, m.start(0), m.end(0)

        # 3. 普通链接
        el.set("href", href)
        return el, m.start(0), m.end(0)

class CiteAutoLinkProcessor(AutolinkInlineProcessor):
    """
    处理 <http://...>
    目标格式: <http://megacite.cid/<cid>>
    """
    def __init__(self, pattern, md, url_mgr, db_callback):
        super().__init__(pattern, md)
        self.url_mgr = url_mgr
        self.db_callback = db_callback

    def _get_full_display_url(self, rel_path):
        """将相对路径转换为完整的 http://host:port/... 用于显示"""
        if not rel_path: return ""
        host = SERVER_CONFIG["host"]
        port = SERVER_CONFIG["port"]
        return f"http://{host}:{port}{rel_path}"

    def handleMatch(self, m, data):
        href = m.group(1) # http://... or http://megacite.cid/...
        
        el = ElementTree.Element("a")
        target_cid = None

        # 1. 识别内部引用
        if href.startswith(CID_SCHEME):
            target_cid = href[len(CID_SCHEME):]
        
        # 2. 识别外部链接并尝试转换
        else:
            target_cid = self.url_mgr.get_cid_from_external_url(href)
            if target_cid:
                # [DB Write] <url> -> <http://megacite.cid/<cid>>
                # 保持尖括号 Autolink 结构
                old_str = m.group(0)
                new_str = f"<{CID_SCHEME}{target_cid}>"
                self.db_callback(old_str, new_str, target_cid)

        if target_cid:
            if href.startswith(CID_SCHEME):
                self.db_callback(None, None, target_cid)

            real_path = self.url_mgr.get_url_by_cid(target_cid)
            if real_path:
                el.set("href", real_path)
                # [Display Fix] 即使数据库存的是 megacite.cid，显示给用户看时要还原成 http://localhost...
                el.text = self._get_full_display_url(real_path)
            else:
                el.set("href", "#unknown-cid")
                el.text = href
            
            return el, m.start(0), m.end(0)
        
        # 普通 Autolink
        return super().handleMatch(m, data)

class CiteReferenceExtension(Extension):
    def __init__(self, **kwargs):
        self.url_mgr = kwargs.pop('url_mgr')
        self.db_callback = kwargs.pop('db_callback')
        super().__init__(**kwargs)

    def extendMarkdown(self, md):
        # 优先级 165 (Backtick 175 > My 165 > Std 160)
        md.inlinePatterns.register(
            CiteLinkProcessor(LINK_RE, md, self.url_mgr, self.db_callback),
            'cite_link', 165
        )
        md.inlinePatterns.register(
            CiteAutoLinkProcessor(AUTOLINK_RE, md, self.url_mgr, self.db_callback),
            'cite_autolink', 165
        )

class HTMLRenderer:
    
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

    def _update_post_content_in_db(self, post_cid: str, old_str: str, new_str: str):
        conn = create_connection()
        try:
            dao = MySQLPostDAO(conn)
            current_context = dao.get_field(post_cid, "context") or ""
            new_context = current_context.replace(old_str, new_str)
            if new_context != current_context:
                dao.update_field(post_cid, "context", new_context)
                print(f"[Renderer] DB Content Updated: {old_str} -> {new_str}")
        finally:
            conn.close()

    def _update_post_references_in_db(self, post_cid: str, refs: set):
        conn = create_connection()
        try:
            ref_dao = MySQLPostReferenceDAO(conn)
            ref_dao.update_references(post_cid, refs)
        finally:
            conn.close()

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
                self._update_post_content_in_db(cid, old_str, new_str)

        md = markdown.Markdown(extensions=[
            CiteReferenceExtension(url_mgr=self.url_mgr, db_callback=processor_callback)
        ])
        content = md.convert(raw_content)

        self._update_post_references_in_db(cid, found_refs)
        
        return self.TEMPLATE_POST.format(
            title=post_data.get("title", "Untitled"),
            date=post_data.get("date", ""),
            author=author_name,
            category=post_data.get("catagory", "default") or "default",
            cid=cid,
            content=content
        )