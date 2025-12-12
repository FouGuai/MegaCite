from typing import Any
import re
import pymysql.err
from dao import MySQLPostDAO, MySQLUrlMapDAO, MySQLUserDAO
from dao.factory import create_connection
from core.auth import verify_token
from core.security import generate_cid
from core.url_manager import URLManager

def _update_url_mapping(conn, cid: str):
    """内部辅助函数：计算并更新 URL 映射"""
    post_dao = MySQLPostDAO(conn)
    owner_id = post_dao.get_field(cid, "owner_id")
    title = post_dao.get_field(cid, "title")
    category = post_dao.get_field(cid, "category")
    
    if not owner_id: 
        return

    user_dao = MySQLUserDAO(conn)
    with conn.cursor() as cur:
        cur.execute("SELECT username FROM users WHERE id = %s", (owner_id,))
        row = cur.fetchone()
        if not row: return
        username = row[0]

    mgr = URLManager()
    safe_title = mgr.safe_title(title or "untitled")
    safe_cat = mgr.safe_title(category or "Default")

    # 构造新路径结构: /username/category/title.html
    url_path = f"/{username}/{safe_cat}/{safe_title}.html"

    map_dao = MySQLUrlMapDAO(conn)
    map_dao.upsert_mapping(cid, url_path)

def post_list(token: str, count: int | None = None) -> list[str]:
    verify_token(token)
    conn = create_connection()
    try:
        dao = MySQLPostDAO(conn)
        limit = count if count is not None else 100
        return dao.list_posts(offset=0, limit=limit)
    finally:
        conn.close()

def post_create(token: str) -> str:
    user_id = verify_token(token)
    new_cid = generate_cid()
    
    # 自动生成唯一默认标题: Untitled-{CID}
    default_title = f"Untitled-{new_cid}"
    default_cat = "Default"
    
    conn = create_connection()
    try:
        dao = MySQLPostDAO(conn)
        dao.create_post(owner_id=user_id, cid=new_cid, title=default_title, category=default_cat, date=None)
        
        # 立即更新映射表
        _update_url_mapping(conn, new_cid)
        
        return new_cid
    finally:
        conn.close()

def post_update(token: str, cid: str, field: str, value: str) -> bool:
    verify_token(token)
    conn = create_connection()
    try:
        dao = MySQLPostDAO(conn)
        
        try:
            # 尝试正常更新
            result = dao.update_field(cid, field, value)
        except pymysql.err.IntegrityError:
            # [冲突解决策略]
            current_title = dao.get_field(cid, "title")
            current_cat = dao.get_field(cid, "category")
            
            target_title = value if field == "title" else current_title
            target_cat = value if field == "category" else current_cat
            
            print(f"[Conflict] Collision detected for '{target_title}' in '{target_cat}'. Auto-resolving...")

            # 循环尝试生成不冲突的标题
            resolved = False
            
            while True:
                match = re.search(r" \(([1-9]\d*)\)$", target_title)
                if match:
                    n = int(match.group(1))
                    prefix = target_title[:match.start()]
                    target_title = f"{prefix} ({n+1})"
                else:
                    target_title = f"{target_title} (1)"
                
                try:
                    update_payload = {}
                    if field == "category":
                        update_payload = {"category": target_cat, "title": target_title}
                    else:
                        update_payload = {"title": target_title}
                    
                    dao.update_post_fields(cid, **update_payload)
                    resolved = True
                    print(f"[Conflict] Resolved to: '{target_title}'")
                    break
                except pymysql.err.IntegrityError:
                    continue
            
            result = resolved
        
        # 只要修改了 title 或 category，就需要重新生成 URL
        if result and field in ("title", "category"):
            _update_url_mapping(conn, cid)
                
        return result
    finally:
        conn.close()

def post_delete(token: str, cid: str) -> bool:
    user_id = verify_token(token)
    conn = create_connection()
    try:
        dao = MySQLPostDAO(conn)
        
        # [安全增强] 检查所有权
        owner_id = dao.get_field(cid, "owner_id")
        if owner_id is None:
            return False # 文章不存在
        
        if owner_id != user_id:
            raise PermissionError("You do not own this post.")
            
        return dao.delete_post(cid)
    finally:
        conn.close()

def post_get(token: str, cid: str, field: str) -> Any:
    verify_token(token)
    conn = create_connection()
    try:
        dao = MySQLPostDAO(conn)
        return dao.get_field(cid, field)
    finally:
        conn.close()

def post_search(token: str, keyword: str) -> list[str]:
    verify_token(token)
    conn = create_connection()
    try:
        dao = MySQLPostDAO(conn)
        return dao.search_posts(keyword)
    finally:
        conn.close()