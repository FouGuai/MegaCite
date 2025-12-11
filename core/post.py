from typing import Any
import pymysql.err
from dao import MySQLPostDAO, MySQLUrlMapDAO, MySQLUserDAO
from dao.factory import create_connection
from core.auth import verify_token
from core.security import generate_cid
from core.url_manager import URLManager

def _update_url_mapping(conn, cid: str, owner_id: int, title: str | None):
    """内部辅助函数：计算并更新 URL 映射"""
    user_dao = MySQLUserDAO(conn)
    with conn.cursor() as cur:
        cur.execute("SELECT username FROM users WHERE id = %s", (owner_id,))
        row = cur.fetchone()
        if not row: return
        username = row[0]

    safe_title = URLManager().safe_title(title or "untitled")
    url_path = f"/{username}/{safe_title}.html"

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
    # CID 是唯一的，所以 Title 在用户范围内也绝对唯一
    default_title = f"Untitled-{new_cid}"
    
    conn = create_connection()
    try:
        dao = MySQLPostDAO(conn)
        dao.create_post(owner_id=user_id, cid=new_cid, title=default_title, date=None)
        
        # 立即更新映射表
        _update_url_mapping(conn, new_cid, user_id, default_title)
        
        return new_cid
    finally:
        conn.close()

def post_update(token: str, cid: str, field: str, value: str) -> bool:
    verify_token(token)
    conn = create_connection()
    try:
        dao = MySQLPostDAO(conn)
        
        try:
            result = dao.update_field(cid, field, value)
        except pymysql.err.IntegrityError:
            # 捕获违反唯一性约束 (IntegrityError)，即 Title 重复
            return False
        
        if result and field == "title":
            owner_id = dao.get_field(cid, "owner_id")
            if owner_id:
                _update_url_mapping(conn, cid, owner_id, value)
                
        return result
    finally:
        conn.close()

def post_delete(token: str, cid: str) -> bool:
    verify_token(token)
    conn = create_connection()
    try:
        dao = MySQLPostDAO(conn)
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