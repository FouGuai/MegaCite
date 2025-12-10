import os
from core.url_manager import URLManager
from services.renderer import HTMLRenderer
from services.db import create_connection

class StaticSiteGenerator:
    """
    生成静态文件到 public/ 目录。
    """
    
    def __init__(self, base_dir="public"):
        self.base_dir = base_dir
        self.url_mgr = URLManager()
        self.renderer = HTMLRenderer()

    def init_output_dir(self):
        if not os.path.exists(self.base_dir):
            os.makedirs(self.base_dir)

    def _get_abs_path(self, rel_path: str) -> str:
        return os.path.join(self.base_dir, rel_path)

    def sync_post_file(self, post_data: dict, author_name: str):
        cid = post_data["cid"]
        title = post_data["title"] or "untitled"
        
        # 1. 获取路径前缀 (username/Title-With-Hyphens)
        rel_prefix = self.url_mgr.register_mapping(cid, author_name, title)
        
        # 2. 拼接 .html 后缀作为物理文件名
        filename = rel_prefix + ".html"
        full_path = self._get_abs_path(filename)
        
        # 3. 写入文件
        os.makedirs(os.path.dirname(full_path), exist_ok=True)
        html = self.renderer.render_post(post_data, author_name, cid)
        
        with open(full_path, "w", encoding="utf-8") as f:
            f.write(html)
        
        print(f"[Gen] Generated: {full_path}")

    def sync_user_index(self, user_id: int):
        conn = create_connection()
        try:
            with conn.cursor() as cur:
                cur.execute("SELECT username FROM users WHERE id=%s", (user_id,))
                row = cur.fetchone()
                if not row: return
                username = row[0]

            with conn.cursor() as cur:
                cur.execute("SELECT cid, title FROM posts WHERE owner_id=%s ORDER BY date DESC", (user_id,))
                rows = cur.fetchall()

            post_list = []
            for r in rows:
                p_cid, p_title = r[0], r[1] or "untitled"
                
                # 获取路径前缀
                rel_prefix = self.url_mgr.register_mapping(p_cid, username, p_title)
                
                # 文件名必须包含 .html
                file_name = os.path.basename(rel_prefix) + ".html"
                post_list.append({"title": p_title, "filename": file_name})
            
            html = self.renderer.render_user_index(username, post_list)
            index_path = self._get_abs_path(f"{username}/index.html")
            
            os.makedirs(os.path.dirname(index_path), exist_ok=True)
            with open(index_path, "w", encoding="utf-8") as f:
                f.write(html)
            
            print(f"[Gen] Index Updated: {index_path}")

        finally:
            conn.close()

    def remove_post_file(self, cid: str):
        rel_prefix = self.url_mgr.remove_mapping(cid)
        if rel_prefix:
            full_path = self._get_abs_path(rel_prefix + ".html")
            if os.path.exists(full_path):
                os.remove(full_path)
                print(f"[Gen] Deleted: {full_path}")