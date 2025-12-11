import os
import shutil
from collections import defaultdict
from core.url_manager import URLManager
from generator.renderer import HTMLRenderer
from dao.factory import create_connection

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
            
        # src_css = os.path.join(os.path.dirname(__file__), "style.css")
        current_dir = os.path.dirname(__file__)
        project_root = os.path.dirname(current_dir)
        src_css = os.path.join(project_root, "templates", "style.css")
        dst_css = os.path.join(self.base_dir, "style.css")
        
        if os.path.exists(src_css):
            shutil.copy(src_css, dst_css)
        else:
            print(f"[Warning] Source CSS not found: {src_css}")

    def _get_abs_path(self, rel_path: str) -> str:
        return os.path.join(self.base_dir, rel_path)

    def remove_post_file_by_meta(self, username: str, category: str, title: str):
        """
        [新增] 根据元数据计算旧路径并删除文件。
        用于在 URL 结构变更（重命名/移动分类）时清理旧文件。
        """
        s_cat = self.url_mgr.safe_title(category or "default")
        s_title = self.url_mgr.safe_title(title or "untitled")
        # 路径结构必须与 register_mapping 保持一致
        rel_prefix = f"{username}/{s_cat}/{s_title}"
        full_path = self._get_abs_path(rel_prefix + ".html")
        
        if os.path.exists(full_path):
            os.remove(full_path)
            print(f"[Gen] Cleaned old file: {full_path}")
            
            # 尝试清理空目录，保持目录整洁
            try:
                parent_dir = os.path.dirname(full_path)
                if not os.listdir(parent_dir):
                    os.rmdir(parent_dir)
            except OSError:
                pass

    def sync_post_file(self, post_data: dict, author_name: str):
        cid = post_data["cid"]
        title = post_data["title"] or "untitled"
        category = post_data.get("category") or "default"
        
        rel_prefix = self.url_mgr.register_mapping(cid, author_name, category, title)
        filename = rel_prefix + ".html"
        full_path = self._get_abs_path(filename)
        
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
                # 修改：增加了 date 字段的查询，且保持 ORDER BY date DESC
                cur.execute("SELECT cid, title, category, date FROM posts WHERE owner_id=%s ORDER BY date DESC", (user_id,))
                rows = cur.fetchall()

            categorized = defaultdict(list)
            for r in rows:
                p_cid, p_title = r[0], r[1] or "untitled"
                p_cat = r[2] or "default"
                p_date = r[3] # 获取日期
                
                rel_prefix = self.url_mgr.register_mapping(p_cid, username, p_cat, p_title)
                
                link_href = f"{self.url_mgr.safe_title(p_cat)}/{os.path.basename(rel_prefix)}.html"
                
                categorized[p_cat].append({
                    "title": p_title, 
                    "filename": link_href,
                    "date": str(p_date) # 存入日期
                })
            
            html = self.renderer.render_user_index(username, categorized)
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